var CampusMap = function(urls, points, base_ignore_types) {
	var that  = this,

		POINTS            = points,
		// Ignore these point types on the base points layer
		BASE_IGNORE_TYPES = base_ignore_types,

		// URLs provided by the template
		STATIC_URL        = urls['static'],
		SEARCH_URL        = urls['search'],
		LOCATION_URL      = urls['location'],
		PARKING_JSON_URL  = urls['parking_json'],
		DINING_URL        = urls['dining'],
		PARKING_KML_URL   = urls['parking_kml'],
		BUILDINGS_KML_URL = urls['buildings_kml'],
		SIDEWALKS_KML_URL = urls['sidewalks_kml'],
		BIKERACKS_URL     = urls['bikeracks'],
		PHONES_URL        = urls['phones'],
		BASE_URL          = urls['base_url'],

		GMAP_OPTIONS = null,
		IMAP_OPTIONS = null,
		IMAP_TYPE    = null,

		MAP           = null,
		SEARCH        = null,
		MENU          = null,
		LAYER_MANAGER = null,
		UTIL          = new Util();

	// Load the Google Maps JS
	if(typeof google === 'undefined') {
		log('Unable to load google code');
		return;
	}

	//
	// Define the map layer options and types
	//

	// Regular Google Map
	GMAP_OPTIONS = {
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
	}

	// Illustrated Map
	IMAP_OPTIONS = { 
		zoom : 14,
		center : new google.maps.LatLng(85.04591,-179.92189), // world's corner
		mapTypeId : 'illustrated',
		mapTypeControl : true
	}
	IMAP_TYPE = {
		tileSize : new google.maps.Size(256,256),
		minZoom: 12,
		maxZoom :16, //can go up to 18
		getTile : function(coordinate, zoom, ownerDocument) {
			var div                   = ownerDocument.createElement('div');
			div.style.width           = this.tileSize.width + 'px';
			div.style.height          = this.tileSize.height + 'px';
			div.style.backgroundImage = UTIL.get_illustrated_tile(coordinate,zoom);
			return div;
		},
		name : "Illustrated",
		alt  : "Show illustrated map",
	}


	// Setup and configure the map
	MAP = new google.maps.Map(document.getElementById('map-canvas'), GMAP_OPTIONS);
	MAP.mapTypes.set('illustrated', IMAP_TYPE); // Register the illustrated map type
	google.maps.event.addListener(MAP, 'maptypeid_changed', function() {
		var type    = MAP.mapTypeId;
		var options = type === 'illustrated' ? IMAP_OPTIONS : GMAP_OPTIONS;
		MAP.setZoom(options.zoom);
		MAP.setCenter(options.center); 
	})

	// Setup and configure the search
	SEARCH = new Search();

	// Setup and configure the menu
	MENU = new Menu();

	// Setup and configure the layers
	LAYER_MANAGER = new LayerManager();

	// Implementation details for the traffic layer
	LAYER_MANAGER.register_layer(
		(function() {
			var traffic_layer   = new Layer('traffic');
			traffic_layer.layer = new google.maps.TrafficLayer();
			return traffic_layer;
		})()
	);

	// Implementation details for the sidewalks layer
	LAYER_MANAGER.register_layer(
		(function() {
			var sidewalk_layer = new Layer('sidewalks');
			sidewalk_layer.layer = new google.maps.KmlLayer(
					SIDEWALKS_KML_URL, 
					{
						preserveViewport : true,
						suppressInfoWindows: true,
						clickable: false
					}
				);
			return sidewalk_layer;
		})()
	);

	// Implementation details for the points layer
	LAYER_MANAGER.register_layer(
		(function() {
			var points_layer     = new Layer('points');
			points_layer.markers = (function() {
				var markers        = [],
					images         = {
						'Building'   : UTIL.get_google_image('yellow'),
						'ParkingLot' : UTIL.get_google_image('yellow'),
						'Group'      : UTIL.get_google_image('yellow2'),
						'Location'   : UTIL.get_google_image('blue'),
					},
					map_point_type = (MAP.mapTypeId === 'illustrated') ? 'ipoint' : 'gpoint';

				$.each(POINTS, function(index, point) {
					var map_point = point[map_point_type];
					if(map_point != null && $.inArray(point.type, BASE_IGNORE_TYPES) == -1) {
						markers.push(
							new google.maps.Marker({
								position : new google.maps.LatLng(map_point[0], map_point[1]),
								map      : MAP,
								icon     : images[point.type],
								location : index,
								visible  : false
							})
						);
					}
				});
				return markers;
			})();
 			return points_layer;
		})()
	);

	// Implementation details for the buildings layer
	LAYER_MANAGER.register_layer(
		(function() {
			var buildings_layer   = new Layer('buildings');
			buildings_layer.layer = new google.maps.KmlLayer(
				BUILDINGS_KML_URL, 
				{
					preserveViewport    :true,
					suppressInfoWindows :true,
					clickable           :false 
				}
			);
			return buildings_layer;
		})()
	);

	// Implementation details for the bikeracks layer
	LAYER_MANAGER.register_layer(
		(function() {
			var bikeracks_layer  = new Layer('bikeracks');
			bikeracks_layer.markers = (function() {
				var markers = [];
				$.ajax({
					url     :BIKERACKS_URL,
					dataType:'json',
					async   :false,
					success :
						function(data, text_status, jq_xhr) {
							if(typeof data.features != 'undefined') {
								$.each(data.features, function(index, rack) {
									if(rack.geometry && rack.geometry.coordinates) {
										markers.push(
											new google.maps.Marker({
												clickable : false,
												position  : new google.maps.LatLng(
													rack.geometry.coordinates[0],
													rack.geometry.coordinates[1]
												),
												map       : MAP,
												visible   : false
											})
										);
									}
								});
							}
						}
				});
				return markers;
			})();
			return bikeracks_layer;
		})()
	);

	// Implementation details for the emergency phones layer
	LAYER_MANAGER.register_layer(
		(function() {
			var phones_layer = new Layer('emergency_phones');
			phones_layer.markers = (function() {
				var markers = [];
				$.ajax({
					url     :PHONES_URL,
					dataType:'json',
					async   :false,
					success :
						function(data, text_status, jq_xhr) {
							var icon   = new google.maps.MarkerImage(
									STATIC_URL + '/images/markers/marker_phone.png',
									new google.maps.Size(20, 34)
								),
								shadow = new google.maps.MarkerImage(
									STATIC_URL + '/images/markers/marker_phone.png',
									new google.maps.Size(37,34),
									new google.maps.Point(20, 0),
									new google.maps.Point(10, 34)
								);

							if(typeof data.features != 'undefined') {
								$.each(data.features, function(index, rack) {
									if(rack.geometry && rack.geometry.coordinates) {
										markers.push(
											new google.maps.Marker({
												clickable : false,
												position  : new google.maps.LatLng(
													rack.geometry.coordinates[0],
													rack.geometry.coordinates[1]
												),
												map       : MAP,
												visible   : false,
												icon      : icon,
												shadow    : shadow
											})
										);
									}
								});
							}
						}
				});
				return markers;
			})();
			return phones_layer;
		})()
	);
	
	// Implementation detail for the parking layer
	LAYER_MANAGER.register_layer(
		(function() {
			var parking_layer = new Layer('parking');
			parking_layer.layer = new google.maps.KmlLayer(
					PARKING_KML_URL,
					{
						preserveViewport    : true,
						suppressInfoWindows : true
					}
			);
			parking_layer.markers = (function() {
				var markers = [];
				$.ajax({
					url      : PARKING_JSON_URL,
					dataType : 'json',
					async    : false,
					success: function(data){
						var icon   = new google.maps.MarkerImage(
								STATIC_URL + 'images/markers/disabled.png', 
								new google.maps.Size(17, 17), //size
								new google.maps.Point(0, 0),  //origin
								new google.maps.Point(10, 8)   //anchor
							);
						if(typeof data.handicap != 'undefined') {
							$.each(data.handicap, function(index, spot) {
								markers.push(
									new google.maps.Marker({
										icon     : icon,
										position : new google.maps.LatLng(
											spot.googlemap_point[0],
											spot.googlemap_point[1]
										), 
										map      : MAP,
										title    : spot.title,
										visible  : false
									})
								);
							});
						}
					}
				});
				return markers;
			})();
			return parking_layer;
		})()
	);

	// Implementation details for the dining layer
	LAYER_MANAGER.register_layer(
		(function() {
			var dining_layer     = new Layer('dining');
			dining_layer.markers = (function() {
				var markers         = [],
					ExistingPoint   = function(lat, lon) {
						this.lat      = lat;
						this.lon      = lon;
						this.count    = 1;
						this.odd_flip = true;
					},
					randomInt       = function() {
						return Math.round(Math.random() * 10) + Math.round(Math.random() * 10);
					},
					existing_points = [],
					adjustment      = 150000,
					icon = new google.maps.MarkerImage(
						STATIC_URL + 'images/markers/knife-fork.png',
						new google.maps.Size(28, 28),  // dimensions
						new google.maps.Point(0,0),  // origin
						new google.maps.Point(16,20)), // anchor 
					shadow = new google.maps.MarkerImage(
						STATIC_URL + 'images/markers/knife-fork-shadow.png',
						new google.maps.Size(46, 22),
						new google.maps.Point(0,0),
						new google.maps.Point(10,13));;

				$.ajax({
					url      : DINING_URL,
					dataType : 'json',
					async    : false,
					success: function(data){
						

						if(typeof data.features != 'undefined') {
							$.each(data.features, function(index, feature) {
								var point = feature.geometry.coordinates;

								// Nudge points if they are on top of each other
								var adjusted = false;
								$.each(existing_points, function(_index, existing_point) {
									if(point[0] == existing_point.lat && point[1] == existing_point.lon) {
										var count = existing_point.count;
										if( (count % 2) == 0) {
											point[0] = point[0] + ((count + randomInt()) / adjustment);
											if( (count % 4) == 0) {
												point[1] = point[1] + ((count + randomInt()) / adjustment);
											} else {
												point[1] = point[1] - ((count + randomInt()) / adjustment);
											}
										} else {
											point[0] = point[0] - ((count + randomInt()) / adjustment);
											if(existing_point.odd_flip) {
												point[1] = point[1] + ((count + randomInt()) / adjustment);
												existing_point.odd_flip = false;
											} else {
												point[1] = point[1] - ((count + randomInt()) / adjustment);
												existing_point.odd_flip = true;
											}
										}
										adjusted = true;
										existing_point.count += 1;
										return false;
									}
								});
								if(!adjusted) {
									existing_points.push(new ExistingPoint(point[0],point[1]))
								}
								markers.push(
									new google.maps.Marker({
										icon     : icon,
										shadow   : shadow,
										position : new google.maps.LatLng(point[0], point[1]),
										title    : feature.properties.name,
										map      : MAP,
										visible  : false
									})
								);
							});
						}
					}
				});
				return markers;
			})();
			return dining_layer;
		})()
	);

	// Display the points layer when the  map loads
	(LAYER_MANAGER.get_layer('points')).toggle();

	// Attach click handles to layer checkboxes
	(function() {
		$.each(LAYER_MANAGER.layers, function(index, layer) {
			var name = layer.name;
			$('input[type="checkbox"][id="' + layer.name + '"]')
				.click(function() {
					// For parking, change menu to legend
					if($(this).attr('id') == 'parking') {
						MENU.change_tabs({
							'label':'Parking',
							'html' :$('#parking-key-content').html()
						});
					}
					layer.toggle();
				});
		});
	})();

	/*********************************
	 *
	 * Layers
	 *
	 *********************************/
	function LayerManager() {
		var that = this;

		this.layers = [];

		this.get_layer = function(name) {
			var layer = null;
			$.each(that.layers, function(index, _layer) {
				if(_layer.name == name) {
					layer = _layer;
					return false;
				}
			});
			return layer;
		}

		this.load_all_layers = function() {
			$.each(that.layers, function(index, layer) {
				layer.toggle();
			});
		}

		this.register_layer = function(layer) {
			that.layers.push(layer);
		}
	}

	function Layer(name) {
		/*
			Layers are sets of objects placed on the map (e.g. points, buidlings,
			sidewalks, etc.)

			Layers are made up of two types of Google Maps items: KML and points.
			Most layers have one or the other; some have both.


			This function represents and interface of what the LayerManager
			expects. Implementations for each layer appear below

		*/

		var that    = this;
		
		this.active  = false;
		this.name    = name;
		this.layer   = null; // the actual Google Maps layer on the map, if applicable
		this.markers = null; // the actual Google Maps markers on the map, if applicable

		this.toggle = function toggle() {
			that.active ? deactivate() : activate();
		}

		function activate() {
			that.active = true;
			if(that.layer != null) {
				that.layer.setMap(MAP);
			}
			if(that.markers != null) {
				$.each(that.markers, function(index, marker) {
					marker.setVisible(true);
				});
			}
		}

		function deactivate() {
			that.active = false;
			if(that.layer != null) {
				that.layer.setMap(null);
			}
			if(that.markers != null) {
				$.each(that.markers, function(index, marker) {
					marker.setVisible(false);
				});
			}
		}
	}
	
	/*********************************
	 *
	 * Menu
	 *
	 *********************************/
	function Menu() {
		/*
			The menu consists of four different faces. The content of
			the first three faces is constant while the content of the 
			fourth face dynamic. The fourth face, referred as the `stage`,
			is where information about locations that are selected is 
			displayed.

			In addition to the four faces, there are are two tabs.
		*/
		var container = $('#menu-wrap'), // contains all of the menu HTML,
			menu      = $('#menu-window'), // this is the window through which the faces are viewed
			tab_one   = $('#tab-one'),
			tab_two   = $('#tab-two');

		// Set all the faces to the same height
		menu.equalHeights();

		// The menu header has a gap the needs to move left and right 
		// depending on how many tabs are displayed
		function reset_tab_gap() {
			var width = $('#menu-header').width() - 10 - tab_one.width();
			if(tab_two.is(':visible')) {
				width -= tab_two.width();
			}
			$('#menu .gap').width(width);
		}
		reset_tab_gap();


		// Next Menu / Previous Menu actions
		$('.nav').click(function(){
			var page_num = $(this).attr('data-nav');
			$.cookie('menu_page', page_num);
			page_num -= 1;
			menu.animate({"margin-left" : '-' + (Number(page_num) * 230) }, 300);
		});

		// Hiding and Showing the menu
		$('#menu-hide,#menu-screen')
			.click(function(e) {
				e.preventDefault();
				var screen = $('#menu-screen');
				if(screen.is(':visible')) {
					menu.slideDown();
					screen.hide();
					container
						.removeClass('closed')
						.animate({'opacity':1}, 300);
				} else {
					menu.slideUp();
					container
						.animate({'opacity':.5}, 300, function() {
							container.addClass('closed');
						});
					screen.show();
				}
			})

		// There are two button in the upper right hand corner of the menu:
		// email and print. They are updated based on various actions
		// ------

		this.change_tabs = function(options) {
			var defaults = {
				'label':false,
				'html' :false
			}

			var settings = $.extend({}, defaults, options);

			// If no label or html is set, go back to the `Menu` tab
			if(!settings.label && !settings.html) {
				menu.animate({'margin-left':0}, 300);
				tab_one.removeClass('off');
				tab_two.addClass('on');
			} else {
				tab_two.removeClass('off');
				tab_one.addClass('on');
				$('#menu-title').html(settings.label); // tab two title
				tab_two.show();

				$('#menu-stage').html(settings.html); // tab two content

				menu.animate({'margin-left':-690}, 300);

				reset_tab_gap();
				menu.equalHeights();
			}
		}

		// Add the menu to the map in the right uppper
		MAP.controls[google.maps.ControlPosition.RIGHT_TOP].push(container[0]);
	}

	/*********************************
	 *
	 * Search
	 *
	 *********************************/
	function Search() {
		var element = null,
			input   = null,
			results = null,
			timer   = null,
			timeout = 400, // milliseconds
			ajax    = null,

			KEYCODES = {
				ENTER      :13,
				LEFT_ARROW :37,
				RIGHT_ARROW:39,
				SHIFT      :16,
				CONTROL    :17,
				OPTION     :18,
				COMMAND    :224,
				DOWN       :40,
				UP         :38,
				ESCAPE     :27,
			};

		// Create and populate the search element
		element = (function() {
			var div    = null,
				form   = null,
				input  = null,
				anchor = null,
				ul     = null;

			div    = document.createElement('div');
			form   = document.createElement('form');
			input  = document.createElement('input');
			anchor = document.createElement('a');
			ul     = document.createElement('ul');

			div.id        = 'search';
			div.style.zIndex = 9999;

			form.method = 'get';
			form.action = SEARCH_URL;
			form.id     = 'search-form';

			input.type         = 'text';
			input.name         = 'q';
			input.autocomplete = 'off';

			anchor.id = 'search-submit';
			anchor.onclick = '$(\'#search-form\').submit()';
			anchor.appendChild(document.createTextNode('search'));

			ul.style.display = 'none';

			form.appendChild(input);
			form.appendChild(anchor);
			
			div.appendChild(form)
			div.appendChild(ul);

			return div;
		})();
		MAP.controls[google.maps.ControlPosition.TOP_LEFT].push(element);
		element = $(element);
		input   = element.find('input')
		results = element.find('ul');

		// Attach the typing events
		input
			.keydown(function(event) {
				var keycode = UTIL.parse_keycode(event);
				if(keycode == KEYCODES.ENTER) {

				}
			});

		input
			.keyup(function(event) {
				var keycode      = UTIL.parse_keycode(event),
					search_query = $(this).val();

				// Whatever happens, next we don't want to keep searching
				// if we are right now
				abort_ajax();

				// Ignore left, right, shift, control, option and command
				// These are text navigation commands
				if($.inArray(keycode, 
						[
							KEYCODES.LEFT_ARROW,
							KEYCODES.RIGHT_ARROW, 
							KEYCODES.SHIFT, 
							KEYCODES.CONTROL, 
							KEYCODES.OPTION, 
							KEYCODES.COMMAND
						]
					) !== -1) {
					return;
				}

				// Search result navigation
				if(keycode === KEYCODES.DOWN) { // Scroll down results
					var li = results.find('.hover');
					if(li.length) {
						li.removeClass('hover');
						li.next().addClass('hover');
					} else {
						results.find('li:first').addClass('hover');
					}
				} else if(keycode === KEYCODES.UP) { // Scroll up results
					var li = results.find('.hover');
					if(li.length) {
						li.removeClass('hover');
						li.prev().addClass('hover');
					} else {
						results.find('li:last').addClass('hover');
					}
				} else if(keycode === KEYCODES.ESCAPE) { // Empty and hide results
					abort_ajax();
					results.empty().hide();
				} else {
					if(search_query === '') {
						results.hide();
					} else {
						results.empty().show();

						// Wait <timeout> duration between keypresses before doing search
						clearTimeout(timer);
						timer = setTimeout(function() {
							results.append('<li><a data-pk="searching">Searching&hellip;</a></li>');

							ajax = $.getJSON(
								[SEARCH_URL, 'json'].join('.'),
								{q:search_query},
								function(data, text_status, jq_xhr) {
									results.empty();

									if(typeof data.results != 'undefined') {
										var locs = data.results.locations,
											orgs = data.results.organizations;

										if(!locs.length) { // There weren't any results
											results.append('<li><a data-pk="null">No results</a></li>');
										} else {

											// Because of the way the search returns results,
											// we need to check to see if the location name
											// actually contains the search term. It could be that
											// an organization under the location contains the search query
											// but the location name itself does not. We want to ignore
											// those results. We also want to prioritize locations
											// with organization matches to those without organization
											// matches. We dont' display just organizations.

											var best_matches   = [], // locations with organizations where the search term is the name
												better_matches = [], // locations with organizations where the search term isn't in the name
												good_matches   = []; // locations without organizations where the search term is in the name

											$.each(locs, function(index, loc) {
												var org_list             = '',
													highlighted_loc_link = UTIL.highlight_term(loc.link, search_query, true);

												// Associate organizations with their locations
												loc.orgs = [];
												$.each(orgs, function(_index, org) {
													if(loc.id == org.bldg_id) {
														// Hightlight the search query in the org name
														org.name = UTIL.highlight_term(org.name, search_query);
														loc.orgs.push(org);
													}
												});

												if(loc.orgs.length && loc.link != highlighted_loc_link) {
													loc.link = highlighted_loc_link;
													best_matches.push(loc);
												} else if(loc.orgs.length) {
													better_matches.push(loc);
												} else if(loc.link != highlighted_loc_link) {
													loc.link = highlighted_loc_link;
													good_matches.push(loc);
												}
											});

											// Keep track of the total amount of locations and organizations
											// we are displaying. We don't want to go over 11 or else the
											// results list will be too long
											var org_loc_count = 0;
											$.each(best_matches.concat(better_matches, good_matches), function(index, loc) {
												var org_html = '';

												org_loc_count += loc.orgs.length;
												$.each(loc.orgs, function(_index, org) {
													org_html += '<li>' + org.name + '</li>';
												});
												if(org_html != '') org_html = '<ul>' + org_html + '</ul>';

												results.append('<li>' + loc.link + org_html + '</ul>');

												if(org_loc_count > 11) {
													results.append('<li class="more"><a href="' + data.response_page_url + '">More Results &hellip;</a></li>');
													return false;
												} 
												org_loc_count++;
											});
										}
									}
								}
							);
						}, timeout);
					}
				}
			});

		function abort_ajax() {
			if(ajax != null) ajax.abort();
		}
	}

	/*********************************
	 *
	 * Utility
	 *
	 *********************************/
	function Util() {

		// Returns the URL of a illustrated map tiles based on the specified
		// coordinate and zoom. If coordinate and/or zoom are outside the illustrated
		// map's viewable area, return a white tile.
		this.get_illustrated_tile = function(coordinate, zoom) {
			var filename = null,
				no_tile  = 'white.png',
				// Smallest map dimensions
				dimensions     = {x:5, y:3},
				scaling_factor = Math.pow(2, (zoom - 13));

			if( // Outside bounds
				(zoom < 12 || coordinate.y < 0 || coordinate.x < 0)
				||
				// Too small
				(zoom === 12 && (coordinate.y > 1 || coordinate.x > 2))
				||
				// Too big
				(coordinate.x >= (dimensions.x * scaling_factor) || coordinate.y >= (dimensions.y*scaling_factor))
				) {
				filename = no_tile;
			} else {
				filename = 'zoom-' + zoom + '/' + zoom + '-' + coordinate.x + '-' + coordinate.y + '.jpg';
			}
			return 'url("http://cdn.ucf.edu/map/tiles/' + filename + '")'; 
		}

		// Wraps a specified term with start and end wraps. Preserves capitalization.
		this.highlight_term = function(string, term, link) {
			if(typeof link != 'undefined' && link) {
				var matches = string.match(/<a([^>]+)>([^<]*)<\/a>/);
				if(matches != null) {
					return '<a' + matches[1] + '>' + UTIL.highlight_term(matches[2], term) + '</a>';
				} else {
					return string;
				}
			} else {
				var low_sub  = string.toLowerCase();
				var term_loc = low_sub.indexOf(term.toLowerCase());
				if(term_loc > - 1) {
					return string.substr(0, term_loc) + '<span class="highlight">' + string.substr(term_loc, term.length) + '</span>' + string.substr(term_loc+ term.length);
				} else {
					return string;
				}
			}
		}

		// Platform generic event keycode parser. Designed to be used with keyup/down
		this.parse_keycode = function(event) {
			return document.layers ? event.which : document.all ? event.keyCode : document.getElementById ? event.keyCode : 0;
		}

		// Returns URL of google icon based on specified color
		this.get_google_image = function(color) {
			return new google.maps.MarkerImage(
				(STATIC_URL + 'images/markers/' + color + '.png'),
				new google.maps.Size(19, 19),
				new google.maps.Point(0,0), 
				new google.maps.Point(10,10));
		}
	}


	// Log a message to the console if it's available
	function log() {
		if(typeof console !== 'undefined') {
			console.log(arguments);
		}
	}
}

