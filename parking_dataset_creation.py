import requests
from PIL import Image
import shapely.geometry as geom
import numpy as np
from shapely.geometry import Point, Polygon
import geopandas as gp
from owslib.wms import WebMapService
import osmnx as ox
from unidecode import unidecode


def get_image(bb, size):
    wms = WebMapService('https://wxs.ign.fr/essentiels/geoportail/r/wms?SERVICE=WMS&REQUEST=GetCapabilities')
    img = wms.getmap(layers=['ORTHOIMAGERY.ORTHOPHOTOS'],
                     styles=['normal'],
                     srs='EPSG:2154',
                     bbox=bb,
                     size=(size, size),
                     format='image/jpeg',
                     transparent=True
                     )
    img = Image.open(img)
    return (img)


def get_area(x_min, y_min, x_max, y_max):
    p1 = Point(x_min, y_max)
    p2 = Point(x_max, y_max)
    p3 = Point(x_max, y_min)
    p4 = Point(x_min, y_min)
    points = [p1, p2, p3, p4, p1]
    poly = Polygon([[p.x, p.y] for p in points])
    data = {'geometry': poly}
    df = gp.GeoDataFrame([data], columns=data.keys())
    df.set_crs("2154")
    return df.area[0] / 1E6


def get_orthophotos(zone, size):
    geometry = ox.geocode_to_gdf(zone).geometry
    bounding_boxes = []

    x_min, y_min, x_max, y_max = geometry.to_crs("2154").bounds.iloc[0]
    surface = get_area(x_min, y_min, x_max, y_max)
    width, height = (x_max - x_min), (y_max - y_min)

    print("the area of {} is {} km²".format(zone, surface))
    print("we are about to download {} images of the zone".format(int(height / size) * int(width / size)))

    for i in range(0, int(height / size)):
        for j in range(0, int(width / size)):
            x1, y1 = x_min + j * size, y_min + i * size
            x2, y2 = x_min + (j + 1) * size, y_min + (i + 1) * size
            bounding_boxes.append((x1, y1, x2, y2))

    orthophotos = []
    for bb in bounding_boxes:
        orthophoto = get_image(bb, 1000)
        orthophoto.save(
            r'C:\Users\j.borderon\Documents\GitHub\data-ia\10-parkings\notebooks\Orthophotos\{}{}.jpg'.format(
                unidecode(zone), bounding_boxes.index(bb)))

    return orthophotos

if __name__ == "__main__":
    zone = "Périgueux"
    size = 500

    orthophotos = get_orthophotos(zone, size)

    for orthophoto in orthophotos:
        print(orthophoto.size)
