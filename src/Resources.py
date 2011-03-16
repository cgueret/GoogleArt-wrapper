'''
Created on Feb 2, 2011

@author: cgueret
'''
import re
import urllib2
from rdflib import ConjunctiveGraph, Literal, RDF, URIRef, BNode
from BeautifulSoup import BeautifulSoup
from datetime import date
from common import DCT, DBP, FOAF, EVENT, BIO, GOOGLE_ROOT, GART, DCMI, GARTW, get_dbpedia_resource

class Resource(object):
    def __init__(self):
        # Create the self.graph and the resource
        self.graph = ConjunctiveGraph()
        self.graph.bind('dct', DCT)
        self.graph.bind('dbprop', DBP)
        self.graph.bind('foaf', FOAF)
        self.graph.bind('event', EVENT)
        self.graph.bind('bio', BIO)
        self._load_data()

    def to_rdfxml(self):
        '''
        Returns an RDF/XML representation of the graph
        '''
        return self.graph.serialize()
    
    def _load_data(self):
        '''
        Load the data into the RDF document, to be defined by each resource
        '''
        pass
            
    
class Homepage(Resource):
    def _load_data(self):
        '''
        Returns an RDF representation of the list of museums
        '''
        document = BeautifulSoup(urllib2.urlopen(GOOGLE_ROOT).read())
        list_block = document.find(id='list')
        for entry in  list_block.findAll('li'):
            city = entry.find('a').find('span').getText()
            name = entry.get('data-bg-museum')
            url = entry.get('data-museum-url')
            this = GARTW['index.rdf']
            museum = GARTW[url[1:]]
            self.graph.add((this, DCT['relation'], museum))
            self.graph.add((museum, DCT['title'], Literal(name))) 
            self.graph.add((museum, DCT['location'], get_dbpedia_resource(city))) 

class Museum(Resource):
    def __init__(self, url):
        self.url = '/museums/'+url
        Resource.__init__(self)
        
    def _load_data(self):
        '''
        Returns an RDF representation of the list of museums
        '''
        document = BeautifulSoup(urllib2.urlopen(GOOGLE_ROOT + self.url).read())
        artwork_list = document.find(id='artworkList')
        for artwork in  artwork_list.findAll('a'):
            resource = GARTW[artwork.get('href')[1:]]
            this = GARTW[self.url]
            self.graph.add((this, DCT['relation'], resource))
            
class Painting(Resource):
    def __init__(self, url):
        self.url = '/museums/'+url
        Resource.__init__(self)
        
    def _load_data(self):
        '''
        Returns an RDF representation of a painting on google art
        '''
        # Load HTML page
        document = BeautifulSoup(urllib2.urlopen(GOOGLE_ROOT + self.url).read())
        info_block = document.find(id='info')
    
        # Create the resource
        this = GART[self.url]
        self.graph.add((this, RDF.type, DCMI['StillImage']))
        self.graph.add((this, RDF.type, DCMI['PhysicalResource']))
        
        # Get general information
        content = info_block.find(attrs={'class':'content'})
        self.graph.add((this, DCT['title'], Literal(content.find('h2').string))) 
        self.graph.add((this, DCT['description'], Literal(content.find(attrs={'class':'altLang'}).string)))
        date_raw = content.find(attrs={'class':'year'}).string
        date_raw = re.search('([0-9]{4})', date_raw).group(0)
        self.graph.add((this, DCT['created'], Literal(date(int(date_raw), 1 , 1))))
        painter = get_dbpedia_resource(content.find('h3').string.split(',')[0])
        if painter == None:       
            painter = BNode()
            self.graph.add((painter, RDF.type, DCT['Agent']))
            self.graph.add((painter, FOAF['name'], content.find('h3').string.split(',')[0]))
        self.graph.add((this, DCT['creator'], painter))
        about_raw = content.findAll('p')[2].getText()
        medium = get_dbpedia_resource(about_raw[:about_raw.index('Height')])
        if medium != None:
            self.graph.add((this, DCT['medium'], URIRef(medium)))
        self.graph.add((this, DBP['height'], Literal(about_raw[about_raw.index('Height') + len('Height : '):about_raw.index('Width')])))
        self.graph.add((this, DBP['width'], Literal(about_raw[about_raw.index('Width') + len('Width : '):])))
        
        # Get extra information
        content = info_block.find(attrs={'class':'exclusive'})
        for link in content.findAll(attrs={'class':'outside'}):
            self.graph.add((this, FOAF['page'], URIRef(link.get('href'))))
        for block in content.findAll('dt'):
            if block.string == 'Tags':
                for list in block.findNextSiblings('dd')[0].findAll('tr'):
                    for k in list.getText().split(','):
                        self.graph.add((this, DCT['subject'], Literal(k)))
            if block.attrMap.has_key('class') and block.get('class') == 'artworkListTrigger':
                for link in block.findNextSiblings('dd')[0].findAll('a'):
                    if link.attrMap['href'] != "#":
                        self.graph.add((this, DCT['relation'], GARTW[link.get('href')[1:]]))
        
