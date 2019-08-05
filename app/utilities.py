# -*- coding: utf-8 -*-

from ast import literal_eval
from bs4 import BeautifulSoup
from datetime import datetime
from pandas import Series, DataFrame
import jellyfish
import json
import numpy as np
import os
import pandas as pd
import requests
import unicodedata
import webbrowser

import app.conn
#import app.log

#logger = app.log.setup_logger(__name__)

#------------------------------------------------------------
def change_mode(self, state, children):
    self.mode_teste = state
    for child in children:
        change_mode(child, state, child.children)

#------------------------------------------------------------
def get_path(file):
    """
    file : relative path from root of project
    """
    cwd = os.path.abspath(os.path.dirname(__file__))
    parent_dir = os.path.join(cwd, "..")
    path = os.path.join(parent_dir, file)
    return path

#------------------------------------------------------------
def open_file(file):
    try:
        path = get_path(file)
        if os.path.exists(path):
            webbrowser.open(path)
        else:
            logger.warning(f"Fichier {path} n'existe pas")
    except Exception as e:
            logger.exception(f"Erreur d'ouverture du fichier : {e}")

#------------------------------------------------------------
def get_config_data():

    cwd = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(cwd, "../docs/config_data.csv")

    config_data = pd.read_csv(path, index_col="parameter")
    config_data = config_data.to_dict()
    config_data = config_data['value']
    config_data['detection_params'] = literal_eval(config_data['detection_params'])

    return config_data

#------------------------------------------------------------

cle_api = get_config_data()['cle_api']

#------------------------------------------------------------
#def output(message, print_statement=True, log_statement=True, type_log='info'):
#    if message == '\n':
#        print(message)
#        logger.new_formatter(mode="newline")


#    if print_statement:
#        print(message)

#    if log_statement:

#------------------------------------------------------------
def get_request(request):
    url = f"http://pharmashopi.com/{request}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

#------------------------------------------------------------
def quel_stock(idproduit):
    """ Trouve la quantite du produit souhaité dans chaque stock 
    (local->id:20, BIOX->id:21, PSL->id:38)

    Parameters
    ----------
    idproduit : str
        Identifiant du produit
    
    Return
    ------
    String avec la quantité du produit dans chaque stock
    """

    l = []
    sbiox = 0
    spsl = 0

    prods = get_request(f"api/products/filter/id/{idproduit}?key={cle_api}")

    for key in prods:
        slocal = int(prods[key]["stock_total_quantity"])
        if "stock" in prods[key]:
            stock = prods[key]["stock"]
            for key in stock:
                if "stock_entries" in stock[key]:
                    entries = stock[key]["stock_entries"]
                    for key in entries:
                        if entries[key]["stock_entry_supplier_id"] == "21":
                            sbiox = int(entries[key]["stock_entry_quantity"])
                        if entries[key]["stock_entry_supplier_id"] == "38":
                            spsl = int(entries[key]["stock_entry_quantity"])
        l = [slocal, sbiox, spsl]

    if len(l) == 0:
        return " "
    elif (l[1] == 0) and (l[2] == 0):
        return str(l[0])
    elif (l[1] != 0) and (l[2] == 0):
        return str(l[0]) + " | BIOX: " + str(l[1])
    elif (l[1] == 0) and (l[2] != 0):
        return str(l[0]) + " | PSL: " + str(l[2])
    elif (l[1] != 0) and (l[2] != 0):
        return str(l[0]) + " | BIOX: " + str(l[1]) + " | PSL: " + str(l[2])


#------------------------------------------------------------
def get_reference(idproduit):
    prods = get_request(f"api/products/filter/id/{idproduit}?key={cle_api}")

    for key in prods:
        ean = prods[key]["ean"]
        if (ean != ""):
            return ean
        else:
            return prods[key]["reference"]


