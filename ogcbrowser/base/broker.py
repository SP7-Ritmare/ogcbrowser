import urllib
import simplejson as json
import hashlib
from owslib.wms import WebMapService
from django.contrib.gis.geos import Polygon
from django.core.cache import cache

from geosk.osk.sos import Catalog

# override ows.swe.common for 1.0 version
from owslib.swe import common as common100
common100.namespaces = {'sml': 'http://www.opengis.net/sensorML/1.0.1',
                        'swe': 'http://www.opengis.net/swe/1.0.1',
                        'swe20': 'http://www.opengis.net/swe/1.0.1',
                        'xlink': 'http://www.w3.org/1999/xlink'}


class BrokerBase(object):
    def __init__(self, config):
        self.config = config
        self.nrecords = 0
        self.records = []
        self.addinfo = []
        self.__dict__.update(config)

    def _harvest(self):
        key = hashlib.md5(json.dumps(self.config, sort_keys=True)).hexdigest()
        c = cache.get(key)
        if c is None:
            c = self.harvest()
            cache.set(key, c, 63072000)
        return c

    def json(self):
        return json.dumps(self.__dict__)

class WMSBroker(BrokerBase):
    def __init__(self, config):
	super(WMSBroker, self).__init__(config)
        if 'wmsurl' not in config:
            self.wmsurl = self.baseurl

    def get_summary(self):
        wms = self._harvest()
        self.nrecords =  len(wms.contents)
        for layer_name, layer in wms.contents.iteritems():
            wms_source= {
                'url': self.wmsurl,
                'params': {'LAYERS': layer.name}
                }
            record = {
                'name': layer.name,
                'title': layer.title,
                'abstract': layer.abstract,
                'type': 'dataset',
                'bbox': layer.boundingBoxWGS84,
                'bbox_coords': Polygon.from_bbox(layer.boundingBoxWGS84).coords,
                'url': None,
                'keywords': layer.keywords,
                'wms_source': wms_source,
                'styles': layer.styles
                }
            self.records.append(record)
        self.addinfo.append(('Total resources', self.nrecords))

    def harvest(self):
        return WebMapService(self.wmsurl, version='1.1.1')

class SOSBroker(BrokerBase):
    def __init__(self, config):
	super(SOSBroker, self).__init__(config)
        if 'sosurl' not in config:
            self.sosurl = self.baseurl

    def harvest(self):
        kvp_url = self.sosurl
        cat = Catalog(kvp_url, version='2.0.0')
        sensors = cat.get_sensors(True)
        self.nrecords =  len(sensors)
        for sensor in sensors:
            if len(sensor['describe_sensor'].sensor_ml.members) > 0 and sensor['describe_sensor'].sensor_ml.members[0] is not None:
                position = self.get_position(sensor['describe_sensor'].sensor_ml.members[0].positions[0])
                bbox = [position['east'], position['north'], position['east'], position['north']]
                point = [position['east'], position['north']]
                abstract = sensor['describe_sensor'].sensor_ml.members[0].description
                name = sensor['describe_sensor'].sensor_ml.members[0].name
                if name is None:
                    name = sensor['name']
                record = {
                    'name': sensor['id'],
                    'title': name,
                    'abstract': abstract or '',
                    'type': 'dataset',
                    'point': point,
                    'bbox': bbox,
                    #'bbox_coords': Polygon.from_bbox(bbox).coords,
                    #'url': None,
                    #'keywords': layer.keywords,
                    #'wms_source': wms_source
                    }
                if self.sosdetails is not None:
                    record['url'] = self.sosdetails + urllib.quote(sensor['id'])

                self.records.append(record)

        self.addinfo.append(('Total resources', self.nrecords))
        # return sensors
        # for s in sensors:
        #     p=s['describe_sensor'].sensor_ml.members[0].positions[0]
        #     if p:
        #         Position(p)

    def get_position(self, position):
        coordinates = {}
        vector = position.find(common100.nspv('swe:Position/swe:location/swe:Vector'))
        v = common100.Vector(vector)
        for c in v.coordinate:
            if c.name == 'easting':
                coordinates['east'] = c.content.value
            if c.name == 'northing':
                coordinates['north'] = c.content.value
        return coordinates

#s['describe_sensor'].sensor_ml.members[0].positions[0]
