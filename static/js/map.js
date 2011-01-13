/*	
	CAMPUS MAP
	UCF Web Communcations
	Summer 2010
	
	valuable resources:
	 - http://code.google.com/apis/maps/documentation/javascript/basics.html
	 - http://econym.org.uk/gmap/custommap.htm
	 - http://groups.google.com/group/Google-Maps-API

*/

// debug
if(!window.console ) {
	window.console = { log: function() { return; } };
}

/******************************************************************************\
 Global Namespace
 the only variable exposed to the window should be Campus_Map
\******************************************************************************/
var Campus_Map = {
	settings : {
		drawn_min_zoom : 12,
		drawn_max_zoom : 17,
		buildings      : false,  // UCF's building data, remove google's
		locations      : false,  // Yellow markers for each location
		traffic        : false
	}
};

Campus_Map.init = function(){
	this.resize();
	//Campus_Map.location_url = Campus_Map.location_url.replace('1', '');
	//Campus_Map.search_url	  = Campus_Map.search_url.replace('foo', '');
};


/******************************************************************************\
 Helpers, Vars, and Placeholders
\******************************************************************************/
Campus_Map.ajax = { abort : function(){} };
Campus_Map.infoWindow = { close : function(){} };


/******************************************************************************\
 Create Google Map
	- stores in Campus_Map.map
\******************************************************************************/
Campus_Map.gmap = function(){
	
	// arbitrary point, looks good on load
	var myLatlng = new google.maps.LatLng(28.6018,-81.1995);
	
	var myOptions = {
		zoom: 16,
		center: myLatlng,
		mapTypeId: google.maps.MapTypeId.ROADMAP,
		panControl: true,
		panControlOptions: {
			position: google.maps.ControlPosition.LEFT_TOP
		},
		zoomControl: true,
		zoomControlOptions: {
			style: google.maps.ZoomControlStyle.LARGE,
			position: google.maps.ControlPosition.LEFT_TOP
		},
		streetViewControl: true,
		streetViewControlOptions: {
			position: google.maps.ControlPosition.LEFT_TOP
		}
	};
	
	// create map
	this.map = new google.maps.Map(document.getElementById("map-canvas"), myOptions);
	
	// add layers & controls
	this.layers.update();
	this.controls();
	
};


/******************************************************************************\
 Controls
	- styles native maptype controls
	- adds custom controls
\******************************************************************************/
Campus_Map.controls = function(){
	
	var settings = $.extend({ 'google': true }, this.options);
	
	// maptypes style
	var restyle = function(){
		var controls = $('.gmnoprint');
		
		if(controls.length < 1){
			//map glitch, not finished loading
			window.setTimeout(restyle, 100);
			return;
		}
		
		if(jQuery.browser.name == 'msie'){
			// won't be first control, need to search for it
			controls.filter(function(){
				if(this.style && this.style.top == "0px" && this.style.right == "0px"){
					$(this).attr('id','maptypes');
					$(this).find('div:first div:first').html('UCF');
				}
			});
		} else {
			controls.first().attr('id','maptypes');
			controls.first().find('div:first div:first').html('UCF');
		}
	};
	
	google.maps.event.addListener(this.map, "tilesloaded", restyle);
	
	// search
	var searchUI = document.createElement('div');
	searchUI.id = "search";
	searchUI.innerHTML = '<form method="get" action="' + 
		Campus_Map.urls.search + '" id="search-form"><input '+
		'type="text" name="q"><a id="search-submit" onclick'+
		'="$(\'#search-form\').submit()">search</a></form>';
	this.map.controls[google.maps.ControlPosition.TOP_LEFT].push(searchUI);
	
	// menu
	var menuUI = document.createElement('div');
	menuUI.id = "menu";
	if(Campus_Map.menu_html === 'undefined' || !Campus_Map.menu_html){
		Campus_Map.menu_html = $('#menu-html').html();
		menuUI.innerHTML = Campus_Map.menu_html;
		$('#menu-html').html('');
	} else {
		menuUI.innerHTML = Campus_Map.menu_html;
	}
	Campus_Map.menu = $(menuUI);
	this.map.controls[google.maps.ControlPosition.RIGHT_TOP].push(menuUI);
	
	// buildings checkbox
	var bcb = Campus_Map.menu.find('#buildings')[0];
	$(bcb).attr('checked', Campus_Map.settings.buildings);
	$(bcb).click(function(){
		Campus_Map.settings.buildings = $(this).is(':checked');
		Campus_Map.layers.buildings.update();
	});
	
	// traffic checkbox
	var tcb = Campus_Map.menu.find('#traffic')[0];
	$(tcb).attr('checked', Campus_Map.settings.traffic);
	$(tcb).click(function(){
		Campus_Map.settings.traffic = $(this).is(':checked');
		Campus_Map.layers.traffic.update();
	});
	
}

