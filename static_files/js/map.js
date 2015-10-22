
var isDesktopWidth = true;
if($(window).width() <  768) {
  isDesktopWidth = false;
}

var CampusMap = function(options) {
	var that = this,
		default_options = {
			'simple'              : false,
			'canvas_id'           : 'map-canvas',
			'pan_control'         : true,
			'zoom_control'        : true,
			'street_view_control' : true,
			'map_type_control'    : true,
			'infobox_location_id' : null,
			'illustrated'         : false
		},

		options = $.extend({}, default_options, options);

	var POINTS            = options.points,

        // Shuttle Route information
        SHUTTLE_ROUTES    = options.shuttle_routes,
        SHUTTLE_STOPS     = options.shuttle_stops,

		// Ignore these point types on the base points layer
		BASE_IGNORE_TYPES = options.base_ignore_types,

		// URLs provided by the template
		STATIC_URL        = options.urls['static'],
		SEARCH_URL        = options.urls['search'],
		LOCATION_URL      = options.urls['location'],
		PARKING_JSON_URL  = options.urls['parking_json'],
		DINING_URL        = options.urls['dining'],
		PARKING_KML_URL   = options.urls['parking_kml'],
		BUILDINGS_KML_URL = options.urls['buildings_kml'],
		SIDEWALKS_KML_URL = options.urls['sidewalks_kml'],
		BIKERACKS_URL     = options.urls['bikeracks'],
		PHONES_URL        = options.urls['phones'],
    AEDS_URL          = options.urls['aeds'],
		STATIONS_URL      = options.urls['stations'],
		BASE_URL          = options.urls['base_url'],

		SIMPLE = options.simple,
		// Simple really means the map on the profile pages.
		// This variable should really be renamed.

		CURRENT_LOCATION = null,

		ACTIVATED_LAYERS = [],

		GMAP_OPTIONS = null,
		IMAP_OPTIONS = null,
		IMAP_TYPE    = null,

		MAP           = null,
		SEARCH        = null,
		MENU          = null,
		LAYER_MANAGER = null,
		INFO_MANAGER  = null,
    SEARCH_RESULTS_SIZE = 0,
		UTIL          = new Util();

  UTIL.resize_canvas();

	// Load the Google Maps JS
	if(typeof google === 'undefined') {
		log('Unable to load google code');
		return;
	}

	// Find out which layers are activated by default based on the URL
	(function() {
		var url   = window.location + "",
			parts = url.split('/');
		if(parts.length > 3) {
			parts = parts.splice(3);
			$.each(parts, function(index, part) {
				if(part != 'map' && part != '') {
					if(part == 'illustrated') {
						options.illustrated = true;
					} else {
						ACTIVATED_LAYERS.push(part);
					}
				}
      });
		}
	})();


	//
	// Define the map layer options and types
	//

	// Regular Google Map

	$zoom = getZoom();

  var mapTypes = {
    mapTypeIds: []
  };
  if(isDesktopWidth) {
    mapTypes = {
      mapTypeIds: [
        google.maps.MapTypeId.ROADMAP,
        google.maps.MapTypeId.SATELLITE,
        google.maps.MapTypeId.HYBRID,
        google.maps.MapTypeId.TERRAIN,
        'illustrated'
      ]
    };
  }

	GMAP_OPTIONS = {
		zoom: $zoom,
		center: new google.maps.LatLng(28.6018,-81.1995),
		mapTypeId: google.maps.MapTypeId.ROADMAP,
		panControl: options.pan_control,
		panControlOptions: {
			position: google.maps.ControlPosition.LEFT_TOP
		},
		zoomControl: options.zoom_control,
		zoomControlOptions: {
			style: google.maps.ZoomControlStyle.LARGE,
			position: google.maps.ControlPosition.LEFT_TOP
		},
		streetViewControl: options.street_view_control,
		streetViewControlOptions: {
			position: google.maps.ControlPosition.LEFT_TOP
		},
		mapTypeControl: options.map_type_control,
		mapTypeControlOptions: mapTypes
	};

	// Illustrated Map
	IMAP_OPTIONS = {
		zoom              : 14,
		center            : new google.maps.LatLng(85.04591,-179.94189), // world's corner
		mapTypeId         : 'illustrated',
		panControl        : options.pan_control,
		zoomControl       : options.zoom_control,
		streetViewControl : options.street_view_control,
		mapTypeControl    : options.map_type_control
	};
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
		alt  : "Show illustrated map"
	};


	// Setup and configure the map
	google.maps.visualRefresh = true;
	MAP = new google.maps.Map(document.getElementById(options.canvas_id), options.illustrated ? IMAP_OPTIONS : GMAP_OPTIONS);
	MAP.mapTypes.set('illustrated', IMAP_TYPE); // Register the illustrated map type
	google.maps.event.addListener(MAP, 'maptypeid_changed', function() {
		var type    = MAP.mapTypeId,
			options = (type === 'illustrated') ? IMAP_OPTIONS : GMAP_OPTIONS,
			gpoints = LAYER_MANAGER.get_layer('gpoints'),
			ipoints = LAYER_MANAGER.get_layer('ipoints');
		MAP.setZoom(options.zoom);
		MAP.setCenter(options.center);
		if(type == 'illustrated') {
			gpoints.deactivate();
			ipoints.activate();
		} else {
			ipoints.deactivate();
			gpoints.activate();
		}
		INFO_MANAGER.clear();
		if(CURRENT_LOCATION != null) {
			UTIL.highlight_location(CURRENT_LOCATION);
		}
	});

	if(!options.simple) {
		$(window).resize(UTIL.resize_canvas);

		// Setup and configure the search
		SEARCH = new Search();

		// Setup and configure the menu
		MENU = new Menu();

    MOBILE_MENU = new MobileMenu();
	}

	// Setup and configure the info boxes
	INFO_MANAGER = new InfoManager();

  	if(!options.simple) {
  		// Setup and configure the layers
  		LAYER_MANAGER = new LayerManager();

      if(isDesktopWidth) {
    		// Implementation details for the traffic layer
    		LAYER_MANAGER.register_layer(
    			(function() {
    				var traffic_layer   = new Layer('traffic');
    				traffic_layer.layer = new google.maps.TrafficLayer();
    				return traffic_layer;
    			})()
    		);
      }

    if(isDesktopWidth) {
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
    }

    if(isDesktopWidth) {
  		// Implementation details for the points layer for the google maps layer
  		LAYER_MANAGER.register_layer(
  			(function() {
  				var points_layer     = new Layer('gpoints');
  				points_layer.markers = (function() {
  					var markers        = [],
  						images         = {
  							'Building'   : UTIL.get_google_image('building'),
  							'ParkingLot' : UTIL.get_google_image('parking'),
  							'Group'      : UTIL.get_google_image('group'),
  							'Location'   : UTIL.get_google_image('location')
  						},
  						map_point_type = 'gpoint';

  					$.each(POINTS, function(index, point) {
  						var map_point = point[map_point_type],
  							marker    = null;
  						if(map_point != null && $.inArray(point.type, BASE_IGNORE_TYPES) == -1) {
  							marker = new google.maps.Marker({
  								position : new google.maps.LatLng(map_point[0], map_point[1]),
  								map      : MAP,
  								icon     : images[point.type],
  								location : index,
  								visible  : false
  							});

  							markers.push(marker);
  							google.maps.event.addListener(marker, 'click', function(event) {
  								UTIL.highlight_location(index);
  							});
  						}
  					});
  					return markers;
  				})();
  	 			return points_layer;
  			})()
  		);
    }

    if(isDesktopWidth) {
  		// Implementation details for the points layer
  		LAYER_MANAGER.register_layer(
  			(function() {
  				var points_layer     = new Layer('ipoints');
  				points_layer.markers = (function() {
  					var markers        = [],
  						images         = {
  							'Building'   : UTIL.get_google_image('building'),
  							'ParkingLot' : UTIL.get_google_image('parking'),
  							'Group'      : UTIL.get_google_image('group'),
  							'Location'   : UTIL.get_google_image('blue')
  						},
  						map_point_type = 'ipoint';

  					$.each(POINTS, function(index, point) {
  						var map_point = point[map_point_type],
  							marker    = null;
  						if(map_point != null && $.inArray(point.type, BASE_IGNORE_TYPES) == -1) {
  							marker = new google.maps.Marker({
  								position : new google.maps.LatLng(map_point[0], map_point[1]),
  								map      : MAP,
  								icon     : images[point.type],
  								location : index,
  								visible  : false
  							});
  							markers.push(marker);
  							google.maps.event.addListener(marker, 'click', function(event) {
  								UTIL.highlight_location(index);
  							});
  						}
  					});
  					return markers;
  				})();
  	 			return points_layer;
  			})()
  		);
    }


    if(isDesktopWidth) {
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
    }

    if(isDesktopWidth) {
  		// Implementation details for the bikeracks layer
  		LAYER_MANAGER.register_layer(
  			(function() {
  				var bikeracks_layer  = new Layer('bikeracks');
  				bikeracks_layer.markers = (function() {
  					var markers = [],
                icon   = {
                    url: STATIC_URL + '/images/markers/bicycle.png',
                    size: new google.maps.Size(25, 25)
                };
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
                            icon: icon,
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
    }

    if(isDesktopWidth) {
      // Implementation details for the emergency phones layer
      LAYER_MANAGER.register_layer(
        (function() {
          var phones_layer = new Layer('emergency-phones');
          phones_layer.markers = (function() {
            var markers = [];
            $.ajax({
              url     :PHONES_URL,
              dataType:'json',
              async   :false,
              success :
                function(data, text_status, jq_xhr) {
                  var icon   = {
                      url: STATIC_URL + '/images/markers/phone.png',
                      size: new google.maps.Size(25, 25)
                  };

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
                            icon      : icon
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
    }
    if(isDesktopWidth) {
      // Implementation details for the aeds layer
      LAYER_MANAGER.register_layer(
        (function() {
          var aeds_layer = new Layer('emergency-aeds');
          aeds_layer.markers = (function() {
            var markers = [];
            $.ajax({
              url     :AEDS_URL,
              dataType:'json',
              async   :false,
              success :
                function(data, text_status, jq_xhr) {
                  var icon   = {
                      url: STATIC_URL + '/images/markers/aed.png',
                      size: new google.maps.Size(32, 32)
                  };

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
                            icon      : icon
                          })
                        );
                      }
                    });
                  }
                }
            });
            return markers;
          })();
          return aeds_layer;
        })()
      );
    }
    if(isDesktopWidth) {
  		// Implementation details for the ev cahrging station layer
  		LAYER_MANAGER.register_layer(
  			(function() {
  				var stations_layer = new Layer('charging-stations');
  				stations_layer.markers = (function() {
  					var markers = [];
  					$.ajax({
  						url     :STATIONS_URL,
  						dataType:'json',
  						async   :false,
  						success :
  							function(data, text_status, jq_xhr) {
  								var icon   = {
  										url: STATIC_URL + '/images/markers/ev.png',
  										size: new google.maps.Size(32, 32)
  								};

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
  													icon      : icon
  												})
  											);
  										}
  									});
  								}
  							}
  					});
  					return markers;
  				})();
  				return stations_layer;
  			})()
  		);
    }

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
							var icon   = {
                url: STATIC_URL + 'images/markers/handicap.png',
                size: new google.maps.Size(25,25),
              };
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
				var dining_layer     = new Layer('food');
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
						icon = {
							url: STATIC_URL + 'images/markers/food.png',
							size: new google.maps.Size(25, 25)
            };

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
										existing_points.push(new ExistingPoint(point[0],point[1]));
									}
									markers.push(
										new google.maps.Marker({
											icon     : icon,
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

    if(isDesktopWidth) {

        (function() {
            $.each(SHUTTLE_STOPS, function(index, stop) {
                $('#shuttle-stop-wrapper select').append($("<option></option>").attr('value', stop.id).text(stop.name));
            });

            var stopMarker = null;
            var stopInfoBox = null;
            $('#shuttle-stop-wrapper select').change(function() {
                var value = $(this).val();
                if (value != '') {
                    for (var key in SHUTTLE_STOPS) {
                        stop = SHUTTLE_STOPS[key];
                        if (stop.id == value) {
                            if (stopMarker != null) {
                                stopMarker.setPosition(new google.maps.LatLng(stop.lat, stop.lon));
                                stopMarker.setVisible(true);
                                var route_names = '';
                                for(var index in stop.routes) {
                                    route_names += '<br><a class="route-link" href="#shuttle-' + stop.routes[index].shortname.replace(/ /g, '-') + '">' + stop.routes[index].shortname + '</a>';
                                }
                                stopInfoBox.setContent('<div><b>Stop:</b> ' + stop.name + '<br><b>Routes:</b>' + route_names +'</div>');
                            } else {
                                stopMarker = new google.maps.Marker({
                                    position : new google.maps.LatLng(
                                        stop.lat,
                                        stop.lon
                                    ),
                                    map      : MAP,
                                    title    : stop.name
                                });

                                var route_names = '';
                                for(var index in stop.routes) {
                                    route_names += '<br><a class="route-link" href="#shuttle-' + stop.routes[index].shortname.replace(/ /g, '-') + '">' + stop.routes[index].shortname + '</a>';
                                }
                                stopInfoBox = new google.maps.InfoWindow({
                                    content: '<div><b>Stop:</b> ' + stop.name + '<br><b>Routes:</b>' + route_names + '</div>'
                                });

                                google.maps.event.addListener(stopMarker, 'click', function() {
                                    stopInfoBox.open(MAP, stopMarker);
                                });
                            }
                            stopInfoBox.open(MAP, stopMarker);
                            MAP.panTo(new google.maps.LatLng(stop.lat, stop.lon));
                            break;
                        }
                    }
                } else {
                    if (stopMarker != null) {
                        stopMarker.setVisible(false);
                        stopInfoBox.close();
                    }
                }
            });

            // actively set click event to Info Windows set above
            $('.route-link').live('click', function(e) {
                e.preventDefault();
                var link = $(this);
                $(link.attr('href')).click();
            });

            $.each(SHUTTLE_ROUTES.routes, function(index, route) {
                // Append a new route label to menu
                var domId = 'shuttle-' + route.shortname.replace(/ /g, '-');
                var categoryDomId = route.category.replace(/ /g, '-').toLowerCase() + '-routes';
                var categoryDom = $('#' + categoryDomId);
                var label = '<label><input type="checkbox" id="' + domId + '"> ' + route.shortname + '</label>';
                categoryDom.append(label);

                if (SHUTTLE_STOPS.length > 0) {
	                // Implementation detail for the shuttle route layer
	                LAYER_MANAGER.register_layer(
	                    (function() {
	                        var shuttle_layer = new Layer(domId);
	                        shuttle_layer.layer = new google.maps.KmlLayer(
	                                BASE_URL + '/shuttles/' + route.id + '/poly/.kml?&_=' + (new Date()).getTime(),
	                                {
	                                    preserveViewport    : true,
	                                    suppressInfoWindows : true
	                                }
	                        );
	                        shuttle_layer.markers = (function(routeId) {
	                            var markers = [];
	                            $.ajax({
	                                url      : '/shuttles/' + routeId + '/stops/.json',
	                                dataType : 'json',
	                                async    : true,
	                                success: function(data){
	                                    if(typeof data.stops != 'undefined') {
	                                        $.each(data.stops, function(index, spot) {
	                                            var stopMarker = new google.maps.Marker({
	                                                position : new google.maps.LatLng(
	                                                    spot.lat,
	                                                    spot.lon
	                                                ),
	                                                map      : MAP,
	                                                title    : spot.name,
	                                                visible  : false
	                                            });
	                                            var infoWindow = new google.maps.InfoWindow({
	                                                content: '<div>Stop: ' + spot.name + '</div>'
	                                            });

	                                            google.maps.event.addListener(stopMarker, 'click', function() {
	                                                infoWindow.open(MAP, stopMarker);
	                                            });

	                                            markers.push(stopMarker);
	                                        });
	                                    }
	                                }
	                            });
	                            return markers;
	                        })(route.id);

	                        shuttle_layer.shuttleRouteId = route.id;

	                        return shuttle_layer;
	                    })()
	                );
								}
            });

            var shuttleInterval =
                setInterval(function() {
                    $.each(LAYER_MANAGER.layers, function(index, layer) {
                        if (layer.shuttleRouteId != null && layer.active) {
                            updateShuttleGpsData(layer);
                        }
                    });
                }, 4000);
            $('#refresh-shuttle-gps').click(function() {
                if($(this).is(':checked')) {
                    shuttleInterval = setInterval(function() {
                            $.each(LAYER_MANAGER.layers, function(index, layer) {
                                if (layer.shuttleRouteId != null && layer.active) {
                                    updateShuttleGpsData(layer);
                                }
                            });
                        }, 4000);
                } else {
                    clearInterval(shuttleInterval);
                }
            });
        })();

    } // End if desktop

		(function() {
			var activated_layer = false;
			// Activated layers
			$.each(ACTIVATED_LAYERS, function(index, layer_name) {
				var layer = LAYER_MANAGER.get_layer(layer_name);
				if (layer_name == 'shuttles') {
					MENU.change_tabs({
						'label':'Shuttles',
						'html' :$('#shuttle-routes-content').clone(true, true).show()
					});
				} else if(layer != null) {
					layer.activate();
					activated_layer = true;
					if(layer.name == 'parking') {
						MENU.change_tabs({
								'label':'Parking',
								'html' :$('#parking-key-content').html()
							});
					}
				}
			});

      if(isDesktopWidth) {
  			if(!activated_layer) {
  				// Display the google map points layer when the  map loads
  				options.illustrated ? (LAYER_MANAGER.get_layer('ipoints')).toggle() : (LAYER_MANAGER.get_layer('gpoints')).toggle();
  			}
      }
		})();


		// Attach click handles to layer checkboxes
		(function() {
			$.each(LAYER_MANAGER.layers, function(index, layer) {
				var name     = layer.name,
					checkbox = $('input[type="checkbox"][id="' + layer.name + '"]');

				if(layer.active) {
					checkbox.attr('checked', 'checked');
				}

				checkbox
					.click(function() {
						// For parking, change menu to legend
						if($(this).attr('id') == 'parking' && $(this).is(':checked')) {
							MENU.change_tabs({
								'label':'Parking',
								'html' :$('#parking-key-content').html()
							});
						}
						layer.toggle();
					});
			});
          // Add click event to Shuttle Routes
          var shuttle_checkbox = $('input[type="checkbox"][id="shuttle-routes"], .shuttle-routes-btn');
          shuttle_checkbox.click(function() {
              if($(this).is(':checked')) {
                  MENU.change_tabs({
                      'label':'Shuttles',
                      'html' :$('#shuttle-routes-content').clone(true, true).show()
                  });
              }
          });

          // Add click event to Shuttle Route Information
          var shuttleInfoButton = $('#shuttle-info-button');
          shuttleInfoButton.click(function(event) {
              event.preventDefault();
              MENU.change_tabs({
                  'label' : 'Shuttles',
                  'html'  : $('#shuttle-info').clone(true, true).show()
              });
          });

          // Add back button for route info or any other buttons that go to the routes menu
          var shuttle_checkbox = $('.shuttle-routes-btn');
          shuttle_checkbox.click(function() {
              MENU.change_tabs({
                  'label':'Shuttles',
                  'html' :$('#shuttle-routes-content').clone(true, true).show()
              });
          });

          if (SHUTTLE_STOPS == 0) {
          	$('#route-information').hide();
          }

          // Add click event to Emergency box
          var emergency_checkbox = $('input[type="checkbox"][id="emergency"], .emergency-btn');
          emergency_checkbox.click(function() {
              if($(this).is(':checked')) {
                  var $html = $('#emergency-content').clone(true, true).show();
                  MENU.change_tabs({
                      'label': 'Emergency',
                      'html' : $html
                  }, function() {
                    $html.find('.init-checked:not(:checked)').trigger('click');
                  });

              }
          });

          // Add back button for route info or any other buttons that go to the routes menu
          var emergency_checkbox = $('.emergency-btn');
          emergency_checkbox.click(function() {
              MENU.change_tabs({
                  'label':'Emergency',
                  'html' :$('#emergency-content').clone(true, true).show()
              });
          });

		})();


		// Search result selection. Tab and infobox population
		// --
		// For some reason I can't get this events list to bind
		// to the #search-form ul element. Bind it to body and
		// pass #search-form ul as an argument
		$('#search > ul > li:not(.more)')
			.live('click', function() {
				var location_id = $(this).find('a').attr('data-pk');
				if(location_id) {

					// Change menu tab to a loading indicator
					MENU.change_tabs({
							label:'Location',
							html :'<div class="item load">Loading...</div>'
						});
					UTIL.highlight_location(
						location_id,
						{
							func: function(data) {
								// Populate the menu tab
								MENU.change_tabs({'html':data.info});
							}
						}

					);
				}
				SEARCH.hide_results();
			})
			.find('a').live('click', function(e) {e.preventDefault()});

		$('body').bind('search-result-highlighted', function(event) {
			var location_id = $("#search-results").find('.hover').find('a').attr('data-pk');
			if(location_id) {
				MENU.change_tabs({
							label:'Location',
							html :'<div class="item load">Loading...</div>'
						});
				UTIL.highlight_location(
					location_id,
					{
						func: function(data) {
							// Populate the menu tab
							MENU.change_tabs({'html':data.info});
						}
					}
				);
			}
		});
	}

	if(options.infobox_location_id != null) {
		UTIL.highlight_location(options.infobox_location_id, {pan:true});
	}

    function updateShuttleGpsData(layer) {
        var markers = [];
        $.ajax({
            url      : '/shuttles/' + layer.shuttleRouteId + '/gps/.json',
            dataType : 'json',
            async: true,
            success: function(data) {
                if(typeof data.locations != 'undefined') {

                    // Remove old GPS locations
                    if(layer.gpsMarkers != null) {
                        $.each(layer.gpsMarkers, function (index, oldGpsMarker) {
                            oldGpsMarker.setMap(null);
                        });
                    }

                    // Add new GPS locations
                    $.each(data.locations, function(index, spot) {
                        var icon = {
                            url: STATIC_URL + '/images/markers/shuttle.png',
                            size: new google.maps.Size(25, 25)
                        },
                        gpsMarker = new google.maps.Marker({
                            position : new google.maps.LatLng(
                                spot.lat,
                                spot.lon
                            ),
                            map     : MAP,
                            title   : spot.name,
                            visible : layer.active,
                            icon    : icon,
                        });
                        var infoWindow = new google.maps.InfoWindow({
                            content: '<div>Shuttle ' + spot.id + '</div>'
                        });

                        google.maps.event.addListener(gpsMarker, 'click', function() {
                            infoWindow.open(MAP, gpsMarker);
                        });

                        markers.push(gpsMarker);
                    });
                }

                layer.gpsMarkers = markers;
            }
        });
    }

	/*********************************
	 *
	 * InfoBox
	 *
	 *********************************/
	 function InfoManager() {
	 	var that = this;

	 	this.infos = [];

	 	this.register = function(info) {
	 		that.infos.push(info);
	 	};

	 	this.clear = function() {
	 		$.each(that.infos, function(index, info) {
	 			info.close();
	 		});
	 		that.infos = [];
	 	};

	 }

	 function Info(position, name, options) {
	 	var that         = this,
	 		lat_lng      = new google.maps.LatLng(position[0], position[1]),
	 		content      =  null,
	 		test_content = null,
	 		default_options  = {
	 			link : null,
	 			pan  : false
	 		};
	 	this.box = null;

	 	options = $.extend({}, default_options, options);

	 	// Wrap the text in a link if neccessary
	 	if(options.link != null) {
	 		name = '<a href="' + options.link + '">' + name + '</a>';
	 	}
	 	content = $('<div class="iBox"><a class="iclose">X</a>' + name + '</div>');

	 	// Create a hidden test box to figure out the correct width
	 	test_content = $('<div id="testBox" class="iBox">' + content + '</div>')[0];
	 	$('body').append(test_content);

		// Close button listener
	 	content.find('.iclose').click(function(e) {
	 		e.preventDefault();
	 		that.box.close();
	 	});
	 	content             = content[0];
	 	// content.style.width = test_content.offsetWidth + 'px';

	 	// Create the box and set it's position
	 	this.box = new InfoBox({
	 		content                : content,
			alignBottom            : true,
			pixelOffset            : new google.maps.Size(-18, -3),
			maxWidth               : 0,
			closeBoxURL            : "",
			pane                   : "floatPane",
			infoBoxClearance       : new google.maps.Size(1, 1),
			enableEventPropagation : false
	 	});
	 	this.box.setPosition(lat_lng);
	 	this.box.open(MAP);

	 	if(options.pan) {
	 		MAP.panTo(lat_lng);
	 	}

	 	this.close = function() {
	 		that.box.close();
	 	};
	 }

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
		};

		this.load_all_layers = function() {
			$.each(that.layers, function(index, layer) {
				layer.toggle();
			});
		};

		this.register_layer = function(layer) {
			that.layers.push(layer);
		};
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

		this.active     = false;
		this.name       = name;
		this.layer      = null; // the actual Google Maps layer on the map, if applicable
		this.markers    = null; // the actual Google Maps markers on the map, if applicable
        this.shuttleRouteId = null;
        this.gpsMarkers = null; // Google marker for gps data that can be used to refresh on an interval (unlike markers)

		this.toggle = function() {
			that.active ? that.deactivate() : that.activate();
		};

		this.activate = function() {
			if(that.active != true) {
				that.active = true;
				if(that.layer != null) {
					that.layer.setMap(MAP);
				}
				if(that.markers != null) {
					$.each(that.markers, function(index, marker) {
						marker.setVisible(true);
					});
				}

                // Get the latest GPS data
                if(that.shuttleRouteId != null) {
                    updateShuttleGpsData(that);
                }
			}
		};

		this.deactivate = function() {
			if(that.active != false) {
				that.active = false;
				if(that.layer != null) {
					that.layer.setMap(null);
				}
				if(that.markers != null) {
					$.each(that.markers, function(index, marker) {
						marker.setVisible(false);
					});
				}
                if(that.gpsMarkers != null) {
                    $.each(that.gpsMarkers, function(index, marker) {
                        marker.setVisible(false);
                    });
                }
			}
		};
	}


  /*********************************
   *
   * Mobile Menu
   *
   *********************************/


  function MobileMenu() {

    var $mobileMenu = $('#mobile-menu'),
        $shuttleMenu = $('#shuttle-menu'),
        $menuItem = $('.menu-item'),
        youAreHereMarker,
        youAreHereInfowindow = new google.maps.InfoWindow({
          content: '<div>You are here!</div>'
        }),
        $loadingTarget = $('.loading-target'),
        locationTimoutId;

    function showMobileMenu() {
      $mobileMenu.addClass('slide-out');
      $mobileMenu.height($( document ).height());
    }

    function closeMobileMenu() {
      $mobileMenu.removeClass('slide-out');
    }

    function mobileMenuHandler() {
      $('#mobile-menu-trigger').click(showMobileMenu);
    }

    function closeMobileMenuIconHandler() {
      $mobileMenu.find('.close-icon').click(closeMobileMenu);
    }

    function closeMobileMenuHandler() {
      $(document).click(function(e) {
        var $target = $(e.target);

         // Hide the mobile menu when anything else is clicked
         if(!$target.closest('#mobile-menu').length && !$target.closest('#mobile-menu-trigger').length) {
            if($mobileMenu.width() > 200) {
              closeMobileMenu();
            }
         }
      });
    }

    function getLocationMarker(position) {
      clearTimeout(locationTimoutId);
      var markerLatLng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude),
          icon   = {
              url: STATIC_URL + '/images/markers/location.png',
              size: new google.maps.Size(25, 25)
          };

      if(youAreHereMarker) {
        youAreHereMarker.setPosition( markerLatLng );
        MAP.panTo( markerLatLng );
        youAreHereInfowindow.open(MAP,youAreHereMarker);
      } else {
        youAreHereMarker = new google.maps.Marker({
          position: markerLatLng,
          map: MAP,
          icon: icon,
          title: "You are here!"
        });

        MAP.panTo(markerLatLng);
        youAreHereInfowindow.open(MAP,youAreHereMarker);

        google.maps.event.addListener(youAreHereMarker, 'click', function(event) {
          youAreHereInfowindow.open(MAP,youAreHereMarker);
        });
      }
      $loadingTarget.closest('.menu-highlight').removeClass('menu-highlight');
      $loadingTarget.toggleClass('fa-spinner fa-pulse fa-compass');
      closeMobileMenu();
    }

    function showError(error) {
      clearTimeout(locationTimoutId);
      $loadingTarget.closest('.menu-highlight').removeClass('menu-highlight');
      $loadingTarget.toggleClass('fa-spinner fa-pulse fa-compass');

      switch(error.code) {
        case error.PERMISSION_DENIED:
            log("User denied the request for Geolocation.");
            break;
        case error.POSITION_UNAVAILABLE:
            alert("Location information is unavailable. Verify that GPS is enabled.");
            break;
        case error.TIMEOUT:
            alert("The request to get location timed out.");
            break;
        case error.UNKNOWN_ERROR:
            alert("Unable to get location.");
            break;
      }
    }

    function disabledGeoHandler() {
      $loadingTarget.closest('.menu-highlight').removeClass('menu-highlight');
      $loadingTarget.toggleClass('fa-spinner fa-pulse fa-compass');
      alert("Location information is unavailable. Verify that GPS is enabled.");
    }

    function getLocation() {
      if (navigator.geolocation) {
        locationTimoutId = setTimeout(disabledGeoHandler, 5000);
        navigator.geolocation.getCurrentPosition(getLocationMarker, showError);
      } else {
        alert("Geolocation is not supported by this browser.");
        closeMobileMenu();
      }
    }

    function toggleMenu($target) {
      var $menu = $target.closest('li'),
          $subMenu = $menu.find('ul').eq(0);

      if($target.is('label')) {
        $menu.toggleClass('menu-highlight');
      }

      if(!$menu.attr('data-menu-highlight') || ($menu.attr('data-menu-highlight') && $menu.attr('data-menu-highlight') === true)) {
        $menu.toggleClass('menu-highlight');
      }

      if($subMenu.length) {
        $subMenu.slideToggle(function() {
          $menu.find('.toggle-icon').eq(0).toggleClass('fa-chevron-down fa-chevron-up');
        });
      }
    }

    function menuItem(e) {
      var $target = $(e.target),
          dataMenu = $target.closest('h4').attr('data-menu');
      toggleMenu($target);

      switch (dataMenu) {
        case 'location':
          $loadingTarget.toggleClass('fa-spinner fa-pulse fa-compass');
          getLocation();
          break;
        case 'parking':
          LAYER_MANAGER.get_layer('parking').toggle();
          break;
        case 'food':
          LAYER_MANAGER.get_layer('food').toggle();
          closeMobileMenu();
          break;
      }

    }

    function menuItemHandler() {
      $menuItem.click(menuItem);
    }

    function initMobileMenu() {
      mobileMenuHandler();
      closeMobileMenuHandler();
      closeMobileMenuIconHandler();
      menuItemHandler();
    }

    initMobileMenu();
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
		var that         = this,
			container    = $('#menu-wrap'), // contains all of the menu HTML,
			menu         = $('#menu-window'), // this is the window through which the faces are viewed
			tab_one      = $('#tab-one'),
			tab_two      = $('#tab-two'),
			header_width = $('#menu-header').width() - 10,
			stage        = $('menu_stage');

		// Set all the faces to the same height
		menu.equalHeights();

		// The menu header has a gap the needs to move left and right
		// depending on how many tabs are displayed
		function reset_tab_gap() {
			var width = header_width - tab_one.width();
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
			});

		tab_one.click(function() {
			that.change_tabs();
		});
		tab_two.click(function() {
			that.change_tabs({
				label:$(this).text(),
				html :stage.html()
			})
		});

		// There are two button in the upper right hand corner of the menu:
		// email and print. They are updated based on various actions
		// ------
		this.change_buttons = function(options) {
			var defaults = {
				'loc_id'  : false,
				'title'   : false,
				'subject' : "UCF Campus Map",
				'body'    : escape("UCF Campus Map\nhttp://map.ucf.edu/"),
				'print'   : BASE_URL + '/print/?',
				'toggle_illustrated' : false
			};

			// setting
			var s = $.extend({}, defaults, options);

			var illustrated = (MAP.mapTypeId === 'illustrated');

			if(s.toggle_illustrated){
				var href = $('#print').attr('href');
				href = href.replace('&illustrated', '');
				if(illustrated) href = href + '&illustrated';
				$('#print').attr('href', href);
				return;
			}

			if(s.loc_id){
				var title   = escape(s.title);
				var link    = BASE_URL + '/?show=' + s.loc_id;
				link = escape(link);
				s.subject = escape("UCF Campus Map - ") + title;
				s.body    = title + escape("\n") + link;
				s.print   = s.print + '&show=' + s.loc_id;
			}

			// update email button
			var mailto = "mailto:?subject=" + s.subject + "&body=" + s.body;
			$('#email').attr('href', mailto);

			// update print button
			if(illustrated) s.print = s.print + '&illustrated';
			$('#print').attr('href', s.print);
		}
		this.change_buttons();

		this.change_tabs = function(options, callback) {
			var defaults = {
				'label':false,
				'html' :false
			}

			var settings = $.extend({}, defaults, options);

			// If no label or html is set, go back to the `Menu` tab
			if(!settings.label && !settings.html) {
				menu.animate({'margin-left':0}, 300);
				tab_one.removeClass('off');
				tab_two.addClass('off');
			} else {
				tab_two.removeClass('off');
				tab_one.addClass('off');
				if(settings.label) {
					$('#menu-title').html(settings.label); // tab two title

				}
				tab_two.show();

				if(settings.html) {
                    $('#menu-stage').empty();
                    if (settings.html instanceof jQuery) { // tab two content
                        settings.html.appendTo('#menu-stage');
                    } else {
                        $('#menu-stage').html(settings.html);
                    }
				}

        menu.animate({'margin-left':-690}, 300, callback);

				reset_tab_gap();
				menu.equalHeights();
			}
		}

		// Add the menu to the map in the upper right
		MAP.controls[google.maps.ControlPosition.RIGHT_TOP].push(container[0]);

    if (typeof callback !== 'undefined' && typeof callback === 'function') {
      console.log('callback!');
      callback();
    }
	}

	/*********************************
	 *
	 * Search
	 *
	 *********************************/
	function Search() {
		var that    = this,
			element = null,
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
				ESCAPE     :27
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
      icon = document.createElement('i');
			ul     = document.createElement('ul');

			div.id        = 'search';
			div.style.zIndex = 9999;

			form.method = 'get';
			form.action = SEARCH_URL;
			form.id     = 'search-form';

			input.type         = 'text';
			input.name         = 'q';
			input.autocomplete = 'off';
      input.placeholder = 'Search Map';

      icon.className = 'fa fa-search fa-2x';

			anchor.id = 'search-submit';
      anchor.title = 'search icon';
      anchor.onclick = submitSearchForm;
			anchor.appendChild(icon);

			ul.id = 'search-results';
			ul.style.display = 'none';

			form.appendChild(input);
			form.appendChild(anchor);

			div.appendChild(form);
			div.appendChild(ul);

			return div;
		})();
		MAP.controls[google.maps.ControlPosition.TOP_LEFT].push(element);
		element = $(element);
		input   = element.find('input');
		results = element.find(' > ul');

    function submitSearchForm () {
      $('#search-form').submit();
    }

    // Hide the search results when anything else is clicked
    $(document).click(function(e) {
      var $target = $(e.target);
      if($target.closest('#search').length === 0) {
        results.hide();
      }
    });

		// Attach the typing events
		input
			.focus(function(event) {
				if($(this).val() != '') {
					$(this).trigger('keyup');
				}
			})
			.keydown(function(event) {
				var keycode = UTIL.parse_keycode(event);
				if(keycode == KEYCODES.ENTER) {

				}
			})
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
					var current = results.find('.hover'),
						next    = null;
					if(current.length) {
						current.removeClass('hover');
						next = current.next();
					} else {
						next = results.find('li:first');
					}
					next.addClass('hover');
					$('body').trigger('search-result-highlighted', [next]);
				} else if(keycode === KEYCODES.UP) { // Scroll up results
					var current = results.find('.hover'),
						next    = null;
					if(current.length) {
						current.removeClass('hover');
						next = current.prev();
					} else {
						next = results.find('li:last');
					}
					next.addClass('hover');
					$('body').trigger('search-result-highlighted', [next]);
				} else if(keycode === KEYCODES.ESCAPE) { // Empty and hide results
					abort_ajax();
					that.hide_results();
				} else {
					if(search_query === '') {
						results.hide();
					} else {
						results.empty().show();

            results.height(SEARCH_RESULTS_SIZE);

						// Wait <timeout> duration between keypresses before doing search
						clearTimeout(timer);
						timer = setTimeout(function() {
							results.append('<li><a data-pk="searching">Searching&hellip;</a></li>');

							ajax = $.getJSON(
								[SEARCH_URL, 'json'].join('.'),
								{q:search_query},
								function(data, text_status, jq_xhr) {
									results.empty();

									if(data && data.results && typeof data.results != 'undefined') {
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
													results.append('<li class="more"><a href="' + data.results_page_url + '">More Results &hellip;</a></li>');
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

		this.hide_results = function() {
			results.empty().hide();
		}
	}

	/*********************************
	 *
	 * Utility
	 *
	 *********************************/
	function Util() {
		var that = this;

		// Returns the URL of a illustrated map tiles based on the specified
		// coordinate and zoom. If coordinate and/or zoom are outside the illustrated
		// map's viewable area, return a white tile.
		this.get_illustrated_tile = function(coordinate, zoom) {
			var filename = null,
				no_tile  = 'white.png',
				// Smallest map dimensions
				dimensions     = {x:2.5, y:3.5},
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
			return 'url("http://cdn.ucf.edu/map/tiles/' + filename + '?_=' + new Date().getTime() + '")';
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
      var icon = {
        url: STATIC_URL + 'images/markers/' + color + '.png',
        size: new google.maps.Size(20, 20)
      };
			return icon;
		}

		// Creates an info box for a location and also executes arbitary function
		// Special handling for Group objects to show each individual info box
		// and set an appropriate zoom level
		this.highlight_location = function(location_id, options) {
			var options = $.extend({
				func              : undefined,
				pan               : false,
				reset_zoom_center : true,
				sublocation       : false
			}, options);

			if(!options.sublocation) INFO_MANAGER.clear();

			$.ajax({
				url      :LOCATION_URL.replace('%s', location_id),
				dataType :'json',
				success  : function(data, text_status, jq_xhr) {
					var map_type       = MAP.mapTypeId;
					var point_type     = (map_type === 'illustrated') ? 'illustrated_point' : 'googlemap_point',
						default_zoom   = (map_type === 'illustrated') ? IMAP_OPTIONS.zoom : GMAP_OPTIONS.zoom,
						default_center = (map_type === 'illustrated') ? IMAP_OPTIONS.center : GMAP_OPTIONS.center;

					if(typeof options.func != 'undefined') {
						options.func(data);
					}

					if(data.object_type == 'Group') {
						CURRENT_LOCATION = location_id;
						// Pan to the group center point
						MAP.panTo((new google.maps.LatLng(data[point_type][0], data[point_type][1])));

						$.each(data.locations.ids, function(index, sub_location_id) {
							that.highlight_location(sub_location_id, {sublocation:true});
							if(index == (data.locations.ids.length - 1)) {
								$('body').bind('highlight-location-loaded', function(event, event_location_id) {
									if(event_location_id == sub_location_id) {
										$('body').unbind('highlight-location-loaded');
										if(typeof data[point_type] != 'undefined') {
											var points           = [],
												distance_total   = 0,
												distance_count   = 0,
												average_distance = null,
												zoom             = null,
												interval         = .09,
												increment        = .05;

											if(SIMPLE) {
												zoom = 16;
											} else {
												if(map_type == 'illustrated') {
													zoom = 16;
												} else {
													zoom = 19;
												}
											}

											// Collect the position of each infobox
											$.each(INFO_MANAGER.infos, function(index, info) {
												var pos = info.box.getPosition();
												if(pos != null) points.push(pos);
											});

											// Caculate the average distance between them
											$.each(points, function(index, point) {
												$.each(points, function(_index, cpoint) {
													if(index != _index) {
														var distance = that.calc_distance(point, cpoint);
														if(distance > 0) {
															distance_total += distance;
															distance_count += 1;
														}
													}
												});
											});
											average_distance = distance_total / distance_count;
											// Iterate to figure out the zoom
											while(average_distance > interval) {
												interval += increment;
												zoom     -= 1;
											}

											if(SIMPLE) {
												MAP.setZoom(zoom - 1);
											} else {
												if(map_type == 'illustrated') {
													if(zoom < 12) zoom = 12;
													if(zoom > 16) zoom = 16;
												} else {
													zoom = (zoom < 15) ? 15 : zoom;
												}
												MAP.setZoom(zoom);
											}
										}
									}
								});
							}
						});
						if(MENU != null) {
							MENU.change_buttons({'loc_id':location_id, 'title': data.name});
						}
					} else {
						// Create the info box(es)
						if(typeof data[point_type] != 'undefined' && data[point_type] != null) {

							INFO_MANAGER.register(
								new Info(
									data[point_type],
									data.name,
									{link: data.profile_link}
								)
							);

							if(!options.sublocation) {
								CURRENT_LOCATION = location_id;
								if(MENU != null) {
									MENU.change_buttons({'loc_id':location_id, 'title': data.name});
								}
							}
							$('body').trigger('highlight-location-loaded', [location_id]);
						}
					}
				}
			});
		}

		// Calculate the distance between two Google LatLng objects
		this.calc_distance = function(a, b) {
			var a_lat = a.lat(),
				a_lng = a.lng(),
				b_lat = b.lat(),
				b_lng = b.lng(),
				x     = null,
				y     = null,
				R     = 6371; // radius of the earth
			a_lat = a_lat * (Math.PI/180);
			a_lng = a_lng * (Math.PI/180);
			b_lat = b_lat * (Math.PI/180);
			b_lng = b_lng * (Math.PI/180);
			return Math.acos(Math.sin(a_lat)*Math.sin(b_lat) + Math.cos(a_lat)*Math.cos(b_lat) * Math.cos(b_lng-a_lng)) * R;
		}

		// Resize the map canvas to be 100% height and width
		this.resize_canvas = function() {
      var viewPort = Number($(window).height()),
          ucfHeader = 100,
          header = Number($('#map header').height()),
          footer = Number($('footer').height()),
          headerFooter = ucfHeader + header + footer,
          height = viewPort - headerFooter,
          menuHeight = height - ($('#search').height() + 90);

			$('#map-canvas').height(height).fadeIn();

      // set search menu height
      if(SEARCH_RESULTS_SIZE === 0) {
        if(menuHeight < 500) {
          SEARCH_RESULTS_SIZE = menuHeight;
        } else {
          SEARCH_RESULTS_SIZE = 500;
        }
      }
		}
	}

	// Log a message to the console if it's available
	function log() {
		if(typeof console !== 'undefined') {
			console.log(arguments);
		}
	}
}

var getZoom = function() {
	$width = $(window).width();

	if ($width < 295) {
		return 14;
	} else if ( $width > 296 && $width < 465 ) {
		return 15;
	} else if ( $width > 466 && $width < 768 ) {
		return 15;
	} else if ( $width > 769 && $width < 1600 ) {
		return 16;
	} else {
		return 17;
	}
}

// Google Analytics Click Tracking

function trackClick(e) {
  var $target = $(e.target).closest('.ga-tracking'),
      category = ($target.attr('data-category')) ? $target.attr('data-category') : '',
      action = ($target.attr('data-action')) ? $target.attr('data-action') : '',
      label = ($target.attr('data-label')) ? $target.attr('data-label') : '';
  _gaq.push(['_trackEvent', category, action, label]);
}

function gaTracking () {
  $('.ga-tracking').live('mousedown', trackClick);
}

$(gaTracking);

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
		$(this).children().css({'min-height': currentTallest});
	});
	return this;
}
