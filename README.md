# Quick development setup

1.  Install Python
    1.  `sudo apt install python3`
    2.  `sudo apt install python3-pip`
2.  Install the required dynamic libraries
    1.  `sudo apt install libgdal-dev`
3.  Install the required Python libraries for the server
    1.  `pip3 install -r requirements.txt`
4.  Setup PostgreSQL
    1.  `sudo apt install postgresql `
    2.  `sudo apt install postgis`
    3.  `sudo -u postgres -i psql`
    4.  `create user USERNAME with password ‘PASSWORD’;`
    5.  `create database retour;`
    6.  `\c retour`
    7.  `create extension postgis;`
    8.  `\q`
5.  Configure the server
    1.  Copy `landscapelab/settings/local_settings.py-dist` to `landscapelab/settings/local_settings.py` and edit the database information according to what was entered in the previous step
    2.  Copy `logging.conf-dist` to `logging.conf` and configure as desired
6.  Fill the database
    1.  `python3 manage.py migrate`
    2.  `python3 manage.py loaddata defaults.json` (TODO: This doesn't load all required data yet)
7.  Insert  geodata from an external folder with a symlink
    1.  `ln -s /external/path/to/resources landscapelab/resources`
8.  Run the server
    1.  `python3 manage.py runserver`

Optional: Test the setup with a request such as `http://127.0.0.1:8000/raster/1768618.0/6008552.0/12.json` (should return valid images) or `http://127.0.0.1:8000/assetpos/get_all_editable_assettypes.json` (should return a list of asset types).

For a more flexible setup, Anaconda and PyCharm are recommended.
  
# Setting up the production environment using bitnami

* install the unofficial wheel builds for GDAL, Fiona and rasterio
* copy the gdal20X.dll and geos_c.dll from the site-packages/osgeo directory in python to the apache2 root directory of bitnami
* add GDAL_LIBRARY_PATH and GEOS_LIBRARY_PATH to local_settings.py and point them to gdal20X.dll and geos_c.dll
* add the environment paths for GDAL_DATA and PROJ_LIB
* add all local ip-adresses into ALLOWED_HOSTS in local_settings.py

# Run the server
* development: `python manage.py runserver`
* production: use a wsgi compatible server and deploy the app
