# -*- coding: utf-8 -*-

from pandas import Series, DataFrame
import json
import requests
import unicodedata

import app.log
import app.utilities

logger = app.log.setup_logger(__name__)

#------------------------------------------------------------
def surnombre(nbrmedic, produits):
    """ Verifie s'il y a au moins un produit dont la quantite est trop grande

    Parameters
    ----------
    nbrmedic : int
        Nombre maximal d'un article par commande (choisi via GUI)
    produits : dict
        Dictionnaire de produits
    """

    for key in produits:
        prod = produits[key]
        if int(prod["quantity"]) > nbrmedic:
            return 1
    return 0
    

#------------------------------------------------------------
def filtrage_picking(nbrcmds, nbrmedic, site_filter, livraison=""):
    """ Trouve le nombre souhaité de commandes avec le type de livraison souhaité
    et avec au maximum un nombre maximal d'un certain article

    Parameters
    ----------
    livraison: str
        Nom du type de livraison (les principales : Colissimo, Mondial Relay et Lettre suivie)
    nbrcmds : int
        Nombre de commandes à imprimer (choisi via GUI)
    nbrmedic : int
        Nombre maximal d'un article par commande (choisi via GUI)
    site_filter : str
        Selectionne le site souhaité

    Return
    ------
    commandes : dict
        Dictionnaire avec les commandes souhaitées
    """

    print("Filtrage")
    print("******************************************\n")

    commandes = {}
    break_var = 0
    limit = str(nbrcmds)

    cmds = app.utilities.get_request(f"api/orders/filter/status/1{site_filter}/filter/orderby/date_created/desc/limit/1")

    for key in cmds:
        derniere_date = cmds[key]["date_created"]

    cmds = app.utilities.get_request(f"api/orders/filter/status/1{site_filter}/filter/orderby/date_created/asc/limit/{limit}")

    if not cmds:
        return commandes

    while True:
        for key in cmds:
            print(f"Filtrage de la commande : {key}")
            cmd = cmds[key]
            produits = cmd["products"]
            date_created = cmd["date_created"]
            shipping = cmd["shipping"]
            method_name = shipping["method_name"]

            if "Retrait" in method_name:
                print(f"La commande {key} a été filtrée (retrait sur place)")
                logger.info(f"La commande {key} a été filtrée (retrait sur place)")
                logger.new_formatter("newline")
            elif surnombre(nbrmedic,produits) != 0:
                print(f"La commande {key} a été filtrée (surnombre d'un article)")
                logger.info(f"La commande {key} a été filtrée (surnombre d'un article)")
                logger.new_formatter("newline")
            elif (livraison != "") and (livraison not in method_name):
                print(f"La commande {key} a été filtrée (livraison n'est pas du type {livraison})")
                logger.info(f"La commande {key} a été filtrée (livraison n'est pas du type {livraison}))")
                logger.new_formatter("newline")
            else:
                commandes[key] = cmd

            if len(commandes) >= nbrcmds:
                break_var = 1
                break

            if derniere_date == date_created:
                break_var = 1
                print("\nToutes les commandes enregistrées ont été analysées")
                print(f"{len(commandes)} commandes du type souhaité ont été trouvées\n")
                break

            limit = str(nbrcmds - len(commandes))

            url_path = f"api/orders/filter/status/1{site_filter}/filter/orderby/date_created/asc/limit/{limit}/filter/date_created/superior/{date_created}"
            cmds = app.utilities.get_request(url_path)

        if break_var == 1:
            break

    print("\n")
    return commandes

#------------------------------------------------------------
def filtrage_arnaque(cmds,prods):
    """Filtre les commandes qui ne sont certainement pas arnaque

    Parameters
    ----------
    cmds : pandas.Dataframe
        Collection des commandes avec les info sélectionnées
    prods : dict
        Collection des ids de produits par commande
    
    Return
    ------
    (cmds,prods) : tuple
        Versions filtrées des entrées
    """
    old_index = cmds.index

    cmds = cmds.dropna(subset=['payment'])

    payment = cmds['payment'].str.lower()
    cmds = cmds.drop(cmds[payment == ''].index 
                     | cmds[payment.str.contains('paypal')].index 
                     | cmds[payment.str.contains('virement bancaire')].index)
    payment = cmds['payment'].str.lower()
    total_payer = cmds['total_payer']
    cmds = cmds.drop((cmds[payment.str.contains('carte bancaire')].index) & (cmds[total_payer > 100].index))
    cmds = cmds.drop('payment', axis=1)
    new_index = cmds.index

    index = old_index.difference(new_index)
    for i in index:
        del prods[i]
        
    return (cmds, prods)
