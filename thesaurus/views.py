from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.core.urlresolvers import resolve
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext, loader
from django.template.context_processors import i18n
from django.utils import translation
from django.conf import settings
from operator import itemgetter, attrgetter
from icu import Collator, Locale
from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE, N3
#from thesaurus.queries import QUERIES, get_preferred_label, get_all_labels
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger

# use this to resolve labels from UNBIS Thesaurus -> (owl:sameAs mappings) -> EuroVoc alignments 
# characterized as skos:exactMatch
EV_ENDPOINT = 'http://open-data.europa.eu/sparqlep'

sparql = SPARQLWrapper('http://52.20.172.127:8000/catalogs/public/repositories/thesaurus')

def index(request):

  return render(request)

def term(request):
  preferred_language = translation.get_language()
  if request.GET and request.GET['uri']:
    uri = request.GET['uri']
    #pref_label = get_preferred_label(uri, preferred_language)
    #all_labels = get_all_labels(uri)
    results = []
    local_children = ["skos:scopeNote","skos:broader","skos:narrower","skos:related"]
    remote_children = ["skos:exactMatch", "skos:broadMatch", "skos:narrowMatch", "skos:closeMatch"]

    for t in local_children:
      querystring = "select  * where { <" + uri + "> " + t + " ?o }"
      sparql.setQuery(querystring)
      sparql.setReturnFormat(JSON)
      results.append({'name':t, 'set': sparql.query().convert()["results"]["bindings"]})

    return render(request, 'thesaurus/term.html', {'results': results})
