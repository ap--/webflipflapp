
import datetime
import random
import string

def replace_latex_cmd_chars(string):
    C = [ ('\\', '\\backslash'),
          ('&', '\\&'),
          ('%', '\\%'),
          ('#', '\\#'),
        # (' ', '\\_'), do not replace spaces
          ('{', '\\{'),
          ('}', '\\}'),
          ('$', '\\textdollar') ]
    for c, lc in CC:
        string = string.replace(c, lc)
    return string
              

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
    def pdflink_from_box(cls, box, out, dpi, keys):
        return cls.pdflink_from_flies(box['flies'], out, dpi, keys)

    @classmethod
    def pdflink_from_flies(cls, flies, out=None, dpi=600, keys=None):
        if keys is None:
            keys = ['Label', '',
                    'Short Identifier','Genotype','---date---']
        if len(keys) != 5:
            raise ValueError("pdflink_from_box requires 5 labelkeys")
        di = keys.index('---date---')
        LG = cls()
        for fly in flies:
            fget = lambda x : fly.get(x, '')
            INP = ["".join(map(fget, k.split('---'))) for k in keys]
            if di >= 0: INP[di] = LG._date
            LG.add_label(*INP)
        if out is None:
            CHARS = string.ascii_uppercase + string.digits
            out = "LABELS_%s.pdf" % "".join(
                random.choice(CHARS) for _ in range(6) )
        return LG.pdflink(out, dpi)

