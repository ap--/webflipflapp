#!/usr/bin/env python
#
# Imports
#

import os
from apiclient.discovery import build

""" using web.py with gae.
    decoratorwebpycompat provides Decorator syntax for webpy """
import web
from decoratorwebpycompat import WebPyOAuth2DecoratorFromClientSecrets

import apgooglelayer.drive

#
# Setup drive and calendar services
#

drive_service = build('drive', 'v2')
calendar_service = build('calendar', 'v3')

decorator = WebPyOAuth2DecoratorFromClientSecrets(
                os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
                scope=['https://www.googleapis.com/auth/drive',
                       'https://www.googleapis.com/auth/calendar'])

GoogleDrive = apgooglelayer.drive.GoogleDrive(drive_service)

#
# RequestHandlers
#

render = web.template.render('templates/')

class index:
    
    @decorator.oauth_aware
    def GET(self):
        has_cred = decorator.has_credentials()
        auth_url = decorator.authorize_url()
        return render.index(has_cred, auth_url)

class Drive:
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        about = GoogleDrive.about(http=http)
        return ('Hello Drive:\n'
                ' name: %s\n') % about['user']['displayName']

class Calendar:
    def GET(self):
        return web.input(code=0).code
        #return 'Hello Calendar'

class Boxes:
    def GET(self):
        return 'Hello Boxes %s' % __name__

#
# URLS
#

WebPyOAuth2 = decorator.callback_handler()
urls = ( "/",           "index",
         "/drive",      "Drive",
         "/calendar",   "Calendar",
         "/boxes",      "Boxes",
         decorator.callback_path, "WebPyOAuth2",
       )
app = web.application(urls, globals())

# GoogleAppEngine name, used in app.yaml
appgae = app.wsgifunc()


