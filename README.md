# Setup

* Install Anaconda and dependencies
  * `conda install gdal`
  * `conda install numpy`
  * `conda install django`
  * `conda install matplotlib`
* Setup IDE with Anaconda environment
  * In PyCharm:
    * Go to Settings -> Project -> Python Interpreter -> Add Anaconda enviroment
    * Create a Python build configuration:
      * Script path: `...\manage.py`
      * Parameters: `runserver`
      * Python interpreter: Anaconda Python environment (the one that was previously added)
* Folder `resources` goes into `retour-middleware\retourmiddleware` (same folder as `areas`, `assetpos`, ...)
* File `settings_secret.py` goes into `retour-middleware\retourmiddleware\retourmiddleware` (same folder as `settings.py`, ...)

To test the setup: Run retour-middleware, open `http://127.0.0.1:8000/assetpos/?filename=forest_areas&tree_multiplier=0.00001` in the browser - you should see tree data.
