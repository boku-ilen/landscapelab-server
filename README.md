# Setup the development version

* install python 3 (we recommend anaconda)
* install project dependencies
  * `pip install -r requirements.txt`
* patch ows library (wmts.py is buggy in current version)
* install postgresql with postgis extension and configure it properly
* copy external (geo-)data folder `resources` into the project's root directory
* copy `logging.conf-dist` to `logging.conf` and (configure it to your needs)
* copy `landscapelab/settings/local-settings.py-dist` to `local-settings.py` in the same directory and configure your database connection there
* create the database schema and apply defaults
  * `python manage.py migrate` TODO
  * `python manage.py loaddata defaults.json` TODO
  
# Setting up the production environment using bitnami

* install the unofficial wheel builds for GDAL, Fiona and rasterio
* copy the gdal20X.dll and geos_c.dll from the site-packages/osgeo directory in python to the apache2 root directory of bitnami
* add GDAL_LIBRARY_PATH and GEOS_LIBRARY_PATH to local_settings.py and point them to gdal20X.dll and geos_c.dll
* add the environment paths for GDAL_DATA and PROJ_LIB
* add all local ip-adresses into ALLOWED_HOSTS in local_settings.py

# Run the server
* development: `python manage.py runserver`
* production: use a wsgi compatible server and deploy the app