/*-------------------------------------------------------------------- 
 * JQuery Plugin: "EqualHeights" & "EqualWidths"
 * by:	Scott Jehl, Todd Parker, Maggie Costello Wachs (http://www.filamentgroup.com)
 *
 * Copyright (c) 2007 Filament Group
 * Licensed under GPL (http://www.opensource.org/licenses/gpl-license.php)
 *
 * Description: Compares the heights or widths of the top-level children of a provided element 
 		and sets their min-height to the tallest height (or width to widest width). Sets in em units 
 		by default if pxToEm() method is available.
 * Dependencies: jQuery library, pxToEm method	(article: http://www.filamentgroup.com/lab/retaining_scalable_interfaces_with_pixel_to_em_conversion/)							  
 * Usage Example: $(element).equalHeights();
   						      Optional: to set min-height in px, pass a true argument: $(element).equalHeights(true);
 * Version: 2.0, 07.24.2008
 * Changelog:
 *  08.02.2007 initial Version 1.0
 *  07.24.2008 v 2.0 - added support for widths
--------------------------------------------------------------------*/

$.fn.equalHeights = function(px) {
	$(this).each(function(){
		var currentTallest = 0;
		$(this).children().each(function(i){
			if ($(this).height() > currentTallest) { currentTallest = $(this).height(); }
		});
		// for ie6, set height since min-height isn't supported
		if ($.browser.msie && $.browser.version === 6.0) { $(this).children().css({'height': currentTallest}); }
		$(this).children().css({'min-height': currentTallest});	
	});
	return this;
}