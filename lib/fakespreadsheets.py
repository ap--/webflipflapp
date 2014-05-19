
import StringIO
import csv
import xlrd
import itertools

class YX(object):
    def __init__(self, y, x):
        self.row = y
        self.col = x

class CT(object):
    def __init__(self, v):
        self.text = v

class Fakecell(object):
    def __init__(self, y, x, v, ssid, wsid):
        self.cell = YX(y, x)
        self.content = CT(v)
        self.url = 'cells/%s/%s/' % (str(ssid), str(wsid))
    def get_id(self):
        return self.url


def fakecellfeed_from_ssid(ssid, http):
    URL = "https://docs.google.com/spreadsheets/d/%s/export?format=xlsx&id=%s"
    resp, content = http.request(URL % (ssid, ssid))
    f = StringIO.StringIO(content)
    xls_spreadsheet = xlrd.open_workbook(f)
    sheet = xls_spreadsheet.sheet_by_index(0)
    ROWS = sheet.nrows
    COLS = sheet.ncols
    CCC = []
    for y, x in itertools.product(range(ROWS), range(COLS)):
        cell = sheet.cell(y, x)
        if len(cell.value) > 0:
            CCC.append(Fakecell(y+1,x+1, cell.value, ssid, 0))
    return CCC
