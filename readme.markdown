# About
Campus map yo

# Working with the Data
## Import/reset data
    python manage.py reset campus
    python manage.py loaddata buildings
    python manage.py loaddata regional_campuses
## Export data
    python manage.py dumpdata --indent 4 campus.building > apps/campus/fixtures/buildings.json  
    python manage.py dumpdata --indent 4 campus.reiongalcampus > apps/campus/fixtures/regional_campuses.json  

if there is updated campus data from the authoritative source, read `data/buildings/readme.markdown`

# helpful:
http://docs.djangoproject.com/en/dev/howto/initial-data/