#!/usr/bin/env python

import os
import web

from apiclient.discovery import build
from decoratorwebpycompat import WebPyOAuth2DecoratorFromClientSecrets

service = build('drive', 'v2')
decorator = WebPyOAuth2DecoratorFromClientSecrets(
                os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
                'https://www.googleapis.com/auth/drive')
                

class Index:

    @decorator.oauth_aware
    def GET(self):
        return ('Hello: has %s\n'
                '       goto "%s"\n'
                ' AND %s')%(str(decorator.has_credentials()),
                                     decorator.authorize_url(),
                                     str(web.ctx))

class Drive:
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        return 'Hello Drive'

class Calendar:
    def GET(self):
        return web.input(code=0).code
        #return 'Hello Calendar'

class Boxes:
    def GET(self):
        return 'Hello Boxes %s' % __name__

WebPyOAuth2 = decorator.callback_handler()

urls = ( "/",           "Index",
         "/drive",      "Drive",
         "/calendar",   "Calendar",
         "/boxes",      "Boxes",
         decorator.callback_path, "WebPyOAuth2",
       )

app = web.application(urls, globals())

appgae = app.wsgifunc()


