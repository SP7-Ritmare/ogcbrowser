var testvar;
String.prototype.trunc = String.prototype.trunc ||
    function(n) {
        return this.length > n ? this.substr(0, n - 1) + '...' : this.substr(0);
    };

var app = angular.module('OgcBrowser', [
    'ui.router',
    'restangular',
    'ui.bootstrap',
    //'ui.bootstrap.modal',
    'openlayers-directive',
    'angular-loading-bar',
    'ngSanitize'
])

app.service('loginModal', function ($modal, $rootScope) {
    function assignCurrentUser (user) {
        $rootScope.currentUser = user;
        return user;
    }
    return function() {
        var instance = $modal.open({
            templateUrl: 'loginModalTemplate.html',
            controller: 'LoginModalCtrl',
            controllerAs: 'LoginModalCtrl'
        });
        return instance.result.then(assignCurrentUser);
    };
});

app.run(function ($rootScope, $state, loginModal) {
    $rootScope.$on('$stateChangeStart', function (event, toState, toParams) {
        var requireLogin = toState.data.requireLogin;
        if (requireLogin && typeof $rootScope.currentUser === 'undefined') {
            event.preventDefault();
            loginModal()
                .then(function () {
                    alert('bbb')
                    return $state.go(toState.name, toParams);
                })
                .catch(function () {
                    alert('ccc')
                    return $state.go('welcome');
                });
        }
    });
});

app.factory("UsersApi", function ($q) {
    function _login (email, password) {
        alert('login');
        var d = $q.defer();
        setTimeout(function () {
            if (email == password)
                d.resolve();
            //defer.reject();
        }, 100);
        return d.promise
    }
    return { login: _login };
});

app.controller('LoginModalCtrl', function ($scope, UsersApi) {
    this.cancel = $scope.$dismiss;
    this.submit = function (email, password) {
        UsersApi.login(email, password).then(function (user) {
            $scope.$close(user);
          });
    };
});

app.config(function($stateProvider, $urlRouterProvider, RestangularProvider) {
    //$urlRouterProvider.otherwise("/nodes");
    $urlRouterProvider.when('','/nodes/list');
    $stateProvider
        .state('welcome', {
            url: "/",
            data: {
                requireLogin: false
            }//,
            //templateUrl: "login.html"
        })
        .state('nodes', {
            url: "/nodes",
            templateUrl: "index.html",
            controller: "ListCtrl",
            data: {
                requireLogin: false
            }
        })
        .state('nodes.list', {
            url: "/list",
            templateUrl: "list.html"
            //controller: "ListCtrl"
        })
        .state('nodes.detail', {
            url: '/:id',
            templateUrl: 'detail.html',
            controller: "DetailCtrl"
        });
    // .state('nodes.run', {
    //     url: '/:id/run',
    //     templateUrl: 'nodes.run.html',
    //     controller: "RunCtrl"
    // })
});

var styles = {
    'Polygon' : [new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'rgba(0, 0, 255, 0.5)',
            lineDash: [4],
            width: 3
        }),
        fill: new ol.style.Fill({
            color: 'rgba(0, 0, 255, 0.0)'
        })
    })],
    'PolygonSelected' : [new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'rgba(0, 0, 255, 0.5)',
            //lineDash: [4],
            width: 1
        }),
        fill: new ol.style.Fill({
            color: 'rgba(0, 0, 255, 0.0)'
        })
    })],
    'LineString' : [new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'rgba(0, 0, 255, 0.5)',
            lineDash: [4],
            width: 1
        }),
        fill: new ol.style.Fill({
            color: 'rgba(0, 0, 255, 0.0)'
        })
    })],
    'LineStringSelected' : [new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: 'rgba(0, 0, 255, 0.5)',
            //lineDash: [4],
            width: 1
        }),
        fill: new ol.style.Fill({
            color: 'rgba(0, 0, 255, 0.0)'
        })
    })],
    'PointSensor': [new ol.style.Style({
        image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
            // anchor: [0.5, 46],
            anchor: [0.5, 1],
            // anchorXUnits: 'fraction',
            // anchorYUnits: 'pixels',
            opacity: 0.75,
            scale: 0.8,
            src: '/static/img/sos_icon.png'
        }))
    })],
    'PointSelected': [new ol.style.Style({
        image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
            // anchor: [0.5, 46],
            anchor: [0.5, 1],
            // anchorXUnits: 'fraction',
            // anchorYUnits: 'pixels',
            opacity: 0.75,
            scale: 0.8,
            src: '/static/img/database-selected.png'
        }))
    })],
    'Point': [new ol.style.Style({
        image: new ol.style.Icon(/** @type {olx.style.IconOptions} */ ({
            // anchor: [0.5, 46],
            anchor: [0.5, 1],
            // anchorXUnits: 'fraction',
            // anchorYUnits: 'pixels',
            opacity: 0.75,
            scale: 0.5,
            src: '/static/img/database.png'
        }))
        // ,
        // text:  new ol.style.Text({
        //     font: '8px Calibri,sans-serif',
        //     text: feature.get('name').trunc(20),
        //     textAlign: 'start',
        //     offsetX: '6',
        //     offsetY: offsetY[Math.floor(Math.random()*offsetY.length)],
        //     fill: new ol.style.Fill({
        //  color: '#00f'
        //     }),
        //     stroke: new ol.style.Stroke({
        //  color: '#fff',
        //  width: 3
        //     })
        // })
    })]
}

