# -*- coding: utf-8 -*-

from fpdf import FPDF
from pandas import DataFrame
from requests.exceptions import HTTPError
from zeep import Client
import datetime
import hashlib
import json
import os
import pandas as pd
import requests
import unicodedata
import zeep

import app.log
import app.utilities

logger = app.log.setup_logger(__name__)

# ----------------------------

def normalize(word):
    """Transforme la string en un format plus simple
    """
    word = word.strip()
    word = unicodedata.normalize('NFD', word)
    word = word.encode('ascii', 'ignore')
    return word.decode("utf-8")

# ----------------------------

def get_info_lettre_suivie(cmd):
    """ Prepare les informations requises pour generer l'etiquette lettre suivie

    Parameters
    ----------
    cmd : dict
        Dict des informations de la commande
    """

    parameters = {}

    customer_info = cmd['customer_info']
    delivery_address = cmd['delivery_address']
    products = cmd['products']

    parameters["Id_Cmd"] = cmd["id"]
    parameters["Expe_Ad1"] = "GATPHARM"
    parameters["Expe_Ad2"] = "7BIS RUE EMILE BLANC"
    parameters["Expe_Ville"] = "DOMENE"
    parameters["Expe_CP"] = "38420"
    parameters["Expe_Pays"] = "France"
    parameters["Expe_Tel1"] = "+330476772308"
    parameters["Dest_Ad1"] = normalize(customer_info['name'])
    parameters["Dest_Ad2"] = normalize(delivery_address['street_address'])
    parameters["Dest_Ad3"] = normalize(delivery_address['suburb'])
    parameters["Dest_Ville"] = normalize(delivery_address['city'])
    parameters["Dest_CP"] = delivery_address['postcode']
    parameters["Dest_Pays"] = normalize(delivery_address['country'])

    prefix = "+"
    phone = customer_info['phone'].replace('(', '')
    phone = phone.replace(')', '')
    phone = phone.replace('+', '')
    if delivery_address['country_code'] == 'FR' and (phone[:2] != '33'):
        prefix = prefix + '33'
    parameters["Dest_Tel1"] = prefix + phone

    poids = 0.0
    for key in products:
        prod = products[key]
        poids += int(prod['quantity']) * float(prod['weight'])

    parameters["Poids"] = str(int(poids * 1000)) + 'g'

    return parameters

# ----------------------------

def make_pdf(data, spacing=1):
    """Génère le pdf de l'etiquette lettre suivie

    Parameters
    ----------
    data : dict
        Dict avec les info pour generer l'etiquette
    spacing : int
        Taille entre chaque ligne
    """
    dimension = [4, 6]
    pdf = FPDF("P", "in", dimension)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    data = [
    "Expediteur",
    f"          {data['Expe_Ad1']}",
    f"          {data['Expe_Ad2']}",
    f"          {data['Expe_CP']} {data['Expe_Ville']}",
    f"          {data['Expe_Pays']}",
    f"          {data['Expe_Tel1']}",
    "",
    'Destinataire',
    f"          {data['Dest_Ad1'].upper()}",
    f"          {data['Dest_Ad2'].upper()}",
    f"          {data['Dest_Ad3'].upper()}",
    f"          {data['Dest_CP']} {data['Dest_Ville']}",
    f"          {data['Dest_Pays']}",
    f"          {data['Dest_Tel1']}",
    "",
    f"Ref Client : {data['Id_Cmd']}                     Poids : {data['Poids']}"
    ]
 
    col_width = pdf.w
    row_height = pdf.font_size

    for item in data:
        if item == "Expediteur":
            pdf.set_font("Arial", size=6)
        elif item == "Destinataire":
            pdf.set_font("Arial", size=10)
        pdf.cell(col_width, row_height * spacing, txt=item)
        pdf.ln(row_height * spacing)

    pdf.line(0.4,0.4,1.6,1.2)
    pdf.line(0.4,1.2,1.6,0.4)

    pdf.output(app.utilities.get_path("docs/etiquette_lettre_suivie.pdf"))

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

