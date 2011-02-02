'''
Created on Feb 2, 2011

@author: cgueret
'''
# http://dublincore.org/documents/dcmi-terms/
# http://www.lespetitescases.net/quel-evenement-ou-comment-contextualiser-le-triplet

from rdflib import ConjunctiveGraph, Namespace, Literal, RDF, URIRef, BNode
from BeautifulSoup import BeautifulSoup
import urllib2
from datetime import date
import gzip
import json
import StringIO
import re
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


def get_painting(paint_reference):
    '''
    Returns an RDF representation of a painting on google art
    '''
    # Load HTML page
    document = BeautifulSoup(urllib2.urlopen(GOOGLE_ROOT + paint_reference).read())
    info_block = document.find(id='info')
    
    # Create the graph and the resource
    graph = ConjunctiveGraph()
    graph.bind('dct', DCT)
    graph.bind('dbprop', DBP)
    graph.bind('foaf', FOAF)
    graph.bind('event', EVENT)
    graph.bind('bio', BIO)
    this = GART[paint_reference]
    graph.add((this, RDF.type, DCMI.StillImage))
    graph.add((this, RDF.type, DCMI.PhysicalResource))
    
    # Get general information
    content = info_block.find(attrs={'class':'content'})
    graph.add((this, DCT['title'], Literal(content.find('h2').string))) 
    graph.add((this, DCT['description'], Literal(content.find(attrs={'class':'altLang'}).string)))
    date_raw = content.find(attrs={'class':'year'}).string
    date_raw = re.search('([0-9]{4})', date_raw).group(0)
    graph.add((this, DCT['created'], Literal(date(int(date_raw), 1 , 1))))
    painter = get_dbpedia_resource(content.find('h3').string.split(',')[0])
    if painter == None:       
        painter = BNode()
        graph.add((painter, RDF.type, DCT['Agent']))
        graph.add((painter, FOAF['name'], content.find('h3').string.split(',')[0]))
    graph.add((this, DCT['creator'], painter))
    about_raw = content.findAll('p')[2].getText()
    medium = get_dbpedia_resource(about_raw[:about_raw.index('Height')])
    if medium != None:
        graph.add((this, DCT['medium'], URIRef(medium)))
    graph.add((this, DBP['height'], Literal(about_raw[about_raw.index('Height')+len('Height : '):about_raw.index('Width')])))
    graph.add((this, DBP['width'], Literal(about_raw[about_raw.index('Width')+len('Width : '):])))
    
    
    # Get extra information
    content = info_block.find(attrs={'class':'exclusive'})
    for link in content.findAll(attrs={'class':'outside'}):
        graph.add((this, FOAF['page'], URIRef(link.attrMap['href'])))
    for block in content.findAll('dt'):
        if block.string == 'Tags':
            for list in block.findNextSiblings('dd')[0].findAll('tr'):
                for k in list.getText().split(','):
                    graph.add((this, DCT['subject'], Literal(k)))
        if block.attrMap.has_key('class') and block.attrMap['class'] == 'artworkListTrigger':
            for link in block.findNextSiblings('dd')[0].findAll('a'):
                if link.attrMap['href'] != "#":
                    graph.add((this, DCT['relation'], GART[link.attrMap['href'][1:]]))
                    #graph.add((URIRef(link.attrMap['href']), DCT['creator'], painter))
                #graph.add((this, DCT['subject'], Literal(k)))
        if block.string == 'Artist Information':
            for item in block.findNextSiblings('dd')[0].findAll('li'):
                text=item.getText()
                location=text[5:]
                if text[:4] == 'Born':
                    event = BNode()
                    graph.add((event, RDF.type, EVENT['Event']))
                    graph.add((event, RDF.type, BIO['Birth']))
                if text[:4] == 'Died':
                    pass
    #print content
    
    return graph.serialize()

if __name__ == '__main__':
    #print get_painting("museums/rijks/night-watch")
    #print get_painting("museums/rijks/river-view-by-moonlight-26")
    print get_painting("museums/uffizi/adoration-of-the-magi-91")
