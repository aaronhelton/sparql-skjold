from django.conf import settings
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper(settings.SPARQL_ENDPOINT)

INDEX_QUERY = """
"""

ORGANIZATION_QUERY = """
  PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#>
  SELECT ?x {
    ?x rdf:type undoc:Organization .
  }
"""

BODIES_QUERY = """
  PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#>
  SELECT ?x {
    ?x rdf:type undoc:Body .
  }
"""

SESSIONS_QUERY = """
  PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#>
  SELECT ?x {
    ?x rdf:type undoc:Session .
  }
"""

MEMBER_STATES_QUERY = """
  PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#>
  SELECT ?x {
    ?x rdf:type undoc:MemberState .
  } ORDER BY ?x
"""

QUERIES = {
  'index':MEMBER_STATES_QUERY,
  'organization':ORGANIZATION_QUERY,
  'bodies':BODIES_QUERY,
  'sessions':SESSIONS_QUERY,
  'member_states':MEMBER_STATES_QUERY,
}


def get_preferred_label(uri,language):
  # While there are other possible label categories, these are quite common. Expand as necessary.
  if uri and language:
    query = """
      PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#>
      SELECT ?label { 
        { <""" + uri + """> skos:prefLabel ?label } union 
        { <""" + uri + """> dcterms:title ?label  } union 
        { <""" + uri + """> rdfs:label ?label  } .
      }
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]
    # Return the first label that matches the language or fallback to English if possible; toss back the URI if all else fails
    return_str = uri
    for res in results:
      if res["label"]["xml:lang"] == language:
        return_str = res["label"]["value"]

    if return_str == uri:
      for res in results:
        if res["label"]["xml:lang"] == 'en':
          return_str = res["label"]["value"]

    return return_str 
  else:
    return False

def get_all_labels(uri):
  if uri:
    query = """
      PREFIX undoc: <http://unontologies.s3-website-us-east-1.amazonaws.com/undoc#>
      SELECT ?label {
        { <""" + uri + """> skos:prefLabel ?label } union
        { <""" + uri + """> dcterms:title ?label  } union
        { <""" + uri + """> rdfs:label ?label  } .
      }
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]
    # Note the return here is a JSON object, not a plain string
    return results
  else: 
    return False
