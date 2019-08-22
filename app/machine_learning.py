# -*- coding: utf-8 -*-

from ast import literal_eval
from bs4 import BeautifulSoup
from pandas import Series, DataFrame
from sklearn import svm
from sklearn.metrics import make_scorer, accuracy_score
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
import numpy as np
import os
import pandas as pd
import requests

import app.conn
import app.filters
import app.log
import app.utilities

logger = app.log.setup_logger(__name__)

#------------------------------------------------------------

def support_vector_machine(data, target):
    """Prépare le classifier du machine learning

    Parameters
    ----------
    data : pandas.DataFrame
        Dataset
    target : pandas.Series
        Valeur cible

    Return
    ------
    classifier : sklearn.svm.classes.SVC
        Classifier du machine learning
    """
    X_train, X_test, y_train, y_test = train_test_split(data, target, test_size=0.5, random_state=0)

    tuned_params = [{'kernel': ['rbf'], 'gamma': [1, 0.1, 1e-2, 1e-3, 1e-4], 'C': [1, 10, 100, 1000]}, 
                    {'kernel': ['linear'], 'C': [1, 10, 100, 1000]}]
    grid_search = GridSearchCV(svm.SVC(probability=True), tuned_params, cv=5)
    grid_search.fit(X_train, y_train)
    logger.info(f"Les mieux parametres pour le machine learning sont : {grid_search.best_params_}")
    classifier = grid_search.best_estimator_
    scores = cross_val_score(classifier, X_test, y_test, cv=5)
    logger.info("Précision: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))
    logger.new_formatter(mode="newline")
    return classifier


#------------------------------------------------------------

def get_cmds():
    """Obtien les ids de commandes des clients sélectionnés
    Utilisé une seule fois. Processus trop lente. Il faut d'abord faire de manipulations dans le backoffice via le browser.
    Les données de sortie sont dans les fichiers 'bad_cmds.csv' et 'good_cmds.csv'

    Return
    ------
    cmds : list
        Toutes les ids des commandes trouvées de tous les clients sélectionés
    """

    cmds = []

    session_info = app.conn.connexion()
    session = session_info[0]
    headers = session_info[1]

    url = 'https://www.espace-contention.com/superadmin/clients-liste.html'

    client_page = session.get(url, headers=headers)
    soup = BeautifulSoup(client_page.text, "html.parser")
    anchor_list = soup.find(id='anchor_liste')
    clients = anchor_list.find_all(attrs={"class": "list_row"})

    refs = []
    for item in clients:
        if item.a != None:
            refs.append(item.a)

    if refs:
        links = list(value.get('href') for value in refs)
        links = list(value for value in links if 'commandes-gestion.html' in value)

        all_orders = []
        i = 1
        for link in links:
            #print(link,i)
            url = f"https://www.espace-contention.com/superadmin/{link}"

            orders_page = session.get(url, headers=headers)
            soup = BeautifulSoup(orders_page.text, "html.parser")
            anchor_list = soup.find(id='anchor_liste')
            orders = anchor_list.find_all(attrs={"class": "list_row"})
            orders = list(value.text.split()[0] for value in orders)
            all_orders.append(orders)
            i += 1

        cmds = list(order for orders in all_orders for order in orders)

    return cmds


#------------------------------------------------------------

def get_raw_data(cmds):
    """Obtien les info de chaque commande
    Utilisé une seule fois. Processus TROP TROP lente.
    Les données de sortie sont dans les fichiers 'bad_cmds_raw_data.csv' et 'good_cmds_raw_data.csv'

    Parameters
    ------
    cmds : list
        Ids de commandes

    Return
    ------
    data : dict
        Toutes les info de toutes les commandes
    """
    data = {}

    i = 1
    for id_cmd in cmds['id_cmd']:
        #print(id_cmd, i)
        cmd = app.utilities.get_request(f"api/orders/filter/id/{str(id_cmd)}")

        for key in cmd:
            cmd = cmd[key]
        data[str(id_cmd)] = cmd
        i += 1

    return data

#------------------------------------------------------------

def get_parsed_data(commandes):
    """Obtien les données relevantes et transformées de chaque commande relevante
    Les données de sortie sont dans les fichiers 'bad_cmds_parsed_data.csv' et 'good_cmds_parsed_data.csv'

    Parameters
    ------
    commandes : dict
        Collection des données des commandes

    Return
    ------
    cmds : pandas.Dataframe
        Collection des données des commandes
    """

    parsed = app.utilities.mining(commandes)
    cmds = parsed[0]
    prods = parsed[1]

    parsed = app.filters.filtrage_fraude(cmds,prods)
    cmds = parsed[0]
    prods = parsed[1]

    cmds = cmds.drop_duplicates(subset='name_client')
    to_del = []
    for key in prods:
        if key not in cmds.index:
            to_del.append(key)
    for item in to_del:
        del prods[item]

    nbrjours = 3
    path = app.utilities.get_path("docs/arnaque/depts_risque.csv")
    depts_risque = pd.read_csv(path, index_col='code')
    path = app.utilities.get_path("docs/arnaque/prods_risque.csv")
    prods_risque = pd.read_csv(path, index_col='id')

    cmds = app.utilities.transform(cmds, prods, depts_risque['risque'], prods_risque, nbrjours)

    return cmds


#------------------------------------------------------------

def prepare_data():
    """Prépare les données qui seront le support du machine learning

    Return
    ------
    (data, target) : tuple
        Dataset et valeur cible du machine learning
    """

    #--------- Etape 1 -----------
    #Ces deux commandes ne fonctionneront pas sans d'abord faire des modifications dans le back-office via browser
    #bad_cmds = get_cmds()
    #good_cmds = get_cmds()

    #bad_cmds = DataFrame(bad_cmds.values(), index=bad_cmds.keys(), columns=['id_cmd'])
    #bad_cmds.index.name = 'index'
    #path = app.utilities.get_path("docs/arnaque/bad_cmds.csv")
    #bad_cmds.to_csv(path)
    #good_cmds = DataFrame(good_cmds.values(), index=good_cmds.keys(), columns=['id_cmd'])
    #good_cmds.index.name = 'index'
    #path = app.utilities.get_path("docs/arnaque/good_cmds.csv")
    #good_cmds.to_csv(path)

    #--------- Etape 2 -----------
    #path = app.utilities.get_path("docs/arnaque/bad_cmds.csv")
    #bad_cmds = pd.read_csv(path, index_col='index')
    #path = app.utilities.get_path("docs/arnaque/good_cmds.csv")
    #good_cmds = pd.read_csv(path, index_col='index')

    #--------------------
    
    #bad_cmds_data = get_raw_data(bad_cmds)
    #good_cmds_data = get_raw_data(good_cmds)

    #path = app.utilities.get_path("docs/arnaque/bad_cmds_raw_data.csv")
    #DataFrame(bad_cmds_data).to_csv(path)
    #path = app.utilities.get_path("docs/arnaque/good_cmds_raw_data.csv")
    #DataFrame(good_cmds_data).to_csv(path)

    #--------- Etape 3 -----------

    #path = app.utilities.get_path("docs/arnaque/bad_cmds_raw_data.csv")
    #bad_cmds_data = pd.read_csv(path, index_col=0)
    #path = app.utilities.get_path("docs/arnaque/good_cmds_raw_data.csv")
    #good_cmds_data = pd.read_csv(path, index_col=0)

    #bad_cmds_data = bad_cmds_data.dropna(axis=1, subset=['products'])
    #good_cmds_data = good_cmds_data.dropna(axis=1, subset=['products'])

    #bad_cmds_data = bad_cmds_data.to_dict()
    #good_cmds_data = good_cmds_data.to_dict()

    #for key in bad_cmds_data:
    #    cmd = bad_cmds_data[key]
    #    cmd['delivery_address'] = literal_eval(cmd['delivery_address'])
    #    cmd['shipping'] = literal_eval(cmd['shipping'])
    #    cmd['payment'] = literal_eval(cmd['payment'])
    #    cmd['customer_info'] = literal_eval(cmd['customer_info'])
    #    cmd['products'] = literal_eval(cmd['products'])

    #for key in good_cmds_data:
    #    cmd = good_cmds_data[key]
    #    cmd['delivery_address'] = literal_eval(cmd['delivery_address'])
    #    cmd['shipping'] = literal_eval(cmd['shipping'])
    #    cmd['payment'] = literal_eval(cmd['payment'])
    #    cmd['customer_info'] = literal_eval(cmd['customer_info'])
    #    cmd['products'] = literal_eval(cmd['products'])

    #--------------------

    #bad_cmds_data = get_parsed_data(bad_cmds_data)
    #good_cmds_data = get_parsed_data(good_cmds_data)

    #path = app.utilities.get_path("docs/arnaque/bad_cmds_parsed_data.csv")
    #bad_cmds_data.to_csv(path)
    #path = app.utilities.get_path("docs/arnaque/good_cmds_parsed_data.csv")
    #good_cmds_data.to_csv(path)

    #--------- Etape 4 -----------

    path = app.utilities.get_path("docs/arnaque/bad_cmds_parsed_data.csv")
    bad_cmds_data = pd.read_csv(path, index_col='id_cmd')
    path = app.utilities.get_path("docs/arnaque/good_cmds_parsed_data.csv")
    good_cmds_data = pd.read_csv(path, index_col='id_cmd')

    #--------------------

    bad_cmds_data['label'] = True
    good_cmds_data['label'] = False

    frames = [bad_cmds_data, good_cmds_data.head(len(bad_cmds_data))]
    cmds = pd.concat(frames)
    cmds = cmds.sort_index()

    target = Series(cmds['label'])
    data = cmds.drop('label', axis=1)

    params = app.utilities.get_config_data()["detection_params"]

    # similarité nom et mail
    if not params["Correlation Nom/Mail"]:
        data = data.drop(['name_email'], axis=1)

    # ignore frais gratuit
    if not params["Ignorer Frait Gratuit"]:
        data = data.drop(['ignore_frait_gratuit'], axis=1)

    # livraison chez le commercant ou bureau de poste
    if not params["Livraison Commerçant/Poste"]:
        data = data.drop(['livraison_commercant'], axis=1)

    # departements francais de risque
    if not params["Départements Risque"]:
        data = data.drop(['dept_risque'], axis=1)

    # produits de risque
    if not params["Produits Risque"]:
        data = data.drop(['produits_risque'], axis=1)

    # client history : premiere_commande ; multiples_commandes
    if not params["Historique Client"]:
        data = data.drop(['premiere_cmd', 'cmds_multiples'], axis=1)

    return (data, target)