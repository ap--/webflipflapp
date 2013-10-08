
import cgi
import datetime
import re
import random
import string



class FlyBoxError(Exception):
    pass


class Box(dict):
    def __init__(self, ssid, wsid):
        default = { 'ssid'    : ssid,
                    'wsid'    : wsid,
                    'name'    : 'N/A',
                    'flipped' : 'N/A',
                    'calid'   : 'N/A',
                    'labels'  : {}, # dict idx : label
                    'flies'   : [], # list of dicts 
                  }
        super(Box, self).__init__(default)



def get_boxes_from_cellfeed(cellfeed):
    #seperate boxes
    BOXES = []
    y_old = y_off = -2
    ym, xm = 0, 0
    ssid, wsid = None, None
    for c in cellfeed:
        # On first run get ssid and wsid
        if (ssid is None) and (wsid is None):
            url = c.get_id()
            result = re.search('cells/(?P<ssid>[^/]*)/(?P<wsid>[^/]*)/', url)
            ssid = result.group('ssid')
            wsid = result.group('wsid')
        # get contents
        y = int(c.cell.row)
        x = int(c.cell.col)
        v = cgi.escape(c.content.text)
        # skip the first two lines
        if y < 3:
            continue
        # ignore everything after a #WFF-IGNORE
        if x == 1 and v == "#WFF-IGNORE":
            break
        # seperate boxes
        if y - y_old < 2:
            y_old = y
        else:
            y_off = y_old = y
            BOXES.append(Box(ssid, wsid))
        by, bx = y-y_off, x
        lastBox = BOXES[-1]
        lastBox['_width'] = max(bx, lastBox.get('_width', 0))
        lastBox['_height'] = max(by, lastBox.get('_height', 0))
        if by == 0 and bx == 1: lastBox['name'] = v
        if by == 0 and bx == 2: lastBox['flipped'] = v[9:] # ugly hack
        if by == 0 and bx == 3: lastBox['calid'] = v[7:] # ugly hack
        if by == 1: lastBox.setdefault('_labels', {})[bx] = v if v else '&nbsp;'
        if by >= 2: lastBox.setdefault('_elements', {})[(by,bx)] = v if v else '&nbsp;'
    # get flies
    for b in BOXES:
        elements = b.pop('_elements', {}) 
        ylen, xlen = b.pop('_height', 0), b.pop('_width', 0)
        labels = b.pop('_labels', {})
        # get labels
        for k in range(xlen):
            ktmp = labels.get(k+1, None)
            if ktmp == '':
                ktmp = None
            b['labels'][k] = ktmp
        # get flies
        for j in range(1,ylen):
            fly = {}
            for i in range(xlen):
                if b['labels'][i] is not None:
                    fly[b['labels'][i]] = elements.get((j+1,i+1), '&nbsp;')
            b['flies'].append(fly)
    
    return BOXES



def get_flies_from_box(ssid, name, boxes):
    for b in boxes:
        if b['name'] == name and b['ssid'] == ssid:
            return b['flies']
    return []


def compare_boxes_and_events_coll(sscoll, clcoll):
    events = []
    boxes = []
    for bb in sscoll.values():
        boxes.extend(bb)
    for ci, cc in clcoll.iteritems():
        for e in cc:
            e['_clid_'] = ci
            events.append(e)
    evIds = [ev['id'] for ev in events]
    ret = []
    for box in boxes:
        bbb = box['calid'].split()
        if len(bbb) > 1:
            bcl = bbb[-1]
            bev = bcl.split('/')[-1]
            bcd = bcl.split('/')[0]
        else:
            bev = ''
            bcd = ''
        if bev in evIds:
            box['mode'] = 'BOXSHOW'
            # figure out when that happens
            ev = next( e for e in events if e['id'] == bev )
            ret.append([box, ev['_clid_'], ev['id']])
        else:
            if bcd == "":
                box['mode'] = 'BOXADD'
            else:
                box['mode'] = 'BOXOVERRIDE'
    return ret

def set_schedule_on_Box(box, clid, evid, GoogleCalendar, http):
    dayonly = {'hour':0,'minute':0,'second':0,'microsecond':0}
    flipped = box.get('modified')
    try:
        flipped = datetime.datetime.strptime(flipped, 'flipped: %Y-%m-%d')
    except:
        flipped = datetime.datetime.strptime('2000-01-01', '%Y-%m-%d')
    
    today = datetime.datetime.today().replace(**dayonly)
    lookahead = today + datetime.timedelta(days=365)
    
    tMin = flipped.isoformat('T')+'Z'
    tMax = lookahead.isoformat('T')+'Z'

    enext = GoogleCalendar.get_instances(calendarId=clid, eventId=evid,
                fields='items(start)', timeMin=tMin, timeMax=tMax, http=http)
    if len(enext) == 0:
        box['scheduled'] = 'N/A'
    else:
        scheduled= datetime.datetime.strptime(enext[0]['start']['date'],'%Y-%m-%d')
        scheduled.replace(**dayonly)
        diff = (scheduled-today).days
        box['scheduled'] = 'in %d days' % diff if diff != 0 else 'today'


def set_modified_on_Box(cellfeed, ssid, boxname):
    date = datetime.datetime.strftime(datetime.datetime.now(), 
            'flipped: %Y-%m-%d')
    url = cellfeed[0].get_id()
    result = re.search('cells/(?P<ssid>[^/]*)/(?P<wsid>[^/]*)/', url)
    ssid = result.group('ssid')
    wsid = result.group('wsid')
    store = [(int(c.cell.row),int(c.cell.col),c.content.text) for c in cellfeed]
    # get cells
    y, x = -1, 2
    for row,col,content in store:
        if row > 2 and content == boxname:
            y = row
            break
    if y > -1:
        return y, x, date, wsid, ssid
    else:
        raise FlyBoxError('set_modified_on_Box: Box not found?')

def set_calid_on_Box(cellfeed, ssid, boxname, calid, eventid):
    value = 'calid: %s/%s' % (calid, eventid)
    url = cellfeed[0].get_id()
    result = re.search('cells/(?P<ssid>[^/]*)/(?P<wsid>[^/]*)/', url)
    ssid = result.group('ssid')
    wsid = result.group('wsid')
    store = [(int(c.cell.row),int(c.cell.col),c.content.text) for c in cellfeed]
    # get cells
    y, x = -1, 3
    for row,col,content in store:
        if row > 2 and content == boxname:
            y = row
            break
    if y > -1:
        return y, x, value, wsid, ssid
    else:
        raise FlyBoxError('set_calid_on_Box: Box not found?')


