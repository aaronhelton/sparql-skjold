from django.shortcuts import render
from django.http import HttpResponse
from django.core.urlresolvers import resolve
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext, loader
from django.template.context_processors import i18n
from django.utils import translation
from django.conf import settings
from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE, N3

sparql = SPARQLWrapper(settings.SPARQL_ENDPOINT)

# indexes or lists
def index(request):
  querystring = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?x ?name { ?x rdf:type undoc:MemberState . 
                   ?x skos:prefLabel ?name filter (lang(?name)='en') . }
  """
  sparql.setQuery(querystring)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()["results"]["bindings"]
  return render(request, 'votedb/member_states.html', {'results': results})

def member_states(request):
  querystring = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?x ?name { ?x rdf:type undoc:MemberState . 
                      ?x skos:prefLabel ?name  filter ( lang(?name) = 'en') }
  """
  sparql.setQuery(querystring)
  sparql.setReturnFormat(JSON)
  results = sparql.query().convert()["results"]["bindings"]
  return render(request, 'votedb/member_states.html', {'results': results})

def sessions(request):
  return render(request, 'votedb/sessions.html')

def bodies(request):
  return render(request, 'votedb/bodies.html')

def member_state(request, uri):

  # UN Member States are defined as a skos:ConceptScheme, so they all have skos:prefLabel properties
  # to do: figure out how to make this obey the language selection
  pref_label_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?name { <""" + uri  + """> skos:prefLabel ?name  filter ( lang(?name) = 'en') }
  """
  pref_labels_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?name { <""" + uri  + """> skos:prefLabel ?name }
  """
  # This is just grabbing a grouped count of records by vote character. Additional link-outs will process these.
  vote_records_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?vc (COUNT(?x) AS ?totalVotes) { 
      ?x rdf:type undoc:CountryVote . 
      ?x undoc:castBy <""" + uri + """> . 
      ?x undoc:voteCharacter ?vc . } 
    GROUP BY ?vc
  """
  sparql.setQuery(pref_label_q)
  sparql.setReturnFormat(JSON)
  pref_label = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(pref_labels_q)
  sparql.setReturnFormat(JSON)
  pref_labels = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(vote_records_q)
  sparql.setReturnFormat(JSON)
  vote_records = sparql.query().convert()["results"]["bindings"]

  return render(request, 'votedb/member_state.html', { 'pref_label': pref_label[0], 'pref_labels': pref_labels, 'vote_records': vote_records })

def by_session(request, uri):
  pref_label_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#>
    select ?name { <""" + uri  + """> skos:prefLabel ?name  filter ( lang(?name) = 'en') }
  """
  vote_records_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#>
    select ?resolution ?title {
      ?y undoc:inSession <""" + uri + """> .
      ?y dcterms:title ?title .
      ?y undoc:resolution ?m .
      ?m rdfs:label ?resolution . }
    ORDER BY ?m
  """
  sparql.setQuery(pref_label_q)
  sparql.setReturnFormat(JSON)
  pref_label = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(vote_records_q)
  sparql.setReturnFormat(JSON)
  vote_records = sparql.query().convert()["results"]["bindings"]

  return render(request, 'votedb/by_session.html', { 'pref_label': pref_label[0], 'vote_records': vote_records })

def by_member(request, uri):
  # to do: DRY out pref_label lookup

  pref_label_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?name { <""" + uri  + """> skos:prefLabel ?name  filter ( lang(?name) = 'en') }
  """
  vote_records_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?y ?vc ?resolution ?title { 
      ?x rdf:type undoc:CountryVote . 
      ?x undoc:castBy <""" + uri + """> . 
      ?x undoc:voteCharacter ?vc . 
      ?y undoc:countryVote ?x . 
      ?y dcterms:title ?title . 
      ?y undoc:resolution ?m . 
      ?m rdfs:label ?resolution . } 
    ORDER BY ?vc ?m
  """
  sparql.setQuery(pref_label_q)
  sparql.setReturnFormat(JSON)
  pref_label = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(vote_records_q)
  sparql.setReturnFormat(JSON)
  vote_records = sparql.query().convert()["results"]["bindings"]

  return render(request, 'votedb/vote_by_member.html', { 'pref_label': pref_label[0], 'vote_records': vote_records })

def vote_record(request, uri):
  pref_label_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?title { <""" + uri  + """> dcterms:title ?title filter ( lang(?title) = 'en') . }
  """
  country_votes_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?c ?who ?what { 
      <""" + uri + """> undoc:countryVote ?cv . 
      ?cv undoc:castBy ?c . 
      ?c skos:prefLabel ?who filter (lang(?who) = 'en') . 
      ?cv undoc:voteCharacter ?what . } 
    ORDER BY ?c
  """
  result_records_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?vote ?count { 
      <""" + uri + """> undoc:resultRecord ?vr . 
      ?vr undoc:resultKey ?vote . 
      ?vr undoc:resultValue ?count . }
  """
  meetings_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?meeting ?uri { <""" + uri + """> undoc:meeting ?m . ?m rdfs:label ?meeting ; undoc:resolverURI ?uri . }
  """
  reports_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?report ?uri { <""" + uri + """> undoc:report ?m . ?m rdfs:label ?report ; undoc:resolverURI ?uri . }  
  """
  resolutions_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?resolution ?uri { <""" + uri + """> undoc:resolution ?m . ?m rdfs:label ?resolution ; undoc:resolverURI ?uri . }
  """
  sparql.setQuery(pref_label_q)
  sparql.setReturnFormat(JSON)
  pref_label = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(country_votes_q)
  sparql.setReturnFormat(JSON)
  country_votes = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(result_records_q)
  sparql.setReturnFormat(JSON)
  result_records = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(meetings_q)
  sparql.setReturnFormat(JSON)
  meetings = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(reports_q)
  sparql.setReturnFormat(JSON)
  reports = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(resolutions_q)
  sparql.setReturnFormat(JSON)
  resolutions = sparql.query().convert()["results"]["bindings"]

  return render(request, 'votedb/vote_record.html', { 'pref_label': pref_label[0], 'country_votes': country_votes, 'result_records': result_records, 'meetings': meetings, 'reports': reports, 'resolutions': resolutions })

def session_record(request, uri):
  pref_label_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?name { <""" + uri  + """> skos:prefLabel ?name  filter ( lang(?name) = 'en') }
  """
  aggregate_results_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select ?vote (sum(xsd:integer(?result)) as ?result) {
      ?vr undoc:inSession <""" + uri + """> . 
      ?vr undoc:resultRecord ?rr . 
      ?rr undoc:resultKey ?vote filter (?vote != 'Total') . 
      ?rr undoc:resultValue ?result .} 
    group by ?vote
  """
  total_vote_records_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select (COUNT(?vr) as ?count) {?vr undoc:inSession <""" + uri + """> .}
  """
  adopted_without_vote_q = """
    PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#> 
    select (COUNT(?vr) as ?count) {
      ?vr undoc:inSession <""" + uri + """> . 
      ?vr undoc:resultRecord ?rr . 
      ?rr undoc:resultKey ?vote . 
      ?rr undoc:resultValue ?result filter (?result = 'ADOPTED WITHOUT VOTE') .}
  """
  sparql.setQuery(pref_label_q)
  sparql.setReturnFormat(JSON)
  pref_label = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(aggregate_results_q)
  sparql.setReturnFormat(JSON)
  aggregate_results = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(total_vote_records_q)
  sparql.setReturnFormat(JSON)
  total_vote_records = sparql.query().convert()["results"]["bindings"]

  sparql.setQuery(adopted_without_vote_q)
  sparql.setReturnFormat(JSON)
  adopted_without_vote = sparql.query().convert()["results"]["bindings"]

  return render(request, 'votedb/session_record.html', { 'pref_label': pref_label[0], 'aggregate_results': aggregate_results, 'total_vote_records': total_vote_records[0], 'adopted_without_vote': adopted_without_vote[0] })

def turtle(request, uri):
  # to do: figure out why this fails
  turtle_q = "select ?p ?o {<" + uri + "> ?p ?o .}"
  sparql.setQuery(turtle_q)
  sparql.setReturnFormat(N3)
  turtle = sparql.query().convert()
  return HttpResponse(turtle, content_type="text/plain")
