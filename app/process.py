# -*- coding: utf-8 -*-

from pandas import Series, DataFrame
from requests.exceptions import HTTPError
import json
import numpy as np
import pandas as pd
import requests
import unicodedata

import app.docs
import app.filters
import app.log
import app.machine_learning
import app.robot
import app.utilities

logger = app.log.setup_logger(__name__)
cle_api = app.utilities.get_config_data()['cle_api']


#------------------------------------------------------------
def setstatus(idcommande):
    """ Change le status d'une commande

    Parameters
    ----------
    idcommande : str
        Identification de la commande
    """

    data = [{"id": idcommande, "status": "2"}]
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    url = f"http://pharmashopi.com/api/orders?key={cle_api}"
    r = requests.put(url, data=json.dumps(data), headers=headers)


#------------------------------------------------------------
def picking(cmds, sortie, livraison, mode_teste):
    """ Fait le picking dans le robot

    Parameters
    ----------
    cmds : dict
        Dictionnaire de commandes
    sortie : 
        Choisit la sortie du robot
    """

    print("Preparation Picking...")
    print("******************************************\n")

    totalquantity = 0
    listeProd = []

    for key in cmds:
        print(f"Traitement de la commande : {key}")
        cmd = cmds[key]
        produits = cmd["products"]

        for key in produits:
            prod = produits[key]
            infoProd = {}
            if str(prod["reference"]) != "":
                totalquantity += int(str(prod["quantity"]))
                infoProd["quantity"] = str(prod["quantity"])
                infoProd["stock"] = app.utilities.quel_stock(prod["id"])
                infoProd["reference"] = str(app.utilities.get_reference(prod["id"]))
                infoProd["brand_name"] = unicodedata.normalize('NFD', prod["brand_name"])
                infoProd["name"] = unicodedata.normalize('NFD', prod["name"])
                infoProd["options"] = app.utilities.get_options(prod, infoProd)
                infoProd["price"] = str(round(float(prod["final_price"]), 2))
                listeProd.append(infoProd)

    print("\n")

    listeProd = sorted(listeProd, key=lambda k: k["brand_name"])

    i = 0
    while i < (len(listeProd) - 1):
        if listeProd[i]["reference"] == listeProd[i + 1]["reference"]:
            listeProd[i]["quantity"] = str(int(listeProd[i]["quantity"]) + int(listeProd[i + 1]["quantity"]))
            listeProd.pop(i + 1)
        else:
            i += 1

    range_cmds = ""
    ordreCmds = list(cmds.keys())
    if ordreCmds != []:
        range_cmds = str (min(ordreCmds)) + "  -->  " + str(max(ordreCmds))

    indexrequette = 1001
    print("Envoi des requetes au robot...")
    print("******************************************\n")
    for prod in listeProd:
        if mode_teste:
            prod["robot_stock"] = '1'
        else:
            prod["robot_stock"] = app.robot.robot_stock(prod["reference"])
        if int(prod["robot_stock"]) < int(prod["quantity"])  :
            print (f"{prod['reference']} - Requete non envoyée au robot. Il ne reste que {prod['robot_stock']} dans le robot")
            logger.info(f"Produit {prod['reference']} : stock du robot ({prod['robot_stock']}) est inférieur à la quantité souhaitée ({prod['quantity']})")
            logger.new_formatter("newline")
        else:
            print (f"{prod['reference']} - Requete envoiée au robot. Il y'en a {prod['robot_stock']} dans le robot")
            logger.info(f"Produit {prod['reference']} : stock du robot ({prod['robot_stock']}) est supérieur ou égal à la quantité souhaitée ({prod['quantity']})")
            if not mode_teste:
                app.robot.retrait(prod["reference"],prod["quantity"],indexrequette,sortie)
            logger.info(f"Le robot a libéré {prod['quantity']} item(s) de l'article {prod['reference']} ")
            logger.new_formatter("newline")
            indexrequette += 1
    print("\n")

    logger.info("Picking préparé pour l'écriture")
    logger.new_formatter("newline")

    app.docs.picking_doc(listeProd, totalquantity, range_cmds, livraison)

    logger.info("Étape Picking finie avec succès")
    logger.new_formatter("newline")


