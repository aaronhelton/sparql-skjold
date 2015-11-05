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
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from .models import Cache
import re, hashlib, json

VOTEDB_ASPECTS = ['index','organizations','bodies','sessions','member_states']
VOTEDB_TYPES = ['member_state','organization','body','session','vote_record']
ASPECT_MAP = {
  'organizations':'organization',
  'bodies':'body',
  'sessions':'session',
  'member_states':'member_state',
  'index':'member_state',
}
AUTO_CHILDREN = {
  'member_state': ['member_sessions','member_vote_records'],
}

sparql = SPARQLWrapper(settings.SPARQL_ENDPOINT)

def index(request):
  preferred_language = translation.get_language()
  collator=Collator.createInstance(Locale(preferred_language))
  if 'aspect' in request.GET:
    aspect = request.GET['aspect']
  else:
    aspect = 'index'
  
  if aspect in VOTEDB_ASPECTS:
    pass
  else:
    raise Http404("Aspect not found")
    
  querystring = QUERIES[aspect]
  
  m = hashlib.md5()
  m.update(querystring)
  md5 = m.hexdigest()
  results = []
  
  try:
    cache_object = Cache.objects.get(md5=md5, language=preferred_language)
    results = cache_object.result_set
  except Cache.DoesNotExist, e:
    sparql.setQuery(querystring)
    sparql.setReturnFormat(JSON)
    this_results = sparql.query().convert()["results"]["bindings"]
        
    for res in this_results:
      res["pref_label"] = get_preferred_label(res['x']['value'], preferred_language)
      results.append(res)
          
    Cache.objects.update_or_create(md5=md5,language=preferred_language,result_set=results)
          
  sorted_results = sorted(results, key=lambda tup: tup['pref_label'], cmp=collator.compare)
  try:
    page = request.GET.get('page', 1)
  except PageNotAnInteger:
    page = 1
  p = Paginator(sorted_results,15,request=request)
  paginated_results = p.page(page)
  return render(request, 'v2/index.html', {'results': paginated_results, 'children':ASPECT_MAP[aspect]})
  

def select(request):
  preferred_language = translation.get_language()
  if request.GET and request.GET['uri']:
    uri = request.GET['uri']
    if request.GET['type'] and request.GET['type'] in VOTEDB_TYPES:
      v_type = request.GET['type']
    
    pref_label = get_preferred_label(uri, preferred_language)
    all_labels = get_all_labels(uri)
    results = []
    for q in AUTO_CHILDREN[v_type]:
      sparql.setQuery(QUERIES[q].replace("{{replaceme}}",uri).replace("{{replacelang}}",preferred_language))
      sparql.setReturnFormat(JSON)
      q_results = sparql.query().convert()["results"]["bindings"]
      for res in q_results:
        res["pref_label"] = get_preferred_label(res[q]["value"], preferred_language)
      results.append({'name':q, 'set': q_results})
    return render(request, 'v2/' + v_type + '.html', {'pref_label': pref_label, 'all_labels': all_labels, 'results': results})
    #else:
    #  raise Http404("Not found")
  else:
    raise Http404("Not found")
    
def search(request):
  
  return render(request, 'v2/search.html', {'results':paginated_results})
  
  
def autocomplete(request):
  
  
  return HttpResponse(json.dumps(results), content_type='application/json')
