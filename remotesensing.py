import pandas as pd
import numpy as np
import ee
import datetime as dt
from IPython.display import Image

def error(err = ""):
    print("\033[0;39;31m " + err + "\033[0;49;39m")

def warning(warn = ""):
    print("\033[0;32;33m " + warn + "\033[0;49;39m")

def message(mssg = None):
    print("\033[0;32;34m " + mssg + "\033[0;49;39m")

class gee:
    """
    This class gets NDVI from Google Earth Engine
    using WGS84 long-lat bounding boxes.
    - box must be a dictionary with keys: xmin, xmax, ymin, ymax.
    - year must be an integer (e.g. 2010).
    - month must be an integer, 1 to 12 (e.g. 2 for February).
    - clouds must be an integer, 1 to 100, masking out pixels with cloud proportion >= clouds.
    """
    def __init__(self, box, year, month, clouds, stat = 'median'):
        self.end_month = {'1': 31, '2': 28, '3': 31, '4': 30,
                          '5': 31, '6': 30, '7': 31, '8': 31,
                          '9': 30, '10': 31, '11': 30, '12': 31}
        self.clouds = clouds
        self.year = year
        self.month = month
        self.start = '{}-{}-{}'.format(year, month, 1)
        self.end = '{}-{}-{}'.format(year, month, self.end_month[str(month)])
        self.box = box
        self.stat = stat
        self.flag = False
        if type(self.box) is not dict:
            error("Error: box is not a dictionary")
            self.flag = True
        if not all([x in self.box.keys() for x in ['xmin', 'xmax', 'ymin', 'ymax']]):
            error("Error: box should have all keys: xmin, xmax, ymin, ymax")
            self.flag = True
    def mask_clouds(self, image):
        qa = image.select('QA60')
        # Bits 10 and 11 are clouds and cirrus, respectively.
        cloudBitMask = 1 << 10
        cirrusBitMask = 1 << 11
        # Both flags should be set to zero, indicating clear conditions.
        mask = qa.bitwiseAnd(cloudBitMask).eq(0)
        image = image.updateMask(mask)
        mask = qa.bitwiseAnd(cirrusBitMask).eq(0)
        image = image.updateMask(mask)
        return image
    def ndvi(self):
        # ___Extent of area as polygon___
        self.area = ee.Geometry.Polygon([
            [self.box['xmin'], self.box['ymin']],
            [self.box['xmax'], self.box['ymin']],
            [self.box['xmax'], self.box['ymax']],
            [self.box['xmin'], self.box['ymax']],
            [self.box['xmin'], self.box['ymin']]
        ])
        # ___NDVI from Coperinus (EE)___
        # first remove images with more than self.cloud covered
        imagecollection = ee.ImageCollection('COPERNICUS/S2')
        imagecollection = imagecollection.filterDate(self.start_date, self.end_date)
        imagecollection = imagecollection.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.clouds))
        # then remove pixels with clouds and cirrus
        imagecollection = imagecollection.map(self.mask_clouds)
        # get near-infrared and red bands
        nir = imagecollection.select('B8')
        red = imagecollection.select('B4')
        self.ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        if self.stat == 'median':
            nir = nir.median()
            red = red.median()
        elif self.stat == 'max':
            nir = nir.max()
            red = red.max()
        else:
            rs.error('stat ' + self.stat + ' not found')
            self.flag = True
        self.ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        self.params = {
            'StartDate': self.start,
            'EndDate': self.end,
            'Year': self.year,
            'Month': self.month,
            'bbox': self.box,
            'MaxCloudCoverage': self.clouds, #range = 0-100
            'ReducerStat': self.stat
        }
    def plot_ndvi(self, show_url = False):
        extremes = self.ndvi.reduceRegion(**{
            'reducer': ee.Reducer.minMax(),
            'geometry': self.area,
            'scale': 30,
            'maxPixels': 1e9
        })
        self.min = extremes.getInfo()['NDVI_min']
        self.max = extremes.getInfo()['NDVI_max']
        url = self.ndvi.getThumbUrl({
            'min': self.min,
            'max': self.max,
            'region': self.area,
            'dimensions': 1000,
            'palette': ['80146E', '83409B', '6C6AB5', '478EC1', '2BABC2', '4AC3BD', '7ED5B8', 'B0E3B8', 'DAEDC2', 'F5F2D8']
        })
        if show_url:
            print(url)
        else:
            return(Image(url = url))
    def initialize_task(self, name = None):
        # Initialize tasks for Earth Engine server
        self.task_ndvi = ee.batch.Export.image.toDrive(image = self.ndvi,
                                                      description = 'ndvi_' + str(self.year) + '_' + str(self.month),
                                                      scale = 10,
                                                      region = self.area,
                                                      folder = 'mols-ndvi',
                                                      fileNamePrefix = 'ndvi_' + str(self.year) + '_' + str(self.month),
                                                      crs = 'EPSG:4326',
                                                      fileFormat = 'GeoTIFF')
    def start_task(self):
        # Start the tasks in Earth Engine server
        self.task_ndvi.start()
    def check_task(self):
        # Check status of tasks in Earth Engine server
        print('--- NDVI', self.year, self.month, '--- ')
        print(self.task_ndvi.status()['state'])
    def cancel_task(self):
        self.task_ndvi.cancel()

