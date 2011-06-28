/*	
	CAMPUS MAP
	UCF Web Communcations
	Summer 2010
	
	valuable resources:
	 - http://code.google.com/apis/maps/documentation/javascript/basics.html
	 - http://econym.org.uk/gmap/custommap.htm
	 - http://groups.google.com/group/Google-Maps-API

*/

/******************************************************************************\
 Global Namespace
 the only variable exposed to the window should be Campus
\******************************************************************************/
var Campus = {
	settings : {
		drawn_min_zoom : 12,
		drawn_max_zoom : 17,
		buildings      : false,  // UCF's building data, remove google's
		points         : false,  // Yellow markers for each location
		traffic        : false
	}
};
/*global window, document, Image, google, $ */

Campus.init = function(){
	this.resize();
	
	// preload images
	var spin = new Image(); spin.src = Campus.urls['static'] + 'style/img/spinner.gif';
	var mark = new Image(); mark.src = Campus.urls['static'] + 'images/markers/gold-with-dot.png';
	var shad = new Image(); shad.src = Campus.urls['static'] + 'images/markers/shadow.png';
	
	// register illustrated map and create map
	Campus.maps[this.settings.map]();
};

/******************************************************************************\
 Helpers, Vars, and Placeholders
\******************************************************************************/
Campus.ajax = { abort : function(){} };
Campus.map  = false;

if(!window.console ) { window.console = { log: function() { return; } }; }

Array.prototype.has=function(v){
	var i;
	for (i=0;i<this.length;i++){
		if (this[i]===v){ return true; }
	}
	return false;
};

/******************************************************************************\
 Maps Wrapper
	houses map options, custom maps, and functions to create the maps
\******************************************************************************/
Campus.maps = {
	
	// Map options for the default Google Map
	gmap_options : {
		zoom: 16,
		center: new google.maps.LatLng(28.6018,-81.1995),
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
		},
		mapTypeControlOptions: {
			mapTypeIds: [google.maps.MapTypeId.ROADMAP, google.maps.MapTypeId.SATELLITE, 'illustrated']
		}
	},
	
	// Custom Map type for the Illustrated Map
	// http://code.google.com/apis/maps/documentation/javascript/maptypes.html#BasicMapTypes
	// note: this code looks a little different than the example because I'm simply
	// creating an object instead of instantiating one with the "new" keyword
	imap_type : {
		tileSize : new google.maps.Size(256,256),
		minZoom: 12,
		maxZoom :19,
		getTile : function(coord, zoom, ownerDocument) {
		  var div = ownerDocument.createElement('div');
		  div.style.width = this.tileSize.width + 'px';
		  div.style.height = this.tileSize.height + 'px';
		  div.style.backgroundImage = this.bg(coord,zoom);
		  return div;
		},
		name : "Illustrated",
		alt : "Show illustrated map"
	},
	imap_options : {
		zoom : 14,
		center : new google.maps.LatLng(85.04591,-179.92189), // world's corner
		mapTypeId : 'illustrated',
		mapTypeControl : true
	},
	
	/* Called from Campus.init - make a map! */
	create : function(options){
		Campus.prevMapType = false;
		if(!Campus.map){
			// init map, switching between map types is not straight-forward
			// must rezoom and recenter because illustrated map sits WAY far away
			Campus.map = new google.maps.Map(document.getElementById("map-canvas"), options);
			Campus.map.mapTypes.set('illustrated',Campus.maps.imap_type);
			google.maps.event.addListener(Campus.map, 'maptypeid_changed', function() {
				// TODO: fix building toggling so it doesn't change zoom
				// TODO: this also breaks traffic
				var type = Campus.map.mapTypeId;
				var options = (type === 'illustrated') ? Campus.maps.imap_options : Campus.maps.gmap_options;
				//Campus.map.setOptions(options); //super slow
				Campus.map.setZoom(options.zoom);
				Campus.map.setCenter(options.center);
				Campus.layers.update();
			});
		}
	},
	gmap : function(){
		this.create(this.gmap_options);
		Campus.map.campus_center = this.gmap_options.center;
		Campus.layers.update();
		Campus.controls();
	},
	imap : function(){
		this.create(this.imap_options);
	}
};

