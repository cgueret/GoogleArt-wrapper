'''
Created on Feb 2, 2011

@author: cgueret
'''
import sys
import tornado.web
import tornado.ioloop
import tornado.httpserver
from Resources import Paint
import os.path

class MainHandler(tornado.web.RequestHandler):
    '''
    Default handler, redirect to the homepage
    '''
    def get(self):
        self.redirect("/static/index.html")
        return

class PaintHandler(tornado.web.RequestHandler):
    '''
    Information about a specific paint
    '''
    def get(self, museum, paint):
        response = ''
        if os.path.isfile('cache/' + museum + "/" + paint):
            response = file('cache/' + museum + "/" + paint).read()
        else:
            paint_obj = Paint('museums/%s/%s' % (museum, paint))
            response = paint_obj.to_rdfxml()
            if not os.path.exists('cache/'):
                os.mkdir('cache/')
            if not os.path.exists('cache/' + museum):
                os.mkdir('cache/' + museum)
            f = open('cache/' + museum + "/" + paint, 'w')
            f.write(response)
            f.close()
        
        self.set_header("Content-Type", "application/rdf+xml")
        self.write(response)


if __name__ == '__main__':
    settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    }

    application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/museums/([^/]*)/([^/]+)/?$", PaintHandler)
    ], **settings)

    http_server = tornado.httpserver.HTTPServer(application)
    p = 10000
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    http_server.listen(p)
    tornado.ioloop.IOLoop.instance().start()