var getStyleFunction = function(selected){
    return function(feature, resolution){
        var geo_type = feature.getGeometry().getType();
        var name = feature.get('name');
        if(selected){
            geo_type += 'Selected';
        }
        if(name == 'sensor'){
            geo_type = 'PointSensor';
        }
        //console.log(geo_type);
        return styles[geo_type];
    };
};

app.controller("DetailCtrl", ['$scope', '$state', '$stateParams', 'OgcBrowserService', 'olHelpers', 'olMapDefaults', 'olData',
                              function ($scope, $state, $stateParams, OgcBrowserService, olHelpers, olMapDefaults, olData) {
                                  $scope.nodesLoaded.then(function(nodes){

                                      var collection = $scope.nodesSelector.getFeatures();
                                      var selectedFeature = $scope.nodesLayer.getSource().getFeatureById($stateParams.id);
                                      collection.clear();
                                      //testvar =  $scope.layerGroup;
                                      collection.push(selectedFeature);
                                  });

                                  OgcBrowserService.getNode($stateParams.id).then(function(node){
                                      $scope.node = node;

                                      olData.getMap($scope.$parent.$id).then(function(map){

                                          var lon = node.geometry.coordinates[0];
                                          var lat = node.geometry.coordinates[1];

                                          var new_center = ol.proj.transform([lon, lat], 'EPSG:4326', 'EPSG:3857');

                                          var view = map.getView();

                                          var duration = 2000;
                                          var start = +new Date();
                                          var pan = ol.animation.pan({
                                              duration: duration,
                                              source: /** @type {ol.Coordinate} */ (view.getCenter()),
                                              start: start
                                          });
                                          var bounce = ol.animation.bounce({
                                              duration: duration,
                                              resolution: 4 * view.getResolution(),
                                              start: start
                                          });
                                          map.beforeRender(pan, bounce);

                                          view.setCenter(new_center);
                                          if(view.getZoom() != 9){
                                              view.setZoom(9);
                                          }

                                          $scope.loadBBOX = function(){
                                              var bboxsource = $scope.bboxlayer.getSource()
                                              angular.forEach(node.records, function(record, key) {
                                                  //console.log(record.bbox_coords);
                                                  if(record.bbox_coords) {
                                                      p = new ol.geom.Polygon(record.bbox_coords);
                                                      //p = new ol.geom.LineString(p.getCoordinates());
                                                      //console.log(p.getLinearRing(0));
                                                      var f = new ol.Feature({name: 'aa'});
                                                      f.setGeometry( p.transform('EPSG:4326', 'EPSG:3857'));
                                                      //console.log(p);
                                                      //testvar = record;

                                                      if(record.type == 'dataset' && record.bbox[0] != '180.0'){
                                                          //console.log(record.bbox.join());
                                                          bboxsource.addFeature(f);
                                                      }
                                                  }

                                                  if(record.point) {
                                                      p = new ol.geom.Point(record.point);
                                                      var f = new ol.Feature({name: 'sensor'});
                                                      f.setGeometry( p.transform('EPSG:4326', 'EPSG:3857'));
                                                      if(record.type == 'dataset' && record.point[0] != '180.0'){
                                                          bboxsource.addFeature(f);
                                                      }
                                                  }
                                              });
                                          };
                                      });
                                  });
                              }]);

