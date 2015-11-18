from django.core.management.base import BaseCommand
from rdflib import ConjunctiveGraph, Namespace, Literal, URIRef, RDF
from rdflib.resource import Resource
from rdflib.namespace import SKOS, NamespaceManager
from rdflib.store import NO_STORE, VALID_STORE
from django.conf import settings
import requests
import os, json

class Command(BaseCommand):
  help = "Index your site's data in an ElasticSearch instance."

  def handle(self, *args, **options):
    es = settings.ELASTIC_SEARCH_URL
    db = os.path.join(settings.BASE_DIR, "db")
    print(es)

    graph = ConjunctiveGraph('Sleepycat')
    graph.open(db, create=False)
    graph.bind('skos', SKOS)

    EU = Namespace('http://eurovoc.europa.eu/schema#')
    UNBIST = Namespace('http://unontologies.s3-website-us-east-1.amazonaws.com/unbist#')

    querystring = "select ?uri where { ?uri rdf:type skos:Concept filter not exists { ?uri rdf:type unbist:PlaceName } . }"

    index = 1
    
    # make the index:
    thes_index = {
      "mappings": {
        "terms": {
          "properties": {
            "scope_notes": {
              "type": "string"
            },
            "uri": {
              "type": "string"
            },
            "alt_labels": {
              "type": "string"
            },
            "alt_labels_orig": {
              "type": "string",
              "index": "not_analyzed"
            },
            "labels": {
              "type": "string"
            },
            "labels_orig": {
              "type": "string",
              "index": "not_analyzed"
            }
          }
        }
      }
    }
    
    r = requests.put(es + 'thesaurus/', data=json.dumps(thes_index))
    

    for uri in graph.query(querystring):
      this_uri = uri[0]
      doc = { 
        "uri": this_uri
      }
      pref_labels = []
      labels_orig_lc = []
      print("Getting preferred labels")
      for label in graph.preferredLabel(URIRef(this_uri)):
        pref_labels.append(label[1])
        if label[1].language in ['en','fr','es']:
          labels_orig_lc.append(label[1].lower())
  
      doc.update({"labels": pref_labels})
      doc.update({"labels_orig": pref_labels + labels_orig_lc})
      
      alt_labels = []
      alt_labels_orig_lc = []
      print("Getting alternate labels")
      for label in graph.objects(URIRef(this_uri), SKOS.altLabel):
        alt_labels.append(label)
        if label.language in ['en','fr','es']:
          alt_labels_orig_lc.append(label.lower())

      doc.update({"alt_labels": alt_labels})
      doc.update({"alt_labels_orig": alt_labels + alt_labels_orig_lc})
        
      scope_notes = []
      print("Getting scope notes")
      for sn in graph.objects(URIRef(this_uri), SKOS.scopeNote):
        scope_notes.append(sn)
      
      doc.update({"scope_notes": scope_notes})
      
      payload = json.dumps(doc)
      
      r = requests.put(es + 'thesaurus/terms/' + str(index), data=payload)
      index += 1