import ee
import geopandas as gpd
import remotesensing as rs #script with gee class to interface with Google Earth Engine
import datetime as dt

ee.Initialize()

# load park shapefile and define boundaries
park = gpd.read_file('data/raw/Mols.shp', crs = 23032)
park = park.to_crs('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
bbox = {'xmin': park.bounds['minx'][0],
        'xmax': park.bounds['maxx'][0],
        'ymin': park.bounds['miny'][0],
        'ymax': park.bounds['maxy'][0]}

test = rs.daily_ndvi(bbox, '2021-05-01', '2021-05-15', 100)

test.ndvi() #get NDVI images (server side)

test.count_tasks() #count number of images to export

test.export() #export to GDrive
