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
		buildings      : false,  // UCF's building data, remove google's
		points         : false,  // Yellow markers for each location
		traffic        : false
	},
	error : function(str) {
		var close = $('<a id="error-close">close</a>');
		close.click(function(e){
			e.preventDefault();
			$('#error').hide().html('');
		});
		var err = $('<p>' + str + '</p>').append(close);
		$('#error').html(err).show();
	}
};
/*global window, document, Image, google, $ */


try{ google; } // things have gone very wrong... where is google?!!!
catch(e){ Campus.error('Google Maps API is currently unavailable'); }

Campus.init = function(){
	this.resize();
	
	// preload images
	var spin = new Image(); spin.src = Campus.urls['static'] + 'style/img/spinner.gif';
	var mark = new Image(); mark.src = Campus.urls['static'] + 'images/markers/gold-with-dot.png';
	var shad = new Image(); shad.src = Campus.urls['static'] + 'images/markers/shadow.png';
	
	// check for errors
	$('#error-close').click(function(e){
		e.preventDefault();
		$('#error').hide().html('');
	});
	
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
		maxZoom :16, //can go up to 18
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
				var type = Campus.map.mapTypeId;
				var prev = Campus.prevMapType;
				Campus.prevMapType = type;
				if(prev !== 'illustrated' && type !== 'illustrated'){
					//switching between compatible google maps
					return;
				}
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
	var tile = "zoom-" + zoom + "/" + zoom + "-" + coord.x + "-" + coord.y + ".jpg";
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
	
	return 'url("http://cdn.ucf.edu/map/tiles/' +tile+'")';
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
		
	// looking at a location
	// not using Campus.info() because that uses an ajax reqeust to load location (already delivered here)
	if(Campus.settings.location){
		var loc = Campus.settings.location;
		if(!loc.googlemap_point || !loc.googlemap_point.length){
			var err = '<code>' + loc.name + '</code> does not have a map location';
			Campus.error(err);
			return;
		}
		var latlng = new google.maps.LatLng(loc.googlemap_point[0], loc.googlemap_point[1]);
		Campus.map.panTo(latlng);
		Campus.info();
		Campus.infoBox.show(loc.name, latlng, loc.profile_link);
		Campus.stage.html(loc.info);
		Campus.menu.show('location');
		
		
		if(!loc.number){
			$('#email').hide();
		} else {
			var permalink = Campus.permalink.replace("%s", loc.number);
			var mailto = Campus.mailto(loc.name, permalink);
			$('#email').attr('href', mailto).show();
		}
	}
	
	// Checkboxes:
	//   the setting name and checkbox ID are the same
	//   cycle through each and add onclick event to init appropriate layer
	//   if layer is already turned on, "check" the checkbox
	var checkboxes = ['buildings', 'sidewalks', 'bikeracks', 'emergency_phones', 'parking', 'traffic'];
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
	
	// upper-right email icon
	Campus.menuIcons  = $('#menu-icons');
	Campus.permalink  = Campus.urls.base_url + '/?show=%s';
	Campus.mailto     = function(title, link){
		title   = escape(title);
		link    = escape(link);
		subject = escape("UCF Campus Map - ") + title;
		body    = title + escape("\n") + link;
		return "mailto:?subject=" + subject + "&body=" + body;
	}
	
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
			Campus.menuIcons.animate({"top" : 28 }, 300);
		} else {
			Campus.stageNext.animate({"width" : 230 }, 300);
			Campus.menuWin.animate({"margin-left" : -246 }, 300);
			Campus.labelStage.html(label);
			Campus.labelStage.removeClass('inactive');
			Campus.labelStage.animate({"padding-left" : 68 }, 300);
			Campus.label.addClass('inactive');
			Campus.menuPages.animate({"top" : -26 }, 300);
			Campus.menuIcons.animate({"top" :  2  }, 300);
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
			if(Campus.map.mapTypeId !== 'naked'){
				Campus.map.setMapTypeId('naked');
			}
			this.layer.setMap(Campus.map);
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
			
			if(on){ this.load(); } else { this.unload(); }
			
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
						var latlng = new google.maps.LatLng(point[0],point[1]);
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
						var latlng = new google.maps.LatLng(point[0],point[1]);
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
		markers: [],
		data   : null,
		loaded : false,
		layer  : { setMap:function(){} },
		load   : function(){
			var _this = this;
			
			// Corner case, first run, load assets and store
			if(!this.loaded){
				this.layer = new google.maps.KmlLayer(Campus.urls.parking_kml, { preserveViewport : true });
				
				// pull down with ajax
				Campus.ajax = $.ajax({
					url: Campus.urls.parking_json,
					dataType: 'json',
					success: function(data){
						_this.data   = data;
						_this.loaded = true;
						_this.load();
					}
				});
				return;
			}
			
			// Catch first run when markers haven't been generated
			if(this.markers.length < 1){
				// custom icon
				var icon   = new google.maps.MarkerImage(Campus.urls['static'] + '/images/markers/disabled.png', new google.maps.Size(32, 32), new google.maps.Point(0, 0));
				var shadow = new google.maps.MarkerImage(Campus.urls['static'] + '/images/markers/disabled.png', new google.maps.Size(32, 32), new google.maps.Point(0, 0), new google.maps.Point(0, 32));
				
				// create and place markers
				for(var spot in this.data.handicap){
					if(this.data.handicap.hasOwnProperty(spot)){
						spot       = this.data.handicap[spot];
						var point  = spot.googlemap_point;
						var latlng = new google.maps.LatLng(
							spot.googlemap_point[0],
							spot.googlemap_point[1]
						);
						this.markers.push(
							new google.maps.Marker({
								icon:icon,
								clickable: false,
								position: latlng, 
								map: Campus.map
							})
						);
					}
				}
			}
			
			// Common case, display assets on map
			this.layer.setMap(Campus.map); // Set parking lot kml layer
			
			// Set markers to visible
			for(var i = 0; i < this.markers.length; i++){
				var marker = this.markers[i];
				if(marker.setVisible){ marker.setVisible(true);}
			}
			return;
		},
		unload : function() {
			if(!this.loaded){ return; }
			this.layer.setMap(null);
			
			for(var i = 0; i < this.markers.length; i++){
				var marker = this.markers[i];
				if(marker.setVisible){ marker.setVisible(false); }
			}
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
Campus.infoMarker = false;
Campus.infoBox    = false;
Campus.info = function(id, pan){
	
	// init infoMarker
	// poor marker, not really being used anymore now that we have the infobox
	if(!Campus.infoMarker){
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
		Campus.infoMarker = marker;
	}
	
	// init infoBox
	if(!Campus.infoBox){
		var box = document.createElement("div");
		$(box).attr('id', 'info-box');
		box.innerHTML = "Campus Map InfoBox";
		var options = {
			content:     box,
			alignBottom: true,
			pixelOffset: new google.maps.Size(-18, -3),
			maxWidth:    0,
			closeBoxURL: "",
			pane:        "floatPane",
			infoBoxClearance: new google.maps.Size(1, 1),
			enableEventPropagation: false
		};
		Campus.infoBox = new InfoBox(options);
		Campus.infoBox.content = function(txt, link){
			if(link) txt = '<a href="' + link + '">' + txt + '</a>';
			var testBox = $('<div id="testBox" class="iBox">' + txt + '</div>')[0];
			$('body').append(testBox).each(function(){
				var iBox = $('<div class="iBox">' + txt + '</div>')[0];
				var width = testBox.offsetWidth + "px";
				iBox.style.width = width;
				Campus.infoBox.setContent(iBox);
				if($.browser.name === "msie"){
					// IE sucks hard
					$(Campus.infoBox.content_).html(txt);
				}
			});
		}
		Campus.infoBox.show = function(txt, loc, link){
			Campus.infoBox.content(txt, link);
			if(loc.length == 2) loc = new google.maps.LatLng(loc[0], loc[1]);
			Campus.infoBox.setPosition(loc);
			Campus.infoBox.open(Campus.map);
			return false;
		}
	}
	
	if(!id || id==="null" || id==="searching"){ 
		// called empty, done to init
		return; 
	}
	
	// show in menu
	Campus.menu.show('Location');
	
	if(Campus.ajax){ Campus.ajax.abort(); }
	Campus.stage.html('<div class="item load">Loading...</div>');
	$('#email').hide()
	var url = Campus.urls.location.replace("%s", id);
	
	Campus.ajax = $.ajax({
		url: url,
		dataType: 'json',
		success: function(data){
			var name = data.name;
			var point = (Campus.map.mapTypeId === 'illustrated') ? 'illustrated_point' : 'googlemap_point';
			Campus.stage.html(data.info);
			if(!data[point] || !data[point].length){
				var err = '<code>' + name + '</code> does not have a map location';
				Campus.error(err);
				return;
			}
			var latlng = new google.maps.LatLng(data[point][0], data[point][1]);
			Campus.infoBox.show(name, latlng, data.profile_link);
			
			var permalink = Campus.permalink.replace("%s", id);
			var mailto = Campus.mailto(name, permalink);
			$('#email').attr('href', mailto).show();
			
			if(pan){ Campus.map.panTo(latlng);  }
		},
		error: function(){
			Campus.stage.html('<div class="item">Error, request failed for building: ' + id + '</div>');
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
	
	$.fn.mapBox = function() {
		// a small jquery plugin to parse attributes and show map infobox
		return this.each(function() {
			Campus.info(); // ensure info box is init
			var link = $(this).find('a');
			var id = link.attr('data-pk');
			if(!Campus.points || !Campus.points[id]){
				Campus.infoBox.close();
				return;
			}
			var point = (Campus.map.mapTypeId === 'illustrated') ? 'ipoint' : 'gpoint';
			var p = Campus.points[id][point];
			if(!p || !p[0] || !p[1]){
				Campus.infoBox.close();
				return;
			}
			var latlng = new google.maps.LatLng(p[0], p[1]);
			var title = Campus.points[id]['name'];
			var url = link.attr('href');
			Campus.infoBox.disableAutoPan_=true;
			Campus.infoBox.show(title, latlng, url);
		});
	}
	
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
				 $('#search li:first').addClass('hover').mapBox();
				 return;
			}
			
			var next = li.next();
			if(next.length > 0){
				li.removeClass('hover');
				li.next().addClass('hover').mapBox();
			}
			return;
		}
		
		//'up' key
		if(keyCode===38 && $('#search ul').html() !== ''){
			li = $('#search .hover');
			if(li.length < 1) { return; }
			li.removeClass('hover');
			li.prev().addClass('hover').mapBox();
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
			if(q.length > 1) {
				search.find('ul').html('<li><a data-pk="searching">Searching&hellip;</a></li>');
				Campus.ajax = $.ajax({
					url: Campus.urls.search + '.json',
					data: {q:q},
					success: function(response, status){
						function highlight_term(string, term) {
							// Wraps a specified term with start and end wraps. Preserves capitalization
							var low_sub  = string.toLowerCase();
							var term_loc = low_sub.indexOf(term.toLowerCase());
							if(term_loc > - 1) {
								return string.substr(0, term_loc) + '<span class="highlight">' + string.substr(term_loc, term.length) + '</span>' + string.substr(term_loc+ term.length);
							} else {
								return string;
							}
						}
						
						$('#search > ul').empty()
						
						if (response.results != undefined && response.results.locations != undefined) {
							// Treat buildings as the top level element
							var locs   = response.results.locations,
								orgs   = response.results.organizations,
								phones = response.results.phonebook,
								query  = response.query;
						
							// TODO: Implement people output
						
							if(locs.length == 0 && orgs.length == 0) {
								$('#search > ul').append('<li><a data-pk="null">No results</a></li>')
							} else {
								
								var loc_org_matches = [],
									org_matches     = [],
									loc_matches     = [];
								
								// Associate organizations with their buildings
								$.each(orgs, function(index, org) {
									
									// Highlight query term
									org.name = highlight_term(org.name, query);
									
									var loc_index = null;
									$.each(locs, function(_index, loc) {
										if(loc.id == org.bldg_id) {
											loc_index = _index;
											return false;
										}
									});
									if(loc_index != null) {
										if(locs[loc_index].orgs == undefined) {
											locs[loc_index].orgs = []
										}
										locs[loc_index].orgs.push(org);
									}
								});
								
								// Highlight the query term
								$.each(locs, function(index, loc) {
									
									var matches          = loc.link.match(/<a([^>]+)>([^<]*)<\/a>/),
										original_link    = loc.link;
									if(matches != null) {
										loc.link = '<a' + matches[1] + '>' +  highlight_term(matches[2], query) + '</a>';
									}
									if(loc.orgs != undefined && original_link.length != loc.link.length) {
										loc_org_matches.push(loc);
									} else if(loc.orgs != undefined && original_link.length == original_link.length) {
										org_matches.push(loc);
									} else {
										loc_matches.push(loc);
									}	
								});
								
								var count = 0;
								$.each(loc_org_matches.concat(org_matches, loc_matches), function(index, loc) {
									if(loc.orgs != undefined) {
										var org_string = '';
										$.each(loc.orgs, function(_index, org) {
											org_string += '<li>' + org.name + '</li>'
											count += 1
										});
										$('#search > ul').append('<li>' + loc.link + '<ul>' + org_string + '</ul></li>');
									} else {
										$('#search > ul').append('<li>' + loc.link + '</li>');
									}
									count += 1
									if(count  > 11) {
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