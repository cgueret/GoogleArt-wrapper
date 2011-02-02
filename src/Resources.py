'''
Created on Feb 2, 2011

@author: cgueret
'''
from rdflib import ConjunctiveGraph, Literal, RDF, URIRef, BNode
from BeautifulSoup import BeautifulSoup
import urllib2
from datetime import date
import gzip
import json
import StringIO
import re
from SPARQLWrapper import SPARQLWrapper, JSON #@UnresolvedImport
from common import DCT, DBP, FOAF, EVENT, BIO, GOOGLE_ROOT, GART, DCMI, WIKIPEDIA_API

class Paint(object):
    def __init__(self, paint_reference):
        '''
        Constructor
        '''
        # Create the self.graph and the resource
        self.graph = ConjunctiveGraph()
        self.graph.bind('dct', DCT)
        self.graph.bind('dbprop', DBP)
        self.graph.bind('foaf', FOAF)
        self.graph.bind('event', EVENT)
        self.graph.bind('bio', BIO)
        self.__load_data(paint_reference)
    
    def to_rdfxml(self):
        '''
        Returns an RDF/XML representation of the graph
        '''
        return self.graph.serialize()
    
    def __get_dbpedia_resource(self, label):
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
        
    def __load_data(self, paint_reference):
        '''
        Returns an RDF representation of a painting on google art
        '''
        # Load HTML page
        document = BeautifulSoup(urllib2.urlopen(GOOGLE_ROOT + paint_reference).read())
        info_block = document.find(id='info')
    
        # Create the resource
        this = GART[paint_reference]
        self.graph.add((this, RDF.type, DCMI['StillImage']))
        self.graph.add((this, RDF.type, DCMI['PhysicalResource']))
        
        # Get general information
        content = info_block.find(attrs={'class':'content'})
        self.graph.add((this, DCT['title'], Literal(content.find('h2').string))) 
        self.graph.add((this, DCT['description'], Literal(content.find(attrs={'class':'altLang'}).string)))
        date_raw = content.find(attrs={'class':'year'}).string
        date_raw = re.search('([0-9]{4})', date_raw).group(0)
        self.graph.add((this, DCT['created'], Literal(date(int(date_raw), 1 , 1))))
        painter = self.__get_dbpedia_resource(content.find('h3').string.split(',')[0])
        if painter == None:       
            painter = BNode()
            self.graph.add((painter, RDF.type, DCT['Agent']))
            self.graph.add((painter, FOAF['name'], content.find('h3').string.split(',')[0]))
        self.graph.add((this, DCT['creator'], painter))
        about_raw = content.findAll('p')[2].getText()
        medium = self.__get_dbpedia_resource(about_raw[:about_raw.index('Height')])
        if medium != None:
            self.graph.add((this, DCT['medium'], URIRef(medium)))
        self.graph.add((this, DBP['height'], Literal(about_raw[about_raw.index('Height') + len('Height : '):about_raw.index('Width')])))
        self.graph.add((this, DBP['width'], Literal(about_raw[about_raw.index('Width') + len('Width : '):])))
        
        # Get extra information
        content = info_block.find(attrs={'class':'exclusive'})
        for link in content.findAll(attrs={'class':'outside'}):
            self.graph.add((this, FOAF['page'], URIRef(link.attrMap['href'])))
        for block in content.findAll('dt'):
            if block.string == 'Tags':
                for list in block.findNextSiblings('dd')[0].findAll('tr'):
                    for k in list.getText().split(','):
                        self.graph.add((this, DCT['subject'], Literal(k)))
            if block.attrMap.has_key('class') and block.attrMap['class'] == 'artworkListTrigger':
                for link in block.findNextSiblings('dd')[0].findAll('a'):
                    if link.attrMap['href'] != "#":
                        self.graph.add((this, DCT['relation'], GART[link.attrMap['href'][1:]]))
        