class daily_ndvi:
    """
    This class gets NDVI images from Google Earth Engine
    using WGS84 long-lat bounding boxes.
    All images between the specified dates are obtained.
    - box must be a dictionary with keys: xmin, xmax, ymin, ymax.
    - start_date must be a string, e.g. 2020-03-30.
    - end_date must be a string, e.g. 2020-03-30.
    - clouds must be an integer, 1 to 100, masking out pixels with cloud proportion >= clouds.
    - stat must be a string, either 'median' or 'max'.
    - scale must be an integer and is the scale at which the images are exported.
    """
    def __init__(self, box, start_date, end_date, clouds, stat = 'median', scale = 30):
        self.clouds = clouds
        self.start_date = start_date
        self.end_date = end_date
        self.start_date = self.start_date.split('-')
        self.start_date = [int(x) for x in self.start_date]
        self.start_date = dt.datetime(*self.start_date)
        self.end_date = self.end_date.split('-')
        self.end_date = [int(x) for x in self.end_date]
        self.end_date = dt.datetime(*self.end_date)
        self.days = (self.end_date - self.start_date).days
        self.box = box
        self.stat = stat
        self.scale = scale
        self.flag = False
        if type(self.box) is not dict:
            error("Box is not a dictionary")
            self.flag = True
        if not all([x in self.box.keys() for x in ['xmin', 'xmax', 'ymin', 'ymax']]):
            error("Box should have all keys: xmin, xmax, ymin, ymax")
            self.flag = True
    def mask_clouds(self, image):
        qa = image.select('QA60')
        # Bits 10 and 11 are clouds and cirrus, respectively.
        cloudBitMask = 1 << 10
        cirrusBitMask = 1 << 11
        # Both flags should be set to zero, indicating clear conditions.
        mask = qa.bitwiseAnd(cloudBitMask).eq(0)
        image = image.updateMask(mask)
        mask = qa.bitwiseAnd(cirrusBitMask).eq(0)
        image = image.updateMask(mask)
        return image
    def calc_ndvi(self, image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)
    def ndvi(self):
        # ___Extent of area as polygon___
        self.area = ee.Geometry.Polygon([
            [self.box['xmin'], self.box['ymin']],
            [self.box['xmax'], self.box['ymin']],
            [self.box['xmax'], self.box['ymax']],
            [self.box['xmin'], self.box['ymax']],
            [self.box['xmin'], self.box['ymin']]
        ])
        self.ndvi = [None for x in range(self.days)]
        for i in range(self.days):
            start_date = self.start_date + dt.timedelta(days = i)
            end_date = self.start_date + dt.timedelta(days = i + 1)
            start_date = str(start_date.year) + '-' + str(start_date.month) + '-' + str(start_date.day)
            end_date = str(end_date.year) + '-' + str(end_date.month) + '-' + str(end_date.day)
            # ___NDVI from Coperinus (EE)___
            message('\n --- Processing ' + start_date + ' --- ')
            imagecollection = ee.ImageCollection('COPERNICUS/S2')
            imagecollection = imagecollection.filterDate(start_date, end_date) #end date is exclusive
            imagecollection = imagecollection.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', self.clouds))
            try: 
                imagecollection.size().getInfo()
            except ee.ee_exception.EEException:
                warning('    EE exception (possibly empty) - skipping ' + start_date)
            else:
                message('    Calculating NDVI')
                # then remove pixels with clouds and cirrus
                imagecollection = imagecollection.map(self.mask_clouds)
                # calculate NDVI
                imagecollection = imagecollection.map(self.calc_ndvi).select('NDVI')
                if self.stat == 'median':
                    self.ndvi[i] = imagecollection.median()
                elif self.stat == 'max':
                    self.ndvi[i] = imagecollection.max()
                else:
                    error('stat ' + self.stat + ' not found')
                    self.flag = True
                if not self.flag:
                    # check if image has values
                    minValue = self.ndvi[i].reduceRegion(**{
                        'reducer': ee.Reducer.min(),
                        'scale': self.scale,
                        'geometry': self.area
                    }).getInfo()['NDVI']
                    if minValue is None: #if no value, skip
                        message('    ' + start_date + ' is empty - skipping')
                        self.ndvi[i] = None
                else:
                    error("Flag = True - something went wrong and I don't know where.")
    def plot(self, image, show_url = False):
        extremes = image.reduceRegion(**{
            'reducer': ee.Reducer.minMax(),
            'geometry': self.area,
            'scale': self.scale,
            'maxPixels': 1e9
        })
        self.min = extremes.getInfo()['NDVI_min']
        self.max = extremes.getInfo()['NDVI_max']
        url = image.getThumbUrl({
            'min': self.min,
            'max': self.max,
            'region': self.area,
            'dimensions': 1000,
            'palette': ['80146E', '83409B', '6C6AB5', '478EC1', '2BABC2', '4AC3BD', '7ED5B8', 'B0E3B8', 'DAEDC2', 'F5F2D8']
        })
        if show_url:
            print("\033[0;32;35m" + url + "\033[0;49;39m")
        else:
            return(Image(url = url))                    
    def count_tasks(self):
        n = sum([x is not None for x in self.ndvi])
        message(" === " + str(n) + ' images to export ===')
    def export(self):
        # ___Export to Google Drive___
        for i in range(self.days):
            if self.ndvi[i] is not None:
                start_date = self.start_date + dt.timedelta(days = i)
                start_date = str(start_date.year) + '-' + str(start_date.month) + '-' + str(start_date.day)
                task_ndvi = ee.batch.Export.image.toDrive(
                    image = self.ndvi[i],
                    description = start_date,
                    scale = self.scale,
                    region = self.area,
                    folder = 'ndvi',
                    fileNamePrefix = start_date,
                    crs = 'EPSG:4326',
                    fileFormat = 'GeoTIFF'
                )
                try:
                    task_ndvi.start()
                except ee.ee_exception.EEException:
                    warning('    EE exception - ' + start_date + 'not exported')
                else:
                    message('    Exporting ' + start_date)