#------------------------------------------------------------
def get_newref(idproduit, stockref):
    """ Trouve la reference correcte du produit souhaité quand il a differents options

    Parameters
    ----------
    idproduit : str
        Identifiant du produit
    stockref : str
        Reference du produit dans le stock
    
    Return
    ------
    String de la reference
    """
    prods = get_request(f"api/products/filter/id/{idproduit}?key={cle_api}")

    if str(stockref) in prod[str(idproduit)]["stock"]:
        return prod[str(idproduit)]["stock"][str(stockref)]["stock_ean"]
    else:
        return prod[str(idproduit)]["reference"]


#------------------------------------------------------------
def get_status(idcommande):
    cmds = get_request(f"api/orders/filter/id/{str(idcommande)}?key={cle_api}")

    for key in cmds:
        status = cmds[key]["status"]
    if status == "1":
        return "Enregistree"
    elif status == "2":
        return "En traitement"


#------------------------------------------------------------
def get_options(prod, infoProd):
    """ Trouve les options existantes du produit

    Parameters
    ----------
    prod : dict
        Dictionnaire du produit complet
    infoProd : dict
        Dictionnaire des informations relevantes du produit

    Return
    ------
    options : str
        Options de l'article en question
    """

    opliste = []
    if "options" in prod:
        stockref = str(prod["stock_reference"])

        if (len(stockref) == 7) or (len(stockref) == 13):
            infoProd["reference"] = get_newref(prod["id"], stockref)
        else:
            infoProd["reference"] = get_newref(prod["id"], str(prod["reference"]))

        for key in prod["options"]:
            option = prod["options"][key]
            chaine1 = unicodedata.normalize('NFD', option["option_name"])
            chaine2 = unicodedata.normalize('NFD', option["option_value_name"])
            opliste.append(f"{chaine1} : {chaine2}")

    if len(opliste) == 0:
        return " "

    opliste.reverse()
    
    options = opliste[0]
    i = 1
    while i < len(opliste):
        options += '\n'
        options += opliste[i]
        i += 1

    return options


#------------------------------------------------------------
def get_sante(idcommande):
    """ Trouve les informations de santé du client

    Parameters
    ----------
    idcommande : str
        Identification de la commande
    """
    cmds = get_request(f"api/orders/filter/id/{idcommande}?key={cle_api}")

    info_sante = {}

    for key in cmds:
        cmd = cmds[key]
        statuses_history = cmd["statuses_history"]
        for key in statuses_history:
            info = []
            status_history = statuses_history[key]
            status_comments = status_history["status_comments"]
            if status_comments != None:
                info = status_comments.split("<br />")
                info = info[1:-1]
                if len(info) > 6 :
                    info = info[-6:]
                info = [item.replace("\r\n", "") for item in info]
                for i in range(len(info)):
                    info_sante[i] = unicodedata.normalize('NFD', info[i])
    
    return info_sante


#------------------------------------------------------------

def get_client_history(id_client):
    """ Trouve les dates des commandes du client

    Parameters
    ----------
    id_client : int
        Id du client 

    Return
    ------
    cmds_dates : list
        Dates des commandes
    """
    print(f"Analyse de l'historique du client {id_client}")

    session_info = app.conn.connexion()
    session = session_info[0]
    headers = session_info[1]

    url = f'https://www.pharmashopi.com/superadmin/clients-liste-edit-{str(id_client)}.html'
    client_page = session.get(url, headers=headers)
    soup = BeautifulSoup(client_page.text, "html.parser")

    anchor_journal = soup.find(id='anchor_journal')

    if not anchor_journal:
        return []

    cmds_logs = anchor_journal.find_all(attrs={"data-page": "FILENAME_ORDERS"})
    cmds_dates = list(value.text[3:13] for value in cmds_logs)

    return cmds_dates


#------------------------------------------------------------

