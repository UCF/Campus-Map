# [UCF Campus Map - Main Campus and Other College Locations in Central Florida](https://map.ucf.edu)
Campus map ... find what you're looking for at UCF.

## Setup
Ensure your environment has virtualenv and pip installed for python
1. Create virtual environment
2. cd to the new virtual environment
3. Clone repo to subdirectory (ex. git clone <url> src)
4. Activate virtual environment

        source bin/activate
5. Install requirements

        pip install -r src/requirements.txt
7. Setup local settings using the local_settings.templ.py file
8. Setup templates/robots.txt using templates/robots.templ.txt
9. Sync the database

        python manage.py syncdb
10. Collect static files

        python manage.py collectstatic -cl

## Working with the Data

### Import the data:

    python manage.py campusdata

The `campusdata` command is a custom management command that resets the campus models and imports all fixtures. Equivalent to:

    python manage.py reset campus
    python manage.py loaddata bikeracks
    python manage.py loaddata buildings
    python manage.py loaddata campuses
    python manage.py loaddata ... [all fixtures in apps/campus/fixtures]


### Export data
    python manage.py dumpdata --indent 4 campus.building > apps/campus/fixtures/buildings.json
    python manage.py dumpdata --indent 4 --natural campus.group > apps/campus/fixtures/groups.json

If there is updated campus data from the authoritative source, read `data/export-import/readme.markdown`

### helpful:
http://docs.djangoproject.com/en/dev/howto/initial-data/

## Code Contribution
Never commit directly to master. Create a branch or fork and work on the new feature. Once it is complete it will be merged back to the master branch.

If you use a branch to develop a feature, make sure to delete the old branch once it has been merged to master.