#------------------------------------------------------------
def bonprep(cmds):
    """ Fait les bons de commande

    Parameters
    ----------
    cmds : dict
        Dictionnaire de commandes
    """

    print("Preparation des bons de commande...")
    print("******************************************\n")

    infoBonprep = {}

    ordreCmds = list(cmds.keys())
    ordreCmds.sort()

    for idcmd in ordreCmds:
        print(f"Traitement de la commande : {idcmd}")

        cmd = cmds[idcmd]
        produits = cmd["products"]

        infoBonprep[idcmd] = {}
        listeProd = []
        totalquantity = 0
        totalht = 0
        totalttc = 0

        for key in produits:
            prod = produits[key]
            infoProd = {}

            infoProd["quantity"] = str(prod["quantity"])
            infoProd["reference"] = str(app.utilities.get_reference(prod["id"]))
            infoProd["name"] = unicodedata.normalize('NFD', prod["name"])
            infoProd["brand_name"] = unicodedata.normalize('NFD', prod["brand_name"])
            infoProd["options"] = app.utilities.get_options(prod, infoProd)
            infoProd["weight"] = ""

            if (str(prod["reference"]) != ""):
                totalquantity += int(str(prod["quantity"]))
                infoProd["weight"] = str(prod["weight"])[:5] + "kg"

            ht = float(prod["final_price"])
            tax_rate = float(prod["tax_rate"])
            final_price = ht + (ht * tax_rate / 100)

            infoProd["ht"] = str(round(ht, 2))
            infoProd["final_price"] = str(round(final_price, 2))

            totalht += ht * int(infoProd["quantity"])
            totalttc += final_price * int(infoProd["quantity"])
                    
            listeProd.append(infoProd)

        listeProd = sorted(listeProd, key=lambda k: k["brand_name"])

        for i in range(len(listeProd)):
            if listeProd[i]["brand_name"] != "":
                break
        listeProd = listeProd[i:] + listeProd[:i]

        infoBonprep[str(idcmd)]["list_prod"] = listeProd
        infoBonprep[str(idcmd)]["total_quantity"] = str(totalquantity)
        infoBonprep[str(idcmd)]["totalht"] = str(round(totalht, 2))
        infoBonprep[str(idcmd)]["totalttc"] = str(round(totalttc, 2))

    print("\n")

    logger.info("Bons de commande préparés pour l'écriture")
    logger.new_formatter("newline")

    app.docs.bonprep_doc(cmds, infoBonprep)

    logger.info("Étape BonCommande finie avec succès")
    logger.new_formatter("newline")


#------------------------------------------------------------
def detection(cmds, nbrjours):
    """ Détecte les arnaques

    Parameters
    ----------
    cmds : dict
        Dictionnaire de commandes
    nbrjours : int
        Commandes multiples du même client dans cet intervalle de jours présente un risque
    """

    print("La détection d'arnaque a commencé\n")
    logger.info("La détection d'arnaque a commencé")
    logger.new_formatter(mode="newline")

    logger.debug("Première étape : collecter uniquement des données utiles à partir de commandes")
    logger.new_formatter(mode="newline")

    parsed = app.utilities.mining(cmds)
    cmds = parsed[0]
    prods = parsed[1]

    logger.debug("Deuxième étape : filtrer les bonnes commandes")
    logger.new_formatter(mode="newline")

    parsed = app.filters.filtrage_arnaque(cmds, prods)
    cmds = parsed[0]
    prods = parsed[1]

    if cmds.empty:
        print("Aucune commande ne présente un risque significatif\n")
        logger.info("Aucune commande ne présente un risque significatif")
        logger.new_formatter(mode="newline")
        print("Détection d'arnaque terminé avec succès\n")
        logger.info("Détection d'arnaque terminé avec succès")
        logger.new_formatter(mode="newline")
        return

    logger.debug("Troisième étape : transformer les données")
    logger.new_formatter(mode="newline")

    cmds = app.utilities.transform(cmds, prods, nbrjours)

    logger.debug("Quatrième étape : préparer les données d'apprentissage automatique")
    logger.new_formatter(mode="newline")

    prepared = app.machine_learning.prepare_data()
    data = prepared[0]
    target = prepared[1]

    logger.debug("Cinquième étape : entraînement, tests, classification")
    logger.new_formatter(mode="newline")

    classifier = app.machine_learning.support_vector_machine(data, target)
    predictions = classifier.predict(cmds)
    prob = classifier.predict_proba(cmds)[:, 1]
    cmds['prediction'] = predictions
    cmds['probability'] = prob

    print("Predictions")
    logger.info("Predictions")
    if cmds['prediction'].sum() == 0:
        print("Aucune commande ne présente un risque significatif")
        logger.info("Aucune commande ne présente un risque significatif")
    else:
        for prediction,prob,index in zip(cmds['prediction'], cmds['probability'], cmds.index):
            if prediction == True:
                logger.warning(f"Commande {index} : potentiel arnaque -> {int(prob * 100)}%")
    print("\n")
    logger.new_formatter(mode="newline")

    print("Détection d'arnaque terminé avec succès\n")
    logger.info("Détection d'arnaque terminé avec succès")
    logger.new_formatter(mode="newline")