/******************************************************************************\
 Custom URL generator for Map Tiles
	The entire map is placed in the far "upper left" corner of the world 
	(latititude 85, longitude -180) so the first tile requested is #1.  Makes
	it easier to chop the map and do the math to determine bounds
\******************************************************************************/
Campus.maps.imap_type.bg = function(coord,zoom) {
	var tile = "zoom_" + zoom + "/" + zoom + "_" + coord.x + "_" + coord.y + ".jpg";
	var nope = "white.png";

	// check to see if requested tile for this zoom is within bounds,
	// if not, return a whilte tile
	if(zoom < 12 || coord.y<0 || coord.x<0){
		tile = nope;
	} else if( zoom === 12){
		// map is 2 tiles tall, 3 wide (zero indexed)
		if(coord.y >1 || coord.x > 2){ tile = nope; }
	} else {
		// smallest map is 5x3
		// for each zoom a tile is divided equally into 4 parts
		var wide = 5;
		var tall = 3;
		var factor = Math.pow(2, (zoom - 13));
		if( coord.x >= wide*factor || coord.y >= tall*factor){ tile = nope; }
	}
	
	return 'url("' 
		+ 'http://webcom.dev.smca.ucf.edu/media/map_old/' 
		+ 'img/illustrated_tiles/' + tile + '")';
};


/******************************************************************************\
 Controls
	- create, init, and push controls onto google map
	- inspect settings and manipulat map as needed
\******************************************************************************/
Campus.controls = function(){
	
	// search
	var searchUI = document.createElement('div');
	searchUI.id = "search";
	searchUI.innerHTML = '<form method="get" action="' + 
		Campus.urls.search + '" id="search-form"><input '+
		'type="text" name="q" autocomplete="off"><a id="search-submit" onclick'+
		'="$(\'#search-form\').submit()">search</a></form>';
	this.map.controls[google.maps.ControlPosition.TOP_LEFT].push(searchUI);
	Campus.searchUI = searchUI;
	this.search(); // init search
	
	// menu
	Campus.menu = $('#menu-wrap');
	this.menuInit();
	this.map.controls[google.maps.ControlPosition.RIGHT_TOP].push(this.menu[0]);
		
	var rc, loc, latlng;
	// looking at a regional campus
	if(Campus.settings.regional_campus){
		rc = Campus.settings.regional_campus;
		latlng = new google.maps.LatLng(rc.googlemap_point[0], rc.googlemap_point[1]);
		Campus.map.panTo(latlng);
		Campus.info(); //inits info marker
		Campus.infoMaker.setPosition(latlng);
		$('#item-title').html(rc.description);
		$('#item-desc').html(rc.html);
	}
	
	// looking at a location (very similar to regional campus)
	if(Campus.settings.location){
		loc = Campus.settings.location;
		latlng = new google.maps.LatLng(loc.googlemap_point[0], loc.googlemap_point[1]);
		Campus.map.panTo(latlng);
		Campus.info();
		Campus.infoMaker.setPosition(latlng);
		$('#item-title').html(loc.name);
		$('#item-desc').html(loc.info);
	}
	
	// Checkboxes:
	//   the setting name and checkbox ID are the same
	//   cycle through each and add onclick event to init appropriate layer
	//   if layer is already turned on, "check" the checkbox
	var checkboxes = ['buildings', 'sidewalks', 'bikeracks', 'emergency_phones', 'parking'];
	var i, id;
	var make_onclick = function(layer){
		return function(){
			Campus.settings[layer] = $(this).is(':checked');
			Campus.layers[layer].update();
		};
	};
	for(i=0; i<checkboxes.length; i++){
		id = checkboxes[i];
		$('#' + id)
			.click(make_onclick(id))
			.attr('checked', Campus.settings[id]);
	}
};

