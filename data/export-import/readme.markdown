# Software needed

## GDAL - Geospatial Data Abstraction Library (python variant)

    $ sudo port install gdal +python26

This is using macports to install gdal with the python26 variant.  The python variant was what I was missing and took a while to figure out what was wrong.

This shit takes forever to compile and install, hours and hours.

afterward you should be able to run
    
    $ python
    Python 2.6.6
    >>> import osgeo
    >>>


# Exporting data from an ESRI shape file

Shapefile sample provided.

## KML
    ogr2ogr -f KML output.kml input.shp

## JSON
the `t_srs` option converts the points from meters to coordinates
    
    ogr2ogr -f geoJSON -t_srs EPSG:4326 buildings_export.json buildings.shp

[helpful resource](http://gis.stackexchange.com/questions/98/how-can-i-convert-kml-to-esris-shapefile-format) 


# Create / Update Buildings

`old_map_dump.py` is a dump from the old webcom map, this file should not be updated/edited

once `buildings_export.json` has been updated, you can run:
    
    python create_update_buildings.py

or if you want to completely destroy all buildings, import from old, and update new on top:
    
    python create_update_buildings.py destroy

and if you want all the output to a file:
    
    python create_update_buildings.py > ~/Desktop/output.txt
or
    
    python create_update_buildings.py destroy > ~/Desktop/output.txt



# New Process

## Analyze differences in the Land & Man. Data
1. Create json export of new data
1. Rename `ArcGIS Export Comparison/new_shp_export.json` to `old...`
1. Using `ArcGIS Export Comparison/export_compare.py` create output
1. Reconcile Merges through the admin
1. Look for missing merges in the "new building" and "old buildings" list

## Import Data
1. Copy the shp exports to `Import ArcGIS Updates`
1. run `Import ArcGIS Updates/import.py`
1. note, it's OK to exit the import script at any time and start again, changes are written to the results file

## Review
1. look at output again to make sure merges went well
1. scan building list for any unintentional duplicates

Sources of errors:
* capitalization of building names
* and building number change is viewed as a "new" and "lost" building

## Give any needed feedback back to land and management

Export data as GeoJSON:

    python manage.py geojson

from the the desktop:

    ogr2ogr -f 'ESRI Shapefile' campus_map.shp campus_map.geo.json -overwrite


