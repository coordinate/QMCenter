import pyproj
import numpy as np
import cv2


_projections = {}


def zone(coordinates):  # coordinates = (latitude, longitude)
    # if 56 <= coordinates[1] < 64 and 3 <= coordinates[0] < 12:
    #     return 32
    # if 72 <= coordinates[1] < 84 and 0 <= coordinates[0] < 42:
    #     if coordinates[0] < 9:
    #         return 31
    #     elif coordinates[0] < 21:
    #         return 33
    #     elif coordinates[0] < 33:
    #         return 35
    #     return 37
    return int((coordinates[1] + 180) / 6) + 1


def letter(coordinates):
    return 'CDEFGHJKLMNPQRSTUVWXX'[int((coordinates[1] + 80) / 8)]


def project(coordinates):  # coordinates = (latitude, longitude)
    z = zone(coordinates)
    # l = letter(coordinates)
    if z not in _projections:
        _projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
    x, y = _projections[z](coordinates[1], coordinates[0])
    if y < 0:
        y += 10000000
    return x, y


def unproject(z, l, x, y):
    if z not in _projections:
        _projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
    if l < 'N':
        y -= 10000000
    lng, lat = _projections[z](x, y, inverse=True)
    return lng, lat


def magnet_color(magnet):
    min_z = np.amin(magnet)
    max_z = np.amax(magnet)
    delta = max_z - min_z
    colors = np.array(((magnet-min_z)/delta)*255, dtype='uint8')
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
            lut[lastval:val, i] = np.linspace(
                lastcol[i], col[i], val - lastval)

        lastcol = col
        lastval = val
    im_color = np.empty(shape=(colors.shape[0], 3), dtype="uint8")
    for i in range(3):
        im_color[:, i] = cv2.LUT(colors, lut[:, i]).reshape(-1)
    return im_color/255


def get_point_cloud(gdal_dem_data, lat0, lon0):
    band = gdal_dem_data.GetRasterBand(1)
    no_data = band.GetNoDataValue()
    dem = gdal_dem_data.ReadAsArray()
    top_left_lon, pixel, turn, top_left_lat, turn_, pixel_ = gdal_dem_data.GetGeoTransform()
    pixel_size = (pixel * np.pi / 180) * 6371 * 1000

    earth = 6371
    lat = float(top_left_lat) * np.pi / 180
    lon = float(top_left_lon) * np.pi / 180
    x, y = ((lon - lon0)*np.cos(lat0)*earth*1000, (lat - lat0)*earth*1000)
    height, width = dem.shape
    # picture is created from top left corner
    x_space = (np.arange(0, width))*pixel_size
    y_space = (np.arange(0, -height, -1))*pixel_size
    xx, yy = np.meshgrid(x_space, y_space)
    assert xx.shape == yy.shape and xx.shape == dem.shape
    X, Y, Z = xx.flatten(), yy.flatten(), dem.flatten()
    mask = Z != no_data
    X = X[mask] + x
    Y = Y[mask] + y
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

    # colors = np.array(((max_z-Z)/delta)*255, dtype='uint8')
    # im_color = cv2.applyColorMap(colors, cv2.COLORMAP_JET).reshape(-1, 3)

    pcd = np.column_stack((X, Y, Z-min_z, im_color/255))
    #print(pcd.shape, len(X))
    #print(pcd[:, 0], pcd.T[0])
    assert len(pcd.shape) == 2 and pcd.shape[0] == len(X) and pcd.shape[1] == 6
    return pcd


