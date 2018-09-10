import os.path

import numpy as np
from osgeo import gdal
import math


def getHDM(request):
    pathParts = request.path.split("/")
    datasetName = os.path.join("DHM" , pathParts[2])
    datasetSplits = 1
    datasetPart = 0
    if len(pathParts) == 5:
        datasetSplits = int(pathParts[3])
        datasetPart = int(pathParts[4])
        print("teil ", datasetPart, " von ",datasetSplits * datasetSplits)
    xpos = datasetPart % datasetSplits
    ypos = int(datasetPart / datasetSplits)
    print("part position = ",xpos,", ",ypos)

    gdal.UseExceptions()

    # Open the data source and read in the extent
    try:
        BASE = os.path.dirname(os.path.abspath(__file__))
        dataset = gdal.Open(os.path.join(BASE, datasetName))
    except RuntimeError as e:
        print('Unable to open ' + datasetName)
        print(e)
        return {"Error": "failed to open file"}
    try:
        srcband = dataset.GetRasterBand(1)
    except RuntimeError as e:
        # for example, try GetRasterBand(10)
        print('Band not found')
        print(e)
        return {"Error": "Band not found"}

    # create array 2d
    print("\n[ Array Statistics ]")
    datasetArray = np.array(dataset.GetRasterBand(1).ReadAsArray())
    print("Shape = ", datasetArray.shape)
    print("Size = ", datasetArray.size)
    print("Array: \n", datasetArray)

    #select correct part
    print("\n[ Part Statistics ]")
    xstart = int((datasetArray.shape[0]/datasetSplits)*xpos)
    xend = int((datasetArray.shape[0]/datasetSplits)*(xpos + 1)) + 1
    ystart = int((datasetArray.shape[1]/datasetSplits)*ypos)
    yend = int((datasetArray.shape[1]/datasetSplits)*(ypos + 1)) + 1
    print("datasetArray[",xstart," : ",xend,", ",ystart," : ",yend,"]")
    datasetArray = datasetArray[xstart : xend, ystart : yend]
    print("Shape = ", datasetArray.shape)
    print("Size = ", datasetArray.size)
    print("Array: \n", datasetArray)

    # set Projection
    proj = gdal.osr.SpatialReference()
    proj.SetWellKnownGeogCS("EPSG:4326")
    dataset.SetProjection(proj.ExportToWkt())

    print("\n[ Statistics ] ")
    # Projection
    print("Projection = ", dataset.GetProjection())

    # Dimensions
    rows = int(datasetArray.shape[0])
    cols = int(datasetArray.shape[1])
    print("DimensionX = ", cols)
    print("DimensionY = ", rows)

    # Number of bands
    print("Number of bands = ", dataset.RasterCount)

    # Metadata for the raster dataset
    print("Metadata = ", dataset.GetMetadata())

    print("\n[ Band '0' Statistics ]")
    # Read the raster band as separate variable
    band = dataset.GetRasterBand(1)

    # Check type of the variable 'band'
    type(band)

    # Data type of the values
    gdal.GetDataTypeName(band.DataType)

    # Compute statistics if needed
    if band.GetMinimum() is None or band.GetMaximum() is None:
        band.ComputeStatistics(0)
        print("Statistics computed.")

    # Fetch metadata for the band
    band.GetMetadata()

    # Print only selected metadata:
    print("NO DATA VALUE = ", band.GetNoDataValue())  # none
    print("BandMin = ", band.GetMinimum())
    print("BandMax = ", band.GetMaximum())

    print("\n[ Geotransformation ]")
    geotransform = dataset.GetGeoTransform()
    if geotransform:
        originTopLeftX = geotransform[0]
        originTopLeftY = geotransform[3]
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5]
        print("OriginRange = ({}, {})".format(originTopLeftX, originTopLeftY))
        print("Pixel Size = ({}, {})".format(pixelWidth, pixelHeight))

    from_col = originTopLeftX / pixelWidth
    from_row = -originTopLeftY / pixelHeight
    to_col = (originTopLeftX + cols) / pixelWidth
    to_row = -(originTopLeftY + rows) / pixelHeight
    print("rows (Y): {} - {} ({}) \ncols (X): {} - {} ({})".format(from_row, to_row, (to_row - from_row), from_col,
                                                                   to_col, (to_col - from_col)))

    # create array 1d
    array1d = np.reshape(datasetArray, (-1, cols * rows))
    print(array1d)

    return {"Data": array1d.tolist()}
