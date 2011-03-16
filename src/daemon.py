'''
Created on Feb 2, 2011

@author: cgueret
'''
import sys
import tornado.web
import tornado.ioloop
import tornado.httpserver
import os.path
from datetime import datetime
from Resources import Painting, Homepage, Museum

def get_cache(object_name, days):
    '''
    Get an entry from the cache, 'days' indicate its maximum age in days
    '''
    file_name = 'cache/' + object_name
    if os.path.isfile(file_name):
        fileage = datetime.fromtimestamp(os.stat(file_name).st_mtime)
        delta = datetime.now() - fileage
        if delta.days < days:
            return file(file_name).read()
    return None

def put_cache(object_name, content):
    '''
    Save a given file into the cache
    '''
    # Create directory structure if needed
    if not os.path.exists('cache/'):
        os.mkdir('cache/')
    a = 'cache/'
    for subdir in object_name.split('/')[:-1]:
        a = a + subdir + '/'
        if not os.path.exists(a):
            os.mkdir(a)
    
    # Save the object
    f = open('cache/' + object_name, 'w')
    f.write(content)
    f.close()

class MainHandler(tornado.web.RequestHandler):
    '''
    Default handler, redirects to the homepage
    '''
    def get(self):
        self.render("index.html")
        return

class MainHandlerRDF(tornado.web.RequestHandler):
    '''
    Default handler, lists the museum in RDF
    '''
    def get(self):
        response = get_cache('index.rdf', 14)
        if response == None:
            response = Homepage().to_rdfxml()
            put_cache('index.rdf', response)
        self.set_header("Content-Type", "application/rdf+xml")
        self.write(response)
    
class PaintingHandler(tornado.web.RequestHandler):
    '''
    Information about a specific painting
    '''
    def get(self, museum, paint):
        painting = museum + "/" + paint
        response = get_cache(painting + '.rdf', 7)
        if response == None:
            response = Painting(painting).to_rdfxml()
            put_cache(painting + '.rdf', response)
        self.set_header("Content-Type", "application/rdf+xml")
        self.write(response)

class MuseumHandler(tornado.web.RequestHandler):
    '''
    Information about a specific museum
    '''
    def get(self, museum):
        response = get_cache(museum + '.rdf', 7)
        if response == None:
            response = Museum(museum).to_rdfxml()
            put_cache(museum + '.rdf', response)
        self.set_header("Content-Type", "application/rdf+xml")
        self.write(response)

if __name__ == '__main__':
    application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/index.rdf$", MainHandlerRDF),
    (r"/museums/([^/]*)/([^/]+)/?$", PaintingHandler),
    (r"/museums/([^/]*)/?$", MuseumHandler)
    ])

    http_server = tornado.httpserver.HTTPServer(application)
    p = 10000
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    http_server.listen(p)
    tornado.ioloop.IOLoop.instance().start()
