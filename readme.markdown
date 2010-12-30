# About
Campus map yo

# Working with the Data
## Import/reset data
    python manage.py reset campus
    python manage.py syncdb

With fixtures, this command should not be needed:
    python manage.py loaddata 'data/campus.json'

## Export data
    python manage.py dumpdata campus > apps/campus/fixtures/initial_data.json 

if there is updated campus data, read `data/buildings/readme.markdown`