def get_info_expedition(cmd, enseigne, private_key):
    """ Prepare les informations requises pour generer l'expedition Mondial Relay

    Parameters
    ----------
    cmd : dict
        Dict des informations de la commande
    enseigne : str
        Parametre de securité pour le web service : regarder la documentation
    private_key : str
        Parametre de securité pour le web service : regarder la documentation

    Return
    ------
    parameters : dict
        Dict avec les info necessaires pour appeler la fonction WSI2_CreationExpedition du web service Mondial Relay
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

def get_info_etiquette(enseigne, expeditions, langue, private_key):
    """ Prepare les informations requises pour generer l'etiquette Mondial Relay

    Parameters
    ----------
    enseigne : str
        Parametre de securité pour le web service : regarder la documentation
    expeditions : str
        Nombre d'expedition généré par Mondial Relaly
    langue : str
        Langue du client
    private_key : str
        Parametre de securité pour le web service : regarder la documentation

    Return
    ------
    parameters : dict
        Dict avec les info necessaires pour appeler la fonction WSI3_GetEtiquettes du web service Mondial Relay
    """
    parameters = {}
    parameters["Enseigne"] = enseigne # Obligatory
    parameters["Expeditions"] = expeditions # Obligatory
    parameters["Langue"] = langue # Obligatory
    parameters["Security"] = generate_security_key(private_key, parameters) # Obligatory

    return parameters

# ----------------------------

def setstatus(id_cmd, status, tracking_code):
    """ Change le status d'une commande

    Parameters
    ----------
    id_cmd : str
        Identification de la commande
    status : int
        Nouvel status de la commande
    tracking_code : str
        Code d'expedition Mondial Relay
    """

    cle_api = app.utilities.get_config_data()['cle_api']
    data = [{"id": id_cmd, "status": str(status), "shipping": {"tracking_code": tracking_code}}]
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    url = f"http://pharmashopi.com/api/orders?key={cle_api}"
    r = requests.put(url, data=json.dumps(data), headers=headers)

# ----------------------------

def add_to_list(id_cmd, exp_nbr, mode_livraison):
    """Ajoute la commande dans la liste du jour. Necessaire pour finaliser les commandes à la main

    Parameters
    ----------
    id_cmd : str
        Identification de la commande
    exp_nbr : str
        Tracking code
    mode_livraison : str
        Mode de livraison
    """
    if mode_livraison == 'Mondial Relay':
        mode_livraison = 'mondial_relay'
        exp_nbr = str('%08d' %  int(exp_nbr))
    elif mode_livraison == 'Lettre suivie':
        mode_livraison = 'lettre_suivie'
        exp_nbr = str(exp_nbr)

    entry = {str(id_cmd): exp_nbr}
    entry = DataFrame(entry.values(), index=entry.keys(), columns=['NumeroColis'])
    entry.index.name  ='NumeroCommande'

    date = datetime.datetime.today()
    file_name = mode_livraison + '_' + date.strftime('%d-%b-%Y')

    path = app.utilities.get_path(f"docs/tracking_{mode_livraison}/{file_name}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0, sep=';', dtype={'NumeroColis': str})
        df = df.append(entry, sort=True)
        df.to_csv(path, sep=';')
    else:
        entry.to_csv(path, sep=';')

# ----------------------------

def lettre_suivie(cmd):
    """Processus lettre suivie
    """
    parameters = get_info_lettre_suivie(cmd)
    logger.info(f"Parametres de l'etiquette : {parameters}")
    logger.new_formatter(mode="newline")
    make_pdf(parameters)

# ----------------------------

def mondial_relay_error(id_cmd, reponse):
    """Print le type d'erreur mondial relay

    Parameters
    ----------
    id_cmd : str
        Identification de la commande
    reponse : dict
        Dict avec la reponse de la requete
    """
    path = app.utilities.get_path("docs/MondialRelay/codes_web_service.csv")
    codes = pd.read_csv(path, index_col='Code', sep=';')
    print(f"Etiquette pour la commande {id_cmd} non générée")
    logger.info(f"Etiquette pour la commande {id_cmd} non générée")
    logger.error(f"Error {reponse['STAT']} : {codes.iloc[int(reponse['STAT'])]['Label']}")
    logger.new_formatter(mode="end_process")

# ----------------------------

def mondial_relay(cmd, mode_teste):
    """Processus mondial relay
    """

    config_data = app.utilities.get_config_data()
    if mode_teste:
        enseigne = config_data["enseigne_testing"]
        private_key = config_data["cle_testing"]
    else:
        enseigne = config_data["enseigne_production"]
        private_key = config_data["cle_production"]

    wsdl = "http://api.mondialrelay.com/Web_Services.asmx?WSDL"
    client = Client(wsdl)
    parameters = get_info_expedition(cmd, enseigne, private_key)
    r_expedition = client.service.WSI2_CreationExpedition(**parameters)
    #r = client.service.WSI2_CreationEtiquette(**parameters_etiquette)

    logger.info(f"Parametres de l'etiquette : {parameters}")
    logger.new_formatter(mode="newline")

    if r_expedition['STAT'] != '0':
        mondial_relay_error(cmd['id'], r_expedition)
        raise()

    exp_nbr = r_expedition['ExpeditionNum']
    r_etiquette = client.service.WSI3_GetEtiquettes(**get_info_etiquette(enseigne, exp_nbr, parameters["Dest_Langage"], private_key))

    if r_etiquette['STAT'] != '0':
        mondial_relay_error(cmd['id'], r_etiquette)
        raise()

    url = "http://www.mondialrelay.com"
    url_etiquette = url + r_etiquette['URL_PDF_10x15']
    #position = url_etiquette.find('format=')
    #url_etiquette = url_etiquette[: position+7] + '10x15' + url_etiquette[position+9 :]
    response = requests.get(url_etiquette)
    file = open(app.utilities.get_path("docs/etiquette_mondial_relay.pdf"), 'wb')
    file.write(response.content)
    file.close()

    return exp_nbr

# ----------------------------

def generer_etiquette(id_cmd, finaliser, mode_livraison, mode_teste, exp_nbr=None):
    """ Création de l'etiquette

    Parameters
    ----------
    id_cmd : str
        Identification de la commande
    finaliser : boolean
        Si on doit finaliser ou non la commande (pas active en raison du back-office)
    mode_livraison : str
        Selectionne le type d'etiquette selon la livraison
    mode_teste : boolean
        Si on est dans le mode de testing ou de production
    exp_nbr : str
        Code d'expedition lettre suivie (le code mondial relay est généré, et pas envoyé avant)
    """

    try:
        cmd = app.utilities.get_request(f"api/orders/filter/id/{id_cmd}")

        for key in cmd:
            cmd = cmd[key]

        if exp_nbr == None:
            exp_nbr = mondial_relay(cmd, mode_teste)
        else:
            lettre_suivie(cmd)

        if not mode_teste: 
            add_to_list(id_cmd, exp_nbr, mode_livraison)

        if finaliser == 1 and not mode_teste:
            setstatus(cmd['id'], '3', exp_nbr)
            print(f"La commande {id_cmd} a changée de status\n")
            logger.info(f"Status de la commande {id_cmd} : {app.utilities.get_status(id_cmd)}")
            logger.new_formatter(mode="newline")

        print(f"Etiquette pour la commande {id_cmd} générée. Son code d'expedition est {exp_nbr}\n\n")
        logger.info(f"Etiquette pour la commande {id_cmd} générée. Son code d'expedition est {exp_nbr}")
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

# ----------------------------

def generate_recap():
    """Fait le recap du jour de mondial relay
    """
    date = datetime.datetime.today()
    file_name_1 = 'recap_' + date.strftime('%d-%b-%Y')
    file_name_2 = 'mondial_relay_' + date.strftime('%d-%b-%Y')

    path = app.utilities.get_path(f'docs/tracking_mondial_relay/{file_name_2}.csv')
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0, sep=';', dtype={'NumeroColis': str})

        path = app.utilities.get_path(f'docs/recap_mondial_relay/{file_name_1}.txt')
        f_recap = open(path, 'w')

        f_recap.write(f"Date de la collecte Mondial Relay : {date.strftime('%d-%b-%Y')}\n\n")
        f_recap.write("Expediteur : GATPHARM\n")
        f_recap.write("             7bis Rue Emile Blanc\n")
        f_recap.write("             38420 - Domene\n\n")
        f_recap.write("Numero de Compte : 826566 (Toopost)\n")
        f_recap.write(f"Numero de Colis : {len(df.index)}\n\n")
        f_recap.write(f"{df}")

        f_recap.close()

        print("Le recap a bien été générée")

    else:
        print(f"Fichier de tracking du jour {date.strftime('%d-%b-%Y')} n'existe pas")