# [UCF Campus Map - Main Campus and Other College Locations in Central Florida](https://map.ucf.edu)
Campus map ... find what you're looking for at UCF.

## Requirements

### Installation Requirements
- Python 3.8+
- pip

### Development Requirements
- node
- gulp-cli

## Installation and Setup
1. Create virtual environment and `cd` to it

        python3 -m venv ENV
        cd ENV
2. Clone repo to a subdirectory (ex. `git clone REPO_URL src`)
3. Activate virtual environment

        source bin/activate
4. `cd` to new src directory and install requirements

        cd src
        pip install -r requirements.txt
5. Set up local settings using the settings_local.templ.py file
6. Set up static_files/templates/robots.txt using static_files/templates/robots.templ.txt
7. Run an initial deployment of the project

        python manage.py deploy

    This command handles migration, static file collection, and initial
    loading of campus app fixtures if no data is available yet in the db
    (see "Working with the Data" below.)
8. Create a superuser: `python manage.py createsuperuser`

Upon completing these steps, you should be able to start Django
(`python manage.py runserver`) successfully.


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


## Development
This project uses gulp to handle minifying/uglifying javascript. Because this project is old, we still use vanilla CSS in lieu of Sass and manually include vendor assets in the repo, so gulp tasks in this project are pretty minimal.

Use the following steps to setup gulp for this project.

1. Run `npm install` from the root directory to install node packages defined in package.json.
2. Run `gulp default` to compile static assets.
3. Make sure up-to-date concatenated/minified files (minified files in `static_files/`) are pushed to the repo when changes are made.
