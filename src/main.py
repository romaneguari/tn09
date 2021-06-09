# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 16:27:57 2021

@author: guari
"""
import pretreatment
import ontoCrawler
import files 
import quantity
import symbolic
import relation
import os
from tqdm import tqdm
from bs4 import BeautifulSoup

def main():

    """
         ----------------------------------------------
        |                                              |
        |         Pré-traitement des tableaux          |
        |                                              |
         ----------------------------------------------
    """
    html_tablesList = []
    tablesList = []
    for file in tqdm(os.listdir('html/')):
         print('\n\nFile title : ',file)
         html = open('html/'+file, 'r', encoding='utf-8').read()
         html = pretreatment.clean_html(html)
         soup = BeautifulSoup(html, 'html.parser')
         soup = soup.article
         tables = soup.find_all('div', attrs={'class': 'tables'})
         for t in tables:
             html_tablesList.append(t)
             tablesList.append(pretreatment.get_table(t))

    #une condition à faire (si les tableaux déjà dans tables je ne fais pas ça)
    pretreatment.extraction(html_tablesList)
    pretreatment.header_corrections(len(html_tablesList))
    
    """
         ----------------------------------------------
        |                                              |
        |        Creation des fichiers utiles:         |
        |                                              |
         ----------------------------------------------
    """

    """
    um contient l'ensemble des unités reconnu par l'ontologie
    """
    um = ontoCrawler.getAllUnits()
    um.to_csv('work_files/unitsRTO.csv', encoding='utf-8')

    """
        umF contient l'ensemble des unités identifiées dans le tableau 
        et qui semble correspondre à une unité de l'ontologue
    """
    #A AMELIORER POUR + D'UNITES DES PERMEABILITES
    umF = files.find_all_units(tablesList,list(um.AltLabel.values))
    umF.to_csv('work_files/unitsVar.csv', encoding='utf-8')

    """
        all_qc donne pour un concept relation l'ensemble des concepts 
        numériques associés
    """
    all_qc = files.find_all_quantity_concepts()
    all_qc.to_csv('work_files/quantityConcepts.csv', encoding='utf-8')

    """
        results_qc donne pour un concept relation son concept résultat
    """
    results_qc = files.get_results_qc(all_qc)
    results_qc.to_csv('work_files/resultsConcepts.csv', encoding='utf-8')

    """
        all_sc donne pour un concept relation l'ensemble des concepts 
        symboliques associés
    """
    all_sc = files.find_all_symbolic_concepts()
    all_sc.to_csv('work_files/symbolicConcepts.csv', encoding='utf-8')

    """
        desambig donne le ou les concepts numériques associés à une unité
    """
    desambig = ontoCrawler.getAssociation()
    desambig.to_csv('work_files/desambig.csv', encoding='utf-8')
    
    ontoSymb = list(all_sc.OntoProcess.values)
    cSymb = list(all_sc.Concept.values)
    symbolic.symbolic_concepts(ontoSymb,cSymb)
    
    """
         ----------------------------------------------
        |                                              |
        |           Traitement des tableaux            |
        |                                              |
         ----------------------------------------------
    """
    k = 1
    for table in tqdm(tablesList):
        html = open('tables/Table '+str(k)+'.html', 'r', encoding='utf-8').read()
        html = pretreatment.clean_html(html)
        soup = BeautifulSoup(html, 'html.parser')
        t = table['content']
        col_type = []
        ncol = len(t[0])
        nlines = len(t)
        symb = 0
        res = []

        for j in range(0,ncol):
            col = []
            for i in range(0,nlines):
                t[i][j] = pretreatment.clean(t[i][j])
                col.append(t[i][j])
            res = pretreatment.column_type(list(um.AltLabel.values), list(umF.UMnew.values), col)
            col_type.append(res)
        if (res == 'Symbolique'):
            symb += 1
        table['type'] = col_type
        ii = 0

        for j in range(0,ncol):
            if(col_type[j][0])=="SYMBOLIC":
                t[0][j]='<sc>'+t[0][j]+'</sc>'
            else:
                t[0][j] = '<qc>'+t[0][j] + '</qc>'
        new_table_content = '<table>'
        for i in range(0,nlines):
            new_table_content+='<tr>'
            for j in range(0,ncol):
                if(i==0):
                    new_table_content +='<th>'
                    new_table_content += t[i][j]
                    new_table_content += '</th>'
                else:
                    new_table_content +='<td>'
                    new_table_content += t[i][j]
                    new_table_content += '</td>'
            new_table_content+='</tr>'
        new_table_content += '<table>'
        new_table_soup = BeautifulSoup(new_table_content,'html.parser')

        #Etape 2 : association d'un concept à une colonne
        qc_list = []
        sc_list = []
        if (symb == ncol):
            print('\n',table['caption'],"tableau non traité car que des colonnes symboliques",ncol)
        else:
            print('\n',table['caption'],"en cours de traitement")
            col_type = table['type']
            index_sym = 0
            index_num = 0
            symbolic_tags = new_table_soup.find_all('sc')
            numeric_tags = new_table_soup.find_all('qc')
            for x in range(0,len(col_type)):
                col = []
                for i in range(0,nlines):
                    col.append(pretreatment.clean(t[i][x]))
                if(col_type[x][0]=='SYMBOLIC'):
                    if(len(symbolic_tags)>index_sym):
                        sc = symbolic_tags[index_sym]
                        sc_type = symbolic.symbolic_final_score(col)
                        sc['type']= sc_type
                        sc_list.append(sc_type)
                        index_sym+=1
                        if(sc_type != ""):
                            for i in range(0,nlines):
                                id = symbolic.getId(sc_list)
                                t[i][x] = '<ai type="'+sc_type.replace('.csv','')+'" id="'+str(id)+'">'+t[i][x]+'</ai>'
                elif (col_type[x][0]=='QUANTITY'):
                    if(len(numeric_tags)>index_num):
                        nc = numeric_tags[index_num]
                        nc_type = quantity.final_scores(col,col_type[x],all_qc,desambig)
                        nc['type'] = nc_type[0]
                        qc_list.append(nc_type[0])
                        index_num+=1
                        if (nc_type[0] != ""):
                            for i in range(0, nlines):
                                id = symbolic.getId(qc_list)
                                if(len(nc_type)>1):
                                    t[i][x] = '<ai type="' + nc_type[0] + '" id="' + str(id-1) + '" unit="'+nc_type[1]+'">' + t[i][x] + '</ai>'
                                else:
                                    t[i][x] = '<ai type="' + nc_type[0] + '" id="' + str(id-1) + '">' + t[i][x] + '</ai>'



        # Etape 3 : association d'une relation à une table

        valid_rc_list = []
        valid_rc_list = relation.getrclist(qc_list, results_qc)
        signature_tab = qc_list + sc_list
        caption = table['caption']
        rc_list = relation.score_final(valid_rc_list, signature_tab, caption, all_qc, all_sc, len(qc_list))
        new_table_content = '<span class="captions">'
        new_table_content += '<span>'

        # Etape 4 : Instanciations
        for rc in rc_list:
            new_table_content += '<rc type = '+str(rc)+ ' ></rc>'
        new_table_content += '<p><span class ="label"> Table '+ str(k) +'</span>'
        new_table_content += str(caption)
        new_table_content += '</p> </span> </span>'
        new_table_content += '<table>'
        new_table_content += str(new_table_soup.tr)
        for i in range(0,nlines):
            new_table_content+='<tr>'
            new_table_content+= relation.addTags(signature_tab,rc_list,results_qc,all_qc,all_sc)
            for j in range(0,ncol):
                if(i!=0):
                    new_table_content +='<td>'
                    new_table_content += t[i][j]
                    new_table_content += '</td>'
            new_table_content+='</tr>'
        new_table_content += '<table>'
        new_table_soup = BeautifulSoup(new_table_content,'html.parser')
        new_table_soup.new_tag('ai')

        title = 'tables/Table '+str(k)+'.html'
        fichier = open(title,'w',encoding='utf-8')
        fichier.write(new_table_soup.prettify(formatter="html"))
        fichier.close()
        k+=1

if __name__ == '__main__':
    main()  