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

from google.appengine.ext import db
from google.appengine.api import users

class UserData(db.Model):
    spreadsheet_id = db.StringProperty()
    spreadsheet_name = db.StringProperty()
    calendar_id = db.StringProperty()
    calendar_name = db.StringProperty()
              
def get_userdata(user):
    if user:
        userdata_k = db.Key.from_path('UserData', user.user_id())
        userdata = db.get(userdata_k)
        return userdata
              
#user = users.get_current_user()
#if user:
#    q = db.GqlQuery("SELECT * FROM UserPrefs WHERE userid = :1", user.user_id())
#    userprefs = q.get()
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

def getmenu2(ud):
    return ud.spreadsheet_name, ud.calendar_name

#
# RequestHandlers
#

render = web.template.render('templates/')

class Index:
    @decorator.oauth_aware
    def GET(self):
        try:
            user = users.get_current_user()
            ud = get_userdata(user)
            if ud is None:
                ud = UserData(key_name=user.user_id(),
                                  spreadsheet_id='',
                                  spreadsheet_name='no spreadsheet',
                                  calendar_id='',
                                  calendar_name='no calendar')
                ud.put()
            has_cred = decorator.has_credentials()
            auth_url = decorator.authorize_url()
            return render.index(has_cred, auth_url, *getmenu2(ud))
        except Exception as e:
            return 'hallo wie %s' % e

class Drive:
    @decorator.oauth_required
    def GET(self):
        user = users.get_current_user()
        ud = get_userdata(user)
        try:
            http = decorator.http()
            tree = GoogleDrive.folder_structure(http=http)
            ident = GoogleDrive.files_as_id_dict(
                    fields='items(id,title,iconLink,mimeType)', http=http)
            selected = web.input(sheet=None).sheet
            if ud is None:
                ud = UserData(key_name=user.user_id(),
                              spreadsheet_id='',
                              spreadsheet_name='no spreadsheet',
                              calendar_id='',
                              calendar_name='no calendar')
                ud.put()
            if selected is not None:
                ud.spreadsheet_id = selected
                ud.spreadsheet_name = ident[selected]['title']
                ud.put()
            else:
                selected = ud.spreadsheet_id

            return render.drive(tree, ident, selected, *getmenu2(ud))
        except Exception as e:
            return 'now it %s' % e


class Calendar:
    @decorator.oauth_required
    def GET(self):
        try:
            user = users.get_current_user()
            ud = get_userdata(user)
            http = decorator.http()
            cl = GoogleCalendar.listcalendars(http=http)       
            selected = web.input(sheet=None).sheet
            if ud is None:
                ud = UserData(key_name=user.user_id(),
                                  spreadsheet_id='',
                                  spreadsheet_name='no spreadsheet',
                                  calendar_id='',
                                  calendar_name='no calendar')
                ud.put()
            if selected is not None:
                ud.calendar_id = selected
                for _e,_i in cl.iteritems():
                    if _i == selected:
                        ud.calendar_name = _e
                        break
                ud.put()
            else:
                selected = ud.calendar_id
            return render.calendar(cl, selected, *getmenu2(ud))
        except Exception as e:
            return 'naw it %s' % e
    

class Boxes:
    @decorator.oauth_required
    def GET(self):
        try:
            user = users.get_current_user()
            ud = get_userdata(user)
            ss_id = '0AvA5wEfgv_7FdHQxWjYzblJyUW9QR0dCTDVMN2NxTFE'
            client = SpreadsheetsClient()
            wfeed = client.get_worksheets(ss_id)
            warn_multiple_worksheets = False if len(wfeed.entry) < 2 else True
            ws = wfeed.entry[0]
            ROWS = int(ws.row_count.text)
            ws_id = ws.get_worksheet_id()            
            cfeed = client.get_cells(ss_id, ws_id)
            store = []
            for cell in cfeed.entry:
                if int(cell.cell.row) < 3:
                    continue
                store.append((int(cell.cell.row), int(cell.cell.col), 
                                cell.content.text))
            store.sort()
            #seperate boxes
            BOXES = [[]]
            y_old = y_off = store[0][0]
            for y,x,v in store:
                if y - y_old < 2:
                    y_old = y
                else:
                    BOXES.append([])
                    y_off = y_old = y
                BOXES[-1].append((y-y_off,x,v))
            #create name, labels, get row and col size
            DBOXES = []
            for box in BOXES:
                d = { 'name'     : '',
                      'labels'   : {},
                      'elements' : {},
                      'size'     : (1,1) }
                ym, xm = -1, -1
                for y,x,v in box:
                    if y > ym: ym = y
                    if x > xm: xm = x
                    if y == 0 and x == 1:
                        d['name'] = v
                    if y == 1:
                        d['labels'][x] = v
                    if y > 1:
                        d['elements'][(y,x)] = v
                d['size'] = (ym,xm) #XXX tricky, but makes sense :)
                DBOXES.append(d)
            return render.boxes(DBOXES, *getmenu2(ud))
        except Exception as e:
            return 'We had a %s' % e
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


