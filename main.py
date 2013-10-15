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
import labels
import requests
import datetime
import json

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

def get_header_info(user,deco):
    return {'has_cred' : deco.has_credentials(),
                'auth_url' : deco.authorize_url(),
                'login_url' : users.create_login_url('/'),
                'logout_url' : users.create_logout_url('/'),
                'nickname' : user.nickname(),
                'email' : user.email() }


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
import traceback
def printerrors(prefix):
    def thedecorator(f):
        def mydecorator(*args,**kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                sp = '%s\n%s\n' % (prefix, '~'*len(prefix))
                if False:
                    se = 'ERROR: %s\n' % str(e)
                    st = traceback.format_exc().strip().replace('\n', '\n> ')
                    web.header('Content-Type', 'text/plain')
                    ret = '%s\n%s\n%s' % (sp, se, st)
                else:
                    web.header('Content-Type', 'text/plain')
                    ret = '%s\n%s\n' % (sp, "An error occurred. Your best option is to reboot your computer.")
                return ret
        return mydecorator
    return thedecorator

#-------------------------------------------------#
# FINALLY, the web interface
# RequestHandlers
#

render = web.template.render('templates/', globals=template_globals, base='bslayout')
render_wo_layout = web.template.render('templates/', globals=template_globals)

class Index(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1034.5: we encountered a')
    @decorator.oauth_aware
    def GET(self):
        user = users.get_current_user()
        info = get_header_info(user, decorator)
        return render.index(info)


class Config(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1051.2: He\'s dead Jim')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        http = decorator.http()
        
        # check spreadsheets
        tree = GoogleDrive.folder_structure(http=http, fields='items(iconLink)')
        spreadsheets = web.input(spreadsheets=[]).spreadsheets

        invalid = []
        names = []
        for selected in spreadsheets:
            name = tree.get_first_where(lambda k: k['id']==selected)['title']
            cells = GoogleSpreadsheets.get_cells_from_first_worksheet(selected, http=http)
            if cells and cells[0].content.text == 'WFF:FLYSTOCK':
                names.append(name)
            else:
                invalid.append(name)
                
        if (not invalid) and spreadsheets:
            ud.set_spreadsheet(",".join(spreadsheets), ",".join(names))

        # check calendars
        cldr = GoogleCalendar.list_calendars(http=http, fields='items(id,summary)')
        calendars = web.input(calendars=[]).calendars

        names = []
        for selected in calendars:
            name = next(c['summary'] for c in cldr if c['id']==selected)
            names.append(name)
        
        if calendars:
            ud.set_calendar(",".join(calendars), ",".join(names))

        # select tabs
        tab = web.input(tab="tab1").tab
        return render.config(tree, cldr, ud, info, invalid, tab)



class Boxes(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1407.1: You green blooded bastard')
    @decorator.oauth_required
    def GET(self):
        web.header('Cache-control', 'must-revalidate')
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        http = decorator.http()

        # GET SELECTED SPREADSHEETS:
        if len(ud.spreadsheet_id.split(',')[0]) == 0:
            web.seeother('/config')
        
        return render.boxes(ud, info)

        # data = web.input(flipped=None, add=None)
        #SSCOLL = {}
        #for ssid in ud.spreadsheet_id.split(','):
        #    cellfeed = GoogleSpreadsheets.get_cells_from_first_worksheet(ssid, http=http)
        #    # If a box got flipped
        #    if bool(data.flipped) and data.ssid == ssid:
        #        args = flyboxes.set_modified_on_Box(cellfeed, data.ssid, data.boxname)
        #        GoogleSpreadsheets.set_cell(*args, http=http)
        #        cellfeed = GoogleSpreadsheets.get_cells_from_first_worksheet(ssid, http=http)
        #    # If a box got added to the calendar
        #    if bool(data.add) and data.ssid == ssid:
        #        BOXES = flyboxes.get_boxes_from_cellfeed(cellfeed)
        #        box = next(b for b in BOXES if b['name'] == data.boxname)
        #        desc = '%s :: %s' % (box['name'], box['ssid'])
        #        nev = GoogleCalendar.add_recurring_1day_event(calendarId=data.clid,
        #                summary=box['name'], description=desc, start=data.start,
        #                recurrence_days=data.freq, location=data.location, http=http)
        #        args = flyboxes.set_calid_on_Box(cellfeed, data.ssid, data.boxname, data.clid, nev['id'])
        #        GoogleSpreadsheets.set_cell(*args, http=http)
        #        cellfeed = GoogleSpreadsheets.get_cells_from_first_worksheet(ssid, http=http)
        #    
        #    SSCOLL[ssid] = flyboxes.get_boxes_from_cellfeed(cellfeed)

        # GET EVENTS
        #CLCOLL = {}
        #if len(ud.calendar_id.split(',')[0]) == 0:
        #    web.seeother('/calendar')
        
        #for clid in ud.calendar_id.split(','):
        #    if len(clid) > 0:
        #        CLCOLL[clid] = GoogleCalendar.iter_events(calendarId=clid, http=http) 
        # SET SCHEDULING DATES
        #for box, clid, evid in flyboxes.compare_boxes_and_events_coll(SSCOLL, CLCOLL):
        #    flyboxes.set_schedule_on_Box(box, clid, evid, GoogleCalendar, http)



class Spreadsheet(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1820.2: Space, the final frontier')
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        data = web.input(ssid=None, ssname=None)
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        if (data.ssid is None):
            raise Exception("no ssid query parameter")
        if (data.ssname is None):
            raise Exception("no ssname query parameter")
        cellfeed = GoogleSpreadsheets.get_cells_from_first_worksheet(data.ssid, http=http)
        boxes = flyboxes.get_boxes_from_cellfeed(cellfeed)
        return render.spreadsheet(data.ssid, data.ssname, boxes, True, ud, info)



class PdfLabels(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1561.8: Humans are highly illogical')
    @decorator.oauth_required
    def GET(self):
        ssid = web.input().ssid 
        bn = web.input(box=None).box

        http = decorator.http()
        cf = GoogleSpreadsheets.get_cells_from_first_worksheet(ssid, http=http)
        boxes = flyboxes.get_boxes_from_cellfeed(cf)
        flies = []
        for box in boxes:
            if (bn is not None) and box['name'] != bn:
                continue
            flies.extend(box['flies'])

        URL, OPTIONS = labels.pdflink(flies)

        r = requests.post(URL, data=OPTIONS)
        r.raise_for_status()
        
        web.header('Content-Type','application/pdf')
        return r.content

    @printerrors('Stardate 1561.8: Humans are highly illogical')
    def POST(self):
        tabledata = web.input().tabledata
        flies = json.loads(tabledata)
        URL, OPTIONS = labels.pdflink(flies)

        r = requests.post(URL, data=OPTIONS)
        r.raise_for_status()
        
        web.header('Content-Type','application/pdf')
        return r.content


class FlyData(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1820.2: Space, the final frontier')
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        data = web.input(ssid=None, ssname=None)
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        if (data.ssid is None):
            raise Exception("no ssid query parameter")
        if (data.ssname is None):
            raise Exception("no ssname query parameter")
        cellfeed = GoogleSpreadsheets.get_cells_from_first_worksheet(data.ssid, http=http)
        boxes = flyboxes.get_boxes_from_cellfeed(cellfeed)
        return render.flydata(data.ssid, data.ssname, boxes, info)


class Flies(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1820.2: Space, the final frontier')
    @decorator.oauth_required
    def GET(self):
        web.header('Cache-control', 'must-revalidate')
        http = decorator.http()
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        return render.flies(ud, info)

class Help(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1820.2: Space, the final frontier')
    @decorator.oauth_aware
    def GET(self):
        http = decorator.http()
        user = users.get_current_user()
        info = get_header_info(user, decorator)
        return render.help(info)

"""
    The oauth2callback is done with the google-webapp stuff thats
    hidden in the oauth2client api.
    !> manually set the redirect in app.yaml
"""
appoauth = decorator.callback_application()

urls = ( "/",            "Index",
         "/config",      "Config",
         "/boxes",       "Boxes",
         "/spreadsheet", "Spreadsheet",
         "/labels",      "PdfLabels",
         "/flies",       "Flies",
         "/flydata",     "FlyData",
         "/help",        "Help",
       )

appgae = web.application(urls, globals()).wsgifunc()
