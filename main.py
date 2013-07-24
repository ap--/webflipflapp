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
import apgooglelayer.calendar

import gdata.spreadsheets.client
from oauth2client_gdata_bridge import OAuth2BearerToken

#
# Setup drive and calendar services
#

drive_service = build('drive', 'v2')
calendar_service = build('calendar', 'v3')

decorator = WebPyOAuth2DecoratorFromClientSecrets(
                os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
                scope=['https://www.googleapis.com/auth/drive',
                       'https://www.googleapis.com/auth/calendar',
                       'https://spreadsheets.google.com/feeds'])

GoogleDrive = apgooglelayer.drive.GoogleDrive(drive_service)
GoogleCalendar = apgooglelayer.calendar.GoogleCalendar(calendar_service)

def SpreadsheetsClient():
    token = OAuth2BearerToken(decorator.credentials)
    return gdata.spreadsheets.client.SpreadsheetsClient(auth_token=token)

#
# RequestHandlers
#

render = web.template.render('templates/')

class Index:
    @decorator.oauth_aware
    def GET(self):
        has_cred = decorator.has_credentials()
        auth_url = decorator.authorize_url()
        return render.index(has_cred, auth_url)


class Drive:
    @decorator.oauth_required
    def GET(self):
        selected = web.input(sheet=None).sheet
        http = decorator.http()
        tree = GoogleDrive.folder_structure(http=http)
        ident = GoogleDrive.files_as_id_dict(
                fields='items(id,title,iconLink,mimeType)', http=http)
        return render.drive(tree, ident, selected)


class Calendar:
    @decorator.oauth_required
    def GET(self):
        selected = web.input(sheet=None).sheet
        http = decorator.http()
        cl = GoogleCalendar.listcalendars(http=http)       
        return render.calendar(cl, selected)


class Boxes:
    @decorator.oauth_required
    def GET(self):
        d = SpreadsheetsClient().get_worksheets('0AvA5wEfgv_7FdHQxWjYzblJyUW9QR0dCTDVMN2NxTFE')
        return 'Hello Boxes %s' % str(d)

#
# URLS
#

WebPyOAuth2 = decorator.callback_handler()
urls = ( "/",           "Index",
         "/drive",      "Drive",
         "/calendar",   "Calendar",
         "/boxes",      "Boxes",
         decorator.callback_path, "WebPyOAuth2",
       )
app = web.application(urls, globals())

# GoogleAppEngine name, used in app.yaml
appgae = app.wsgifunc()


