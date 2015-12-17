from os.path import join, splitext
import json
import requests
from urlparse import urlparse
# from lxml import etree
from owslib.etree import etree
from owslib.csw import CatalogueServiceWeb
from owslib.wms import WebMapService
from owslib.iso import MD_Metadata
from owslib import util
from owslib.swe.common import Quantity
from owslib.namespaces import Namespaces
from owslib.wms import WebMapService
from thredds_crawler.crawl import Crawl

from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.contrib.gis.geos import Polygon
from django.core.cache import cache


from geosk.osk.sos import Catalog
from broker import WMSBroker, SOSBroker

def get_namespaces():
    n = Namespaces()
    namespaces = n.get_namespaces()
    namespaces['tds'] = 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0'
    return namespaces

namespaces = get_namespaces()

class HomePageView(TemplateView):

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        return context

def get_wmsurl(request):
    url = request.GET['url']
    print url
    node = {
        'baseurl': url
    }
    wms = WMSBroker(node)
    wms.get_summary()
    return HttpResponse(wms.json(), content_type = "application/json")


def get_node(request, id):
    # r = Registry('http://adamassoft.it/jbossTest/registry/monitor/SP5/nodes')
    r = Registry('http://sp7.irea.cnr.it/registry/monitor/nodes/')
    nodes = r.nodes
    node = (item for item in nodes if item["id"] == int(id)).next()
    if node['type'] == 'tds':
        key = 'ogcbrowser-node-%s' % id
        basehostname = urlparse(node['baseurl']).hostname
        _node = cache.get(key)
        if _node is None:
            key_crawler = 'ogcbrowser-node-%s-crawler' % id
            c = cache.get(key_crawler)
            if c is None:
                print 'Start crawling ... '
                c = Crawl(node['tdsurl'])
                localds = [ds for ds in c.datasets if urlparse(ds.catalog_url).hostname == basehostname]
                for ds in localds[:1000]:
                    ds.tdsmd = TDS_Metadata(ds.metadata)

                cache.set(key_crawler, c, 200000000)

            isods = [ds for ds in c.datasets if hasattr(ds, 'isomd')]
            wmsds = [ds for ds in c.datasets for s in ds.services if s.get("service").lower() == "wms"]
            localds = [ds for ds in c.datasets if urlparse(ds.catalog_url).hostname == basehostname]

            blockcount = 0

            records = []

            for ds in localds[:1000]:
                print 'Get dataset ', ds.id
                if not hasattr(ds, 'completed') or not ds.completed:
                    iso = None
                    for s in ds.services:
                        if s.get("service").lower() == "iso":
                            iso = s.get("url")
                            r = requests.get(iso)
                            ds.isomd = MD_Metadata(etree.fromstring(r.text.encode('utf8')))
                        elif s.get("service").lower() == "wms":
                            try:
                                ds.wms = WebMapService(s.get("url"))
                            except etree.XMLSyntaxError:
                                pass
                    ds.completed = True
                    blockcount += 1

                    catalog = ds.catalog_url
                    if catalog.endswith('.xml'):
                        _catalog = splitext(catalog)
                        catalog = "{}.html".format(_catalog[0])
                    if  hasattr(ds, 'isomd'):
                        r = ds.isomd.identification
                        bbox = [r.bbox.minx, r.bbox.miny, r.bbox.maxx, r.bbox.maxy]
                        bbox = [float(v) for v in bbox]
                        bbox_coords = Polygon.from_bbox(bbox).coords
                    elif hasattr(ds, 'wms'):
                        if len(ds.wms.contents) > 0:
                            layer = ds.wms.contents.itervalues().next()
                            bbox = [float(v) for v in layer.boundingBoxWGS84]
                            bbox_coords = Polygon.from_bbox(bbox).coords
                        else:
                            bbox = [-180.0, -88.0, 180.0, 88.0]
                            bbox_coords = Polygon.from_bbox(bbox).coords
                    else:
                        bbox = [-180.0, -88.0, 180.0, 88.0]
                        bbox_coords = Polygon.from_bbox(bbox).coords
                    abstract = ds.tdsmd.summary if hasattr(ds, 'tdsmd') and hasattr(ds.tdsmd, 'summary') else ''
                    if isinstance(abstract, list):
                        abstract = '. '.join(abstract)
                    record = {
                        'title': ds.name,
                        'abstract': abstract,
                        'type': 'dataset',
                        'bbox': bbox,
                        'bbox_coords': bbox_coords,
                        'url': catalog
                        }
                    for s in ds.services:
                        if s.get("service").lower() == "wms":
                            record['wmsurl'] = s.get("url")

                    records.append(record)

                    if blockcount == 1000:
                        print "save block cache"
                        cache.set(key, records, 200000000)
                        blockcount = 0

            node['nrecords'] = len(c.datasets)
            node['records'] = records

            node['addinfo'] = [
                ('Total resources', node['nrecords']),
                ('Local resources', len(localds)),
                ('Access WMS', len(wmsds)),
                ('Access ISO', len(isods))
            ]

            cache.set(key, node, 200000000)
        else:
            node = _node # cache







    if node['type'] == 'sk':
        if 'wmsurl' not in node or node['wmsurl'] is None:
            node['wmsurl'] = join(node['baseurl'],'geoserver','wms')
        else:
            node['wmsurl'] = remove_qs_param(node['wmsurl'], 'request')
            node['wmsurl'] = remove_qs_param(node['wmsurl'], 'service')
            node['wmsurl'] = remove_qs_param(node['wmsurl'], 'version')
        wms = WMSBroker(node)
        wms.get_summary()

        return HttpResponse(wms.json(), content_type = "application/json")

        # csw_url = node['baseurl'] + 'catalogue/csw'
        # csw = CatalogueServiceWeb(csw_url)
        # csw.getrecords2(maxrecords=100)
        # node['nrecords'] = csw.results['matches']
        # node['records'] = []
        # for rec in csw.records:
        #     r = csw.records[rec]
        #     bbox = [r.bbox.maxx, r.bbox.maxy, r.bbox.minx, r.bbox.miny]
        #     try:
        #         url = (item for item in r.references if item["scheme"] == 'WWW:LINK-1.0-http--link').next()
        #     except StopIteration:
        #         url = None
        #     record = {
        #         'title': r.title,
        #         'abstract': r.abstract,
        #         'type': r.type,
        #         'bbox': bbox,
        #         'bbox_coords': Polygon.from_bbox(bbox).coords,
        #         'url': url['url'] if url is not None else None
        #         }
        #     node['records'].append(record)
        #     if url is not None:
        #         wms_source= {
        #             'url': wms_url,
        #             'params': {'LAYERS': layer.name}
        #             }

        # node['addinfo'] = [
        #     ('Total resources', node['nrecords'])
        #     ]

    if node['type'] == 'wms':
        wms = WMSBroker(node)
        wms.get_summary()
        return HttpResponse(wms.json(), content_type = "application/json")

    if node['type'] == 'sos':
        sos = SOSBroker(node)
        sos.harvest()
        return HttpResponse(sos.json(), content_type = "application/json")

    return HttpResponse(json.dumps(node, indent=4), content_type = "application/json")

