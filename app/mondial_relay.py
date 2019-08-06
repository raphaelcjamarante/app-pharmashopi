# -*- coding: utf-8 -*-

from pandas import DataFrame
from requests.exceptions import HTTPError
from zeep import Client
import datetime
import hashlib
import json
import os
import pandas as pd
import pandas as pd
import requests
import unicodedata
import zeep

import app.log
import app.utilities

logger = app.log.setup_logger(__name__)
cle_api = app.utilities.get_config_data()['cle_api']

# ----------------------------

def generate_security_key(private_key, parameters):
    """ Prepare la clé de securité selon la documentation Mondial Relay

    Parameters
    ----------
    private_key : str
        Parametre de securité pour le web service : regarder la documentation
    parameters : dict
        Parametres selectionnés pour generer l'etiquette
    """
    security_key = ""
    for key in parameters:
        security_key = security_key + parameters[key].strip(" ")
    security_key = security_key + private_key
    security_key = security_key.strip()
    security_key = hashlib.md5(security_key.encode('utf-8'))
    security_key = security_key.hexdigest().upper()

    return security_key

# ----------------------------
def normalize(word):
    word = word.strip()
    word = unicodedata.normalize('NFD', word)
    word = word.encode('ascii', 'ignore')
    return word.decode("utf-8")

# ----------------------------

def get_info_mondial_relay(cmd, enseigne, private_key):
    """ Prepare les informations requises pour generer l'etiquette

    Parameters
    ----------
    cmd : dict
        Dict des informations de la commande
    enseigne : str
        Parametre de securité pour le web service : regarder la documentation
    private_key : str
        Parametre de securité pour le web service : regarder la documentation
    """

    parameters = {}

    customer_info = cmd['customer_info']
    delivery_address = cmd['delivery_address']
    shipping = cmd['shipping']
    language = cmd['language']
    currency = cmd['currency']
    products = cmd['products']

    parameters["Enseigne"] = enseigne # Obligatory
    parameters["ModeCol"] = "CCC" # Obligatory (CCC|CDR|CDS|REL)

    #mode_liv = ""
    #if delivery_address['company'] == 'Livraison en Point Relais':
    #    mode_liv = '24R'
    parameters["ModeLiv"] = '24R' # Obligatory (LCC|LD1|LDS|24R|24L|24X|ESP|DRI)
    parameters["NDossier"] = "" # Facultative
    parameters["NClient"] = cmd["id"] # Facultative
    parameters["Expe_Langage"] = 'FR' # Obligatory (ISO code)
    parameters["Expe_Ad1"] = "GATPHARM" # Obligatory
    parameters["Expe_Ad2"] = "" # Facultative
    parameters["Expe_Ad3"] = "7BIS RUE EMILE BLANC" # Obligatory
    parameters["Expe_Ad4"] = "" # Facultative
    parameters["Expe_Ville"] = "DOMENE" # Obligatory
    parameters["Expe_CP"] = "38420" # Obligatory
    parameters["Expe_Pays"] = "FR" # Obligatory (ISO code)
    parameters["Expe_Tel1"] = "+330476772308" # Obligatory
    parameters["Expe_Tel2"] = "" # Facultative
    parameters["Expe_Mail"] = "" # Facultative
    parameters["Dest_Langage"] = language # Obligatory (ISO code)

    name = normalize(customer_info['name'])
    position = name.find(" ")
    name = name[position+1 :] + " " + name[:position]
    parameters["Dest_Ad1"] = name # Obligatory
    parameters["Dest_Ad2"] = "" # Facultative
    parameters["Dest_Ad3"] = normalize(delivery_address['street_address']) # Obligatory
    parameters["Dest_Ad4"] = "" # Facultative
    parameters["Dest_Ville"] = normalize(delivery_address['city']) # Obligatory
    parameters["Dest_CP"] = delivery_address['postcode'] # Obligatory
    parameters["Dest_Pays"] = delivery_address['country_code'] # Obligatory (ISO code)

    prefix = "+"
    phone = customer_info['phone'].replace('(', '')
    phone = phone.replace(')', '')
    phone = phone.replace('+', '')
    if delivery_address['country_code'] == 'FR' and (phone[:2] != '33'):
        prefix = prefix + '33'
    parameters["Dest_Tel1"] = prefix + phone # Facultative / Obligatory for home delivery
    parameters["Dest_Tel2"] = "" # Facultative
    parameters["Dest_Mail"] = customer_info['email'] # Facultative

    poids = 0.0
    for key in products:
        prod = products[key]
        poids += int(prod['quantity']) * float(prod['weight'])
    poids = int(poids * 1000)
    if poids < 20 :
        poids = 20

    parameters["Poids"] = str(poids) # Obligatory (en grammes)
    parameters["Longueur"] = "" # Facultative
    parameters["Taille"] = "" # Facultative
    parameters["NbColis"] = "1" # Obligatory
    parameters["CRT_Valeur"] = "0" # Obligatory
    parameters["CRT_Devise"] = "" # Facultative
    parameters["Exp_Valeur"] = "" # Facultative
    parameters["Exp_Devise"] = "" # Facultative
    parameters["COL_Rel_Pays"] = "" # Facultative / Obligatory if collected in Point Relais
    parameters["COL_Rel"] = "" # Facultative / Obligatory if collected in Point Relais
    parameters["LIV_Rel_Pays"] = delivery_address['country_code'] # Facultative / Obligatory if collected in Point Relais
    LIV_Rel = ""
    if "mondial_relay" in shipping:
        LIV_Rel = str(shipping["mondial_relay"]["relay_id"]) # Facultative / Obligatory if collected in Point Relais
    parameters["LIV_Rel"] = LIV_Rel
    parameters["TAvisage"] = "" # Facultative
    parameters["TReprise"] = "" # Facultative
    parameters["Montage"] = "" # Facultative
    parameters["TRDV"] = "" # Facultative
    parameters["Assurance"] = "" # Facultative
    parameters["Instructions"] = "" # Facultative
    parameters["Security"] = generate_security_key(private_key, parameters) # Obligatory
    #parameters["Texte"] = "" # Facultative (pas pris en compte pour generer la cle de securite)

    return parameters

