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

