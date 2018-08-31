to get this to run on a local machine:
 - create a file called settings_secret.py which contains the SECRET_KEY
 - create a floder called DHM in returmiddleware/hdm
 - fill said folder with heightmaps
 
127.0.0.1:8000/dhm/<heightmap-filename> should now return the converted json data