def get_nodes(request):
    # r = Registry('http://adamassoft.it/jbossTest/registry/monitor/SP5/nodes')
    r = Registry('http://sp7.irea.cnr.it/registry/monitor/nodes/')
    nodes = r.nodes
    return HttpResponse(json.dumps(nodes), content_type = "application/json")


#  allora il WMS di EnvEurope e'  questo: http://geoserver.lteritalia.it/lter_europe/wms
#  mentre il SOS e': http://sp7.irea.cnr.it/tomcat/envsos/sos
#  tieni conto che c'e' tutto questo elenco
#  http://sp7.irea.cnr.it/monitor/
#  (non completo)
#  Stefano aggiungerei anche questo: http://ritmare.artov.isac.cnr.it/thredds/catalog.html

class Registry(object):
    _nodes = [
        {
            "id": 2,
            "name": "SK - CNR ISMAR Lesina",
            "baseurl": "http://sk.fg.ismar.cnr.it/",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [15.3505744 , 41.864194]},
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 3,
            "name": "SK - CNR ISSIA Bari",
            "baseurl": "http://starkit.ba.issia.cnr.it/",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [16.8822, 41.1122346]},
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 4,
            "name": "SK - CNR IREA uos Milano",
            "baseurl": "http://skmi.irea.cnr.it/",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [9.2322153, 45.4797019]},
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 5,
            "name": "SK - CNR ISMAR Osservativo Venezia",
            "baseurl": "http://vesk.ve.ismar.cnr.it/",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [12.354236120073102, 45.43047678226529]},
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 6,
            "name": "SK - IAMC Oristano",
            "baseurl": "http://sk.oristano.iamc.cnr.it/",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [8.59953,39.90246]},
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 7,
            "name": "SHAPE Adriatic Atlas",
            "baseurl": "http://atlas.shape-ipaproject.eu/",
            "wmsurl": "http://atlas.shape-ipaproject.eu/wms?",
            "logo": "http://www.shape-ipaproject.eu/pages/images/logo-shape2.jpg",
            "type": "wms",
            "geometry": {"type": "Point", "coordinates": [11.3624415, 44.5073008]},
            "standards": ["WMS"]
        },
        {
            "id": 8,
            "name": "ADRIPLAN",
            "baseurl": "http://data.adriplan.eu/",
            "logo": "http://data.adriplan.eu/static/geonode/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [12.355672, 45.437473]},
            "standards": ["WMS"]
        },
        {
            "id": 9,
            "name": "LTER Italia",
            "baseurl": "http://geoserver.lteritalia.it/",
            "wmsurl": "http://geoserver.lteritalia.it/lter_europe/wms",
            "logo": "http://www.lteritalia.it/sites/default/files/logo_website_2_0.png",
            "type": "wms",
            "geometry": {"type": "Point", "coordinates": [12.512708954787087, 41.90050957752439]},
            "standards": ["WMS"]
        },
        {
            "id": 10,
            "name": "THREDDS Data Server ISMAR-VE",
            #"baseurl": "http://tds.ve.ismar.cnr.it:8080/thredds/creus.html",
            "baseurl": "http://tds.ve.ismar.cnr.it:8080/thredds/catalog.html",
            "logo": "http://www.unidata.ucar.edu/img/v3/logos/thredds-50x50.png",
            "type": "tds",
            "geometry": {"type": "Point", "coordinates": [12.356425542369735, 45.43744319849026]},
            "standards": ["OPENDAP", "WMS", "NCML", "UDDC", "ISO"]
        },
        {
            "id": 70,
            "name": "CNR THREDDS Catalog for RITMARE Project",
            #"baseurl": "http://tds.ve.ismar.cnr.it:8080/thredds/creus.html",
            "baseurl": "http://ritmare.artov.isac.cnr.it/thredds/catalog.html",
            'tdsurl': 'http://tds.ve.ismar.cnr.it:8080/thredds/catalog.xml',
            "logo": "http://www.unidata.ucar.edu/img/v3/logos/thredds-50x50.png",
            "type": "tds",
            "geometry": {"type": "Point", "coordinates": [12.6470986, 41.8396651]},
            "standards": ["OPENDAP", "WMS", "NCML", "UDDC", "ISO"]
        },
        {
            "id": 83,
            "name": "THREDDS Data Server ISAC CNR",
            "tdsurl": "http://tds.bo.isac.cnr.it:8080/thredds/catalog.xml",
            "baseurl": "http://tds.bo.isac.cnr.it:8080/thredds/catalog.html",
            "logo": "http://www.unidata.ucar.edu/img/v3/logos/thredds-50x50.png",
            "type": "tds",
            "geometry": {"type": "Point", "coordinates": [11.3383544,44.5222407]},
            "standards": ["OPENDAP", "WMS", "NCML", "UDDC", "ISO"]
        },
        {
            "id": 13,
            "name": "LTER Europe SOS",
            "baseurl": "http://sp7.irea.cnr.it/tomcat/envsos/",
            "sosurl": "http://sp7.irea.cnr.it/tomcat/envsos/sos",
            "logo": "https://portal.opengeospatial.org/public_ogc/compliance/badge.php?s=SOS%201.0.0",
            "type": "sos",
            "geometry": {"type": "Point", "coordinates": [8.5433946,45.9312374]},
            "standards": ["SOS"]
        },
        {
            "id": 14,
            "name": "ISMAR Venezia SOS",
            "baseurl": "http://www.ismar.cnr.it/infrastrutture/piattaforma-acqua-alta/",
            "sosurl": "http://david.ve.ismar.cnr.it/52nSOSv3_WAR/sos?",
            "logo": "https://portal.opengeospatial.org/public_ogc/compliance/badge.php?s=SOS%201.0.0",
            "type": "sos",
            "geometry": {"type": "Point", "coordinates": [12.354236120073102, 45.43047678226529]},
            "standards": ["SOS"]
        },
        {
            "id": 15,
            "name": "DEMO SK IREA",
            "baseurl": "http://demo-sk.irea.cnr.it/",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [9.2322153, 45.4797019]},
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 16,
            "name": "GET-IT OGS",
            "baseurl": "http://geonodenodc.ogs.trieste.it/",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [13.76551, 45.70631]},
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 17,
            "name": "GET-IT ISMAR Ancona",
            "baseurl": "http://getit.an.ismar.cnr.it/",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [13.49843, 43.614165]},
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 18,
            "name": "GET-IT ISMAR La Spezia",
            "baseurl": "http://sk.sp.ismar.cnr.it",
            "logo": "http://geosk.ve.ismar.cnr.it/static/geosk/img/logo.png",
            "type": "sk",
            "geometry": {"type": "Point", "coordinates": [9.88122, 44.08351]}, #TODO sistemare coordinate
            "standards": ["WMS", "WFS", "WCS", "SOS", "CSW"]
        },
        {
            "id": 19,
            "name": "THREDDS Data Server NOAA",
            "baseurl": "http://oceanwatch.pfeg.noaa.gov/thredds/catalog.html",
            "logo": "http://www.unidata.ucar.edu/img/v3/logos/thredds-50x50.png",
            "type": "tds",
            "geometry": {"type": "Point", "coordinates": [-77.034012, 38.893181]}, #TODO sistemare coordinate
            "standards": ["OPENDAP", "WMS", "NCML", "UDDC", "ISO"]
        },
    ]
    url = None
    def __init__(self, url):
        self.url = url
    @property
    def nodes(self):
        key = self.url
        c = cache.get(key)
        if c is not None:
            return c
        if self.url is not None:
            r = requests.get(self.url)
            if r.status_code == 200:
                _json = r.json()
                spezia = None
                for n in _json:
                    if n['id'] == 70:
                        n['baseurl'] = 'http://tds.ve.ismar.cnr.it:8080/thredds/catalog.html'
                        n['tdsurl'] = 'http://tds.ve.ismar.cnr.it:8080/thredds/catalog.xml'
                    if n['id'] == 71:
                        n['baseurl'] = 'http://ritmare.artov.isac.cnr.it/thredds/catalog.html'
                        n['tdsurl'] = 'http://ritmare.artov.isac.cnr.it/thredds/catalog.html'
                    if n['id'] == 73:
                        n['wmsurl'] = 'http://geonodenodc.ogs.trieste.it/geoserver-ritmare/ows?service=WMS&request=GetCapabilities'
                    if n['id'] == 75:
                        spezia = n
                    if n['id'] == 82:
                        n['geometry'] = {"type": "Point", "coordinates": [12.354236120073102, 45.43047678226529]}
                        n['type'] = 'sos'
                        n['sosdetails'] = 'http://icpsm.get-it.it/sensors/sensor/ds/?format=text/html&sensor_id='
                    if n['id'] == 83:
                        n['baseurl'] = 'http://tds.bo.isac.cnr.it:8080/thredds/catalog.html'
                        n['tdsurl'] = 'http://tds.bo.isac.cnr.it:8080/thredds/catalog.xml'
                        n['geometry'] = {"type": "Point", "coordinates": [11.3383544,44.5222407]}

                # remove spezia
                if spezia is not None:
                    _json.remove(spezia)

                # _json.append({
                #     "id": 14,
                #     "name": "ICPSM SOS",
                #     "baseurl": "http://www.comune.venezia.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/1748",
                #     "sosurl": "http://icpsm.get-it.it/observations/sos/kvp?",
                #     "sosdetails": "http://icpsm.get-it.it/sensors/sensor/ds/?format=text/html&sensor_id=",
                #     "logo": "https://portal.opengeospatial.org/public_ogc/compliance/badge.php?s=SOS%202.0.0",
                #     "type": "sos",
                #     "geometry": {"type": "Point", "coordinates": [12.354236120073102, 45.43047678226529]},
                #     "standards": ["SOS"]
                # })

                # _json.append({
                #     "id": 15,
                #     "name": "THREDDS Data Server ISAC CNR",
                #     "baseurl": "http://tds.bo.isac.cnr.it:8080/thredds/catalog.html",
                #     "tdsurl": "http://tds.bo.isac.cnr.it:8080/thredds/catalog.xml",
                #     "logo": "http://www.unidata.ucar.edu/img/v3/logos/thredds-50x50.png",
                #     "type": "tds",
                #     "geometry": {"type": "Point", "coordinates": [11.3383544,44.5222407]},
                #     "standards": ["OPENDAP", "WMS", "NCML", "UDDC", "ISO"]
                # })


                return _json
        return self._nodes

