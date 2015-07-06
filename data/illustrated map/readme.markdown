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

-- Post Script Actions --
The map applications requires a particular directory structure for the tile images. Use the following structure:

```
.
+-- white.png
+-- zoom-12
|	+-- 12-0-0.jpg
|	+-- 12-0-1.jpg
|	+-- ...
+-- zoom-13
|	+-- 13-0-0.jpg
|	+-- 13-0-1.jpg
|	+-- ...
+--	...
```

Unfortunately, the script will output the files with the format `[0-5]_x_x.jpg` with the 0 image being a full size image (which we do not use). To quickly rename the files you can use the `rename` utility (available for install with apt, yum and brew). Once installed use the following command to mass rename the files:

`rename 's/^1/12/' 1-*.jpg`

`rename 's/^2/13/' 2-*.jpg` and so on.

Then use a `mv` command to get the files in the appropriate directories: `mv 12-*.jpg zoom-12/`, `mv 13-*.jpg zoom-13/` and so on.