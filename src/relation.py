from multiprocessing import Pool
import string
import nltk
import collections
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from stop_words import get_stop_words

"""
Similarité cosinus
"""
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

"""
Fonction getrclist
Param qc_list : liste des concepts numériques apparaissant dans le tableau
Param results_qc : liste de tous les concepts numériques étant des concepts résultats 
Retourne la liste des relations concepts pouvant apparaitre dans le tableau si le concept 
resultat de la relation est présent dans la signature du tableau 
"""
def getrclist(qc_list, results_qc):
    rc = []
    relation_concepts = list(results_qc.Relation.values)
    quantity_concepts_associated = list(results_qc.Concept.values)
    for relconcept in qc_list:
        for i in range(0,len(quantity_concepts_associated)):
            if(relconcept==quantity_concepts_associated[i]):
                    rc.append(relation_concepts[i])
    return rc

"""
Fonction score_content 
Param signature_tab : liste contenant la signature du tableau 
Param r : liste contenant la signature de la relation r
Retourne le score content qui correspond au nombre de concept de l'intersection des 
concepts dans le tableau et des concepts de la relation r sur le nombre de concepts 
dans la relation r
"""
def score_content(signature_tab, r):
    inter=0
    sign_r= len(r)
    for concept in signature_tab:
        if concept in r:
            inter+=1
    return inter/sign_r

"""
Fonction advantage 
Param scores : dictionnaire des relations et leurs score final associées
Param n : nb de concept résultat
Retourne entre 0 à n relations si elles possèdent un écart significatif avec celle d'après
"""
def advantage(scores,n):
    concept = []
    i = 0
    while(i<n):
        best = 0.0
        secondBest = 0.0
        res = 0
        for key,value in scores.items():
            if value>best:
                secondBest = best
                best = value
                bestconcept = key
        if(best!=0.0):
            res = (best-secondBest)/best
            if(res>0.1):
                concept.append(bestconcept)
                scores[bestconcept]=0;
        i+=1
    return concept

"""
Fonction score_final
Param valid_rc_list
Retourne une liste des concepts relations retenus pour le tableau 
"""
def score_final(valid_rc_list,signature_tab,caption,qc,sc,n):
    relations_qc = list(qc.Relation.values)
    qc_concepts_associated = list(qc.Concept.values)
    relations_sc = list(sc.Relation.values)
    sc_concepts_associated = list(sc.Concept.values)
    final_scores = {}
    for rel in valid_rc_list:
        sign_rel = []
        for i in range(0,len(relations_qc)):
            if(relations_qc[i]==rel):
                sign_rel.append(qc_concepts_associated[i])
        for i in range(0,len(relations_sc)):
            if(relations_sc[i]==rel):
                sign_rel.append(sc_concepts_associated[i])
        score_c = score_content(signature_tab, sign_rel)
        score_caption = cosine_sim(caption, rel.replace('_', ' '))
        final_scores[rel] = 1-(1-score_caption)*(1-score_c)
    return advantage(final_scores,n)

def addTags(signature_tab,rc_list,results_qc,qc,sc):
    #Dictionnaire relation : nb de fois qu'elle apparait
    relations_tab = {}
    relations_results_qc = list(results_qc.Relation.values)
    qc_results_concepts_associated = list(results_qc.Concept.values)
    for rel in rc_list:
        n = 0
        #try catch
        i = relations_results_qc.index(rel)
        r = qc_results_concepts_associated[i]
        for c in signature_tab:
            if(c==r):
                n+=1
        relations_tab[rel] = n
    relations_qc = list(qc.Relation.values)
    qc_concepts_associated = list(qc.Concept.values)
    relations_sc = list(sc.Relation.values)
    sc_concepts_associated = list(sc.Concept.values)
    result = ''
    for rel in rc_list:
        sign_rel = []
        for i in range(0, len(relations_qc)):
            if (relations_qc[i] == rel):
                sign_rel.append(qc_concepts_associated[i])
        for i in range(0, len(relations_sc)):
            if (relations_sc[i] == rel):
                sign_rel.append(sc_concepts_associated[i])
        j = relations_tab[rel]
        while(j>0):
            i = relations_results_qc.index(rel)
            r = qc_results_concepts_associated[i]
            result += '<rc type="'+rel+'" id="'+str(j-1)+'">'
            result += '<ai type="'+r+'" id="'+str(j-1)+'"></ai>'
            instances = []
            for c1 in sign_rel:
                for c2 in signature_tab:
                    if(c1==c2 and c2!=r):
                        instances.append(c2)
            for ins in instances:
                result += '<ai type="' +ins+ '"></ai>'
            result+='</rc>'
            j=j-1
    return result








