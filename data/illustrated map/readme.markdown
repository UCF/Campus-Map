To create the illustrated tiles, you will need the illustrated map (it's ~350mb and way too large to attach to this project will need to contact University Marketing at UCF if needed).

The native size of the illustration is 7500px x 4500px  (5:3 ratio)

Note: 1 map tile is 256px x 256px

The smallest resolution of the map will sit at 5 tiles wide by 3 tiles tall.  Each time a zoom level is increased, the dimensions are doubled.  Using the table below, the map falls between zoom 15 and 16.  Instead of shrinking the map to 20x12 tiles, I enlarge it to 40x24 tiles.

Once you have an image at resolution 10240x6144, you can use the attached photoshop script to chop it into tiles.  Place the `map tiles` directory on your desktop and run the script.  Note, the script will fail/throw an error while saving if the directory does not exist.


    Zoom    dpi    Tile Resolution    Pixel Resolution
    ------------------------------------------------------
    13      72      5x3                1280  x   768
    14      144     10x6               2560  x  1536
    15      288     20x12              5120  x  3072
    16      576     40x24              10240 x  6144


not used:
`17          1152        80x48                   20480 x 12288`

