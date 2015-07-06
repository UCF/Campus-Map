To create the illustrated tiles, you will need the illustrated map (it's ~350mb and way too large to attach to this project will need to contact University Marketing at UCF if needed).

The native size of the illustration is about 5250px x 7000px  (3:4 ratio)

Note: 1 map tile is 256px x 256px

The smallest resolution of the map will sit at 2 tiles wide by 2 tiles tall.  Each time a zoom level is increased, the dimensions are doubled.

Use the attached photoshop script to chop it into tiles.  Place the `map tiles` directory on your desktop and run the script. Note, the script will fail/throw an error while saving if the directory does not exist.

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