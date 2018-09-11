from django.http import JsonResponse
import os.path
# from .shp_reader import *
from .shp_to_json import get_trees
import json

# from osgeo import gdal
from osgeo import ogr


# Create your views here.
def index(request):
    path_parts = request.path.split("/")
    file_name = path_parts[2]
    BASE = os.path.dirname(os.path.abspath(__file__))
    gen_file_path = os.path.join(BASE, "generatedFiles", file_name + ".json")
    file_path = os.path.join(BASE, "inputFiles", file_name + ".shp")

    if os.path.isfile(gen_file_path) and False:  # deactivated while debugging
        print("opening ", gen_file_path)

        with open(gen_file_path) as f:
            data = json.load(f)
        return JsonResponse(data)
    elif os.path.isfile(file_path):
        print("opening %s" % file_path)

        driver = ogr.GetDriverByName('ESRI Shapefile')
        if driver is None:
            return JsonResponse({"Error": "driver not available ESRI Shapefile"})

        data_set = driver.Open(file_path, 0)

        if data_set is None:
            return JsonResponse({"Error": "could not open " + file_path})
        else:
            print("opened %s" % file_path)
            data = get_trees(data_set, request.path)

            print("saving data to file")
            with open(gen_file_path, 'w') as outfile:
                json.dump(data, outfile)

            print("returning json")
            # return JsonResponse(data, json_dumps_params={'indent': 2})
            return JsonResponse(data)
    else:
        return JsonResponse({"Error": "file %s.shp does not exist" % file_name})