/******************************************************************************\
 Menu
	the menu is paginated, the separate pages are floating in a wide
	"menu-window" (2000px) with the wrapper set to overflow:hidden.  The window
	is shuffled left/right to display different pages.
\******************************************************************************/
Campus.menuInit = function(){

	// sliding windows
	Campus.menuWin = $('#menu-window');
	Campus.menuWin.equalHeights();
	Campus.menuMargin = -246;
	$('.nav').click(function(){
		var winNum = $(this).attr('data-nav');
		$('.nav').removeClass('active');
		$('#nav-'+winNum).addClass('active');
		Campus.menuMargin = '-' + (Number(winNum) * 230 + 16);
		Campus.menuWin.animate({"margin-left" : Campus.menuMargin }, 300);
		$.cookie('menu_page', winNum);
	});
	
	var menu_page = Number($.cookie('menu_page'));
	if(menu_page > 1){
		$('#nav-' + menu_page).click();
	}

	Campus.stage = $('#menu-stage');
	Campus.stageVisible = false;
	Campus.stageNext  = $('#menu-stage-next');
	Campus.label      = $('#menu-label-main');
	Campus.labelStage = $('#menu-label-stage');
	Campus.menuPages  = $('#menu-pages');

	Campus.label.click(function(){
		Campus.menu.show('main');
	});
	Campus.labelStage.click(function(){
		Campus.menu.show($(this).html());
	});

	Campus.menu.show = function(label){
		if(label==='main'){
			Campus.stageNext.animate({"width" : 0 }, 300);
			Campus.menuWin.animate({"margin-left" : Campus.menuMargin }, 300);
			Campus.label.removeClass('inactive');
			Campus.labelStage.addClass('inactive');
			Campus.menuPages.animate({"top" : 2 }, 300);
		} else {
			Campus.stageNext.animate({"width" : 230 }, 300);
			Campus.menuWin.animate({"margin-left" : -246 }, 300);
			Campus.labelStage.html(label);
			Campus.labelStage.removeClass('inactive');
			Campus.labelStage.animate({"padding-left" : 68 }, 300);
			Campus.label.addClass('inactive');
			Campus.menuPages.animate({"top" : -26 }, 300);
		}
	};

	// menu hiding
	var menuToggle = function(){
		if(Campus.menuHidden){
			//show
			Campus.menuWin.slideDown();
			Campus.menu.removeClass('closed');
			Campus.menu.animate({"opacity" : 1 }, 300);
			Campus.menuHidden = false;
			$.cookie('hide_menu', false);
		} else {
			//hide
			Campus.menuWin.slideUp();
			Campus.menu.animate({"opacity" : 0.5 }, 300, function(){
				Campus.menu.addClass('closed');
			});
			Campus.menuHidden = true;
			$.cookie('hide_menu', true);
		}
		return false;
	};
	// this doesn't seem intuitive (setting 'true' to false) but the value 
	// needs to be flipped so the 'toggle' function can be used (we dont' want
	// to toggle away from previous state)
	Campus.menuHidden = $.cookie('hide_menu') === 'true' ? false : true;
	menuToggle();
	$('#menu-hide').click(menuToggle);
	$('#menu-screen').click(menuToggle);
};


