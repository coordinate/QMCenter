import psutil
import struct
import crcmod
import gdal
import pyproj
import numpy as np
import cv2
import re
import json

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication
from plyfile import PlyData, PlyElement

_ = lambda x: x
_projections = {}


def utm_zone(coordinates):  # coordinates = (longitude, latitude)
    # if 56 <= coordinates[0] < 64 and 3 <= coordinates[1] < 12:
    #     return 32
    # if 72 <= coordinates[0] < 84 and 0 <= coordinates[1] < 42:
    #     if coordinates[1] < 9:
    #         return 31
    #     elif coordinates[1] < 21:
    #         return 33
    #     elif coordinates[1] < 33:
    #         return 35
    #     return 37
    return int((coordinates[0] + 180) / 6) + 1


def letter(coordinates):
    return 'CDEFGHJKLMNPQRSTUVWXX'[int((coordinates[1] + 80) / 8)]


def project(coordinates, zone=None):  # coordinates = (longitude, latitude)
    if not zone:
        zone = utm_zone(coordinates)
    l = 'N' if coordinates[1] > 0 else 'S'
    # print(zone, l)
    if zone not in _projections:
        _projections[zone] = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84')
    x, y = _projections[zone](coordinates[0], coordinates[1])
    if y < 0:
        y += 10000000
    return x, y, zone, l


def project_array(x, y, srcp='latlong', dstp='utm', zone=None):
    """
    Project a numpy (n,2) array in projection srcp to projection dstp
    Returns a numpy (n,2) array.
    """
    if not zone:
        zone = utm_zone((x[0], y[0]))
    l = 'N' if y[0] > 0 else 'S'
    p1 = pyproj.Proj(proj=srcp, datum='WGS84')
    p2 = pyproj.Proj(proj=dstp, zone=zone, ellps='WGS84')
    fx, fy = pyproj.transform(p1, p2, x, y)
    # Re-create (n,2) coordinates
    return fx, fy, zone, l


def unproject(z, l, x, y):
    if z not in _projections:
        _projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
    if l < 'N':
        y -= 10000000
    lng, lat = _projections[z](x, y, inverse=True)
    return lng, lat


def magnet_color(magnet, min_m=None, max_m=None):
    if not min_m and not max_m:
        min_m = np.amin(magnet)
        max_m = np.amax(magnet)
    delta = max_m - min_m
    if delta:
        colors = np.array(((magnet-min_m)/delta)*255)
        colors[colors > 255] = 255
        colors[colors < 0] = 0
        colors = colors.astype('uint8')
    else:
        colors = np.repeat(0.5*255, len(magnet)).astype('uint8')
    lut = np.empty(shape=(256, 3), dtype="uint8")
    cmap = (
        (0, (0, 0, 255)),
        (0.2, (128, 128, 255)),
        (0.5, (255, 255, 255)),
        (0.8, (255, 128, 128)),
        (1.0, (255, 0, 0))
    )

    lastval, lastcol = cmap[0]
    for step, col in cmap[1:]:
        val = int(step * 256)
        for i in range(3):
            lut[lastval:val, i] = np.linspace(lastcol[i], col[i], val - lastval)

        lastcol = col
        lastval = val
    im_color = np.empty(shape=(colors.shape[0], 3), dtype="uint8")
    for i in range(3):
        im_color[:, i] = cv2.LUT(colors, lut[:, i]).reshape(-1)
    return im_color/255


