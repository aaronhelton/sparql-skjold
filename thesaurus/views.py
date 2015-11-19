from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.core.urlresolvers import resolve
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext, loader
from django.template.context_processors import i18n
from django.utils import translation
from operator import itemgetter, attrgetter
from icu import Collator, Locale
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
import re, hashlib, json, requests
from rdflib import ConjunctiveGraph, Namespace, Literal, URIRef, RDF
from rdflib.resource import Resource
from rdflib.namespace import SKOS, NamespaceManager
from rdflib.store import NO_STORE, VALID_STORE
from django.conf import settings
import elasticpy as ep

# We will open a graph store via RDFLib. It is assumed to already exist, but a management
# command will be available to ensure this.
import os
path = os.path.join(settings.BASE_DIR, 'db')
graph = ConjunctiveGraph('Sleepycat')
graph.open(path, create=False)
graph.bind('skos', SKOS)

EU = Namespace('http://eurovoc.europa.eu/schema#')
UNBIST = Namespace('http://unontologies.s3-website-us-east-1.amazonaws.com/unbist#')
ROUTABLES = {
  'Collection':SKOS.Collection,
  'Concept':SKOS.Concept,
  'ConceptScheme':SKOS.ConceptScheme,
  'Domain':EU.Domain,
  'MicroThesaurus':EU.MicroThesaurus,
  'GeographicTerm':UNBIST.GeographicTerm,
}



ES_ENDPOINT = 'http://localhost:9200/'

def index(request):
  preferred_language = translation.get_language()
  collator = Collator.createInstance(Locale(preferred_language))
  if request.GET.get('aspect'):
    aspect = request.GET['aspect']

  else:
    aspect = 'Collection'

  try:
    aspect_uri = ROUTABLES[aspect]
  except KeyError:
    aspect_uri = ROUTABLES['Collection']

  this_results = []
  for res in graph.subjects(RDF.type, aspect_uri):
    r = Resource(graph,res)
    if Resource(graph,UNBIST.PlaceName) in list(r[RDF.type]):
      continue
    res_label = get_preferred_label(res,preferred_language)
    this_results.append({'uri': res, 'pref_label':res_label})
  #sorted_results =  sorted(this_results, key=lambda tup: tup['pref_label'], cmp=collator.compare)
  sorted_results =  sorted(this_results, key=lambda tup: tup['pref_label'])

  try:
    page = request.GET.get('page',1)
  except PageNotAnInteger:
    page = 1

  p = Paginator(sorted_results, 20, request=request)
  paginated_results = p.page(page)

  return render(request, 'thesaurus/index.html', {'results': paginated_results, 'target': 'instances', 'aspect':aspect })

def term(request):
  preferred_language = translation.get_language()
  collator = Collator.createInstance(Locale(preferred_language))
  if request.GET.get('uri'):
    uri = request.GET['uri']

    pref_label = get_preferred_label(URIRef(uri), preferred_language)
    pref_labels = graph.preferredLabel(URIRef(uri))

    breadcrumbs = []
    breadcrumbs_q = "prefix skos: <http://www.w3.org/2004/02/skos/core#> prefix unbist: <http://unontologies.s3-website-us-east-1.amazonaws.com/unbist#> prefix eu: <http://eurovoc.europa.eu/schema#> select ?domain ?microthesaurus where { { ?domain skos:member ?microthesaurus . ?microthesaurus skos:member <" + uri + "> . } union { ?domain rdf:type eu:Domain . ?domain skos:member <" + uri + "> } . }"
    for res in graph.query(breadcrumbs_q):
      bc = {}
      bc.update({'domain':{'uri':res.domain, 'pref_label': get_preferred_label(res.domain, preferred_language)}})
      microthesaurus = None
      if res.microthesaurus:
        bc.update({'microthesaurus': {'uri':res.microthesaurus, 'pref_label': get_preferred_label(res.microthesaurus, preferred_language)}})
      breadcrumbs.append(bc)

    scope_notes = []
    sns = graph.objects(subject=URIRef(uri),predicate=SKOS.scopeNote)
    for s in sns:
      if s.language == preferred_language:
        scope_notes.append(s)

    alt_labels = []
    als = graph.objects(subject=URIRef(uri),predicate=SKOS.altLabel)
    for a in als:
      if a.language == preferred_language:
        alt_labels.append(a)

    relationships = []
    for c in [SKOS.broader,SKOS.related,SKOS.narrower,SKOS.member]:
      this_results = []
      for rel in graph.objects(subject=URIRef(uri),predicate=c):
        rel_label = get_preferred_label(rel,preferred_language)
        this_results.append({'type':c.split('#')[1], 'uri': rel, 'pref_label':rel_label})
      #sorted_results = sorted(this_results, key=lambda tup: tup['pref_label'], cmp=collator.compare)
      sorted_results = sorted(this_results, key=lambda tup: tup['pref_label'])
      for sr in sorted_results:
        relationships.append(sr)

    matches = []
    for t in [SKOS.relatedMatch, SKOS.broadMatch, SKOS.closeMatch, SKOS.exactMatch, SKOS.narrowMatch]:
      matches_q = "select ?" + t.split('#')[1] + " where { <" + uri +"> owl:sameAs ?osa . ?" + t.split('#')[1] + " <" + t + "> ?osa }"
      for m in graph.query(matches_q):
        matches.append({'type':t.split('#')[1], 'uri': m})

    descriptions = []

    rdf_types = []
    for t in graph.objects(subject=URIRef(uri),predicate=RDF.type):
      rdf_types.append({'short_name':t.split('#')[1], 'uri':t})

    return render(request, 'thesaurus/term.html', {
      'rdf_types': rdf_types,
      'pref_label': pref_label, 
      'pref_labels': pref_labels,
      'alt_labels':alt_labels, 
      'breadcrumbs':breadcrumbs, 
      'scope_notes':scope_notes,
      'relationships':relationships,
      'matches':matches })
  else:
    raise Http404