/******************************************************************************\
 Map Layers
\******************************************************************************/
Campus_Map.layers = {
	update : function(){
		this.buildings.update();
		this.traffic.update();
	},
	
	/* Google's traffic layer */
	traffic : {
		loaded : false,
		layer  : { setMap:function(){} },
		update : function() {
			if(!this.loaded){
				this.layer  = new google.maps.TrafficLayer();
				this.loaded = true;
			}
			var on = Campus_Map.settings.traffic;
			if(on){
				this.layer.setMap(Campus_Map.map);
			} else {
				this.layer.setMap(null);
			}
		}
	},
	
	/* Display building shapes based on UCF data */
	buildings : {
		loaded : false,
		layer  : { setMap:function(){} },
		load   : function(){
			if(!this.loaded){
				// send KML to google
				// http://code.google.com/apis/maps/documentation/javascript/overlays.html#KMLLayers
				this.layer = new google.maps.KmlLayer(Campus_Map.urls.kml, { preserveViewport : true });
				
				// strip map of google elements
				// http://code.google.com/apis/maps/documentation/javascript/maptypes.html#StyledMaps
				// http://gmaps-samples-v3.googlecode.com/svn/trunk/styledmaps/wizard/index.html
				var styles = [ { featureType: "landscape.man_made", elementType: "geometry", stylers: [ { visibility: "off" } ] },{ featureType: "poi.sports_complex", elementType: "geometry", stylers: [ { visibility: "off" } ] } ];
				var naked = new google.maps.StyledMapType( styles, { name : "Naked" } );
				Campus_Map.map.mapTypes.set('naked', naked);
				
				this.loaded = true;
			}
			Campus_Map.map.setMapTypeId('naked');
			this.layer.setMap(Campus_Map.map);
		},
		unload : function() {
			Campus_Map.map.setMapTypeId(google.maps.MapTypeId.ROADMAP);
			this.layer.setMap(null);
		},
		update : function(){
			var on = Campus_Map.settings.buildings;
			if(on) this.load(); else this.unload();
		}
	}
	
};


/******************************************************************************\
 Resize
	sets map to 100% height and width
	attaches function to window resize
\******************************************************************************/
Campus_Map.resize = function(){
	
	Campus_Map.resize_tries = 0;
	
	var browser = $.browser.name + "" + $.browser.versionX
	if(browser === "firefox2" || browser === "msie6") { return; }
	
	var resize = function(){
		var height = document.documentElement.clientHeight;
		var blackbar = document.getElementById('UCFHBHeader');
		height -= blackbar ? blackbar.clientHeight : 0;
		height -= $('#map header')[0].clientHeight;
		height -= document.getElementById('map-foot').clientHeight;
		height -= $('footer')[0].clientHeight;
		height -= 2; // top + bottom border
		
		var canvas   = document.getElementById('map-canvas');
		canvas.style.height = height + "px";
		
		// sometimes blackbar is slow to load
		if(!blackbar){
			if(++Campus_Map.resize_tries > 3) { return; }
			window.setTimeout(resize, 50);
		} else {
			Campus_Map.resize_tries = 0;
		}
		
		// iphone, hide url bar
		if(jQuery.os.name === "iphone"){
			height += 58;
			document.getElementById('map-canvas').style.height = height + "px";
			window.scrollTo(0, 1);
		}
	};
	
	resize();
	
	// if not mobile, attach resize fn to window
	if( jQuery.os.name === "iphone" || (
		jQuery.os.name === "linux" && jQuery.browser.name === "safari") ) { return; }	
	window.onresize = resize;
	
};


/******************************************************************************\
 Create illustrated map
	- 
\******************************************************************************/
Campus_Map.imap = function(){	 
	var CoordMapType= function(){};
	
	CoordMapType.prototype.tileSize = new google.maps.Size(256,256);
	CoordMapType.prototype.minZoom = 12;
	CoordMapType.prototype.maxZoom = 16; // have tiles for 17 as well (they're grainy)
	CoordMapType.prototype.alt = "UCF Illustrated Campus Map";	  

	CoordMapType.prototype.getTile = function(coord, zoom, ownerDocument) {
	  var div = ownerDocument.createElement('DIV');
	  div.style.width = this.tileSize.width + 'px';
	  div.style.height = this.tileSize.height + 'px';
	  div.style.backgroundImage = 'url("' + Campus_Map.media + 'img/illustrated_tiles/' + Campus_Map.imap.getTileUrl(coord, zoom) + '")';
	  return div;
	};
	
	var map;
	var worldsCorner = new google.maps.LatLng(85.04591,-179.92189);
	var coordinateMapType = new CoordMapType();

	var mapOptions = {
		zoom: 14,
		center: worldsCorner,
		mapTypeControl: false
	};
	this.map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);

	// Now attach the coordinate map type to the map's registry
	this.map.mapTypes.set('coordinate',coordinateMapType);

	// We can now set the map to use the 'coordinate' map type
	this.map.setMapTypeId('coordinate');
};

