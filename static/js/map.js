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

// helper
Array.prototype.has=function(v){
	for (i=0;i<this.length;i++){
		if (this[i]==v) return true;
	}
	return false;
}

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
	// creating an object instead of instantiating one wiht the "new" keyword
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
		if(!Campus.map){
			// init map, switching between map types is not straight-forward
			// must rezoom and recenter because illustrated map sits WAY far away
			Campus.map = new google.maps.Map(document.getElementById("map-canvas"), options);
			Campus.map.mapTypes.set('illustrated',Campus.maps.imap_type);
			google.maps.event.addListener(Campus.map, 'maptypeid_changed', function() {
				var options = (Campus.map.mapTypeId == 'illustrated') ? 
					Campus.maps.imap_options : Campus.maps.gmap_options;
				//Campus.map.setOptions(options);
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
 (latititude 85, longitude -180) so the first tile requested is #1.  Makes it
 easier to chop the map and do the math to determine bounds

 see "readme" in the map_tiles dir
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
		if(coord.y >1 || coord.x > 2) tile = nope;
	} else {
		// smallest map is 5x3
		// for each zoom a tile is divided equally into 4 parts
		var wide = 5;
		var tall = 3;
		var factor = Math.pow(2, (zoom - 13));
		if( coord.x >= wide*factor || coord.y >= tall*factor) tile = nope;
	}
	
	return 'url("' 
		+ 'http://webcom.dev.smca.ucf.edu/media/map_old/' 
		+ 'img/illustrated_tiles/' + tile + '")';
};


/******************************************************************************\
 Controls
	- styles native maptype controls
	- adds custom controls
\******************************************************************************/
Campus.controls = function(){
	
	var settings = $.extend({ 'google': true }, this.options);
	
	// maptypes style
	var restyle = function(){
		
		var controls = $('.gmnoprint');
		
		var styled = false;
		if(controls.length < 1){
			//map glitch, not finished loading
			console.log("maptype glitch");
			window.setTimeout(restyle, 100);
			return;
		}
		
		// find the maptype control
		controls.filter(function(){
			if(this.style && this.style.top == "0px" && this.style.right == "0px"){
				$(this).attr('id','maptypes');
				$(this).find('div:first div:first').html('UCF');
				styled = true;
			}
		});
		
		if(!styled){
			console.log("maptype glitch");
			window.setTimeout(restyle, 200);
		} else {
			console.log("map styled");
		}
		
	};
	
	// kills load time
	//google.maps.event.addListener(this.map, "tilesloaded", restyle);
	
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
	var menuUI = document.createElement('div');
	menuUI.id = "menu";
	if(Campus.menu_html === 'undefined' || !Campus.menu_html){
		Campus.menu_html = $('#menu-html').html();
		menuUI.innerHTML = Campus.menu_html;
		$('#menu-html').html('');
	} else {
		menuUI.innerHTML = Campus.menu_html;
	}
	Campus.menu = $(menuUI);
	var menuToggle = function(){
		if(Campus.menuHidden){
			//show
			Campus.menu.find('.body').show();
			Campus.menu.find('#menu-hide').html('hide');
			Campus.menu.removeClass('closed');
			Campus.menuHidden = false;
			$.cookie('hide_menu', false);
		} else {
			//hide
			Campus.menu.find('.body').hide();
			Campus.menu.find('#menu-hide').html('show');
			Campus.menu.addClass('closed');
			Campus.menuHidden = true;
			$.cookie('hide_menu', true);
		}
	};
	// this doesn't seem intuitive (setting 'true' to false) but the value 
	// needs to be flipped so the 'toggle' function can be used (we dont' want
	// to toggle away from previous state)
	Campus.menuHidden = $.cookie('hide_menu') == 'true' ? false : true;
	menuToggle();
	Campus.menu.find('#menu-hide').click(menuToggle);
	this.map.controls[google.maps.ControlPosition.RIGHT_TOP].push(menuUI);
	
	// looking at a regional campus
	if(Campus.settings.regional_campus){
		var rc = Campus.settings.regional_campus;
		var latlng = new google.maps.LatLng(rc.googlemap_point[0], rc.googlemap_point[1]);
		Campus.map.panTo(latlng);
		Campus.info(); //inits info marker
		Campus.infoMaker.setPosition(latlng);
		Campus.menu.find('#item-title').html(rc.description);
		Campus.menu.find('#item-desc').html(rc.html);
	}
	
	// looking at a location (very similar to regional campus)
	if(Campus.settings.location){
		var loc = Campus.settings.location;
		var latlng = new google.maps.LatLng(loc.googlemap_point[0], loc.googlemap_point[1]);
		Campus.map.panTo(latlng);
		Campus.info();
		Campus.infoMaker.setPosition(latlng);
		Campus.menu.find('#item-title').html(loc.name);
		Campus.menu.find('#item-desc').html(loc.info);
	}
	
	// buildings checkbox
	var bcb = $('#buildings')[0];
	$(bcb).attr('checked', Campus.settings.buildings);
	$(bcb).click(function(){
		Campus.settings.buildings = $(this).is(':checked');
		Campus.layers.buildings.update();
	});
	
	// traffic checkbox
	var tcb = Campus.menu.find('#traffic')[0];
	$(tcb).attr('checked', Campus.settings.traffic);
	$(tcb).click(function(){
		Campus.settings.traffic = $(this).is(':checked');
		Campus.layers.traffic.update();
	});
	
	// walking paths checkbox
	var scb = $('#sidewalks')[0];
	$(scb).attr('checked', Campus.settings.sidewalks);
	$(scb).click(function(){
		Campus.settings.sidewalks = $(this).is(':checked');
		Campus.layers.sidewalks.update();
	});
	
	// bikeracks paths checkbox
	var br = Campus.menu.find('#bikeracks')[0];
	$(br).attr('checked', Campus.settings.bikeracks);
	$(br).click(function(){
		Campus.settings.bikeracks = $(this).is(':checked');
		Campus.layers.bikeracks.update();
	});

	// emergency phones paths checkbox
	var phones = Campus.menu.find('#emergency_phones')[0];
	$(phones).attr('checked', Campus.settings.emergency_phones);
	$(phones).click(function(){
		Campus.settings.emergency_phones = $(this).is(':checked');
		Campus.layers.emergency_phones.update();
	});
	
	// parking lots
	var scb = $('#parking')[0];
	$(scb).attr('checked', Campus.settings.parking);
	$(scb).click(function(){
		Campus.settings.parking = $(this).is(':checked');
		Campus.layers.parking.update();
	});
	
}

/******************************************************************************\
 Map Layers
\******************************************************************************/
Campus.layers = {
	update : function(){
		this.buildings.update();
		this.traffic.update();
		this.points.update();
		this.sidewalks.update();
		this.bikeracks.update();
		this.emergency_phones.update();
		this.parking.update();
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
				
				// strip map of google elements
				// http://code.google.com/apis/maps/documentation/javascript/maptypes.html#StyledMaps
				// http://gmaps-samples-v3.googlecode.com/svn/trunk/styledmaps/wizard/index.html
				var styles = [ 
					{ featureType: "landscape.man_made", elementType: "geometry", stylers: [ { visibility: "off" } ] },
					{ featureType: "poi.school", elementType: "geometry", stylers: [ { visibility: "off" } ] },
					{ featureType: "poi.sports_complex", elementType: "geometry", stylers: [ { visibility: "off" } ] } 
				];
				var naked = new google.maps.StyledMapType( styles, { name : "Naked" } );
				Campus.map.mapTypes.set('naked', naked);
				
				this.loaded = true;
			}
			Campus.map.setMapTypeId('naked');
			this.layer.setMap(Campus.map);
		},
		unload : function() {
			if(!this.loaded) return;
			Campus.map.setMapTypeId(google.maps.MapTypeId.ROADMAP);
			this.layer.setMap(null);
		},
		update : function(){
			var on = Campus.settings.buildings;
			if(on) this.load(); else this.unload();
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
			for(var id in points ) {
				var p = points[id].point;
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
			if(!this.loaded) return;
			this.layer.setMap(null);
		},
		update : function(){
			var on = Campus.settings.sidewalks;
			if(on) this.load(); else this.unload();
		}
	},
	
	/* Place marker on each bike rack */
	bikeracks : {
		loaded  : false,
		geo     : false,
		markers : [],
		load    : function(){
			
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
				for(var i in this.markers){
					var marker = this.markers[i];
					if(marker.setVisible) marker.setVisible(true);
				}
				return;
			}
			
			// create and place markers
			for(var i in this.geo.features){
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
			
		},
		unload : function() {
			if(!this.loaded) return;
			for(var i in this.markers){
				var marker = this.markers[i];
				if(marker.setVisible) marker.setVisible(false);
			}
		},
		update : function(){
			var on = Campus.settings.bikeracks;
			if(on) this.load(); else this.unload();
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
				for(var i in this.markers){
					var marker = this.markers[i];
					if(marker.setVisible) marker.setVisible(true);
				}
				return;
			}
			
			// custom icon
			var icon = new google.maps.MarkerImage(Campus.urls.static + '/images/markers/marker_phone.png', new google.maps.Size(20, 34));
			var shadow = new google.maps.MarkerImage(Campus.urls.static + '/images/markers/marker_phone.png', new google.maps.Size(37,34), new google.maps.Point(20, 0), new google.maps.Point(10, 34));
			
			// create and place markers
			for(var i in this.geo.features){
				var phone = this.geo.features[i];
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
			
		},
		unload : function() {
			if(!this.loaded) return;
			for(var i in this.markers){
				var marker = this.markers[i];
				if(marker.setVisible) marker.setVisible(false);
			}
		},
		update : function(){
			var on = Campus.settings.emergency_phones;
			if(on) this.load(); else this.unload();
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
			if(!this.loaded) return;
			this.layer.setMap(null);
		},
		update : function(){
			var on = Campus.settings.parking;
			if(on) this.load(); else this.unload();
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
	
	if(!id || id=="null" || id=="searching"){ return; }
	if(Campus.ajax){ Campus.ajax.abort(); }
	var title = $('#item-title');
	var desc  = $('#item-desc');
	title.html("Loading...");
	desc.html("");
	desc.addClass('load');
	
	var url = Campus.urls['location'].replace("%s", id);
	
	Campus.ajax = $.ajax({
		url: url,
		dataType: 'json',
		success: function(data){
			var name = data.name;
			if(data.abbreviation){ name += ' (' + data.abbreviation + ')'; }
			title.html(name);
			desc.html(data.info);
			desc.removeClass('load');
			var latlng = new google.maps.LatLng(data.googlemap_point[0], data.googlemap_point[1]);
			Campus.infoMaker.setPosition(latlng);
			if(pan){ Campus.map.panTo(latlng);  }
		},
		error: function(){
			title.html("Error");
			desc.html("Request failed for building: " + id);
			desc.removeClass('load');
		}
	});
}


/******************************************************************************\
 Resize
	sets map to 100% height and width
	attaches function to window resize
\******************************************************************************/
Campus.resize = function(){
	
	Campus.resize_tries = 0;
	
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
	
	var search = $(Campus.searchUI);
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
			if(pk == "more-results"){ return; }
			event.preventDefault();
			if(li.length < 1){ 
				li = $('#search li');
				if(li.length == 1) {
					pk = li.find('a').attr('data-pk');
				}
			}
			if(pk && pk !== "searching" && pk != "null"){
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
		
		//'escape' key
		if(keyCode===27){
			Campus.ajax.abort();
			search.find('ul').remove();
			return;
		}
		
		// ajax search
		if(Campus.ajax){ Campus.ajax.abort(); }
		var q = input.val();
		if(!q){
			search.find('ul').remove();
			return;
		} else {
			if(search.find('ul').length < 1){ 
				search.append('<ul></ul>');
			}
		}
		
		search.find('ul').html('<li><a data-pk="searching">Searching&hellip;</a></li>');
		Campus.ajax = $.ajax({
			url: Campus.urls['search'] + '.list',
			data: {q:q},
			success: function(html){
				//show results
				$("#search ul").html(html);
				//attach event to open info window
				$('#search li:not(.more)').click(function(event){
					event.preventDefault();
					pk = $(this).find('a').attr('data-pk');
					$('#search li').removeClass('hover');
					$(this).addClass('hover');
					Campus.info(pk, true);
				});
			}
		});

	});//keyup
	
	// hide results on mapclick
	google.maps.event.addListener(this.map, "click", function(){
		search.find('ul').remove(); 
	});
	
	// set z-index and focus, but must wait until loaded in dom
	var style = function(){
		if($('#search input').length > 0){
			$('#search').css('z-index', 15);
			$('#search input').focus();
		} else {
			//console.log("search glitch");
			setTimeout(style, 250);
		}
	}
	style();
	
};//search
