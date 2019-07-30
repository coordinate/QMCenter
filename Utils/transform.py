import pyproj


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
    l = letter(coordinates)
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
    min_magnet = 67458
    max_magnet = 67516
    middle_mag = (max_magnet - min_magnet)/2 + min_magnet
    res = (magnet-min_magnet)/(max_magnet-min_magnet)
    if res >= 0.5:
        # res_max = ((magnet-middle_mag) / (max_magnet - middle_mag)) * 255
        res_max = ((magnet-max_magnet) / (middle_mag - max_magnet)) * 255
        return 255/255, res_max/255, res_max/255, 1
    res_min = ((magnet-min_magnet) / (middle_mag-min_magnet)) * 255
    return res_min/255, res_min/255, 255/255, 1