class TDS_Metadata(object):
    """ Process gmd:MD_Metadata """
    def __init__(self, md=None):
        self.summary = []
        for d in md.findall(util.nspath_eval('tds:documentation', namespaces)):
            dtype = d.attrib.get('type')
            if dtype is not None and dtype.lower() == 'summary':
                self.summary.append(util.testXMLValue(d))
            elif dtype is not None and dtype.lower() == 'rights':
                self.rights = util.testXMLValue(d)
            title = d.attrib.get(util.nspath_eval('xlink:title', namespaces))
            if title:
                self.title = title
            href = d.attrib.get(util.nspath_eval('xlink:href', namespaces))
            if href:
                self.href = href

            #tmp['href'] = i.attrib.get(util.nspath_eval('xlink:href', namespaces))
            #tmp['title'] = i.attrib.get(util.nspath_eval('xlink:title', namespaces))
            #self.operateson.append(tmp)

            # <documentation type="rights">Freely available</documentation>
            #if d.attrib.get(
            #o = CI_ResponsibleParty(i)
            #self.contact.append(o)

class Position(object):
    # ci sono problemi con la versione del namespace swe
    def __init__(self, element):
        for el in element.findall(util.nspath_eval('swe:Position/swe:location/swe:Vector/swe:coordinate', Namespaces().get_namespaces())):
            if el.attrib.get('name') == 'easting':
                self.easting = Quantity(el.find(util.nspath_eval('swe20:Quantity', namespaces)))
            if el.attrib.get('name') == 'northing':
                self.northing = Quantity(el.find(util.nspath_eval('swe20:Quantity', namespaces)))
            if el.attrib.get('name') == 'altitude':
                self.altitude = Quantity(el.find(util.nspath_eval('swe20:Quantity', namespaces)))


        #   <sml:position xmlns:sml="http://www.opengis.net/sensorML/1.0.1" xmlns="http://www.opengis.net/sos/1.0" xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc" xmlns:om="http://www.opengis.net/>
        #   <swe:Position gml:id="SYSTEM_LOCATION" referenceFrame="...">
        #     <!--esempio referenceFrame="urn:ogc:def:crs:EPSG::3004"-->
        #     <swe:location>
        #       <swe:Vector gml:id="STATION_LOCATION">
        #         <swe:coordinate name="easting">
        #           <swe:Quantity>
        #             <swe:uom code="degree"/>
        #             <swe:value>8.6827097</swe:value>
        #           </swe:Quantity>
        #         </swe:coordinate>
        #         <swe:coordinate name="northing">
        #           <swe:Quantity>
        #             <swe:uom code="degree"/>
        #             <swe:value>45.233181</swe:value>
        #           </swe:Quantity>
        #         </swe:coordinate>
        #         <swe:coordinate name="altitude">
        #           <swe:Quantity>
        #             <swe:uom code="m"/>
        #             <swe:value>106</swe:value>
        #           </swe:Quantity>
        #         </swe:coordinate>
        #       </swe:Vector>
        #     </swe:location>
        #   </swe:Position>
        # </sml:position>


from urllib import urlencode
from urlparse import urlparse, parse_qs, urlunparse


def remove_qs_param(url, param):
    parsed = urlparse(url)
    qd = parse_qs(parsed.query, keep_blank_values=True)
    filtered = dict( (k, v) for k, v in qd.iteritems() if not k.upper() == param.upper())
    return urlunparse([
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        urlencode(filtered, doseq=True), # query string
        parsed.fragment
    ])
