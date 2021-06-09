# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 12:17:43 2021

@author: guari
"""
import os
import re
import pandas as pd
import nltk
import distance
from rdflib import *
from nltk.corpus import words 

def cleanUM(x):
    x = re.sub(r'\^', '', x)
    x = re.sub(r'-', '−', x)
    x = re.sub(r'µ', 'μ', x)
    # x = re.sub(r'\^', '', x)
    return x

def jaccard_indice(list1, list2):
    return len(set(list1).intersection(set(list2))) / len(set(list1).union(set(list2)))

def similarity_extended(list1, list2):
    return max(0.0, (min(len(list1), len(list2)) - distance.levenshtein(list1, list2)) / (min(len(list1), len(list2))))

def find_all_units(tablesList, um):
    if 'unitsVar.csv' not in os.listdir('work_files/'):
        units = []
        cleara = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', ' ', ',', '±', '–', '×', '^', '-', ';', '(']
        clearb = ['.', ' ', ',', '±', '-', '×', ';', ')']
        for table in tablesList:
            tab = table['content']
            for i in range(0,len(tab)):
                for j in range(0,len(tab[i])):
                    tok = nltk.word_tokenize(tab[i][j])
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
                            if unit not in units and unit not in um:
                                units.append(unit)
            #print(units)
        variants = {}
        for i in units:
            a = re.split(r'[. /\\()]', cleanUM(i))
            variants[i] = []
            for j in um:
                b = re.split(r'[. /\\]', cleanUM(j))
                if jaccard_indice(a, b) >= 0.4:
                    if similarity_extended(a, b) >= 0.4\
                            and [jaccard_indice(a, b), j, similarity_extended(a, b)] not in variants[i]:
                        variants[i].append([similarity_extended(a, b), j, jaccard_indice(a, b)])
        df = pd.DataFrame(None, columns=['UMnew', 'UMrto', 'Scores'])
        for i in variants:
            if variants[i]:
                #print('RETENU',variants[i])
                df = df.append({'UMnew': i,
                                'UMrto': max(variants[i])[1],
                                'Scores': (max(variants[i])[0], max(variants[i])[2])},
                               ignore_index=True)
    else:
        df = pd.read_csv('work_files/unitsVar.csv', encoding='utf-8')
        del df['Unnamed: 0']
    return df

def find_all_quantity_concepts():
    if 'quantityConcepts.csv' not in os.listdir('work_files/'):
         g = Graph()
         g = g.parse('input_files/TRANSMAT.owl')
         onto = open('input_files/TRANSMAT.owl', encoding='utf-8').read()
         relations_arguments = g.query("SELECT DISTINCT ?relation ?argument WHERE {"
                                          "?relation rdfs:subClassOf ?perm ."
                                          "?relation ?child ?noeud ."
                                          "{?noeud ?primar ?argument} UNION {?noeud ?second ?argument}"
                                          "}",
                                          initBindings={
                                              'primar': URIRef('http://www.w3.org/2002/07/owl#allValuesFrom'),
                                              'second': URIRef('http://www.w3.org/2002/07/owl#someValuesFrom')})
         
         df = pd.DataFrame(None, columns=['Relation', 'Concept','OntoProcess'])
         relations = []
         arguments = []
         for ra in relations_arguments:
             relations.append(ra[0].split('#')[-1])
             arguments.append(ra[1].split('#')[-1])
             spaces = len(re.findall('\n +?<skos:Concept rdf:ID="' + ra[1].split('#')[-1] + '">', onto)[0].split('<')[0][
                            1:]) if re.findall('\n +?<skos:Concept rdf:ID="' + ra[1].split('#')[-1] + '">', onto) else 0
             area = re.findall(' ' * spaces + '<skos:Concept rdf:ID="' + ra[1].split('#')[
                 -1] + '">.+?' + '\n' + ' ' * spaces + '</skos:Concept>\n', onto, re.DOTALL)
             if area:
                 if 'hasNumericalValue' in ' '.join(re.findall('<owl:onProperty rdf:resource=".+?/>\n', area[0])):
                     df = df.append({'Relation': ra[0].split('#')[-1], 'Concept': ra[1].split('#')[-1], 'OntoProcess':ra[1]},
                                ignore_index=True)
    else:
        df = pd.read_csv('work_files/quantityConcepts.csv', encoding='utf-8')
        del df['Unnamed: 0']
    return df

def find_all_symbolic_concepts():
    if 'symbolicConcepts.csv' not in os.listdir('work_files/'):
         g = Graph()
         g = g.parse('input_files/TRANSMAT.owl')
         onto = open('input_files/TRANSMAT.owl', encoding='utf-8').read()
         relations_arguments = g.query("SELECT DISTINCT ?relation ?argument WHERE {"
                                          "?relation rdfs:subClassOf ?perm ."
                                          "?relation ?child ?noeud ."
                                          "{?noeud ?primar ?argument} UNION {?noeud ?second ?argument}"
                                          "}",
                                          initBindings={
                                              'primar': URIRef('http://www.w3.org/2002/07/owl#allValuesFrom'),
                                              'second': URIRef('http://www.w3.org/2002/07/owl#someValuesFrom')})
         
         df = pd.DataFrame(None, columns=['Relation', 'Concept','OntoProcess'])
         relations = []
         arguments = []
         typee = []
         for ra in relations_arguments:
             relations.append(ra[0].split('#')[-1])
             arguments.append(ra[1].split('#')[-1])
             spaces = len(re.findall('\n +?<skos:Concept rdf:ID="' + ra[1].split('#')[-1] + '">', onto)[0].split('<')[0][
                            1:]) if re.findall('\n +?<skos:Concept rdf:ID="' + ra[1].split('#')[-1] + '">', onto) else 0
             area = re.findall(' ' * spaces + '<skos:Concept rdf:ID="' + ra[1].split('#')[
                 -1] + '">.+?' + '\n' + ' ' * spaces + '</skos:Concept>\n', onto, re.DOTALL)
             if area:
                 if 'hasNumericalValue' not in ' '.join(re.findall('<owl:onProperty rdf:resource=".+?/>\n', area[0])):
                     df = df.append({'Relation': ra[0].split('#')[-1], 'Concept': ra[1].split('#')[-1], 'OntoProcess':ra[1]},
                                ignore_index=True)
    else:
        df = pd.read_csv('work_files/symbolicConcepts.csv', encoding='utf-8')
        del df['Unnamed: 0']
    return df

def get_results_qc(all_qc):
    if 'resultsConcepts.csv' not in os.listdir('work_files/'):
        df = pd.DataFrame(None, columns=['Relation', 'Concept'])
        relations = list(all_qc.Relation.values)
        qc_concepts = list(all_qc.Concept.values)
        df = df.append({'Relation': 'impact_factor_component_relation', 'Concept': 'component_qty_value'}, ignore_index=True)
        df = df.append({'Relation': 'matrix_properties_thickness', 'Concept': 'thickness'},ignore_index=True)
        df = df.append({'Relation': 'matrix_properties_ph', 'Concept': 'ph'}, ignore_index=True)
        df = df.append({'Relation': 'matrix_properties_aw', 'Concept': 'aw'}, ignore_index=True)
        df = df.append({'Relation': 'matrix_properties_water_content', 'Concept': 'water_content'}, ignore_index=True)

        for i in range(0,len(relations)):
            if(relations[i].replace('_relation','')==qc_concepts[i]):
                df = df.append({'Relation': relations[i], 'Concept': qc_concepts[i]},ignore_index=True)
    else:
        df = pd.read_csv('work_files/resultsConcepts.csv', encoding='utf-8')
        del df['Unnamed: 0']
    return df
