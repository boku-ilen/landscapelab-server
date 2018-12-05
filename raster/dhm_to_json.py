import os.path
import logging
import numpy as np
from osgeo import gdal
from django.contrib.staticfiles import finders
# import math

logger = logging.getLogger('MainLogger')

def getDHM(request):
    if 'filename' not in request.GET:
        return {'Error': 'no filename specified'}
    datasetName = finders.find(os.path.join('dhm', request.GET.get('filename')))
    splits = int(request.GET.get('splits') if 'splits' in request.GET else 1)
    part = int(request.GET.get('part') if 'part' in request.GET else 0)
    skip = int(request.GET.get('skip') if 'skip' in request.GET else 0)

    xpos = part % splits
    ypos = int(part / splits)
    logger.info("part position = %d, %d" % (xpos, ypos))

    gdal.UseExceptions()

    # Open the data source and read in the extent
    try:
        BASE = os.path.dirname(os.path.abspath(__file__))
        dataset = gdal.Open(os.path.join(BASE, datasetName))
    except RuntimeError as e:
        logger.error('Unable to open %s' % datasetName)
        logger.error(e)
        return {"Error": "failed to open file"}
    except TypeError as e:
        logger.error('Unable to open %s' % datasetName)
        logger.error(e)
        return {"Error": "failed to open file"}
    try:
        srcband = dataset.GetRasterBand(1)
    except RuntimeError as e:
        # for example, try GetRasterBand(10)
        logger.error('Band not found')
        logger.error(e)
        return {"Error": "Band not found"}

    # create array 2d
    logger.info("[ Array Statistics ]")
    datasetArray = np.array(dataset.GetRasterBand(1).ReadAsArray())
    logger.info("Shape = %s", str(datasetArray.shape))
    logger.info("Size = %s" % str(datasetArray.size))
    logger.info("Array: %s", str(datasetArray))

    # skip rows
    if skip != 0:
        keepX = range(0, datasetArray.shape[0], skip+1)
        keepY = range(0, datasetArray.shape[1], skip+1)
        deleteX = []
        deleteY = []
        for e in range(0, datasetArray.shape[0]):
            if e not in keepX:
                deleteX.append(e)
        for e in range(0, datasetArray.shape[1]):
            if e not in keepY:
                deleteY.append(e)
        logger.info("deleteX = %s" % str(deleteX))
        datasetArray = np.delete(datasetArray, list(deleteX), axis=0)
        datasetArray = np.delete(datasetArray, list(deleteY), axis=1)

    # select correct part
    logger.info("[ Part Statistics ]")
    xstart = int((datasetArray.shape[0] / splits) * xpos)
    xend = int((datasetArray.shape[0] / splits) * (xpos + 1)) + 1
    ystart = int((datasetArray.shape[1] / splits) * ypos)
    yend = int((datasetArray.shape[1] / splits) * (ypos + 1)) + 1

    logger.info("datasetArray[%d : %d, %d : %d]" % (xstart, xend, ystart, yend))
    datasetArray = datasetArray[xstart: xend, ystart: yend]
    logger.info("Shape = %s" % str(datasetArray.shape))
    logger.info("Size = %d" % datasetArray.size)
    logger.info("Array: %s" % str(datasetArray))

    # set Projection
    proj = gdal.osr.SpatialReference()
    proj.SetWellKnownGeogCS("EPSG:4326")
    dataset.SetProjection(proj.ExportToWkt())

    logger.info("[ Statistics ] ")
    # Projection
    logger.info("Projection = %s" % str(dataset.GetProjection()))

    # Dimensions
    rows = int(datasetArray.shape[0])
    cols = int(datasetArray.shape[1])
    logger.info("DimensionX = %d" % cols)
    logger.info("DimensionY = %d" % rows)

    # Number of bands
    logger.info("Number of bands = %d" % dataset.RasterCount)

    # Metadata for the raster dataset
    logger.info("Metadata = %s" % str(dataset.GetMetadata()))

    logger.info("[ Band '0' Statistics ]")
    # Read the raster band as separate variable
    band = dataset.GetRasterBand(1)

    # Check type of the variable 'band'
    type(band)

    # Data type of the values
    gdal.GetDataTypeName(band.DataType)

    # Compute statistics if needed
    if band.GetMinimum() is None or band.GetMaximum() is None:
        band.ComputeStatistics(0)
        logger.info("Statistics computed.")

    # Fetch metadata for the band
    band.GetMetadata()

    # Print only selected metadata:
    logger.info("NO DATA VALUE = %s" % str(band.GetNoDataValue()))  # none
    logger.info("BandMin = %d" % band.GetMinimum())
    logger.info("BandMax = %d" % band.GetMaximum())

    logger.info("[ Geotransformation ]")
    geotransform = dataset.GetGeoTransform()
    if geotransform:
        originTopLeftX = geotransform[0]
        originTopLeftY = geotransform[3]
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5]
        logger.info("OriginRange = ({}, {})".format(originTopLeftX, originTopLeftY))
        logger.info("Pixel Size = ({}, {})".format(pixelWidth, pixelHeight))

    # create array 1d
    array1d = np.reshape(datasetArray, (-1, cols * rows))
    logger.info(array1d)

    factor = skip + 1
    return {"Data": array1d.tolist(),
            "Metadata": {
                "PixelSize": [pixelWidth * factor, pixelHeight * factor],
                "OriginRange": [originTopLeftX, originTopLeftY],
                "ArrayDimensions": [cols - 1, rows - 1]
            }}
