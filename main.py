#!/usr/bin/env python

import os
from apiclient.discovery import build

import web
from oauth2client.appengine import OAuth2DecoratorFromClientSecrets
from oauth2client_webpy_bridge import FakeWebapp2RequestHandler

import apgooglelayer.drive
import apgooglelayer.calendar

import gdata.spreadsheets.client
from oauth2client_gdata_bridge import OAuth2BearerToken

from google.appengine.ext import db
from google.appengine.api import users

import flyboxes
import onlinetex
import pprint

import json
template_globals = {"json_encode": json.dumps}

import requests

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

drive_service = build('drive', 'v2')
calendar_service = build('calendar', 'v3')

GoogleDrive = apgooglelayer.drive.GoogleDrive(drive_service)
GoogleCalendar = apgooglelayer.calendar.GoogleCalendar(calendar_service)

def SpreadsheetsClient():
    # this returns a authenticated spreadsheet client
    token = OAuth2BearerToken(decorator.credentials)
    return gdata.spreadsheets.client.SpreadsheetsClient(auth_token=token)



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
        tree = GoogleDrive.folder_structure(http=http)
        ident = GoogleDrive.files_as_id_dict(
                fields='items(id,title,iconLink,mimeType)', http=http)
        selected = web.input(sheet=None).sheet
        if selected is not None:
            ud.set_spreadsheet(selected, ident[selected]['title'])

        return render.drive(tree, ident, ud.spreadsheet_id, *ud.get_names())


class Calendar(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1137.8: She\'s giving all she\'s got')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        http = decorator.http()
        cl = GoogleCalendar.listcalendars(http=http, key='id')       
        selected = web.input(sheet=None).sheet
        if selected is not None:
            ud.set_calendar(selected, cl[selected])
        return render.calendar(cl, ud.calendar_id, *ud.get_names())


class CalendarW(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1137.8: She\'s giving all she\'s got')
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        http = decorator.http()
        cl = GoogleCalendar.listcalendars(http=http, key='id')       
        selected = web.input(sheet=None).sheet
        if selected is not None:
            ud.set_calendar(selected, cl[selected])
        
        EVENTS = {}
        GoogleCalendar.calendarId = ud.calendar_id
        for ev in GoogleCalendar.iterevents(http=http,
                fields="items(start,recurrence,location,summary,description)"):
            _id = ev.pop('id')
            EVENTS[_id] = ev
        web.header('Content-Type', 'text/plain') 
        return pprint.pformat(EVENTS)


class Boxes(FakeWebapp2RequestHandler):
    @printerrors('Stardate 1407.1: You green blooded bastard')
    @decorator.oauth_required
    def GET(self):
        _i = web.input(pdf=None, flipped=None)
        user = users.get_current_user()
        ud = get_userdata(user)
        if not ud.spreadsheet_id:
            web.seeother('/drive')
        # get Boxes and Events
        client = SpreadsheetsClient()
        if bool(_i.flipped):
            flyboxes.set_lastModified_on_Box(client, _i.ssid, _i.boxname)
        BOXES = flyboxes.get_boxes_from_spreadsheet(client, ud.spreadsheet_id)
        # IF PDF is requested we can stop here
        if bool(_i.pdf):
            error, data = flyboxes.choose_pdf_from_boxes(_i.ssid,_i.boxname,BOXES)
            web.header('Content-Type','text/plain' if error else 'application/pdf')
            return data


        # ELSE: 
        EVENTS = GoogleCalendar.get_events_from_calendar(ud.calendar_id, 
                                                         http=decorator.http())
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
         "/calendarw",   "CalendarW",
         "/boxes",      "Boxes",
       )

appgae = web.application(urls, globals()).wsgifunc()