/******************************************************************************\
 Map Layers
\******************************************************************************/
Campus.layers = {
	update : function(){
		this.buildings.update();
		this.points.update();
		this.sidewalks.update();
		this.bikeracks.update();
		this.emergency_phones.update();
		this.parking.update();
	},
	
	/* Google's traffic layer */
	traffic : {
		layer  : new google.maps.TrafficLayer(),
		update : function() {
			var on = Campus.settings.traffic;
			if(on){
				this.layer.setMap(Campus.map);
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
				this.layer = new google.maps.KmlLayer(Campus.urls.buildings_kml, { preserveViewport : true, suppressInfoWindows: true, clickable: false });
				this.loaded = true;
			}
			if(Campus.map.mapTypeId === 'naked'){
				this.layer.setMap(Campus.map);
			} else {
				Campus.map.setMapTypeId('naked');
			}
		},
		unload : function() {
			if(!this.loaded){ return; }
			if(Campus.map.mapTypeId !== 'roadmap'){ Campus.map.setMapTypeId('roadmap'); }
			this.layer.setMap(null);
		},
		naked  : false,
		update : function(){
			if(Campus.map.mapTypeId === 'illustrated'){ return; }
			var on = Campus.settings.buildings;
			if(on){ this.load(); } else { this.unload(); }
			
			if(!this.naked){
				// create naked map type, strip map of google elements
				// http://code.google.com/apis/maps/documentation/javascript/maptypes.html#StyledMaps
				// http://gmaps-samples-v3.googlecode.com/svn/trunk/styledmaps/wizard/index.html
				var styles = [ 
					{ featureType: "landscape.man_made", elementType: "geometry", stylers: [ { visibility: "off" } ] },
					{ featureType: "poi.school", elementType: "geometry", stylers: [ { visibility: "off" } ] },
					{ featureType: "poi.sports_complex", elementType: "geometry", stylers: [ { visibility: "off" } ] } 
				];
				var naked = new google.maps.StyledMapType( styles, { name : "Naked" } );
				Campus.map.mapTypes.set('naked', naked);
			}
			
		}
	},
	
	/* points populated in base template */
	points : {
		update : function(){
			// should only run once
			if(!Campus.settings.points){ return; }
			var map = Campus.map;
			var points = Campus.points;
			var image = new google.maps.MarkerImage(
				(Campus.urls['static'] + 'images/markers/yellow.png'),
				new google.maps.Size(19, 19),
				new google.maps.Point(0,0),
				new google.maps.Point(10,10));
			var point = (Campus.map.mapTypeId === 'illustrated') ? 'ipoint' : 'gpoint';
			var id;
			for(id in points ) {
				if(points.hasOwnProperty(id)){
					var p = points[id][point];
					if(!p || !p[0] || !p[1]){ continue; }
					var latLng = new google.maps.LatLng(p[0], p[1]);
					var marker = new google.maps.Marker({
						position: latLng,
						map: map,
						icon: image,
						location: id
					});
					google.maps.event.addListener(marker, 'click', function(event) {
						Campus.info(this.location, false);
					});
				}
			}
		}
	},
	
	/* Display sidewalk lines based on UCF data */
	sidewalks : {
		loaded : false,
		layer  : { setMap:function(){} },
		load   : function(){
			if(!this.loaded){
				this.layer = new google.maps.KmlLayer(Campus.urls.sidewalks_kml, { preserveViewport : true, suppressInfoWindows: true, clickable: false });
				this.loaded = true;
			}
			this.layer.setMap(Campus.map);
		},
		unload : function() {
			if(!this.loaded){ return; }
			this.layer.setMap(null);
		},
		update : function(){
			var on = Campus.settings.sidewalks;
			if(on){ this.load(); } else { this.unload(); }
		}
	},
	
	/* Place marker on each bike rack */
	bikeracks : {
		loaded  : false,
		geo     : false,
		markers : [],
		load    : function(){
			var i;
			
			// load geo location
			if(!this.loaded){
				// bikeracks delivered with request
				if( Campus.settings.bikeracks_geo !== undefined && Campus.settings.bikeracks_geo.features) {
					this.geo = Campus.settings.bikeracks_geo;
					this.loaded = true;
				} else {
					// pull down with ajax
					Campus.ajax = $.ajax({
						url: Campus.urls.bikeracks,
						dataType: 'json',
						success: function(data){
							Campus.layers.bikeracks.geo = data;
							Campus.layers.bikeracks.loaded = true;
							Campus.layers.bikeracks.load();
						}
					});
					return;
				}
			}
			
			// markers have already been created, show them
			if(this.markers.length > 0){
				for(i=0; i < this.markers.length; i++){
					var marker = this.markers[i];
					if(marker.setVisible){ marker.setVisible(true); }
				}
				return;
			}
			
			// create and place markers
			for(i in this.geo.features){
				if(this.geo.features.hasOwnProperty(i)){
					var rack = this.geo.features[i];
					if(rack.geometry && rack.geometry.coordinates){
						var point = rack.geometry.coordinates;
						var latlng = new google.maps.LatLng(point[1],point[0]);
						this.markers.push(
							new google.maps.Marker({
								clickable: false,
								position: latlng, 
								map: Campus.map
							})
						);
					}
				}
			}
			
		},
		unload : function() {
			if(!this.loaded){ return; }
			var i;
			for(i=0; i< this.markers.length; i++){
				var marker = this.markers[i];
				if(marker.setVisible){ marker.setVisible(false); }
			}
		},
		update : function(){
			var on = Campus.settings.bikeracks;
			if(on){ this.load(); } else { this.unload(); }
		}
	},
	
	emergency_phones : {
		/* really similar to bikeracks (but with different icon), should probalby abstract this a bit */
		loaded  : false,
		geo     : false,
		markers : [],
		load    : function(){
			
			// load geo location
			if(!this.loaded){
				// geoinfo delivered with request
				if( Campus.settings.phones_geo !== undefined && Campus.settings.phones_geo.features) {
					this.geo = Campus.settings.phones_geo;
					this.loaded = true;
				} 
				// pull down with ajax
				else {
					
					Campus.ajax = $.ajax({
						url: Campus.urls.phones,
						dataType: 'json',
						success: function(data){
							Campus.layers.emergency_phones.geo = data;
							Campus.layers.emergency_phones.loaded = true;
							Campus.layers.emergency_phones.load();
						}
					});
					return;
				}
			}
			
			// markers have already been created, show them
			if(this.markers.length > 0){
				var i;
				for(i=0; i<this.markers.length; i++){
					var marker = this.markers[i];
					if(marker.setVisible){ marker.setVisible(true); }
				}
				return;
			}
			
			// custom icon
			var icon = new google.maps.MarkerImage(Campus.urls['static'] + '/images/markers/marker_phone.png', new google.maps.Size(20, 34));
			var shadow = new google.maps.MarkerImage(Campus.urls['static'] + '/images/markers/marker_phone.png', new google.maps.Size(37,34), new google.maps.Point(20, 0), new google.maps.Point(10, 34));
			
			// create and place markers
			var f;
			for(f in this.geo.features){
				if(this.geo.features.hasOwnProperty(f)){
					var phone = this.geo.features[f];
					if(phone.geometry && phone.geometry.coordinates){
						var point = phone.geometry.coordinates;
						var latlng = new google.maps.LatLng(point[1],point[0]);
						this.markers.push(
							new google.maps.Marker({
								icon:icon,
								shadow: shadow,
								clickable: false,
								position: latlng, 
								map: Campus.map
							})
						);
					}
				}
			}
			
		},
		unload : function() {
			if(!this.loaded){ return; }
			var i;
			for(i=0; i < this.markers.length; i++){
				var marker = this.markers[i];
				if(marker.setVisible){ marker.setVisible(false); }
			}
		},
		update : function(){
			var on = Campus.settings.emergency_phones;
			if(on){ this.load(); } else { this.unload(); }
		}
	},
	
	/* Display parking lots (much like sidewalks) */
	parking : {
		loaded : false,
		layer  : { setMap:function(){} },
		load   : function(){
			if(!this.loaded){
				this.layer = new google.maps.KmlLayer(Campus.urls.parking_kml, { preserveViewport : true });
				this.loaded = true;
			}
			this.layer.setMap(Campus.map);
		},
		unload : function() {
			if(!this.loaded){ return; }
			this.layer.setMap(null);
		},
		update : function(){
			var on = Campus.settings.parking;
			if(on){ this.load(); } else { this.unload(); }
		}
	}
	
};


