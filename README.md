# Setup

* install python 3 (we recommend anaconda)
* install project dependencies
  * `pip install -r requirements.txt`
* install postgresql with postgis extension and configure it properly
* copy external (geo-)data folder `resources` into the project's root directory
* copy `logging.conf-dist` to `logging.conf` and (configure it to your needs)
* copy `retourmiddleware/settings/local-settings.py-dist` to `local-settings.py` in the same directory and configure your database connection there
* create the database schema and apply defaults
  * `python manage.py migrate` TODO
  * `python manage.py loaddata defaults.json` TODO

# Run the server
`python manage.py runserver`
