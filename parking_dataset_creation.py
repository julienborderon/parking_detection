import requests
from PIL import Image
import shapely.geometry as geom
import numpy as np
from shapely.geometry import Point, Polygon
import geopandas as gp
from owslib.wms import WebMapService
import osmnx as ox
from unidecode import unidecode
from io import BytesIO

def get_image(bb, size, crs, img_type):
    bbox_str = ",".join(map(str, bb))
    base_url = 'https://wxs.ign.fr/ortho/geoportail/r/wms'
    url = (f"{base_url}?SERVICE=WMS&REQUEST=GetMap&LAYERS=ORTHOIMAGERY.ORTHOPHOTOS"
           f"&STYLES=normal&CRS={crs}&BBOX={bbox_str}&WIDTH={size}&HEIGHT={size}&FORMAT={img_type}&TRANSPARENT=TRUE")

    response = requests.get(url)

    # Vérifier le statut de la réponse
    if response.status_code == 200:
        if img_type == 'image/jpeg':
            img = Image.open(BytesIO(response.content))
            return img
        elif img_type == 'image/geotiff':
            with MemoryFile(response.content) as memfile:
                with memfile.open() as dataset:
                    img_data = dataset.read()
                    img_transform = dataset.transform
                    img_crs = dataset.crs
            return img_data, img_transform, img_crs
    else:
        print(f"Erreur lors de la récupération de l'image : {response.status_code}")


# Fonction pour obtenir la surface d'une bounding box

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


# Fonction pour convertir une bounding box d'un CRS à un autre

def bbox_to_new_crs(bbox):
    # Créer un transformateur de CRS (EPSG:2154 à EPSG:4326)
    transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=False)

    # Convertir les coins de la bounding box
    x_min, y_min = transformer.transform(bbox[0], bbox[1])
    x_max, y_max = transformer.transform(bbox[2], bbox[3])

    new_bbox = (x_min, y_min, x_max, y_max)

    return new_bbox


# Fonction principale pour obtenir les orthophotos

def get_orthophotos(size, result_dir, specific_zone=None, zone=None, df_specific=None):
    if specific_zone:
        geometry = ox.geocode_to_gdf(zone).geometry
    else:
        geometry = df_specific.geometry
        zone = "zone"

    bounding_boxes = []

    x_min, y_min, x_max, y_max = geometry.to_crs("2154").bounds.iloc[0]
    surface = get_area(x_min, y_min, x_max, y_max)
    width, height = (x_max - x_min), (y_max - y_min)

    print("la surface de la ville de {} est de {} km²".format(zone, surface))
    print("on va télécharger {} orthos".format(int(height / size) * int(width / size)))

    for i in range(0, int(height / size)):
        for j in range(0, int(width / size)):
            x1, y1 = x_min + j * size, y_min + i * size
            x2, y2 = x_min + (j + 1) * size, y_min + (i + 1) * size
            bounding_boxes.append((x1, y1, x2, y2))

    for bb in bounding_boxes:
        jpg_file_path = result_dir + '\{}_{}_jpg.jpg'.format(unidecode(zone), bounding_boxes.index(bb))
        geotiff_file_path = result_dir + '\{}_{}_tif.tif'.format(unidecode(zone), bounding_boxes.index(bb))
        if os.path.exists(jpg_file_path):
            continue
        orthophoto_jpg = get_image(bb, 1000, 'EPSG:2154', 'image/jpeg')
        orthophoto_jpg.save(jpg_file_path)
        orthophoto_geo, img_transform, img_crs = get_image(bbox_to_new_crs(bb), 1000, 'EPSG:4326', 'image/geotiff')
        with rasterio.open(geotiff_file_path, 'w', driver='GTiff', height=orthophoto_geo.shape[1],
                           width=orthophoto_geo.shape[2],
                           count=orthophoto_geo.shape[0], dtype=orthophoto_geo.dtype, crs=img_crs,
                           transform=img_transform) as dst:
            dst.write(orthophoto_geo)
    return

if __name__ == "__main__":
    zone = "Périgueux"
    size = 500

    orthophotos = get_orthophotos(zone, size)

    for orthophoto in orthophotos:
        print(orthophoto.size)