app.controller("ListCtrl", ['$scope', '$state', 'OgcBrowserService', 'olHelpers', 'olMapDefaults', 'olData', '$sce',
                            function ($scope, $state, OgcBrowserService, olHelpers, olMapDefaults, olData, $sce) {
                                angular.extend($scope, {
                                    defaults: {
                                        interactions: {
                                            mouseWheelZoom: true
                                        },
                                        controls: {
                                            'zoom': true,
                                            'rotate': true,
                                            'attribution': true
                                        }
                                    }
                                });
                                $scope.setMapExtent = function(extent){
                                    olData.getMap($scope.$id).then(function(map){
                                        extent = ol.proj.transformExtent(extent, 'EPSG:4326', 'EPSG:3857');
                                        map.getView().fitExtent(extent, map.getSize());
                                        if(map.getView().getZoom() > 9){
                                            map.getView().setZoom(11);
                                        }
                                    });
                                };
                                $scope.addWMSLayer = function(extent, source, title){
                                    source.projection = ol.proj.Projection('EPSG:3857')
                                    // var layer = new ol.layer.Image({
                                    //  extent: ol.proj.transform(extent, 'EPSG:4326', 'EPSG:3857'),
                                    //  source: new ol.source.ImageWMS(source)
                                    // });
                                    source.params['TILED'] = true;
                                    var layer = new ol.layer.Tile({
                                        title: title,
                                        extent: ol.proj.transformExtent(extent, 'EPSG:4326', 'EPSG:3857'),
                                        source: new ol.source.TileWMS(source)
                                    });
                                    olData.getMap($scope.$id).then(function(map){
                                        //map.removeLayer($scope.extraLayerGroup);
                                        var layers = $scope.extraLayerGroup.getLayers()
                                        //if(!layers){
                                        //    layers = new ol.Collection;
                                        //}
                                        layers.push(layer);
                                        //$scope.extraLayerGroup.setLayers(layers);
                                        //map.addLayer($scope.extraLayerGroup);
                                        //testvar = layer;
                                        //map.addLayer(layer);
                                    });
                                };

                                $scope.initCenter = {lat: 42.437473,lon: 12.355672,zoom: 6}

                                $scope.setInitCenter = function(){
                                    $scope.center = angular.copy($scope.initCenter);
                                };
                                $scope.setInitCenter();

                                $scope.clearAll = function(){
                                    olData.getMap($scope.$id).then(function(map){
                                        $scope.extraLayerGroup.setLayers();
                                        map.removeLayer($scope.extraLayerGroup);
                                    });
                                    $scope.bboxlayer.getSource().clear();
                                };

                                $scope.nodesSource = new ol.source.GeoJSON(
                                    ({
                                        defaultProjection: "EPSG:4326",
                                        projection: "EPSG:3857",
                                        object: {
                                            'type': 'FeatureCollection',
                                            features: [
                                            ]
                                        }
                                    })
                                );
                                var nodesLayerId = 'nodes-layer';
                                $scope.nodesLayer = new ol.layer.Vector(
                                    {
                                        title: 'RITMARE Nodes',
                                        id: nodesLayerId,
                                        source: $scope.nodesSource,
                                        style: getStyleFunction(false)
                                    }
                                );
                                var bboxsource = new ol.source.GeoJSON(
                                    ({
                                        defaultProjection: "EPSG:4326",
                                        projection: "EPSG:3857",
                                        object: {
                                            'type': 'FeatureCollection',
                                            features: [
                                            ]
                                        }
                                    })
                                );

                                $scope.bboxlayer = new ol.layer.Vector(
                                    {
                                        title: 'BBOXs/Locations',
                                        id: 'layersExtension',
                                        source: bboxsource,
                                        style: getStyleFunction(false)
                                    }
                                );

                                olData.getMap($scope.$id).then(function(map){
                                    $scope.extraLayerGroup = new ol.layer.Group({
                                        title: 'Additional layers',
                                        layers: []
                                    });

                                    $scope.layerGroup = new ol.layer.Group({
                                        title: 'Overlays',
                                        layers: [
                                            $scope.nodesLayer,
                                            $scope.bboxlayer
                                        ]
                                    });
                                    $scope.layerSwitcher = new ol.control.LayerSwitcher();
                                    //testvar = $scope.layerSwitcher;
                                    map.addLayer( $scope.layerGroup);
                                    map.addLayer( $scope.extraLayerGroup);
                                    map.addControl($scope.layerSwitcher);
                                    map.addControl(new ol.control.ZoomToExtent({
                                        extent: [83947, 4245897, 2666907, 6207577]
                                    }));
                                    map.addControl(new ogcb.CleanAll({
                                        extraLayerGroup: $scope.extraLayerGroup,
                                        bboxlayer: $scope.bboxlayer
                                    }));
                                    $scope.nodesSelector = new ol.interaction.Select({
                                        style: getStyleFunction(true),
                                        layers: [$scope.nodesLayer]
                                    });
                                    var collection = $scope.nodesSelector.getFeatures();
                                    collection.on('add', function(evt){

                                        var id = collection.item(0).get('id');
                                        $state.go('nodes.detail', {id: id});
                                    });
                                    map.addInteraction($scope.nodesSelector);
                                });

                                $scope.nodesLoaded = OgcBrowserService.getNodes();
                                $scope.nodesLoaded.then(function(nodes){
                                    angular.extend($scope, {nodes: nodes});
                                    angular.forEach(nodes, function(value, key) {
                                        var f = new ol.Feature({id: value.id, name: value.name});
                                        f.setId(value.id);
                                        f.setGeometry(new ol.geom.Point(ol.proj.transform(value.geometry.coordinates, 'EPSG:4326', 'EPSG:3857')));
                                        $scope.nodesSource.addFeature(f);
                                    });

                                    // olData.getMap($scope.$id).then(function(map){
                                    //  $nodesLayer.getExtent();

                                    // });


                                    //alert($scope.nodesSource);
                                    //.readFeature({geometry:  {"type": "Point", "coordinates": [12.355672, 45.437473]} });
                                    //console.log(nodes);
                                    //
                                });


                            }
                           ]);// end controller

