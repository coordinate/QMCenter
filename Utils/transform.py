import gdal
import pyproj
import numpy as np
import cv2
import open3d as o3d


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
    return 'CDEFGHJKLMNPQRSTUVWXX'[int((coordinates[0] + 80) / 8)]


def project(coordinates, zone=None):  # coordinates = (longitude, latitude)
    if not zone:
        zone = utm_zone(coordinates)
    # l = letter(coordinates)
    if zone not in _projections:
        _projections[zone] = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84')
    x, y = _projections[zone](coordinates[0], coordinates[1])
    if y < 0:
        y += 10000000
    return x, y, zone


def project_array(x, y, srcp='latlong', dstp='utm', zone=None):
    """
    Project a numpy (n,2) array in projection srcp to projection dstp
    Returns a numpy (n,2) array.
    """
    if not zone:
        zone = utm_zone((x[0], y[0]))
    p1 = pyproj.Proj(proj=srcp, datum='WGS84')
    p2 = pyproj.Proj(proj=dstp, zone=zone, ellps='WGS84')
    fx, fy = pyproj.transform(p1, p2, x, y)
    # Re-create (n,2) coordinates
    return fx, fy, zone


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


def get_point_cloud(filename, progress, zone):
    progress.setValue(12)
    gdal_dem_data = gdal.Open(filename)
    no_data = gdal_dem_data.GetRasterBand(1).GetNoDataValue()
    dem = gdal_dem_data.ReadAsArray()
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
    X, Y, zone = project_array(X, Y, zone=zone)
    progress.setValue(98)
    pcd = np.column_stack((X, Y, Z-min_z, im_color/255))
    #print(pcd.shape, len(X))
    #print(pcd[:, 0], pcd.T[0])
    assert len(pcd.shape) == 2 and pcd.shape[0] == len(X) and pcd.shape[1] == 6
    return pcd, zone


def save_point_cloud(point_cloud, path):
    pcd = o3d.PointCloud()
    points = point_cloud[:, :3]
    colors = point_cloud[:, 3:]
    pcd.points = o3d.Vector3dVector(points)
    pcd.colors = o3d.Vector3dVector(colors)
    o3d.write_point_cloud(path, pcd)


def read_point_cloud(path):
    pcd = o3d.read_point_cloud(path)
    points = np.asarray(pcd.points)
    # x, y, z = points[0]
    # z_min = np.amin(points[:, 2])
    # points = np.column_stack((points[:, 0] - x, points[:, 1] - y, points[:, 2] - z_min))
    colors = np.asarray(pcd.colors)
    return np.concatenate((points, colors), axis=1)
