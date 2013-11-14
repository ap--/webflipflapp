
import StringIO
import csv

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
    URL = "https://docs.google.com/feeds/download/spreadsheets/Export?key=%s&exportFormat=csv"
    resp, content = http.request(URL % ssid)
    f = StringIO.StringIO(content)
    reader = csv.reader(f)
    CCC = []
    for y,row in enumerate(reader):
        for x,cell in enumerate(row):
            #yield Fakecell(y,x,cell)
            if len(cell) > 0:
                CCC.append(Fakecell(y+1,x+1,cell, ssid, 0))
    return CCC
