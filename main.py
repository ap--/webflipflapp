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
import datetime

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

def get_header_info(user, deco):
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
                se = 'ERROR: %s\n' % str(e)
                st = traceback.format_exc().strip().replace('\n', '\n> ')
                web.header('Content-Type', 'text/plain')
                ret = '%s\n%s\n%s' % (sp, se, st)
                return ret
        return mydecorator
    return thedecorator

#-------------------------------------------------#
# FINALLY, the web interface
# RequestHandlers
#

render = web.template.render('templates/', globals=template_globals, base='layout')
render_wo_layout = web.template.render('templates/', globals=template_globals)

class Index(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1034.5: we encountered a')
    @decorator.oauth_aware
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        return render.index(info)


class Drive(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1051.2: He\'s dead Jim')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        http = decorator.http()
        tree = GoogleDrive.folder_structure(http=http, fields='items(iconLink)')
        selections = web.input(selected=[]).selected
        invalid = web.input(invalid=[]).invalid
        if selections:
            ids, names, invalid = [], [], []
            for selected in selections:
                name = tree.get_first_where(lambda k: k['id']==selected)['title']
                cells = GoogleSpreadsheets.get_cells_from_first_worksheet(selected, http=http)
                if cells and cells[0].content.text == 'WFF:FLYSTOCK':
                    ids.append(selected)
                    names.append(name)
                else:
                    invalid.append(selected)
            if invalid:
                raise web.seeother('/drive?'+'&'.join(['invalid=%s' % sid for sid in invalid]))
            ud.set_spreadsheet(",".join(ids), ",".join(names))
        return render.drive(tree, ud, invalid, info)


class Calendar(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1137.8: She\'s giving all she\'s got')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        http = decorator.http()
        cldr = GoogleCalendar.list_calendars(http=http, fields='items(id,summary)')
        selections = web.input(selected=[]).selected
        if selections:
            ids, names = [], []
            for selected in selections:
                name = next(c['summary'] for c in cldr if c['id']==selected)
                ids.append(selected)
                names.append(name)
            ud.set_calendar(",".join(ids), ",".join(names))
        return render.calendar(cldr, ud, info)


class Boxes(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1407.1: You green blooded bastard')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        http = decorator.http()
        # data = web.input(flipped=None, add=None)

        # GET SELECTED SPREADSHEETS:
        #SSCOLL = {}
        if len(ud.spreadsheet_id.split(',')[0]) == 0:
            web.seeother('/drive')

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

        return render.boxes(ud, info)


class Spreadsheet(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1820.2: Space, the final frontier')
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        data = web.input(ssid=None)
        if data.ssid is None:
            raise Exception("no ssid query parameter")
        cellfeed = GoogleSpreadsheets.get_cells_from_first_worksheet(data.ssid, http=http)
        boxes = flyboxes.get_boxes_from_cellfeed(cellfeed)
        return render_wo_layout.spreadsheet(data.ssid, boxes)



class PdfLabels(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1561.8: Humans are highly illogical')
    @decorator.oauth_required
    def GET(self):
        data = web.input(box=[])
        store = {}
        for ssb in data.box:
            ssid, boxname = ssb.split('/')
            store[ssid] = store.get(ssid, []) + [boxname]

        Flies = []
        for ssid, boxnames in store.iteritems():
            cf = GoogleSpreadsheets.get_cells_from_first_worksheet(ssid, http=http)
            boxes = flyboxes.get_boxes_from_cellfeed(cf)
            
            for boxname in boxnames:
                Flies.extend(flyboxes.get_flies_from_box(ssid, boxname, boxes))
        
        URL, OPTIONS = flyboxes.pdflink_from_flies(Flies)
        
        r = requests.put(URL, data=OPTIONS)
        r.raise_for_status()
        
        web.header('Content-Type','application/pdf')
        return r.content



"""
    The oauth2callback is done with the google-webapp stuff thats
    hidden in the oauth2client api.
    !> manually set the redirect in app.yaml
"""
appoauth = decorator.callback_application()

urls = ( "/",            "Index",
         "/drive",       "Drive",
         "/calendar",    "Calendar",
         "/boxes",       "Boxes",
         "/spreadsheet", "Spreadsheet",
       )

appgae = web.application(urls, globals()).wsgifunc()
