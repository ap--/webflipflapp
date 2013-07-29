#!/usr/bin/env python

### PATH
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib_third_party'))


### WebServer
import web
from oauth2client.appengine import OAuth2DecoratorFromClientSecrets
from oauth2client_webpy_bridge import FakeWebapp2RequestHandler
import json; template_globals = {"json_encode": json.dumps}


### Google API interfaces
from apiclient.discovery import build
import apgooglelayer.drive
import apgooglelayer.calendar
import apgooglelayer.spreadsheets


### Google Appengine imports
from google.appengine.ext import db
from google.appengine.api import users


### Flyflippingdstuff
import flyboxes
import onlinetex


### Debugging
import pprint
def webDEBUG(ob):
    web.header('Content-Type', 'text/plain')
    return pprint.pformat(ob)


#--------------------------------------------------
# Defining the database stuff for userdata storage
#

class UserData(db.Model):
    spreadsheet_id = db.StringProperty()
    spreadsheet_name = db.StringProperty()
    calendar_id = db.StringProperty()
    calendar_name = db.StringProperty()
        
    def get_names(self):
        return self.spreadsheet_name, self.calendar_name

    def has_spreadsheet(self):
        return spreadsheey_id != ''

    def has_calendar(self):
        return spreadsheey_id != ''

    def set_spreadsheet(self, _id, name):
        self.spreadsheet_id = _id
        self.spreadsheet_name = name
        self.put()

    def set_calendar(self, _id, name):
        self.calendar_id = _id
        self.calendar_name = name
        self.put()


def get_userdata(user):
    userdata_k = db.Key.from_path('UserData', user.user_id())
    userdata = db.get(userdata_k)
    if userdata is None:
        userdata = UserData(key_name=user.user_id(), 
                        spreadsheet_id='', spreadsheet_name='no spreadsheet',
                        calendar_id='', calendar_name='no calendar')
        userdata.put()
    return userdata


#-------------------------------------------------
# Setting up the OAuth2 authorization and google-
#  api-interfaces

decorator = OAuth2DecoratorFromClientSecrets(
                os.path.join(os.path.dirname(__file__), 'client_secrets.json'),
                scope=['https://www.googleapis.com/auth/drive',
                       'https://www.googleapis.com/auth/calendar',
                       'https://spreadsheets.google.com/feeds'])

GoogleDrive = apgooglelayer.drive.GoogleDrive()
GoogleCalendar = apgooglelayer.calendar.GoogleCalendar()
GoogleSpreadsheets = apgooglelayer.spreadsheets.GoogleSpreadsheets()



"""~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""
def printerrors(prefix):
    def thedecorator(f):
        def mydecorator(*args,**kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                return prefix + (' %s' % e)
        return mydecorator
    return thedecorator

#-------------------------------------------------#
# FINALLY, the web interface
# RequestHandlers
#

render = web.template.render('templates/', globals=template_globals)

class Index(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1034.5: we encountered a')
    @decorator.oauth_aware
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        has_cred = decorator.has_credentials()
        auth_url = decorator.authorize_url()
        return render.index(has_cred, auth_url, *ud.get_names())


class Drive(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1051.2: He\'s dead Jim')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        http = decorator.http()
        tree = GoogleDrive.folder_structure(http=http, fields='items(iconLink)')
        selected = web.input(selected=None).selected
        if selected is not None:
            name = tree.get_first_where(lambda k: k['id']==selected)['title']
            ud.set_spreadsheet(selected, name)
        return render.drive(tree, ud.spreadsheet_id, *ud.get_names())


class Calendar(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1137.8: She\'s giving all she\'s got')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        http = decorator.http()
        cldr = GoogleCalendar.list_calendars(http=http, fields='items(id,summary)')
        selected = web.input(selected=None).selected
        if selected is not None:
            name = next(c['summary'] for c in cldr if c['id']==selected)
            ud.set_calendar(selected, name)
        return render.calendar(cldr, ud.calendar_id, *ud.get_names())


class Boxes(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1407.1: You green blooded bastard')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        http = decorator.http()
        data = web.input(pdf=None, flipped=None)
        
        # get Boxes and Events
        cellfeed = GoogleSpreadsheets.get_cells_from_first_worksheet(
                                            ud.spreadsheet_id, http=http)
        if bool(data.flipped):
            args = flyboxes.set_modified_on_Box(cellfeed,
                                            data.ssid, data.boxname)
            GoogleSpreadsheets.set_cell(*args, http=http)
            web.seeother('/boxes')
        BOXES = flyboxes.get_boxes_from_cellfeed(cellfeed)

        # IF PDF is requested we can stop here
        if bool(data.pdf):
            error, data = flyboxes.choose_pdf_from_boxes(data.ssid,
                                                data.boxname, BOXES)
            web.header('Content-Type','text/plain' if error else 'application/pdf')
            return data
        # ELSE: 
        EVENTS = GoogleCalendar.iter_events(calendarId=ud.calendar_id, http=http)
        #return webDEBUG(EVENTS) 
        flyboxes.compare_boxes_and_events(BOXES, EVENTS)
            
        return render.boxes(BOXES, *ud.get_names())


"""
    The oauth2callback is done with the google-webapp stuff thats
    hidden in the oauth2client api.
    !> manually set the redirect in app.yaml
"""
appoauth = decorator.callback_application()

urls = ( "/",           "Index",
         "/drive",      "Drive",
         "/calendar",   "Calendar",
         "/boxes",      "Boxes",
       )

appgae = web.application(urls, globals()).wsgifunc()
