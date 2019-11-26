import struct
import crcmod
import gdal
import pyproj
import numpy as np
import cv2
import re
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
        colors = np.array(((magnet-min_m)/delta)*255, dtype='uint16')
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
    progress.setValue(12)
    gdal_dem_data = gdal.Open(filename)
    no_data = gdal_dem_data.GetRasterBand(1).GetNoDataValue()
    dem = gdal_dem_data.ReadAsArray()
    assert len(dem.shape) < 3, _('Wrong tif type. Too many channels.')
    top_left_lon, pixel_w, turn, top_left_lat, turn_, pixel_h = gdal_dem_data.GetGeoTransform()
    assert top_left_lon != 0 and top_left_lat != 0, _("Couldn't define metadata (top left corner)!")

    progress.setValue(25)
    height, width = dem.shape
    # picture is created from top left corner
    x_space = (np.arange(0, width))*abs(pixel_w) + top_left_lon
    y_space = (np.arange(0, -height, -1))*abs(pixel_h) + top_left_lat
    xx, yy = np.meshgrid(x_space, y_space)
    assert xx.shape == yy.shape and xx.shape == dem.shape
    X, Y, Z = xx.flatten(), yy.flatten(), dem.flatten()
    mask = Z != no_data
    progress.setValue(38)
    X = X[mask]
    Y = Y[mask]
    Z = Z[mask]
    min_z = np.amin(Z)
    max_z = np.amax(Z)
    delta = max_z - min_z
    colors = np.array(((Z-min_z)/delta)*255, dtype='uint8')

    lut = np.empty(shape=(256, 3), dtype="uint8")
    cmap = (
        (0, (255, 213, 0)),
        (0.2, (255, 85, 0)),
        (0.5, (255, 0, 0)),
        (0.8, (230, 4, 0)),
        (1.0, (192, 3, 0))
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
    X, Y, zone, letter = project_array(X, Y, zone=zone)
    progress.setValue(98)
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
    pattern = bytes([0xFF, 0x7E, 0x1A]) + b'.{27}'
    packets = re.findall(pattern, file, flags=re.DOTALL)
    length = len(packets)
    gpst_arr = np.empty(length, dtype=np.uint64)
    freq_arr = np.empty(length, dtype=np.uint32)
    sig1_arr = np.empty(length, dtype=np.int16)
    sig2_arr = np.empty(length, dtype=np.int16)
    sens_temp_arr = np.empty(length, dtype=np.uint16)
    lamp_temp_arr = np.empty(length, dtype=np.uint16)
    status_arr = np.empty(length, dtype=np.uint8)
    dc_current_arr = np.empty(length, dtype=np.uint16)
    board_temp_arr = np.empty(length, dtype=np.int8)

    for i in range(length):
        magic = packets[i][:2]
        assert magic == bytes((0xFF, 0x7E))
        packet_size = struct.unpack('<B', packets[i][2:3])[0]
        if packets[i][-1] != crc8(packets[i][3:-1]) or packet_size != 26:
            print("error")

        data_layout = '<cQLhhHHBHh'

        data, gpst, frequency, sig1, sig2, sens_temp, lamp_temp, status, dc_current, board_temp = struct.unpack(data_layout, packets[i][3:-1])
        gpst_arr[i] = gpst
        freq_arr[i] = frequency
        sig1_arr[i] = sig1
        sig2_arr[i] = sig2
        sens_temp_arr[i] = sens_temp
        lamp_temp_arr[i] = lamp_temp
        status_arr[i] = status
        dc_current_arr[i] = dc_current
        board_temp_arr[i] = board_temp
        progress.setValue((i/length) * 99)

    return gpst_arr, freq_arr, sig1_arr, sig2_arr, sens_temp_arr, lamp_temp_arr, status_arr, dc_current_arr, board_temp_arr