def search(request):
  preferred_language = translation.get_language()
  if request.GET.get('q'):
    results = []
    q = request.GET['q']
    search = ep.ElasticSearch()
    search.size(8000)
    labels_q = ep.ElasticQuery().match('labels',q)
    labels_results = search.search_advanced('thesaurus','terms',labels_q)
    for res in labels_results["hits"]["hits"]:
      results.append({'pref_label': get_preferred_label(URIRef(res["_source"]["uri"]), preferred_language), 'uri':res["_source"]["uri"]})
      
    alt_labels_q = ep.ElasticQuery().match('alt_labels',q)
    alt_labels_results = search.search_advanced('thesaurus','terms',alt_labels_q)
    for res in alt_labels_results["hits"]["hits"]:
      pref_label = get_preferred_label(URIRef(res["_source"]["uri"]), preferred_language)
      to_append = {'pref_label': pref_label, 'uri':res["_source"]["uri"]}
      if not to_append in results:
        results.append(to_append)
    
    query = ep.ElasticQuery().match('_all',q)
    this_results = search.search_advanced('thesaurus','terms',query)
    #print(this_results["hits"]["hits"])

    for res in this_results["hits"]["hits"]:
      pref_label = get_preferred_label(URIRef(res["_source"]["uri"]), preferred_language)
      to_append = {'pref_label': pref_label, 'uri':res["_source"]["uri"]}
      if not to_append in results:
        results.append(to_append)
    try:
      page = request.GET.get('page',1)
    except PageNotAnInteger:
      page = 1

    p = Paginator(results, 20, request=request)
    paginated_results = p.page(page)
    return render(request, 'thesaurus/search.html', {'results': paginated_results })

def autocomplete(request):
  preferred_language = translation.get_language()
  if request.GET.get('q'):
    results = []
    q = request.GET['q']
    search = ep.ElasticSearch()
    search.size(10)
    labels_q = ep.ElasticQuery().wildcard('labels_orig',"*" + q + "*")
    labels_results = search.search_advanced('thesaurus','terms',labels_q)
    matching_uris = []
    for res in labels_results["hits"]["hits"]:
      matching_uris.append(res["_source"]["uri"])
          
    if len(matching_uris) < 2:
      alt_labels_q = ep.ElasticQuery().wildcard('alt_labels_orig',"*" + q + "*")
      alt_labels_results = search.search_advanced('thesaurus','terms',alt_labels_q)
      #matching_uris = []
      for res in alt_labels_results["hits"]["hits"]:
        matching_uris.append(res["_source"]["uri"])
        
    uris = set(matching_uris)
    for u in uris:
      results.append({'url':u, 'value':get_preferred_label(URIRef(u),preferred_language)})
      
  return HttpResponse(json.dumps(results), content_type='application/json')

def get_preferred_label(resource, language):
  default_language = settings.LANGUAGE_CODE
  if not language:
    language = default_language
  label = graph.preferredLabel(resource, lang=language)
  if len(label) > 0:
    return label[0][1]
  else:
    label = graph.preferredLabel(resource, lang=default_language)
    if len(label) > 0:
      return label[0][1]
    else:
      return resource