/******************************************************************************\
 Custom ULR generator for Map Tiles

 The entire map is placed in the far "upper left" corner of the world 
 (latititude 85, longitude -180) so the first tile requested is #1.	 Makes it
 easier to chop the map and do the math to determine bounds

 see "readme" in the map_tiles dir
\******************************************************************************/
Campus_Map.imap.getTileUrl = function(coord,zoom) {
	var tile = "zoom_" + zoom + "/" + zoom + "_" + coord.x + "_" + coord.y + ".jpg";
	var nope = "white.png"; //white tile

	// check to see if requested tile for this zoom is within bounds,
	// if not, return a whilte tile
	if(zoom < 12 || coord.y<0 || coord.x<0){
		return nope;
	} else if( zoom === 12){
		// map is 2 tiles tall, 3 wide (zero indexed)
		if(coord.y >1 || coord.x > 2){ return nope; }
	} else {
		// smallest map is 5x3
		// for each zoom a tile is divided equally into 4 parts
		var wide = 5;
		var tall = 3;
		var factor = window.Math.pow(2, (zoom - 13));
		if( coord.x >= wide*factor || coord.y >= tall*factor){ return nope; }
	}
	return tile;
};

/******************************************************************************\
 Plots location on the Google Map
	- locations are populated in the base template
\******************************************************************************/
Campus_Map.locationMarkers = function(){
	var map = this.map;
	var locations = this.locations;
	var image = new google.maps.MarkerImage(
		(this.media + 'img/markers/yellow.png'),
		new google.maps.Size(19, 19),
		new google.maps.Point(0,0),
		new google.maps.Point(9,9));
	for(var id in locations ) {
		var loc = locations[id];
		var latLng = new google.maps.LatLng(loc.x, loc.y);
		var marker = new google.maps.Marker({
			position: latLng,
			map: map,
			icon: image,
			locationId: id
			
		});
		google.maps.event.addListener(marker, 'click', function(event) {
			Campus_Map.locationInfo(this.locationId);
		});
	}
};


/******************************************************************************\
 Location Information
	- used when clicking marker
	- used when searching
\******************************************************************************/
Campus_Map.locationInfo = function(id){
	var locations = this.locations;
	if(locations[id] === undefined || !locations[id]){
		$('#search-help').html('No coordinate data available.  Check the <a href="admin/campus/location/' + id + '/">admin</a>.');
	} else {
		Campus_Map.ajax.abort();
		$("#search ul").html('');
		var latlng = new google.maps.LatLng(locations[id].x,locations[id].y);
		Campus_Map.map.panTo(latlng);
		Campus_Map.map.panBy(0, -100);
		this.infoWindow.close();
		this.infoWindow = new google.maps.InfoWindow({
			content: '<div id="location-info">Loading...</div>',
			position: latlng
		});
		this.infoWindow.open(this.map);
		this.infoWindowListen = google.maps.event.addListener(this.infoWindow, 'domready', function(event) {
			Campus_Map.ajax = $.ajax({
				url: Campus_Map.location_url + id,
				success: function(html){
					google.maps.event.removeListener(Campus_Map.infoWindowListen);
					Campus_Map.infoWindow.setContent(html);
				},
				error: function(){
					google.maps.event.removeListener(Campus_Map.infoWindowListen);
					Campus_Map.infoWindow.setContent('<a href="'+this.url+'">Request</a> failed.  Check <a href="admin/campus/location/' + id + '/">location</a>.');
				}
			});
		});
	}
};


/******************************************************************************\
 Search
	- attach events to search input
\******************************************************************************/
Campus_Map.search = function(){
	$('#search input').focus();
	var location_list_item = false;
	
	$('#search input').keydown(function(event){
		Campus_Map.ajax.abort();
		
		//parse keycode
		var keyCode =
			document.layers ? event.which :
			document.all ? event.keyCode :
			document.getElementById ? event.keyCode : 0;
		
		//left and right keys
		if(keyCode===37 || keyCode ===39){ return; }
		
		//'down' key
		if(keyCode===40 && $('#search ul').html() !== ''){
			var li = $('#search .hover');
			
			if(li.length < 1){
				 $('#search li:first').addClass('hover');
				 return;
			}
			
			var next = li.next();
			if(next.length > 0){
				li.removeClass('hover');
				li.next().addClass('hover');
			}
			return;
			
		}
		
		//'up' key
		if(keyCode===38 && $('#search ul').html() !== ''){
			var li = $('#search .hover');
			if(li.length < 1) { return; }
			li.removeClass('hover');
			li.prev().addClass('hover');
			return;
		}
		
		//'enter' key
		if(keyCode===13){
			var li = $('#search .hover');
			if(li.length > 0){
				// parse location ID
				var id = li.find('a').attr('href').substring(1);
				Campus_Map.locationInfo(id);
				return;
			}
			li = $('#search li');
			if(li.length===1){
				var id = li.find('a').attr('href').substring(1);
				Campus_Map.locationInfo(id);
			}
			return;
		}
		
		// ajax search
		var q = $(this).val();
		if(!q){
			$("#search ul").html('');
			return;
		}
		
		$("#search ul").html('<li>Searching...</li>');
		Campus_Map.ajax = $.ajax({
			url: Campus_Map.urls.search,
			data: {q:q},
			success: function(html){
				//show results
				$("#search ul").html(html);
				//attach event to open info window
				$('#search li').click(function(event){
					event.preventDefault();
					var id = $(this).find('a').attr('href').substring(1);
					Campus_Map.locationInfo(id);
				});
			}
		});

	});//keydown
	
};//search
