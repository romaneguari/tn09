# -*- coding: utf-8 -*-
"""
Created on Thu Jan 28 14:15:27 2021

@author: guari
"""

import os
import files 
import ontoCrawler

import pandas as pd
from rdflib import *
from multiprocessing import Pool
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

def sim(x):
    return cosine_sim(x[0], x[1])

def score_title(cell,concept):
    df = pd.read_csv('work_files/concepts/'+concept, encoding='utf-8')
    terms = list(df.term.values)
    new = []
    for t in terms:
        new.append([cell,t])
    with Pool(7) as p:
        res = p.map(sim, new)
    if(res):
        return max(res)
    return 0

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
    #print(res)
    return concept

def score_cell(cell, concept):
    df = pd.read_csv('work_files/concepts/'+concept, encoding='utf-8')
    terms = list(df.term.values)
    print(terms)
    new = []
    for t in terms:
        new.append([cell,t])
    with Pool(7) as p:
        res = p.map(sim, new)
    score = 0
    for r in res:
        score += r
    return score 

def score_content(col_content,associated_concepts):
    candidates = {}
    for concept in os.listdir('work_files/concepts'):
        candidates[concept] = 0
        for c in associated_concepts:
            if(c == concept):
                candidates[concept] += 1
        candidates[concept] = candidates[concept]/len(col_content)
    return candidates

def score_final(score_title,score_content):
    return (1-(1-score_title)*(1-score_content))

def parcoursTermes(c,g,terms):
    argument_child = g.query("SELECT ?x WHERE {"
                             "?x rdfs:subClassOf ?arg"
                             "}",
                             initBindings={'arg': URIRef(c)})
    if(argument_child):
        for a in argument_child:
            terms.append(a[0])
            parcoursTermes(a[0], g,terms)
    else:
        return terms
    return terms

def symbolic_concepts(ontoSymb,cSymb):
    g = Graph()
    g.parse('input_files/TRANSMAT.owl')
    o = []
    c = []
    for i in range(0,len(cSymb)):
        if cSymb[i] not in c:
            c.append(cSymb[i])
    for i in range(0,len(ontoSymb)):
        if ontoSymb[i] not in o:
            o.append(ontoSymb[i])
    sConcepts = [c,o]
    for i in range(0,len(sConcepts[0])):
        if sConcepts[0][i]+'.csv' not in os.listdir('work_files/concepts'):
            terms = []
            terms = parcoursTermes(sConcepts[1][i],g,terms)
            df = pd.DataFrame(None, columns=['term'])
            for t in terms:
                label = ontoCrawler.labelA(t, g)
                for l in label:
                    df = df.append({'term': l[0]}, ignore_index=True)
            df.to_csv('work_files/concepts/'+sConcepts[0][i]+'.csv', encoding='utf-8')
    return 

def symbolic_final_score(col):
    associated_concept = []
    for i in range (1,len(col)):
        scores = {}
        for concept in os.listdir('work_files/concepts'):
            print(concept)
            scores[concept] = score_cell(col[i],concept)
        associated_concept.append(advantage(scores))
    content = score_content(col[1:],associated_concept)
    final_scores = {}
    for concept in os.listdir('work_files/concepts'):
        title = score_title(col[0], concept)
        final_scores[concept] = score_final(title,content[concept])
    print(final_scores)
    return advantage(final_scores)

def getId(sc_list):
    sc = sc_list[len(sc_list)-1]
    id=0
    for concept in sc_list:
        if(concept==sc):
            id+=1
    return id




def main():

    col = ['titre','nanocomposite','banana','meat']
    print(symbolic_final_score(col))
        
    
if __name__ == '__main__':
    main()
      