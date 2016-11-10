# -*- coding: utf-8 -*-

from ..common import unwrap_pages
from apiclient.discovery import build

import datetime

class GoogleCalendar(object):

    def __init__(self, service=None):
        if service is None:
            self.service = build('calendar', 'v3')
        else:
            self.service = service

    @unwrap_pages
    def list_calendars(self, **kwargs):
        http = kwargs.pop('http', None)
        return self.service.calendarList().list(**kwargs).execute(http=http)

    @unwrap_pages
    def iter_events(self, **kwargs):
        http = kwargs.pop('http', None)
        return self.service.events().list(**kwargs).execute(http=http)

    def delete_event(self, calendarId, eventId, http=None):
        return self.service.events().delete(calendarId=calendarId,
                                    eventId=eventId).execute(http=http)

    def add_raw_event(self, calendarId, event, http=None):
        return self.service.events().insert(calendarId=calendarId,
                                    body=event).execute(http=http)
    @unwrap_pages
    def get_instances(self, **kwargs):
        http = kwargs.pop('http', None)
        return self.service.events().instances(**kwargs).execute(http=http)


    def add_recurring_1day_event(self, calendarId, summary, description,
            recurrence_days, start, location, http=None):
        _start = start
        _end = (datetime.datetime.strptime(_start, '%Y-%m-%d')
                + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        
        ev = { 'summary'     : summary,
               'description' : description,
               'recurrence'  : [u'RRULE:FREQ=DAILY;INTERVAL=%s' % recurrence_days],
               'start'       : {'date' : _start},
               'end'         : {'date' : _end},
               'location'    : location,
               'reminders'   : { 'useDefault' : False,
                                 'overrides' : [{'method' : 'email',
                                                 'minutes': 24*60 }] } }

        return self.add_raw_event(calendarId, ev, http=http)


    """
    def _addcalendar(self, summary, description, timezone):
        cl = { 'summary'     : summary,
               'description' : description,
               'timeZone'    : timezone,
               'reminders'   : {'useDefault' : False},
               'defaultReminders' : []}
        ret = self.service.calendars().insert(body=cl).execute()
        return ret['id']


        if self.calendarId is None:
            raise ValueError('please set calendarId')
        start = date
        end = start + duration
        start = start.isoformat('T')
        end = end.isoformat('T')
        event = {
            'summary': summary,
            'start': { 'dateTime': start,
                       'timeZone': self.FCTIMEZONE },
            'end': { 'date': end,
                     'timeZone': self.FCTIMEZONE },
            'description' : description,
            'location' : location,
                }
        
        self.service.events().insert(calendarId=self.calendarId,
                                     body=event).execute()

    
    """

            
