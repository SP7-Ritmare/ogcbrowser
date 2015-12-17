/**
 * Define a namespace for the application.
 */
window.ogcb = {};
var ogcb = window.ogcb;

/**
 * @constructor
 * @extends {ol.control.Control}
 * @param {Object=} opt_options Control options.
 */
ogcb.CenterZoom = function(opt_options) {
    var options = opt_options || {};
    var button = document.createElement('button');
    button.innerHTML = 'E';

    var this_ = this;
    var handleCenterZoom = function(e) {
        this_.getMap().getView().CenterZoom(0);
    };

    button.addEventListener('click', handleRotateNorth, false);
    button.addEventListener('touchstart', handleRotateNorth, false);

    var element = document.createElement('div');
    element.className = 'rotate-north ol-unselectable ol-control';
    element.appendChild(button);

    ol.control.Control.call(this, {
        element: element,
        target: options.target
    });
};
ol.inherits(ogcb.RotateNorthControl, ol.control.Control);
