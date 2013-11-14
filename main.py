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
import fakespreadsheets


### Google API interfaces
from apiclient.discovery import build
import apgooglelayer.drive
import apgooglelayer.calendar
from apgooglelayer.spreadsheets.oauth2client_gdata_bridge import OAuth2BridgeError


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
    labelpagesize = db.StringProperty()

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

    def set_labelpagesize(self, size):
        self.labelpagesize = size
        self.put()


def get_userdata(user):
    userdata_k = db.Key.from_path('UserData', user.user_id())
    userdata = db.get(userdata_k)
    if userdata is None:
        userdata = UserData(key_name=user.user_id(), 
                        spreadsheet_id='', spreadsheet_name='no spreadsheet',
                        calendar_id='', calendar_name='no calendar',
                        labelpagesize='a4')
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
                    ret = '%s\n%s\n' % (sp, "An error occurred. Your best option is to reboot your computer. (if your tried to print labels, try generating fewer at once.)")
                return ret
        return mydecorator
    return thedecorator

#-------------------------------------------------#
# FINALLY, the web interface
# RequestHandlers
#

render = web.template.render('templates/', base='bslayout')
render_wo_layout = web.template.render('templates/')

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
            cells = fakespreadsheets.fakecellfeed_from_ssid(selected, http)
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

        # template
        pagesize = web.input(pagesize=None).pagesize
        if pagesize is None:
            try:
                mp = ud.labelpagesize
            except:
                ud.set_labelpagesize("a4")
        else:
            ud.set_labelpagesize(pagesize)


        # select tabs
        tab = web.input(tab="tab1").tab
        return render.config(tree, cldr, ud, info, invalid, tab)


class Boxes(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1407.1: You green blooded bastard')
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        # GET SELECTED SPREADSHEETS:
        if len(ud.spreadsheet_id.split(',')[0]) == 0:
            web.seeother('/config')
        return render.boxes(ud, info)


class Flies(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1820.2: Space, the final frontier')
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        user = users.get_current_user()
        ud = get_userdata(user)
        info = get_header_info(user, decorator)
        # GET SELECTED SPREADSHEETS:
        if len(ud.spreadsheet_id.split(',')[0]) == 0:
            web.seeother('/config')
        return render.flies(ud, info)



class BoxData(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1820.2: Space, the final frontier')
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        try:
            data = web.input()
            ssid, ssname = data.ssid, data.ssname
            cellfeed = fakespreadsheets.fakecellfeed_from_ssid(ssid, http)
            boxes = flyboxes.get_boxes_from_cellfeed(cellfeed)
        except OAuth2BridgeError:
            # web.seeother(decorator.authorize_url())
            raise # this should be handled by decorator.oauth_required
        except Exception as e: #replace with BoxError
            boxtext = e.message
            return render_wo_layout.boxdata("ERROR", ssid, ssname, [], boxtext )
        else:
            return render_wo_layout.boxdata("OK", ssid, ssname, boxes, "" )


class FlyData(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1820.2: Space, the final frontier')
    @decorator.oauth_required
    def GET(self):
        http = decorator.http()
        data = web.input()
        try:
            ssid, ssname = data.ssid, data.ssname # throws AttributeError on failure
            cellfeed = fakespreadsheets.fakecellfeed_from_ssid(ssid, http)
            boxes = flyboxes.get_boxes_from_cellfeed(cellfeed) # throws FlyBoxError
        except (AttributeError, flyboxes.FlyBoxError) as e:
            return render_wo_layout.flydata("ERROR", ssid, ssname, [], e.message )
        except OAuth2BridgeError:
            raise # this should be handled by decorator.oauth_required 
        #>
        return render_wo_layout.flydata("OK", ssid, ssname, boxes, "" )




class PdfLabels(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1561.8: Humans are highly illogical')
    @decorator.oauth_required
    def GET(self):
        ssid = web.input().ssid 
        bn = web.input(box=None).box
        user = users.get_current_user()
        ud = get_userdata(user)
        try:
            ps = ud.labelpagesize
        except:
            ps = 'a4'

        http = decorator.http()
        cf = fakespreadsheets.fakecellfeed_from_ssid(ssid, http)
        boxes = flyboxes.get_boxes_from_cellfeed(cf)
        flies = []
        for box in boxes:
            if (bn is not None) and box['name'] != bn:
                continue
            flies.extend(box['flies'])

        URL, OPTIONS = labels.pdflink(flies, template=ps)

        r = requests.post(URL, data=OPTIONS)
        r.raise_for_status()
        
        web.header('Content-Type','application/pdf')
        return r.content

    @printerrors('Stardate 1561.8: Humans are highly illogical')
    def POST(self):
        tabledata = web.input().tabledata
        try:
            skip = int(web.input(skip=0).skip)
        except:
            skip = 0
        user = users.get_current_user()
        ud = get_userdata(user)
        try:
            ps = ud.labelpagesize
        except:
            ps = 'a4'
        flies = json.loads(tabledata)
        URL, OPTIONS = labels.pdflink(flies, skip=skip, template=ps)

        r = requests.post(URL, data=OPTIONS)
        r.raise_for_status()
        
        web.header('Content-Type','application/pdf')
        return r.content


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
         "/boxdata",     "BoxData",
         "/labels",      "PdfLabels",
         "/flies",       "Flies",
         "/flydata",     "FlyData",
         "/help",        "Help",
       )

appgae = web.application(urls, globals()).wsgifunc()
