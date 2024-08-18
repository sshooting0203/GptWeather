import math
class LamcParameter:
    def __init__(self, Re, grid, slat1, slat2, olon, olat, xo, yo, first):
        self.Re = Re
        self.grid = grid
        self.slat1 = slat1
        self.slat2 = slat2
        self.olon = olon
        self.olat = olat
        self.xo = xo
        self.yo = yo
        self.first = first
def lamcproj(lon, lat, map, code):
    PI = math.asin(1.0) * 2.0
    DEGRAD = PI / 180.0
    RADDEG = 180.0 / PI
    
    re = map.Re / map.grid
    slat1 = map.slat1 * DEGRAD
    slat2 = map.slat2 * DEGRAD
    olon = map.olon * DEGRAD
    olat = map.olat * DEGRAD

    sn = math.tan(PI * 0.25 + slat2 * 0.5) / math.tan(PI * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(PI * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(PI * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    if code == 0:
        ra = math.tan(PI * 0.25 + lat * DEGRAD * 0.5)
        ra = re * sf / math.pow(ra, sn)
        theta = lon * DEGRAD - olon
        if theta > PI:
            theta -= 2.0 * PI
        if theta < -PI:
            theta += 2.0 * PI
        theta *= sn
        x = (ra * math.sin(theta)) + map.xo
        y = (ro - ra * math.cos(theta)) + map.yo
    else:
        xn = x - map.xo
        yn = ro - y + map.yo
        ra = math.sqrt(xn * xn + yn * yn)
        if sn < 0.0:
            ra = -ra
        alat = math.pow((re * sf / ra), (1.0 / sn))
        alat = 2.0 * math.atan(alat) - PI * 0.5
        if abs(xn) <= 0.0:
            theta = 0.0
        else:
            if abs(yn) <= 0.0:
                theta = PI * 0.5
                if xn < 0.0:
                    theta = -theta
            else:
                theta = math.atan2(xn, yn)
        alon = theta / sn + olon
        lat = alat * RADDEG
        lon = alon * RADDEG
    return x, y
def convert_to_xy(lon, lat):
    map = LamcParameter(
        Re=6371.00877,
        grid=5.0,
        slat1=30.0,
        slat2=60.0,
        olon=126.0,
        olat=38.0,
        xo=210 / 5.0,
        yo=675 / 5.0,
        first=0
    )
    x, y = lamcproj(lon, lat, map, 0)
    return int(x + 1.5), int(y + 1.5)
