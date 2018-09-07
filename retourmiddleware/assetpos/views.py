from django.http import JsonResponse
import os.path
from .shp_reader import *
import json

from osgeo import gdal

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
        print("opening ",filePath)
        BASE = os.path.dirname(os.path.abspath(__file__))
        dataset = gdal.Open(os.path.join(BASE,filePath))

        return JsonResponse(calcAssetPos(dataset))
    else:
        return JsonResponse({"Error": "file " +fileName+ ".shp does not exist"})