#------------------------------------------------------------
def detection_arnaque(nbrcmds, sites, nbrjours, mode_teste):
    """ Fait juste la detection d'arnaque dans les dernieres commandes choisis, n'importe leurs status

    Parameters
    ----------
    nbrcmds : str
        Nombre de commandes à imprimer (choisi via GUI)
    sites : dict
        Informations des sites à rechercher
    nbrjours : int
        Commandes multiples du même client dans cet intervalle de jours présente un risque
    mode_teste : boolean
        (Pas utilisé)
    """

    logger.info(f"Paramètres de la procedure de détection: \n"
                f"Nombre de commandes : {nbrcmds} \n"
                f"Nombre de jours pour vérifier les commandes multiples : {nbrjours} \n"
                f"Sites recherchés : Pharmashopi ({sites['Pharmashopi']}) / Espace Contention ({sites['Espace Contention']})")
    logger.new_formatter(mode="newline")

    print("Chargement des commandes...")
    print("******************************************\n")
    site = ""
    if sites["Pharmashopi"] == True and sites["Espace Contention"] == True:
        site = ""
    elif sites["Pharmashopi"] == True:
        site = "/filter/store_id/pharmashopi"
    elif sites["Espace Contention"] == True:
        site = "/filter/store_id/contention"
    else:
        logger.warning("Aucun site n'a été sélectionné")
        logger.new_formatter(mode="newline")
        logger.info("Procesus terminé avec succès")
        logger.new_formatter(mode="end_process")
        return

    try:
        cmds = app.utilities.get_request(f"api/orders{site}/filter/orderby/date_created/desc/limit/{nbrcmds}?key={cle_api}")
        detection(cmds, nbrjours)
        print('Procesus terminé avec succès\n\n')
        logger.info("Procesus terminé avec succès")
        logger.new_formatter(mode="end_process")

    except HTTPError as http_error:
        logger.exception("HTTP exception occurred")
        logger.new_formatter(mode="newline")
        logger.info("Procesus interrompu")
        logger.new_formatter(mode="end_process")
        return
    except Exception as error:
        logger.exception("Exception occurred")
        logger.new_formatter(mode="newline")
        logger.info("Procesus interrompu")
        logger.new_formatter(mode="end_process")
        return

#------------------------------------------------------------
def bonetpick(nbrcmds, nbrmedic, sites, sortie, livraison, nbrjours, mode_teste):
    """ Fait le request et appele picking et bonprep

    Parameters
    ----------
    nbrcmds : str
        Nombre de commandes à imprimer (choisi via GUI)
    nbrmedic : str
        Nombre maximal d'un article par commande (choisi via GUI)
    sites : dict
        Informations des sites à rechercher
    sortie : 
        Choisit la sortie du robot
    livraison : str
        Filtre le mode de livraison (Colissimo, Mondial Relay et Lettre suivie)
    """

    logger.info(f"Paramètres de la procedure de picking: \n"
                f"Nombre de commandes : {nbrcmds} \n"
                f"Nombre de medicaments maximal : {nbrmedic} \n"
                f"Sites recherchés : Pharmashopi ({sites['Pharmashopi']}) / Espace Contention ({sites['Espace Contention']}) \n"
                f"Livraison quelconque (0) ou Colissimo (1) ou Mondial Relay (2) : {livraison} \n"
                f"Sortie du robot (au cas où il est actif) : {sortie}")
    logger.new_formatter(mode="newline")

    print("Chargement des commandes...")
    print("******************************************\n")
    site = ""
    if sites["Pharmashopi"] == True and sites["Espace Contention"] == True:
        site = ""
    elif sites["Pharmashopi"] == True:
        site = "/filter/store_id/pharmashopi"
    elif sites["Espace Contention"] == True:
        site = "/filter/store_id/contention"
    else:
        logger.warning("Aucun site n'a été sélectionné")
        logger.new_formatter(mode="newline")
        logger.info("Procesus terminé avec succès")
        logger.new_formatter(mode="end_process")
        return

    try:
        cmds = app.filters.filtrage_picking(nbrcmds, nbrmedic, site, livraison)

        if cmds:
            logger.info(f"Commandes selectionnées par les filtres : {list(cmds.keys())}")
            logger.new_formatter(mode="newline")
        else:
            logger.warning("Aucune commande n'a été trouvée")
            logger.new_formatter(mode="newline")
            logger.info("Procesus terminé avec succès")
            logger.new_formatter(mode="end_process")
            return

        picking(cmds, sortie, livraison, mode_teste)
        bonprep(cmds)
        print("Fichiers prets a imprimer\n")

        ordreCmds = list(cmds.keys())
        ordreCmds.sort()

        if not mode_teste:
            for key in cmds:
                setstatus(key)
                print(f"La commande {key} a changée de status")
                logger.info(f"Status de la commande {key} : {app.utilities.get_status(key)}")
            logger.new_formatter(mode="newline")
            print("\n")

        detection(cmds, nbrjours)

        print('Procesus terminé avec succès\n\n')
        logger.info("Procesus terminé avec succès")
        logger.new_formatter(mode="end_process")

    except HTTPError as http_error:
        logger.exception("HTTP exception occurred")
        logger.new_formatter(mode="newline")
        logger.info("Procesus interrompu")
        logger.new_formatter(mode="end_process")
        return
    except Exception as error:
        logger.exception("Exception occurred")
        logger.new_formatter(mode="newline")
        logger.info("Procesus interrompu")
        logger.new_formatter(mode="end_process")
        return