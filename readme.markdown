# About
Campus map yo

# Working with the Data

## Import the data:

    python manage.py campusdata

The `campusdata` command is a custom management command that resets the campus models and imports all fixtures. Equivalent to:

    python manage.py reset campus
    python manage.py loaddata bikeracks
    python manage.py loaddata buildings
    python manage.py loaddata campuses
    python manage.py loaddata ... [all fixtures in apps/campus/fixtures]


## Export data
    python manage.py dumpdata --indent 4 campus.building > apps/campus/fixtures/buildings.json  
    python manage.py dumpdata --indent 4 --natural campus.group > apps/campus/fixtures/groups.json

If there is updated campus data from the authoritative source, read `data/export-import/readme.markdown`

# helpful:
http://docs.djangoproject.com/en/dev/howto/initial-data/