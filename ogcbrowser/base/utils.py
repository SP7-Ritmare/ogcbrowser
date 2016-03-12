import random
import rdflib
import skos
from influxdb import InfluxDBClient
from datetime import timedelta, datetime


class SkosConcepts(object):
    def __init__(self):
        self.graph = rdflib.Graph()
        self.loader = skos.RDFLoader(self.graph)

    def get_concept(self, url):
        try:
            return self.loader[url]
        except KeyError:
            self.graph.parse(url, format="application/rdf+xml")
            self.loader = skos.RDFLoader(self.graph)
            return self.loader[url]


class SosInfluxdb(object):
    def __init__(self, dbname, host='localhost', port=8086, username='root', password='root'):
        self.client = InfluxDBClient(host, port, username, password, dbname)
        self.concepts = SkosConcepts()
        self.procedures_labels = None

    def insert_observation(self, obs, measurement):
        concept = self.concepts.get_concept(obs['observableProperty'])
        if self.procedures_labels is not None:
            p_label = self.procedures_labels[obs['procedure']]
        else:
            p_label = obs['procedure']

        j = [
            {
                "measurement": measurement,
                "tags": {
                    "procedure": p_label,
                    "observedProperty": concept.prefLabel
                },
                "time": obs['phenomenonTime'],
                "fields": {
                    "value": float(obs['result']['value'])
                }
            }
        ]
        self.client.write_points(j)