def similaire(name, company, email):
    """ Trouve les proportions de similarité entre le nom du client ou le nom de l'entreprise du client, et son mail

    Parameters
    ----------
    name : string
        Nom du client 
    company : string
        Entreprise du client 
    email : string
        Mail du client

    Return
    ------
    max_sim : float
        Similarité maximal
    """
    position = email.find('@')
    domaine = email[position+1 :]
    domaine = domaine.split('.')[0]
    email = email[:position]

    name = name.replace('-', ' ')
    name = name.split()
    company = company.split()
    email = email.replace('.', ' ')
    email = email.replace('-', ' ')
    email = email.replace('_', ' ')
    email = email.split()

    max_sim = 0

    max_sim = jellyfish.jaro_winkler(''.join(name).lower(), ''.join(email).lower())
    if max_sim == 1:
        return max_sim

    similaires = list(jellyfish.jaro_winkler(n.lower(), e.lower()) for n in name for e in email)
    max_sim_2 = max(similaires)
    if max_sim_2 == 1:
        return max_sim_2
    if max_sim < max_sim_2:
            max_sim = max_sim_2

    if company:
        similaires = list(jellyfish.jaro_winkler(n.lower(), e.lower()) for n in company for e in email)
        max_sim_2 = max(similaires)
        if max_sim < max_sim_2:
            max_sim = max_sim_2

        similaires = list(jellyfish.jaro_winkler(n.lower(), domaine.lower()) for n in company)
        max_sim_2 = max(similaires)
        if max_sim < max_sim_2:
            max_sim = max_sim_2
    
    return max_sim

#------------------------------------------------------------

def mining(cmds):
    """ Fait le mining des informations relevantes dans la détection d'arnaque

    Parameters
    ----------
    cmds : dict
        Dictionnaire de commandes
    
    Return
    ------
    (cmds_info,prods_info) : tuple
        pandas.Dataframe des commandes (avec les info sélectionnées) et dict des ids de produits par commande
    """

    commandes = DataFrame(cmds)
    commandes = commandes.dropna(axis=1, subset=['products'])
    ids_cmds = commandes.columns

    to_del = []
    for key in cmds:
        if key not in ids_cmds:
            to_del.append(key)
    for item in to_del:
        del cmds[item]

    adresse_livraison = ((cmds[key]['delivery_address']['postcode'], 
                          cmds[key]['delivery_address']['country_code'], 
                          cmds[key]['delivery_address']['company']) for key in cmds)
    adresse_livraison = DataFrame(adresse_livraison, index=ids_cmds, columns=['postcode', 'country', 'company'])
    adresse_livraison.index.name = 'id_cmd'

    type_livraison = (cmds[key]['shipping']['method_name'] for key in cmds)
    type_livraison = DataFrame(type_livraison, index=ids_cmds, columns=['shipping'])
    type_livraison.index.name = 'id_cmd'

    payement = (cmds[key]['payment']['method_name'] for key in cmds)
    payement = DataFrame(payement, index=ids_cmds, columns=['payment'])
    payement.index.name = 'id_cmd'

    info_client = ((cmds[key]['customer_info']['name'], 
                    cmds[key]['customer_info']['email'], 
                    cmds[key]['customer_info']['id']) for key in cmds)
    info_client = DataFrame(info_client, index=ids_cmds, columns=['name_client', 'email', 'id_client'])
    info_client.index.name = 'id_cmd'

    ids_prods = Series({key2: key for key in cmds for key2 in cmds[key]['products']})
    produits = (cmds[key]['products'][key2] for key in cmds for key2 in cmds[key]['products'])
    produits = DataFrame(produits, index=[ids_prods, ids_prods.index])
    produits.index.names = ['id_cmd', 'id_prod']
    produits['total_payer'] = (produits['final_price'].astype(float) 
                              * produits['quantity'].astype(float) 
                              * (1 + (produits['tax_rate'].astype(float) / 100)))
    
    total_payer = produits['total_payer'].groupby('id_cmd').sum()

    produits = produits[produits['id'] != 'FP']
    produits = produits[produits['id'] != 'CP']
    produits = produits[produits['id'] != 'AV']

    prods_info = list(produits['id'].groupby('id_cmd'))
    prods_info = {item[0]: list(item[1].values) for item in prods_info}

    cmds_info = adresse_livraison.join(type_livraison).join(payement).join(info_client).join(total_payer)

    return (cmds_info, prods_info)

