
import re
import requests
import datetime
from gdata.spreadsheets.data import CellEntry, Cell


class FlyBoxError(Exception):
    pass


class Box(dict):

    def __init__(self, spreadsheet_cellfeed):
        self._cellfeed = spreadsheet_cellfeed

        if not self._cellfeed:
            raise FlyBoxError('%s: cellfeed empty' % self.__class__.__name__)
        else:
            url = self._cellfeed[0].get_id()
            result = re.search('cells/(?P<ssid>[^/]*)/(?P<wsid>[^/]*)/', url)
            self._ssid = result.group('ssid')
            self._wsid = result.group('wsid')

        default = { 'ssid'          : self._ssid,
                    'wsid'          : self._wsid,
                    'calid'         : '',
                    'modified'      : 'flipped: N/A',
                    'name'          : '',
                    'labels'        : {}, # dict of {col : value}
                    'elements'      : {}, # dict of {(row,col) : value}
                    'flies'         : [],
                    'size'          : [0,0],
                    'mode'          : '' }

        super(Box, self).__init__(default)


def get_boxes_from_cellfeed(cellfeed):
    #seperate boxes
    BOXES = []
    y_old = y_off = -2
    ym, xm = 0, 0
    store = [(int(c.cell.row),int(c.cell.col),c.content.text) for c in cellfeed]
    for y,x,v in store:
        if y < 3:
            continue
        if y - y_old < 2:
            y_old = y
        else:
            y_off = y_old = y
            BOXES.append(Box(cellfeed))
        by, bx = y-y_off, x
        BOXES[-1]['size'][:] = map(max,zip([by,bx],BOXES[-1]['size']))
        if by == 0 and bx == 1: BOXES[-1]['name'] = v
        if by == 0 and bx == 2: BOXES[-1]['modified'] = v
        if by == 0 and bx == 3: BOXES[-1]['calid'] = v
        if by == 1: BOXES[-1].setdefault('labels', {})[bx] = v
        if by >= 2: BOXES[-1].setdefault('elements', {})[(by,bx)] = v
    # get flies, and pdf
    for b in BOXES:
        elements = b.pop('elements', {}) 
        ylen, xlen = b.pop('size')
        labels = b.get('labels', {})
        b['flies'] = []
        for j in range(2,ylen+1):
            fly = {labels[i]:elements.get((j,i),'') for i in range(1, xlen+1) }
            b['flies'].append(fly)
        b['pdf'] = LabelGenerator.pdflink_from_box(b)
    
    return BOXES

   
def choose_pdf_from_boxes(ssid, name, boxes):
    for b in boxes:
        if b['name'] == name and b['ssid'] == ssid:
            URL, OPTIONS = b['pdf']
            # for some reason, we need a PUT request...
            r = requests.put(URL, data=OPTIONS)
            try:
                r.raise_for_status()
                return False, r.content
            except:
                raise
            return True, "Error: when generating the pdf"
    return True, "Error: box not found"


def compare_boxes_and_events(boxes, events):
    evIds = [ev['id'] for ev in events]
    for box in boxes:
        if box['calid'] == '' or box['id'] not in evIds:
            box['mode'] = 'BOXADD'
        elif box['calid']:
            box['mode'] = 'BOXOVERRIDE'
        else:
            box['mode'] = 'BOXSHOW'


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


class LabelGenerator(object):

    TEMPLATE_START = [
    "\\documentclass[a4paper,10pt]{article}",
    "\\usepackage{lmodern}",
    "\\usepackage[T1]{fontenc}",
    "\\usepackage{array}",
    "\\usepackage{seqsplit}",
    "\\renewcommand{\\tabcolsep}{1mm}",
    "\\linespread{0.4}",
    "\\usepackage[newdimens]{labels}",
    "\\LabelCols=4",
    "\\LabelRows=16",
    "\\LeftPageMargin=8mm",
    "\\RightPageMargin=8mm",
    "\\TopPageMargin=15mm",
    "\\BottomPageMargin=12mm",
    "\\InterLabelColumn=0.0mm",
    "\\InterLabelRow=0.0mm",
    "\\LeftLabelBorder=2mm",
    "\\RightLabelBorder=1mm",
    "\\TopLabelBorder=0.0mm",
    "\\BottomLabelBorder=0.0mm",
    "\\newcommand{\\prettylabel}[5]{%",
    "\\genericlabel{%",
    "\\begin{tabular}{|l r| @{}m{0mm}@{}}",
    "\\hline",
    "~ & ~ & ~ \\\\[-1.5mm] % ",
    "\\multicolumn{3}{|l|}{\\textsf{\\footnotesize{#3}}} \\\\[0.5mm] ",
    "\\multicolumn{2}{m{42.7mm}}{\\texttt{\\tiny{\\seqsplit{#4}}}} & \\rule{0pt}{5mm} \\\\",
    "\\texttt{\\textbf{\\tiny{#5}}} & %",
    "\\sffamily{\\textbf{\\large{#1}}\\textit{#2}} & ~ \\\\",
    "\\hline",
    "\\end{tabular}",
    "}",
    "}",
    "",
    "\\begin{document}\n" ]
    TEMPLATE_LABEL = "\\prettylabel{%s}{%s}{%s}{%s}{%s}"
    TEMPLATE_STOP = ["\n\\end{document}"]
    
    def __init__(self):
        self._date = datetime.datetime.strftime(datetime.datetime.now(), 
                                                '%a %d %b %Y') 
        self._labels = []

    def add_label(self, _id,mod,shortident,desc,date=None):
        if date is None:
            date = self._date
        self._labels.append((self.TEMPLATE_LABEL % (_id,mod,shortident,desc,date)))

    def clear(self):
        self._labels = []

    def pdflink(self, out='out.pdf', dpi=600):
        URL = 'http://sciencesoft.at/image/latexurl/%s' % out
        tex = "\n".join(self.TEMPLATE_START+self._labels+self.TEMPLATE_STOP)
        OPTIONS = {'src' : unicode(tex, 'utf-8'),
               'dev' : 'pdfwrite',
               'papersize' : 'a4',
               'dpi' : dpi,
               'result' : 'false',
               'template' : 'no'}
        return URL, OPTIONS
    
    @classmethod
    def pdflink_from_box(cls, box, out='pdf.out', dpi=600, keys=None):
        if keys is None:
            keys = ['Label', 'Modifier1---Modifier2---Modifier3',
                    'Short Identifier','Genotype','---date---']
        if len(keys) != 5:
            raise ValueError("pdflink_from_box requires 5 labelkeys")
        LG = cls()
        di = keys.index('---date---')
        for fly in box['flies']:
            fget = lambda x : fly.get(x, '')
            INP = ["".join(map(fget, k.split('---'))) for k in keys]
            if di >= 0: INP[di] = LG._date
            LG.add_label(*INP)
        out = box['name'].replace(':','')+'.pdf'
        return LG.pdflink(out, dpi)


