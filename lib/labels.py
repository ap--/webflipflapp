#!/usr/bin/env python

import csv
import sys
import datetime
import string
import random

def replace_latex_cmd_chars(string):
    CC = [ ('\\', '\\backslash'),
           ('&nbsp;', ' '), # needs to be before & replacement.
           ('&gt;', '>'),
           ('&lt;', '<'),
           ('_', '\\textunderscore'),
           ('&', '\\&'),
           ('%', '\\%'),
           ('#', '\\#'),
           # (' ', '\\_'), do not replace spaces
           ('{', '\\{'),
           ('}', '\\}'),
           ('$', '\\textdollar'), ]
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
#TEMPLATE_LABEL = "\\prettylabel{%s}{%s}{%s}{%s}{%s}"
TEMPLATE_STOP = ["\n\\end{document}"]
 


def get_tex(flies):

    SELECT = { 0 : 'Label', 1 : None, 2 : 'Short Identifier', 3 : 'Genotype', 4 : None}
    OVERRIDE = ( None, None, None, None, datetime.datetime.now().strftime('%Y-%m-%d') )

    LABELS = []
    for fly in flies:
        fields = row2fields(fly, SELECT, OVERRIDE)
        LABELS.append( label(fields) )

    return "\n".join( TEMPLATE_START + LABELS + TEMPLATE_STOP ) 


def pdflink(flies, out=None, dpi=600):
    URL = 'http://sciencesoft.at/image/latexurl/%s' % out
    tex = get_tex(flies)
    OPTIONS = {'src' : unicode(tex, 'utf-8'),
               'dev' : 'pdfwrite',
               'papersize' : 'a4',
               'dpi' : dpi,
               'result' : 'false',
               'template' : 'no'}
    if out is None:
        CHARS = string.ascii_uppercase + string.digits
        out = "LABELS_%s.pdf" % "".join( random.choice(CHARS) for _ in range(6) )
    return URL, OPTIONS
    