#------------------------------------------------------------

def transform(cmds, prods, nbrjours):
    """ Fait la transformation des données sélectionnées pour les préparer au machine learning

    Parameters
    ----------
    cmds : pandas.Dataframe
        Collection des commandes avec les info sélectionnées
    prods : dict
        Collection des ids de produits par commande
    nbrjours : int
        Commandes multiples du même client dans cet intervalle de jours présente un risque

    Return
    ------
    cmds : pandas.DataFrame
        Entrée transformée
    """

    params = get_config_data()["detection_params"]

    cwd = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(cwd, '../docs/arnaque/depts_risque.csv')
    depts_risque = pd.read_csv(path, index_col='code')
    depts_risque = depts_risque['risque']
    path = os.path.join(cwd, '../docs/arnaque/prods_risque.csv')
    prods_risque = pd.read_csv(path, index_col='id')

    # similarité nom et mail
    if params["Correlation Nom/Mail"]:
        name_email = []
        for name, company, email in zip(cmds['name_client'], cmds['company'], cmds['email']):
            name_email.append(similaire(name, company, email))
        cmds['name_email'] = name_email
    cmds = cmds.drop(['name_client', 'email', 'company'], axis=1)

    # ignore frais gratuit
    if params["Ignorer Frait Gratuit"]:
        shipping = cmds['shipping'].str.lower()
        total_payer = cmds['total_payer']
        index = (cmds[~shipping.str.contains('gratuit')].index) & (cmds[total_payer > 65].index)
        cmds['ignore_frait_gratuit'] = False
        cmds.loc[index,'ignore_frait_gratuit'] = True
    cmds = cmds.drop('total_payer', axis=1)

    # livraison chez le commercant ou bureau de poste
    if params["Livraison Commerçant/Poste"]:
        shipping = cmds['shipping'].str.lower()
        index = cmds[shipping.str.contains('commerçant')].index
        cmds['livraison_commercant'] = False
        cmds.loc[index,'livraison_commercant'] = True
    cmds = cmds.drop('shipping', axis=1)

    # departements francais de risque
    if params["Départements Risque"]:
        index = cmds[cmds['country'] == 'FR'].index
        cmds.loc[index,'postcode'] = cmds.loc[index,'postcode'].str[:2]
        cmds['dept_risque'] = False
        for index, code in zip(index,cmds.loc[index, 'postcode']):
            cmds.loc[index, 'dept_risque'] = depts_risque[int(code)]
    cmds = cmds.drop(['country', 'postcode'], axis=1)

    # produits de risque
    if params["Produits Risque"]:
        risque = {}
        for key in prods:
            risque[key] = 0
            ids_prods = prods[key]
            for id_prod in ids_prods:
                if id_prod.isdigit():
                    if int(id_prod) in prods_risque.index:
                        risque[key] += 1
        cmds['produits_risque'] = cmds.index.map(risque)


    # client history : premiere_commande ; multiples_commandes
    if params["Historique Client"]:
        premiere_cmd = []
        cmds_multiples = []
        for id_client in cmds['id_client']:
            if id_client == '0':
                premiere_cmd.append(True)
                cmds_multiples.append(1)
            else:
                cmds_dates = get_client_history(id_client)
                if len(cmds_dates) <= 1:
                    premiere_cmd.append(True)
                else:
                    premiere_cmd.append(False)
                nbr_cmds = 1
                if cmds_dates:
                    for date, i in zip(cmds_dates, range(len(cmds_dates))):
                        cmds_dates[i] = datetime.strptime(date, '%d/%m/%Y')
                    date_actuel = cmds_dates[0]
                    for date in cmds_dates[1:]:
                        if (date_actuel - date).days <= nbrjours:
                            nbr_cmds += 1
                        else:
                            break
                cmds_multiples.append(nbr_cmds)
        cmds['premiere_cmd'] = premiere_cmd
        cmds['cmds_multiples'] = cmds_multiples

    cmds = cmds.drop('id_client', axis=1)

    return cmds
