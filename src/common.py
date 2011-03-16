'''
Created on Feb 2, 2011

@author: cgueret
'''
import urllib2
import gzip
import json
import StringIO
from rdflib import Namespace
from SPARQLWrapper import SPARQLWrapper, JSON #@UnresolvedImport

GOOGLE_ROOT = "http://www.googleartproject.com/"
WIKIPEDIA_API = "http://en.wikipedia.org/w/api.php?"

# Namespaces
GART = Namespace("http://www.googleartproject.com/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
DCT = Namespace("http://purl.org/dc/terms/")
DCMI = Namespace("http://purl.org/dc/dcmitype/")
DBP = Namespace("http://dbpedia.org/property/")
EVENT = Namespace("http://linkedevents.org/ontology/")
BIO = Namespace("http://purl.org/vocab/bio/0.1/")
GARTW = Namespace("http://linkeddata.few.vu.nl/googleart/")

def get_dbpedia_resource(label):
    '''
    Get a resource DBPedia matching a given page title in Wikipedia
    ''' 
    # Get the name of the wikipedia page, if any
    url = WIKIPEDIA_API + 'action=query&format=json&indexpageids&prop=info&inprop=url&titles=' + urllib2.quote(label.encode('utf-8'))
    request = urllib2.Request(url)
    request.add_header('Accept-Encoding', 'gzip')
    request.add_header('User-Agent', 'cgueret/christophe.gueret@gmail.com')
    response = urllib2.urlopen(request)
    raw_text = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
    result = json.load(raw_text)['query']
    if len(result['pageids']) == 1 and result['pageids'][0] == '-1':
        return None
    fullurl = result['pages'][result['pageids'][0]]['fullurl']
    
    # Get the matching DBPedia resource
    query = "select ?s where {?s <http://xmlns.com/foaf/0.1/page> <%s>}" % fullurl
    sparql = SPARQLWrapper("http://lod.openlinksw.com/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()["results"]["bindings"]
    if len(results) < 1:
        return None
    resource = results[0]["s"]["value"]

    return resource
