#!/usr/bin/env python

import web

urls = ( "/",           "Index",
         "/drive",      "Drive",
         "/calendar",   "Calendar",
         "/boxes",      "Boxes",
       )

class Index:
    def GET(self):
        return 'Hello'

class Drive:
    def GET(self):
        return 'Hello Drive'

class Calendar:
    def GET(self):
        return 'Hello Calendar'

class Boxes:
    def GET(self):
        return 'Hello Boxes'


app = web.application(urls, globals())

appgae = app.wsgifunc()


