# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 17:45:26 2021

@author: guari
"""

import distance 
import re 
from rdflib import *
import ontoCrawler 
import string
import nltk 
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from stop_words import get_stop_words

stemmer = nltk.stem.porter.PorterStemmer()
remove_punctuation_map = dict((ord(char),None) for char in string.punctuation)
stop_words = get_stop_words('en')
warnings.filterwarnings("ignore") #to ignore stopwords warning

def stem_tokens(text):
    return [stemmer.stem(token) for token in text]

def normalize(text):
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

def cosine_sim(text1,text2):
    vectorizer = TfidfVectorizer(
        tokenizer = normalize,
        stop_words = stop_words,
        ngram_range = (1,1))
    tfidf = vectorizer.fit_transform([text1,text2])
    return ((tfidf * tfidf.T).A)[0,1]


def jaccard_indice(list1, list2):
    return len(set(list1).intersection(set(list2))) / len(set(list1).union(set(list2)))

def similarity_extended(list1, list2):
    return max(0.0, (min(len(list1), len(list2)) - distance.levenshtein(list1, list2)) / (min(len(list1), len(list2))))

def score_unit(u,desambig):
    concepts = []
    candidates = {}
    if not u:
        return candidates
    units = list(desambig.Unit.values)
    if u in units:
        indexes = desambig[desambig['Unit']==u].index.tolist()
        for i in range(0,len(indexes)):
            concepts.append(desambig['Concept'][indexes[i]])
    else:
        for unit in units:
            if jaccard_indice(unit, u) >= 0.4 and similarity_extended(unit, u) >= 0.4:
                indexes = desambig[desambig['Unit']==unit].index.tolist()
                for i in range(0,len(indexes)):
                    newConcept = desambig['Concept'][indexes[i]]
                    if newConcept not in concepts:
                        concepts.append(desambig['Concept'][indexes[i]])
    for i in concepts:
        candidates[i]=(1/len(concepts))
    return candidates

#scores_unit est une liste de dico de concept candidat 
def numeric_scoreContent(scores_unit):
    numericColumn_scoresContent = {}
    for i in range(0,len(scores_unit)):
        for key, value in scores_unit[i].items():
            if key in numericColumn_scoresContent:
                if(value > numericColumn_scoresContent[key]):
                    numericColumn_scoresContent[key] = value
            else:
                numericColumn_scoresContent[key] = value
    return numericColumn_scoresContent
 
def score_title(cell,qc):
    cell = re.sub('\^a','',cell)
    cell = re.sub('\^b','',cell)
    cell = re.sub('\^c','',cell)
    g = Graph()
    g = g.parse('input_files/TRANSMAT.owl')
    scoresTitle = {}
    concepts = []
    for q in qc.Concept.values:
        if q not in concepts:
            concepts.append(q)
    labels = []
    for o in qc.OntoProcess.values:
        if o not in labels:
            labels.append(o)
         
    for i in range(0,len(concepts)):
        res = 0
        label = ontoCrawler.labelA(labels[i], g)
        for l in label:
            res = max(cosine_sim(cell,l[0].value),res)
            if(l[1]):
                res = max(cosine_sim(cell,l[1].value),res)
        if(res!=0.0):
            scoresTitle[concepts[i]]=res
    return scoresTitle

#scores est un dico de concepts candidats 
def advantage(scores):
    best = 0.0
    secondBest = 0.0
    concept = ''
    res=0
    for key,value in scores.items():
        if value>best:
            secondBest = best
            best = value
            bestconcept = key
    if(best!=0.0):
        res = (best-secondBest)/best
        if(res>0.1):
            concept = bestconcept
    return concept
    
def scoreFinal(score_title,score_content):
    return (1-(1-score_title)*(1-score_content))


def final_scores(col,unit,qc,desambig):
    candidates = []
    for u in unit[1]:
        candidates.append(score_unit(u,desambig))
    content_scores = numeric_scoreContent(candidates)
    title_scores = score_title(col[0],qc)
    finalScores = {}
    for concept in qc.Concept.values:
        if concept in title_scores and concept in content_scores:
            finalScores[concept] = scoreFinal(title_scores[concept], content_scores[concept])
        elif concept in title_scores and concept not in content_scores:
            finalScores[concept] = scoreFinal(title_scores[concept], 0)
        elif concept in content_scores and concept not in title_scores:
            finalScores[concept] = scoreFinal(0, content_scores[concept])
    #surement un moyen plus rapide
    final_concept = []
    final_concept.append(advantage(finalScores))
    concepts_list = list(desambig.Concept.values)
    units_list = list(desambig.Unit.values)
    units = []
    for i in range(0, len(concepts_list)):
        if final_concept[0] == concepts_list[i]:
            units.append(units_list[i])
    for u in unit[1]:
        if u in units:
            final_concept.append(u)
    return final_concept

def getId(qc_list):
    qc = qc_list[len(qc_list)-1]
    id=0
    for concept in qc_list:
        if(concept==qc):
            id+=1
    return id