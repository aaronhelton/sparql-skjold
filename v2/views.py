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
from v2.queries import QUERIES, get_preferred_label, get_all_labels

VOTEDB_ASPECTS = ['index','organizations','bodies','sessions','member_states']
VOTEDB_TYPES = ['member_state','organization','body','session','vote_record']
ASPECT_MAP = {
  'organizations':'organization',
  'bodies':'body',
  'sessions':'session',
  'member_states':'member_state',
  'index':'member_state',
}

sparql = SPARQLWrapper(settings.SPARQL_ENDPOINT)

def index(request):
  preferred_language = translation.get_language()
  collator=Collator.createInstance(Locale(preferred_language))
  if 'aspect' in request.GET:
    aspect = request.GET['aspect']
    if aspect in VOTEDB_ASPECTS:
      sparql.setQuery(QUERIES[aspect])
      sparql.setReturnFormat(JSON)
      results = sparql.query().convert()["results"]["bindings"]
      for res in results:
        res["pref_label"] = get_preferred_label(res['x']['value'], preferred_language)
      return render(request, 'v2/index.html', {'results': results, 'children':ASPECT_MAP[aspect]})
    else:
      raise Http404("Aspect not found")
  else:
    aspect = 'index'
    sparql.setQuery(QUERIES[aspect])
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]
    for res in results:
      res["pref_label"] = get_preferred_label(res['x']['value'].encode("utf-8"), preferred_language)
    sorted_results = sorted(results, key=lambda tup: tup['pref_label'], cmp=collator.compare)
    return render(request, 'v2/index.html', {'results': sorted_results, 'children':ASPECT_MAP[aspect]})
  

def select(request):
  preferred_language = translation.get_language()
  if request.GET and request.GET['uri']:
    uri = request.GET['uri']
    if request.GET['type'] and request.GET['type'] in VOTEDB_TYPES:
      v_type = request.GET['type']
    
    pref_label = get_preferred_label(uri, preferred_language)
    all_labels = get_all_labels(uri)
      
    return render(request, 'v2/' + v_type + '.html', {'pref_label': pref_label, 'all_labels': all_labels})
    #else:
    #  raise Http404("Not found")
  else:
    raise Http404("Not found")
