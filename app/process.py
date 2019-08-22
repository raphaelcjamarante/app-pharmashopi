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
import app.model.batch
import app.model.commande
import app.robot
import app.utilities

logger = app.log.setup_logger(__name__)

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
    url = f"http://pharmashopi.com/api/orders"
    r = requests.put(url, data=json.dumps(data), headers=headers)

#------------------------------------------------------------
def picking(batch, sortie, mode_teste):
    """ Fait le picking dans le robot

    Parameters
    ----------
    cmds : dict
        Dictionnaire de commandes
    sortie : 
        Choisit la sortie du robot
    mode_teste : 
     Selectionne le mode testing ou le mode production
    """

    print("\nEnvoi des requetes au robot...")
    print("******************************************\n")

    indexrequette = 1001

    prods_info = batch.prods_info

    for key in prods_info:
        ref = key
        qte = prods_info[key]['total_qte']
        robot_stock = prods_info[key]['robot_stock']

        if int(robot_stock) < qte:
            print (f"{ref} - Requete non envoyée au robot. Il ne reste que {robot_stock} dans le robot")
            logger.info(f"Produit {ref} : stock du robot ({robot_stock}) est inférieur à la quantité souhaitée ({qte})")
            logger.new_formatter("newline")
        else:
            print (f"{ref} - Requete envoiée au robot. Il y'en a {robot_stock} dans le robot")
            logger.info(f"Produit {ref} : stock du robot ({robot_stock}) est supérieur ou égal à la quantité souhaitée ({qte})")
            if not mode_teste:
                app.robot.retrait(ref, qte, indexrequette, sortie)
                indexrequette += 1
                logger.info(f"Le robot a libéré {qte} item(s) de l'article {ref} ")
            logger.new_formatter("newline")
    print("\n")

    logger.info("Étape Picking Robot finie avec succès")
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
def detection_arnaque(nbrcmds, sites, nbrjours, mode_teste, mode_detection, id_cmd=None):
    """ Fait juste la detection d'arnaque dans les dernieres commandes choisis, n'importe leurs status

    Parameters
    ----------
    nbrcmds : int
        Nombre de commandes à imprimer (choisi via GUI)
    sites : dict
        Informations des sites à rechercher
    nbrjours : int
        Commandes multiples du même client dans cet intervalle de jours présente un risque
    mode_teste : bool
        (Pas utilisé)
    mode_detection : str
        Selectionne mode detection batch ou detection singulaire
    id_cmd : str
        Identification de la commande dans le mode singulaire
    """

    logger.info(f"Paramètres de la procedure de détection: \n"
                f"Nombre de commandes : {nbrcmds} \n"
                f"Nombre de jours pour vérifier les commandes multiples : {nbrjours} \n"
                f"Sites recherchés : Pharmashopi ({sites['Pharmashopi']}) / Espace Contention ({sites['Espace Contention']})")
    logger.new_formatter(mode="newline")

    print("Chargement des commandes...")
    print("******************************************\n")

    try:
        site = app.utilities.get_site(sites)
        if site == None:
            logger.warning("Aucun site n'a été sélectionné")
            logger.new_formatter(mode="newline")
        else:
            if mode_detection == 'batch':
                cmds = app.utilities.get_request(f"api/orders{site}/filter/orderby/date_created/desc/limit/{nbrcmds}")
            else:
                cmds = app.utilities.get_request(f"api/orders/filter/id/{id_cmd}")
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
    """ Fait le processus picking

    Parameters
    ----------
    nbrcmds : int
        Nombre de commandes à imprimer (choisi via GUI)
    nbrmedic : int
        Nombre maximal d'un article par commande (choisi via GUI)
    sites : dict
        Informations des sites à rechercher
    sortie : int
        Choisit la sortie du robot
    livraison : str
        Filtre le mode de livraison (Colissimo, Mondial Relay et Lettre suivie)
    nbrjours : int
        Commandes multiples du même client dans cet intervalle de jours présente un risque (pas utilisé)
    mode_teste : boolean
        Selectionne mode teste ou mode production
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

    try:
        site = app.utilities.get_site(sites)
        if site == None:
            logger.warning("Aucun site n'a été sélectionné")
            logger.new_formatter(mode="newline")
        else:
            cmds = app.filters.filtrage_picking(nbrcmds, nbrmedic, site, livraison)
            if cmds == {}:
                logger.warning("Aucune commande n'a été trouvée")
                logger.new_formatter(mode="newline")
            else:
                logger.info(f"Commandes selectionnées par les filtres : {list(cmds.keys())}")
                logger.new_formatter(mode="newline")

                batch = app.model.batch.Batch(cmds, mode_teste)
                picking(batch, sortie, mode_teste)
                app.docs.picking_doc(batch, livraison)
                app.docs.bonprep_doc(batch.cmds, livraison)
                print("Fichiers prets a imprimer\n")

                ordre_cmds = list(cmds.keys())
                ordre_cmds.sort()

                if not mode_teste:
                    for key in ordre_cmds:
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