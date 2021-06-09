# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 18:45:28 2021

@author: guari
"""

import re
from bs4 import BeautifulSoup
import nltk
nltk.download('punkt')
nltk.download('words')
from nltk.corpus import words 
from html_table_extractor.extractor import Extractor
import quantity

def clean_html(html):
    for r in re.findall('<sup>.+?</sup>', html, re.DOTALL):
        html = re.sub(re.escape(r), '^'+r[5:-6], html) 
    for r in re.findall('<math>.+?</math>', html, re.DOTALL):
        html = re.sub(re.escape(r), '', html)
    html = re.sub(' +', ' ', html)
    return html

def clean(txt):
    txt = re.sub('−', '-', txt)
    txt = re.sub('_', ' ', txt)
    txt = re.sub('·', ' ', txt)
    txt = re.sub('/', ' / ', txt)
    txt = re.sub('%', ' % ', txt)
    txt = re.sub('\n+', ' ', txt)
    txt = re.sub('\t', ' ', txt)
    txt = re.sub("′", "'", txt)
    txt = re.sub('\xa0', ' ', txt)
    txt = re.sub(' +', ' ', txt)
    """
    while txt[0] == ' ':
        txt = txt[1:]
    while txt[-1] == ' ':
        txt = txt[:-1]
    """
    return txt

def header(table,n):
    html = open('tables/Table '+str(n)+'.html', 'r', encoding='utf-8').read()
    soup = BeautifulSoup(html, 'html.parser')
    t = table['content']
    thead = soup.thead
    header = []
    for i in range(0,len(thead.contents)):
        if(thead.contents[i]!='\n'):
            header.append(thead.contents[i])
    content = []
    for tr in header:
        h = []
        for i in range(0,len(tr.contents)):
            if(tr.contents[i]!='\n'):
                h.append(tr.contents[i])
        content.append(h)
    new_header = '<thead> \n <tr>'
    for c in t[0]:
        new_header += '\n <th>'+c+'</th>'
    new_header += '\n </tr> \n </thead>'
    if(new_header!=''):
        start = html.find('<thead')
        end = html.find('/thead>')
        end +=7
        header = html[start:end]
        new_html = html[0:start]+new_header+html[end:-1]
        file = open('tables/Table '+str(n)+'.html', 'w', encoding='utf-8')
        file.write(new_html)
        file.close()
    return    
    
def no_header(table,n):
    html = open('tables/Table '+str(n)+'.html', 'r', encoding='utf-8').read()
    start = html.find('<tbody')
    end = html.find('</tr>')
    end += 5
    soup = BeautifulSoup(html, 'html.parser')
    r = soup.find_all('tr')
    new_html = html[0:start]+'<thead>\n'+str(r[0])+'\n</thead> \n <tbody>'+html[end:-1]
    file = open('tables/Table '+str(n)+'.html', 'w', encoding='utf-8')
    file.write(new_html)
    file.close()
    table['header'] = 1
    return 

def get_table(t):
    labels = t.find_all('span', attrs={'class': 'label'})
    captions = t.find_all('span', attrs={'class': 'captions'})
    legend = t.find_all('p', attrs={'class': 'legend'})
    footnotes = t.find_all('dl', attrs={'class': 'footnotes'})
    for t2 in t.find_all('table'):
        header_size = 0
        if t2.find_all('thead'):
            h = t2.find_all('thead')
            header_size = len(re.findall('<tr',str(h[0])))
        extractor = Extractor(t2)
        extractor.parse()
        content = extractor.return_list()
        if(header_size!=1):
            for i in range(1,header_size):
                for j in range(0,len(content[i])):
                    if(content[0][j]!=content[i][j]):
                        content[0][j] += ' ' + content[i][j]
                    content[i][j] = ''       
        tab = {'label': labels[0].text if labels else '',
               'caption': captions[0].text.replace(labels[0].text, '') if captions else '',
               'legend': [x.text for x in legend] if legend else '',
               'footnote': [x.text for x in footnotes] if footnotes else '',
               'header' : header_size,
               'content': content
               }
    return tab

def extraction(tablesList):
    for i in range(0,len(tablesList)):
        title = 'tables/Table '+str(i+1)+'.html'
        fichier = open(title,'w',encoding='utf-8')
        fichier.write(str(tablesList[i]))
        fichier.close()
    return 
        
def header_corrections(n):
    for i in range(0,n): 
        html = open('tables/Table '+str(i+1)+'.html', 'r', encoding='utf-8').read()
        soup = BeautifulSoup(html, 'html.parser')
        t = get_table(soup)
        if t['header']==0:
            no_header(t,i+1)
        if t['header']!=1:
            header(t,i+1)
    return 


def has_unit(um,umF,cell):
    unit = cell[ cell.find( '(' )+1 : cell.find( ')' ) ]
    if(unit!=cell):
        if ((unit in um) or (unit in umF)):
            return unit
    cleara = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', ' ', ',', '±', '–', '×', '^', '-', ';', '(']
    clearb = ['.', ' ', ',', '±', '-', '×', ';', ')']
    if(len(cell)==0):
        return False
    tok = nltk.word_tokenize(cell)
    for t in range(0, len(tok)):
        if tok[t].replace('^', '') in um and re.findall('[^0-9]', tok[t].replace('^', '')):
            indice = t + 1
            unit = tok[t]
            while indice < len(tok) and \
                (tok[indice].lower() not in words.words() and len(tok[indice].lower()) > 1):
                unit = unit + ' ' + tok[indice]
                indice += 1
            indice = t-1
            while indice > 0 and \
                (tok[indice].lower() not in words.words() and len(tok[indice].lower()) > 1):
                unit = tok[indice] + ' ' + unit
                indice -= 1
            while unit and unit[0] in cleara:
                unit = unit[1:]
            while unit and unit[-1] in clearb:
                unit = unit[:-1]
            if ((unit in um) or (unit in umF)):
                return unit
    return False

def has_scientific_number(cell):
    if re.findall('([+-])?(\d)([.,])?(\d)*\s?([eE]|(x(\s)?10^))([+-])?(\d)+',cell):
        return True
    return False

def numeric_indicators(cell):
    return len(re.findall('[0-9]+[.,]?[0-9]*',cell))

def symbolic_indicators(cell):
    return len(re.findall('[a-zA-Z][/*]*',cell))


def column_type(um, umF, col):
    ans = []
    num = 0
    symb = 0
    units = []
    for i in range(0, len(col)):
        unit = False
        if (col[i]):
            unit = (has_unit(um, umF, col[i]))
        else:
            col[i] = ''
        if (unit):
            units.append(unit)
        if unit or (has_scientific_number(col[i]) or (numeric_indicators(col[i]) > symbolic_indicators(col[i]))):
            num += 1
        elif (numeric_indicators(col[i]) < symbolic_indicators(col[i])):
            symb += 1
    if (num >= symb):
        ans.append('QUANTITY')
        ans.append(units)
    else:
        ans.append('SYMBOLIC')
    return ans