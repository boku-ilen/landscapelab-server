from django.http import JsonResponse
import os.path
from .shp_reader import *
import json

#from osgeo import gdal
from osgeo import ogr

# Create your views here.
def index(request):
    pathParts = request.path.split("/")
    fileName = pathParts[2]
    BASE = os.path.dirname(os.path.abspath(__file__))
    genfilePath = os.path.join(BASE, "generatedFiles",fileName + ".json")
    filePath = os.path.join(BASE, "inputFiles",fileName+".shp")

    if os.path.isfile(genfilePath):
        print("opening ",genfilePath)

        with open(genfilePath) as f:
            data = json.load(f)
        return JsonResponse(data)
    elif os.path.isfile(filePath):
        print("opening %s" % filePath)

        driver = ogr.GetDriverByName('ESRI Shapefile')
        if driver is None:
            return JsonResponse({"Error": "driver not available ESRI Shapefile"})

        dataset = driver.Open(filePath, 0)

        if dataset is None:
            return JsonResponse({"Error": "could not open "+filePath})
        else:
            print("opened %s" % filePath)
            data = calcAssetPos(dataset,request.path)
            with open(genfilePath, 'w') as outfile:
                json.dump(data,outfile)

            return JsonResponse(data)
    else:
        return JsonResponse({"Error": "file %s.shp does not exist" % fileName})