#------------------------------------------------------------
def get_etiquette(enseigne, expeditions, langue, private_key):
    

    parameters = {}

    parameters["Enseigne"] = enseigne # Obligatory
    parameters["Expeditions"] = expeditions
    parameters["Langue"] = langue
    parameters["Security"] = generate_security_key(private_key, parameters) # Obligatory

    return parameters

#------------------------------------------------------------
def setstatus(idcmd, status, tracking_code):
    """ Change le status d'une commande

    Parameters
    ----------
    idcmd : str
        Identification de la commande
    status : int
        Nouvel status de la commande
    tracking_code : str
        Code d'expedition Mondial Relay
    """

    data = [{"id": idcmd, "status": str(status), "shipping": {"tracking_code": tracking_code}}]
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    url = f"http://pharmashopi.com/api/orders?key={cle_api}"
    r = requests.put(url, data=json.dumps(data), headers=headers)
 
# ----------------------------

def add_to_list(idcmd, exp_nbr):
    entry = {str(idcmd): str('%08d' %  int(exp_nbr))}

    entry = DataFrame(entry.values(), index=entry.keys(), columns=['NumeroColis'])
    entry.index.name  ='NumeroCommande'

    date = datetime.datetime.today()
    file_name = 'mondial_relay_' + date.strftime('%d-%b-%Y')

    path = app.utilities.get_path(f'docs/tracking_mondial_relay/{file_name}.csv')
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0, sep=';', dtype={'NumeroColis': str})
        df = df.append(entry, sort=True)
        df.to_csv(path, sep=';')
    else:
        entry.to_csv(path, sep=';')


# ----------------------------
def generer_etiquette(idcmd, finaliser, mode_teste):
    """ Création de l'etiquette

    Parameters
    ----------
    idcmd : str
        Identification de la commande
    finaliser : str
        Si on souhaite ou non finaliser la commande apres la generation d'etiquette
    """

    config_data = app.utilities.get_config_data()
    if mode_teste:
        enseigne = config_data["enseigne_testing"]
        private_key = config_data["cle_testing"]
    else:
        enseigne = config_data["enseigne_production"]
        private_key = config_data["cle_production"]

    try:
        cmd = app.utilities.get_request(f"api/orders/filter/id/{idcmd}?key={cle_api}")

        for key in cmd:
            cmd = cmd[key]

        wsdl = "http://api.mondialrelay.com/Web_Services.asmx?WSDL"
        client = Client(wsdl)
        parameters = get_info_mondial_relay(cmd, enseigne, private_key)
        r_expedition = client.service.WSI2_CreationExpedition(**parameters)
        #r = client.service.WSI2_CreationEtiquette(**parameters_etiquette)

        logger.info(f"Parametres de l'etiquette : {parameters}")
        logger.new_formatter(mode="newline")

        if r_expedition['STAT'] == '0':
            exp_nbr = r_expedition['ExpeditionNum']
            r_etiquette = client.service.WSI3_GetEtiquettes(**get_etiquette(enseigne, exp_nbr, parameters["Dest_Langage"], private_key))

            if r_etiquette['STAT'] == '0':
                url = "http://www.mondialrelay.com"
                url_etiquette = url + r_etiquette['URL_PDF_10x15']
                #position = url_etiquette.find('format=')
                #url_etiquette = url_etiquette[: position+7] + '10x15' + url_etiquette[position+9 :]
                response = requests.get(url_etiquette)
                file = open(app.utilities.get_path("docs/etiquette_mondial_relay.pdf"), 'wb')
                file.write(response.content)
                file.close()

                if not mode_teste : 
                    add_to_list(idcmd, exp_nbr)

                if (finaliser == 1) and not mode_teste:
                    setstatus(cmd['id'], '3', exp_nbr)
                    print(f"La commande {idcmd} a changée de status\n")
                    logger.info(f"Status de la commande {idcmd} : {app.utilities.get_status(idcmd)}")
                    logger.new_formatter(mode="newline")

                print(f"Etiquette pour la commande {idcmd} générée. Son code d'expedition est {exp_nbr}\n\n")
                logger.info(f"Etiquette pour la commande {idcmd} générée. Son code d'expedition est {exp_nbr}")
                logger.new_formatter(mode="end_process")

            else:
                path = app.utilities.get_path("docs/MondialRelay/codes_web_service.csv")
                codes = pd.read_csv(path, index_col='Code', sep=';')
                print(f"Etiquette pour la commande {idcmd} non générée")
                logger.info(f"Etiquette pour la commande {idcmd} non générée")
                logger.error(f"Error {r_etiquette['STAT']} : {codes.iloc[int(r_etiquette['STAT'])]['Label']}")
                logger.new_formatter(mode="end_process")
        else:
            path = app.utilities.get_path("docs/MondialRelay/codes_web_service.csv")
            codes = pd.read_csv(path, index_col='Code', sep=';')
            print(f"Etiquette pour la commande {idcmd} non générée")
            logger.info(f"Etiquette pour la commande {idcmd} non générée")
            logger.error(f"Error {r_expedition['STAT']} : {codes.iloc[int(r_expedition['STAT'])]['Label']}")
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