/******************************************************************************\
 Locaiton Information
\******************************************************************************/
Campus.infoMaker = false;
Campus.info = function(id, pan){
	
	// init infoMaker
	if(!Campus.infoMaker){
		var image = new google.maps.MarkerImage(
				(Campus.urls['static'] + 'images/markers/gold-with-dot.png'),
				new google.maps.Size(32, 32),  // dimensions
				new google.maps.Point(0,0),  // origin
				new google.maps.Point(16,32)); // anchor 
		var shadow = new google.maps.MarkerImage(
				Campus.urls['static'] + 'images/markers/shadow.png',
				new google.maps.Size(59, 32),
				new google.maps.Point(0,0),
				new google.maps.Point(15, 32));
		var marker = new google.maps.Marker({
			map: Campus.map,
			shadow: shadow,
			clickable: false,
			icon: image
		});
		Campus.infoMaker = marker;
	}
	
	// show in menu
	Campus.menu.show('Location');
	
	if(!id || id==="null" || id==="searching"){ return; }
	if(Campus.ajax){ Campus.ajax.abort(); }
	var title = $('#item-title');
	var desc  = $('#item-desc');
	title.html("Loading...");
	desc.html("");
	desc.addClass('load');
	
	var url = Campus.urls.location.replace("%s", id);
	
	Campus.ajax = $.ajax({
		url: url,
		dataType: 'json',
		success: function(data){
			var name = data.name;
			if(data.abbreviation){ name += ' (' + data.abbreviation + ')'; }
			title.html(name);
			desc.html(data.info);
			desc.removeClass('load');
			var point = (Campus.map.mapTypeId === 'illustrated') ? 'illustrated_point' : 'googlemap_point';
			var latlng = new google.maps.LatLng(data[point][0], data[point][1]);
			Campus.infoMaker.setPosition(latlng);
			if(pan){ Campus.map.panTo(latlng);  }
		},
		error: function(){
			title.html("Error");
			desc.html("Request failed for building: " + id);
			desc.removeClass('load');
		}
	});
};


