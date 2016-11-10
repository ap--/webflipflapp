#!/usr/bin/python

import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.keyring_storage import Storage
from oauth2client.tools import run
import getpass


def get_service(secrets, scope, service_name, 
                service_version, keyring_storename):
    """
    return a service for google
    """
    flow = flow_from_clientsecrets(secrets, scope=scope,
                    redirect_uri='http://localhost:8080')
    store = Storage(keyring_storename, getpass.getuser())
    # Check if we already have credentials
    credentials = store.get()
    if not credentials or credentials.invalid:
        # if not, spawn a browser to get credentials
        credentials = run(flow, store)
    # finally create a service object:
    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build(service_name, service_version, http=http)
    return service


def get_drive_service(secrets, keyring_storename, ver='v2'):
    """
    return a service for google drive
    """
    return get_service(secrets, 
            scope='https://www.googleapis.com/auth/drive',
            service_name='drive', service_version=ver,
            keyring_storename=keyring_storename)


def get_calendar_service(secrets, keyring_storename, ver='v3'):
    """
    return a service for google calendar
    """
    return get_service(secrets, 
            scope='https://www.googleapis.com/auth/calendar',
            service_name='calendar', service_version=ver,
            keyring_storename=keyring_storename)