app.service("OgcBrowserService",
            function( $http, $q ) {
                return({
                    getNodes: getNodes,
                    getNode: getNode,
                });

                function getNode(id) {
                    var request = $http({
                        method: "get",
                        url: "/api/nodes/" + id ,
                        params: {
                            action: "get"
                        }
                    });

                    return( request.then( handleSuccess, handleError ) );

                }

                function getNodes() {
                    var request = $http({
                        method: "get",
                        url: "/api/nodes",
                        params: {
                            action: "get"
                        }
                    });

                    return( request.then( handleSuccess, handleError ) );

                }

                function handleError( response ) {
                    // The API response from the server should be returned in a
                    // nomralized format. However, if the request was not handled by the
                    // server (or what not handles properly - ex. server error), then we
                    // may have to normalize it on our end, as best we can.
                    if (
                        ! angular.isObject( response.data ) ||
                            ! response.data.message
                    ) {
                        return( $q.reject( "An unknown error occurred." ) );
                    }

                    // Otherwise, use expected error message.
                    return( $q.reject( response.data.message ) );
                }


                // I transform the successful response, unwrapping the application data
                // from the API response payload.
                function handleSuccess( response ) {
                    return( response.data );
                }
            }
           );

app.filter('startFrom', function() {
    return function(input, start) {
        start = +start; //parse to int
        return input.slice(start);
    };
});


// namespace
window.ogcb = {};
var ogcb = window.ogcb;

// control to clean
ogcb.CleanAll = function(opt_options) {
    var options = opt_options || {};
    var tipLabel = 'Clear all';

    var button = document.createElement('button');
    button.innerHTML = 'C';

    var this_ = this;
    var extraLayerGroup = options.extraLayerGroup;
    var bboxlayer = options.bboxlayer;
    var handleCleanAll = function(e) {
        var layersCollection = extraLayerGroup.getLayers();
        while(layersCollection.getLength() > 0){
            layersCollection.pop();
        }
        bboxlayer.getSource().clear();
    };

    button.addEventListener('click', handleCleanAll, false);
    button.addEventListener('touchstart', handleCleanAll, false);

    var element = document.createElement('div');
    element.className = 'ogcb-clean-all ol-unselectable ol-control';
    element.appendChild(button);

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });
};
ol.inherits(ogcb.CleanAll, ol.control.Control);