/******************************************************************************\
 Resize
	sets map to 100% height and width
	attaches function to window resize
\******************************************************************************/
Campus.resize = function(){
	Campus.resize_tries = 0;
	
	var browser = $.browser.name + " " + $.browser.versionX;
	if(browser === "firefox 2" || browser === "msie 6") { return; }
	
	var resize = function(){
		var height = document.documentElement.clientHeight;
		var blackbar = document.getElementById('UCFHBHeader');
		
		height -= blackbar ? blackbar.clientHeight : 0;
		height -= $('#map header')[0].clientHeight;
		height -= $('footer')[0].clientHeight;
		height -= 2 + 17; // borders + margin
		
		var canvas   = document.getElementById('map-canvas');
		canvas.style.height = height + "px";
		
		// iphone, hide url bar
		if($.os.name === "iphone"){
			height += 58;
			document.getElementById('map-canvas').style.height = height + "px";
			window.scrollTo(0, 1);
		}
	};
	
	resize();
	
	// if not mobile, attach resize fn to window
	if( $.os.name === "iphone" || (
		$.os.name === "linux" && $.browser.name === "safari") ) { return; }	
	window.onresize = resize;
	
};


/******************************************************************************\
 Search
	recieved quite a bit of feedback about this.  After watching people use the 
	search, an important observation is that people instinctively hit "enter" 
	after they type their search, even if the results are ajax'd.
	
	Getting the "intuitive" feel has been difficult.
	Currently the behavior is:
		* typing initiates search
		* ignore enter key while searching
		* single result + enter = display result & close search
		* up/down key = navigates & highlights results
		* highlighted result + enter = display result & close search
		* mouse clicking result = display result & keep search open
		* mouse clicking the search button = search results page
		* "more results" = search results page
		* escape key closes & cancels everything
\******************************************************************************/
Campus.search = function(){
	
	var search = $(Campus.searchUI),
		search_timer = null,
		search_typing_timeout = 400; // milliseconds
	var input  = search.find('input');
	
	search.keydown(function(event){
		//parse keycode
		var keyCode =
			document.layers ? event.which :
			document.all ? event.keyCode :
			document.getElementById ? event.keyCode : 0;
		
		//'enter' key
		if(keyCode===13){
			var li = $('#search .hover');
			var pk = li.find('a').attr('data-pk');
			if(pk === "more-results"){ return; }
			event.preventDefault();
			if(li.length < 1){ 
				li = $('#search li');
				if(li.length === 1) {
					pk = li.find('a').attr('data-pk');
				}
			}
			if(pk && pk !== "searching" && pk !== "null"){
				search.find('ul').remove(); 
			}
			Campus.info(pk, true);
		}
	});//keydown
		
	search.keyup(function(event){
		
		//parse keycode
		var keyCode =
			document.layers ? event.which :
			document.all ? event.keyCode :
			document.getElementById ? event.keyCode : 0;
		
		//enter, left, right, shift, control, option, command
		var ignore = [13, 37, 39, 16, 17, 18, 224];
		if(ignore.has(keyCode)){ return; }
		
		var li;
		
		//'down' key
		if(keyCode===40 && $('#search ul').html() !== ''){
			li = $('#search .hover');
			
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
			li = $('#search .hover');
			if(li.length < 1) { return; }
			li.removeClass('hover');
			li.prev().addClass('hover');
			return;
		}
		
		//'escape' key
		if(keyCode===27){
			Campus.ajax.abort();
			search.find('ul').remove();
			return;
		}
		
		// ajax search
		try{ Campus.ajax.abort(); }
		catch(e) { /* ie sux */ }
		
		var q = input.val();
		if(!q){
			search.find('ul').remove();
			return;
		} else {
			if(search.find('ul').length < 1){ 
				search.append('<ul></ul>');
			}
		}
		
		function _do_search() {
			if(q.length > 3) {
				search.find('ul').html('<li><a data-pk="searching">Searching&hellip;</a></li>');
				Campus.ajax = $.ajax({
					url: Campus.urls.search + '.json',
					data: {q:q},
					success: function(response, status){
						
						$('#search > ul').empty()
						
						var buildings = response.results
						
						if(buildings.length == 0) {
							$('#search > ul').append('<li><a data-pk="null">No results</a></li>')
						} else {
							$.each(buildings, function(index, building) {
								$('#search > ul').append('<li>' + building.link + '</li>');
								if((index + 1) > 9) {
									$('#search > ul').append('<li class="more"><a href="' + response.results_page_url + '" data-pk="more-results">More results &hellip;</a></li>');
									return false;
								}
							});
						}
								
						//attach event to open info window
						$('#search li:not(.more)').click(function(event){
							event.preventDefault();
							var pk = $(this).find('a').attr('data-pk');
							$('#search li').removeClass('hover');
							$(this).addClass('hover');
							Campus.info(pk, true);
						});
					}
				});
			} else {
				search.find('ul').html('<li><a data-pk="longer-search-term">A longer search term is required</a></li>');
			}
		}
		
		clearTimeout(search_timer);
		search_timer = setTimeout(_do_search,search_typing_timeout);

	});//keyup
	
	// hide results on mapclick
	google.maps.event.addListener(this.map, "click", function(){
		search.find('ul').remove(); 
	});
	
	// set z-index and focus, but must wait until loaded in dom
	Campus.searchStyle = function(){
		if($('#search input').length > 0){
			$('#search').css('z-index', 15);
			$('#search input').focus();
		} else {
			//console.log("search glitch");
			window.setTimeout(Campus.searchStyle, 250);
		}
	};
	Campus.searchStyle();
	
};//search


/******************************************************************************\
 JQuery Plugin: "EqualHeights"
 by: Scott Jehl, Todd Parker, Maggie Costello Wachs (http://www.filamentgroup.com)
\******************************************************************************/
Campus.equalFailTime = 0;
$.fn.equalHeights = function(px) {
	$(this).each(function(){
		var currentTallest = 0;
		$(this).children().each(function(i){
			if ($(this).height() > currentTallest) { currentTallest = $(this).height(); }
		});
		// for ie6, set height since min-height isn't supported
		if ($.browser.msie && $.browser.version === 6.0) { $(this).children().css({'height': currentTallest}); }
		$(this).children().css({'min-height': currentTallest});
		
		// hack to retry equal heights because it takes a while to render in dom
		if(currentTallest > 0){
			Campus.equalFailTime = 0;
		} else {
			Campus.equalFail = $(this);
			Campus.equalFailTime += 250;
			if(Campus.equalFailTime > 1000){ Campus.equalFailTime = 0; }
			else {
				window.setTimeout(function(){Campus.equalFail.equalHeights();}, Campus.equalFailTime);
			}
		}
	});
	return this;
};