# Deploy

Instructions for deploying tagged versions

## 0.1.0

Lots of model changes that will have to be merged.

First - create an export for posterity:
    python manage.py dumpdata --indent 4 campus > apps/campus/fixtures/2010-03-18.json

Export just the buildings:
    python manage.py dumpdata --indent 4 campus.building > apps/campus/fixtures/buildings-backup.json

I know some buildings have been added and modified, might want to inspect the two fixtures:
    apps/campus/fixtures/buildings.json
and the one that was just created, `buildings-backup.json`

Do some magic to make these files one `buildings.json` fixture.

Commit `buildings.json` back to github.

Reset campus and load fixtures:
    python manage.py reset campus
    python manage.py loaddata buildings campuses sidewalks locations bikeracks phones