def get_point_cloud(filename, progress, zone):
    gdal_dem_data = gdal.Open(filename)
    assert gdal_dem_data is not None, _('Wrong tif type.')
    assert gdal_dem_data.RasterCount == 1, _('Wrong tif type. Too many channels.')
    no_data = gdal_dem_data.GetRasterBand(1).GetNoDataValue()
    size = 4 * gdal_dem_data.RasterYSize * gdal_dem_data.RasterYSize
    step = int(np.ceil(np.sqrt(size // (512 * 1024 * 1024))))
    step = max(1, step)
    if psutil.virtual_memory().available <= 6 * (size/step**2):
        raise MemoryError
    gdal.SetCacheMax(round((psutil.virtual_memory().available - 2 * (size/step**2)) / 2))
    arr = []
    for i in range(0, gdal_dem_data.RasterYSize, step):
        arr.append(np.copy(gdal_dem_data.ReadAsArray(0, i, gdal_dem_data.RasterXSize, 1)[:, ::step]))
        progress.setValue((i / gdal_dem_data.RasterYSize) * 25)
        QApplication.processEvents()
    dem = np.vstack(tuple(arr))

    top_left_lon, pixel_w, turn, top_left_lat, turn_, pixel_h = gdal_dem_data.GetGeoTransform()
    pixel_h *= step
    pixel_w *= step
    del gdal_dem_data, arr
    assert top_left_lon != 0 and top_left_lat != 0, _("Couldn't define metadata (top left corner)!")

    progress.setValue(25)
    height, width = dem.shape
    # picture is created from top left corner
    x_space = (np.arange(0, width))*abs(pixel_w) + top_left_lon
    y_space = (np.arange(0, -height, -1))*abs(pixel_h) + top_left_lat
    xx, yy = np.meshgrid(x_space.astype(np.float32), y_space.astype(np.float32))

    assert xx.shape == yy.shape and xx.shape == dem.shape
    X, Y, Z = xx.flatten(), yy.flatten(), dem.flatten()
    del xx, yy, dem

    mask = Z != no_data
    progress.setValue(38)
    QApplication.processEvents()
    X = X[mask]
    Y = Y[mask]
    Z = Z[mask]
    min_z = np.amin(Z)
    max_z = np.amax(Z)
    delta = max_z - min_z
    colors = np.array(((Z-min_z)/delta)*255, dtype='uint8')

    lut = np.empty(shape=(256, 3), dtype="uint8")
    # cmap = (
    #     (0, (255, 213, 0)),
    #     (0.2, (255, 85, 0)),
    #     (0.5, (255, 0, 0)),
    #     (0.8, (230, 4, 0)),
    #     (1.0, (192, 3, 0))
    # )
    cmap = (
        (0, (59, 140, 64)),
        (0.25, (162, 166, 68)),
        (0.5, (214, 212, 153)),
        (0.75, (217, 154, 37)),
        (1.0, (191, 107, 33))
    )

    lastval, lastcol = cmap[0]
    for step, col in cmap[1:]:
        val = int(step * 256)
        for i in range(3):
            lut[lastval:val, i] = np.linspace(
                lastcol[i], col[i], val - lastval)

        lastcol = col
        lastval = val
    im_color = np.empty(shape=(colors.shape[0], 3), dtype="uint8")
    for i in range(3):
        im_color[:, i] = cv2.LUT(colors, lut[:, i]).reshape(-1)

    progress.setValue(84)
    QApplication.processEvents()
    X, Y, zone, letter = project_array(X, Y, zone=zone)
    progress.setValue(98)
    QApplication.processEvents()
    pcd = np.column_stack((X, Y, Z, im_color))
    #print(pcd.shape, len(X))
    #print(pcd[:, 0], pcd.T[0])
    assert len(pcd.shape) == 2 and pcd.shape[0] == len(X) and pcd.shape[1] == 6
    return pcd, zone, letter


def save_point_cloud(point_cloud, path):
    dt = [('x', '<f4'), ('y', '<f4'), ('z', '<f4'), ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')]
    vertex = np.array(np.zeros(point_cloud.shape[0]), dtype=dt)
    vertex['x'] = point_cloud[:, 0]
    vertex['y'] = point_cloud[:, 1]
    vertex['z'] = point_cloud[:, 2]
    vertex['red'] = point_cloud[:, 3]
    vertex['green'] = point_cloud[:, 4]
    vertex['blue'] = point_cloud[:, 5]
    el = PlyElement.describe(vertex, 'vertex')
    PlyData([el]).write(path)


def read_point_cloud(path):
    pcd = PlyData.read(path)
    data = pcd.elements[0].data
    if 4 * 6 * 2 * data.shape[0] >= psutil.virtual_memory().available * 0.8:
        raise MemoryError
    x = np.array(data['x'])
    y = np.array(data['y'])
    z = np.array(data['z'])
    red = np.array(data['red'])
    green = np.array(data['green'])
    blue = np.array(data['blue'])
    points = np.column_stack((x, y, z, red, green, blue))
    return points


def parse_mag_file(filepath, progress):
    crc8 = crcmod.predefined.mkCrcFun('crc-8-maxim')
    file = open(filepath, 'rb').read()
    gpst_arr = np.zeros(300000, dtype=np.uint64)
    freq_arr = np.zeros(300000, dtype=np.uint32)
    sig1_arr = np.zeros(300000, dtype=np.int32)
    sig2_arr = np.zeros(300000, dtype=np.int16)
    # sens_temp_arr = np.empty(length, dtype=np.uint16)
    # lamp_temp_arr = np.empty(length, dtype=np.uint16)
    # status_arr = np.empty(length, dtype=np.uint8)
    # dc_current_arr = np.empty(length, dtype=np.uint16)
    # board_temp_arr = np.empty(length, dtype=np.int8)
    length = len(file)
    position = 0
    gpst_counter = 0
    last_timestamp = None
    low_mask = 0xFFFF

    while position + 1 < length:
        if file[position] == 0xFE and position + file[position + 1] + 4 <= length:
            data_size = file[position + 1]
            packet = file[position:position+data_size+5]
            # if packet[-1] != crc8(packet[position+1:-1]):
            #     if packet[3] == 0x28:
            #         last_timestamp = None
            #     position += 1
            #     continue
            if packet[3] == 0x27 and last_timestamp:
                data_layout = '<HHIi'
                gpst, sig2, frequency, sig1 = struct.unpack(data_layout, packet[4:-1])

                low_timestamp = last_timestamp & low_mask
                high_timestamp = last_timestamp & ~low_mask
                high_time = high_timestamp if gpst >= low_timestamp else (high_timestamp + (low_mask + 1))

                last_timestamp = high_time + gpst
                gpst = high_time + gpst

                if position >= len(gpst_arr):
                    gpst_arr.resize(len(gpst_arr) + 100000)
                    freq_arr.resize(len(gpst_arr) + 100000)
                    sig1_arr.resize(len(gpst_arr) + 100000)
                    sig2_arr.resize(len(gpst_arr) + 100000)

                gpst_arr[gpst_counter] = gpst
                freq_arr[gpst_counter] = frequency
                sig1_arr[gpst_counter] = sig1
                sig2_arr[gpst_counter] = sig2
                gpst_counter += 1
            elif packet[3] == 0x28:
                data_layout = '<QbbHHHhHh'
                last_timestamp, version, status, lamp_t, lamp_v, dc_current, chamber_t, chamber_v, main_unit_t = \
                    struct.unpack(data_layout, packet[4: 4 + 22])
            position += data_size + 5
        else:
            position += 1

            progress.setValue((position / length) * 99)
            QApplication.processEvents()

    gpst_arr = np.copy(gpst_arr[0:gpst_counter])
    freq_arr = np.copy(freq_arr[0:gpst_counter])
    sig1_arr = np.copy(sig1_arr[0:gpst_counter])
    sig2_arr = np.copy(sig2_arr[0:gpst_counter])

    return gpst_arr, freq_arr, sig1_arr, sig2_arr
        # , sens_temp_arr, lamp_temp_arr, status_arr, dc_current_arr, board_temp_arr


class CICFilter(QObject):
    signal_output = pyqtSignal(object)

    def __init__(self):
        QObject.__init__(self)
        self.first_integrator = np.uint64(0)
        self.second_integrator = np.uint64(0)
        self.d_1_1 = np.uint64(0)
        self.d_1_2 = np.uint64(0)

        self.d_2_1 = np.uint64(0)
        self.d_2_2 = np.uint64(0)

        self.first_diff = np.uint64(0)
        self.output = np.uint64(0)
        self.counter = 0
        self.decimate_idx = 1

    def filtering(self, array):
        for i in range(len(array)):
            self.first_integrator = array[i] + self.first_integrator
            self.second_integrator = self.first_integrator + self.second_integrator
            self.counter += 1
            if self.counter % self.decimate_idx == 0:
                self.first_diff = self.second_integrator - self.d_1_1
                self.d_1_1 = self.d_1_2
                self.d_1_2 = self.second_integrator

                self.output = self.first_diff - self.d_2_1
                self.d_2_1 = self.d_2_2
                self.d_2_2 = self.first_diff
                k = (2 * self.decimate_idx) ** 2
                self.signal_output.emit(self.output / k)


class IIRFilter(QObject):
    def __init__(self):
        QObject.__init__(self)

        self.filters = {}
        try:
            with open('filters.json') as json_file:
                self.filters = json.load(json_file)
        except FileNotFoundError:
            pass

        self.clear_data = [0] * 10
        self.filtered_data = [0] * 10

        self.current_filter = None

    def set_current_filter(self, filter):
        if filter in self.filters:
            self.current_filter = filter
            self.clear_data = [0] * 10
            self.filtered_data = [0] * 10

    def filtering(self, array):
        if self.current_filter is None:
            return array
        out_put = np.zeros(array.shape)

        for i in range(len(array)):
            data = array[i]
            for block in self.filters[self.current_filter]:
                numerators = block[0:3]
                denumerators = block[3:5]
                G = block[-1]
                data = self.filter_data(data, numerators, denumerators, G)
            out_put[i] = data
        return out_put

    def filter_data(self, data, numerators, denumenators, G):
        self.clear_data.insert(0, data)
        self.clear_data.pop()
        filtered = 0
        for i in range(len(numerators)):
            filtered += numerators[i] * self.clear_data[i]
        for j in range(len(denumenators)):
            filtered -= denumenators[j] * self.filtered_data[j]
        self.filtered_data.insert(0, filtered)
        self.filtered_data.pop()
        return filtered * G

