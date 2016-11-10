#!/usr/bin/env python

from gdata.spreadsheets.client import SpreadsheetsClient
from gdata.spreadsheets.data import CellEntry, Cell
from gdata.client import Unauthorized

from oauth2client_gdata_bridge import OAuth2BearerToken, OAuth2BridgeError, oauth2errorconversion
from oauth2client.client import AccessTokenRefreshError


__all__ = ['SpreadsheetsError', 'GoogleSpreadsheets']


class GoogleSpreadsheetsError(Exception):
    pass


class GoogleSpreadsheets(object):

    def __init__(self, credentials=None, decorator=None,
                 spreadsheet_id=None, worksheet_id=None):
        self._decorator = None
        self._oauth2token = None
        if decorator is None and credentials is None:
            self._oauth2token = None
        else:
            self._decorator = decorator if decorator else None
            cred = decorator.credentials if decorator else credentials
            self._oauth2token = OAuth2BearerToken(cred)
        self._spreadsheet_id = spreadsheet_id
        self._worksheet_id = worksheet_id

    def set_credentials(self, credentials):
        self._oauth2token = OAuth2BearerToken(credentials)
    
    def set_decorator(self, decorator):
        self._decorator = decorator

    def set_spreadsheet_id(self, spreadsheet_id):
        self._spreadsheet_id = spreadsheet_id

    def get_spreadsheet_id(self):
        return self._spreadsheet_id

    def set_worksheet_id(self, worksheet_id):
        self._spreadsheet_id = spreadsheet_id

    def get_worksheet_id(self):
        return self._worksheet_id

    @property
    def service(self):
        return self._service()
    
    def _service(self, http=None):
        if not (http or self._oauth2token or self._decorator):
            raise GoogleSpreadsheetsError('please set oauth2 credentials'
                                    ' or oauth2 decorator')
        if http:
            token = OAuth2BearerToken(http.request.credentials)
        elif self._decorator:
            token = OAuth2BearerToken(self._decorator.credentials)
        else:
            token = self._oauth2token
        try:
            return SpreadsheetsClient(auth_token=token)
        except Unauthorized as e:
            raise AccessTokenRefreshError(e.message)
    
    @oauth2errorconversion
    def get_worksheets(self, spreadsheet_id=None, http=None):
        ssid = spreadsheet_id if spreadsheet_id else self.get_spreadsheet_id()
        if ssid is None:
            raise GoogleSpreadsheetsError('please set or provide spreadsheet_id')
        return self._service(http).get_worksheets(ssid).entry

    @oauth2errorconversion
    def get_worksheets_as_ids(self, spreadsheet_id=None, http=None):
        WS = self.get_worksheets(spreadsheet_id, http)
        return [(ws.get_worksheet_id(), ws.title.text) for ws in WS]

    @oauth2errorconversion
    def get_cells_from_worksheet(self, worksheet_id=None, spreadsheet_id=None,
                                        http=None):
        ssid = spreadsheet_id if spreadsheet_id else self.get_spreadsheet_id()
        wsid = worksheet_id if worksheet_id else self.get_worksheet_id()
        if ssid is None:
            raise GoogleSpreadsheetsError('please set or provide spreadsheet_id')
        if wsid is None:
            raise GoogleSpreadsheetsError('please set or provide worksheet_id')
        return self._service(http).get_cells(ssid, wsid).entry

    @oauth2errorconversion
    def get_cells_from_first_worksheet(self, spreadsheet_id=None, http=None):
        wsid = self.get_worksheets_as_ids(spreadsheet_id, http)[0][0]
        return self.get_cells_from_worksheet(wsid, spreadsheet_id, http)

    @oauth2errorconversion
    def get_indexed_cells_content_from_worksheet(self, worksheet_id=None,
                                            spreadsheet_id=None, http=None):
        ret = []
        for cell in self.get_cells_from_worksheet(
                                worksheet_id, spreadsheet_id, http):
            ret.append((int(cell.cell.row),
                        int(cell.cell.col),
                        cell.content.text))
        return ret

    @oauth2errorconversion
    def set_cell(self, row, col, content, worksheet_id=None,
                                    spreadsheet_id=None, http=None):
        row = str(row)
        col = str(col)
        content = str(content)
        new_cell = CellEntry(cell=Cell(row=row, col=col, input_value=content))
        ssid = spreadsheet_id if spreadsheet_id else self.get_spreadsheet_id()
        wsid = worksheet_id if worksheet_id else self.get_worksheet_id()
        if ssid is None:
            raise GoogleSpreadsheetsError('please set or provide spreadsheet_id')
        if wsid is None:
            raise GoogleSpreadsheetsError('please set or provide worksheet_id')
        CELL_URL = ('https://spreadsheets.google.com/feeds/'
                    'cells/%s/%s/private/full/R%sC%s') % (ssid,wsid,row,col)
        tmp = self._service(http)
        tmp.update(new_cell, 
                auth_token=tmp.auth_token, uri=CELL_URL, force=True)
        return

