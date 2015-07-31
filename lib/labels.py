#!/usr/bin/env python

import csv
import sys
import datetime
import string
import random
import requests
import re

def replace_latex_cmd_chars(string):
    CC = [ ('\\', '\\textbackslash '),
           ('&nbsp;', ' '), # needs to be before & replacement.
           ('&gt;', '>'),
           ('&lt;', '<'),
           ('_', '\\textunderscore '),
           ('&', '\\& '),
           ('%', '\\% '),
           ('#', '\\# '),
           # (' ', '\\_'), do not replace spaces
           ('{', '\\{ '),
           ('}', '\\} '),
           ('^', '\\textasciicircum '),
           ('$', '\\textdollar '), ]
    for c, lc in CC:
        string = string.replace(c, lc)
    return string.strip()


def crop_string(string, N):
    if len(string) > N:
        string = string[:N-2] + '...'
    return string


def label(fields):
    LIMITS = [12,5,27,80,30]
    fields = map(lambda s: crop_string(*s), zip(fields, LIMITS))
    fields = map(replace_latex_cmd_chars, fields)
    return "\\prettylabel{%s}{%s}{%s}{%s}{%s}" % tuple(fields)


def row2fields(row, select, override=(None,)*5):
    fields = []
    for i in range(5):
        if override[i] is not None:
            fields.append(override[i])
        else:
            fields.append( row[select[i]] if select.get(i) is not None else '' )
    return fields

TEMPLATE_US_START = [
    "\\documentclass[letter,10pt]{article}",
    "\\usepackage{lmodern}",
    "\\usepackage[T1]{fontenc}",
    "\\usepackage{array}",
    "\\usepackage{seqsplit}",
    "\\renewcommand{\\tabcolsep}{1mm}",
    "\\linespread{0.4}",
    "\\usepackage[newdimens]{labels}",
    "\\LabelCols=4",
    "\\LabelRows=15",
    "\\LeftPageMargin=8mm",
    "\\RightPageMargin=8mm",
    "\\TopPageMargin=15mm",
    "\\BottomPageMargin=12mm",
    "\\InterLabelColumn=7.5mm",
    "\\InterLabelRow=0.0mm",
    "\\LeftLabelBorder=2mm",
    "\\RightLabelBorder=2mm",
    "\\TopLabelBorder=0.0mm",
    "\\BottomLabelBorder=0.0mm",
    "\\newcommand{\\prettylabel}[5]{%",
    "\\genericlabel{%",
    "\\begin{tabular}{|l r| @{}m{0mm}@{}}",
    "\\hline",
    "~ & ~ & ~ \\\\[-1.5mm] % ",
    "\\multicolumn{3}{|l|}{\\textsf{\\footnotesize{#3}}} \\\\[0.5mm] ",
    "\\multicolumn{2}{m{38.7mm}}{\\texttt{\\tiny{\\seqsplit{#4}}}} & \\rule{0pt}{5mm} \\\\",
    "\\texttt{\\textbf{\\tiny{#5}}} & %",
    "\\sffamily{\\textbf{\\large{#1}}\\textit{#2}} & ~ \\\\",
    "\\hline",
    "\\end{tabular}",
    "}",
    "}",
    "",
    "\\begin{document}\n" ]

TEMPLATE_A4_START = [
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
#TEMPLATE_LABEL = "\\prettylabel{%s}{%s}{%s}{%s}{%s}"
TEMPLATE_SKIP = ["\\addresslabel{}"]
TEMPLATE_STOP = ["\n\\end{document}"]
 


def get_tex(flies, skip=0, template='a4', repeats=1):

    if template == 'us':
        TEMPLATE_START = TEMPLATE_US_START
    else:
        TEMPLATE_START = TEMPLATE_A4_START

    SELECT = { 0 : 'Label', 1 : None, 2 : 'Short Identifier', 3 : 'Genotype', 4 : None}
    OVERRIDE = ( None, None, None, None, datetime.datetime.now().strftime('%Y-%m-%d') )

    try:
        repeats = max(min(100, repeats), 1)
    except:
        repeats = 1

    LABELS = []
    for fly in flies:
        fields = row2fields(fly, SELECT, OVERRIDE)
        LABELS.extend( [label(fields)]*repeats )

    return "\n".join( TEMPLATE_START + (TEMPLATE_SKIP*skip) + LABELS + TEMPLATE_STOP ) 


def create_output(flies, template='a4', provider="lp1", skip=0, repeats=1):
    """Creates the output files requested by the user"""
    tex = get_tex(flies, skip=int(skip), template=template, repeats=repeats)
    try:
        tex = unicode(tex, 'utf-8')
    except:
        pass
    if provider == "lp1":
        content_type, data = pdf_from_sciencesoft(tex, template)
    elif provider == "lp2":
        content_type, data = pdf_from_mendelu(tex)
    elif provider == "lp3":
        content_type, data = pdf_from_halle(tex)
    elif provider == "lp4":
        content_type, data = 'text/plain', tex
    else:
        raise Exception("Unknown latex compiler '%s'" % provider)
    return content_type, data

def pdf_from_sciencesoft(tex, template):
    # sciencesoft.at online latex compiler
    OPTIONS = {'src' : tex,
               'dev' : 'pdfwrite',
               'papersize' : 'a4',
               'dpi' : 600,
               'result' : 'false',
               'template' : 'no'}
    if template == 'us':
        OPTIONS['papersize'] = 'letter'
    CHARS = string.ascii_uppercase + string.digits
    out = "LABELS_%s.pdf" % "".join( random.choice(CHARS) for _ in range(6) )

    URL = 'http://sciencesoft.at/image/latexurl/%s' % out

    r = requests.post(URL, data=OPTIONS)
    r.raise_for_status()
    return "application/pdf", r.content


def pdf_from_mendelu(tex):
    # tex.mendelu.cz online latex compiler
    OPTIONS = {'pole' : tex,
               'pdf' : 'PDF',
               'preklad' : 'latex',
               'pruchod' : 1,
               '.cgifields' : 'komprim'}
    URL = 'https://tex.mendelu.cz/en/'

    r = requests.post(URL, data=OPTIONS)
    r.raise_for_status()
    return "application/pdf", r.content


def pdf_from_halle(tex):
    # latex.informatik,uni-halle.de
    URL = 'http://latex.informatik.uni-halle.de/latex-online/latex.php'

    # get a new id from the website
    r = requests.get(URL)
    r.raise_for_status()
    iddata = r.content
    myid = re.findall('name="id" value="(.*)"', iddata)[0]

    # request to compile the pdf
    OPTIONS = {'quellcode' : tex,
               'id' : myid,
               'spw' : 1,
               'finit': 'nothing',
               'aformat' : 'PDF',
               'compile' : u'\u00DCbersetzen'}
    r = requests.post(URL, data=OPTIONS)
    r.raise_for_status()

    # download the created pdf
    PDFURL = "http://latex.informatik.uni-halle.de/latex-online/temp/olatex_%s.pdf" % myid
    r = requests.get(PDFURL)
    r.raise_for_status()
    data = r.content

    # cleanup temporary files
    CLEANURL = 'http://latex.informatik.uni-halle.de/latex-online/aufraeumen.php'
    OPTIONS = {'id' : myid,
               'spw' : 1}
    r = requests.post(CLEANURL, data=OPTIONS)
    r.raise_for_status()

    return "application/pdf", data
