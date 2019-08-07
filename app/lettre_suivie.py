# -*- coding: utf-8 -*-

from fpdf import FPDF
from pandas import DataFrame
from requests.exceptions import HTTPError
import datetime
import json
import os
import pandas as pd
import requests
import unicodedata

import app.log
import app.utilities

logger = app.log.setup_logger(__name__)

# ----------------------------
def normalize(word):
    word = word.strip()
    word = unicodedata.normalize('NFD', word)
    word = word.encode('ascii', 'ignore')
    return word.decode("utf-8")

# ----------------------------

def get_info_lettre_suivie(cmd):
    """ Prepare les informations requises pour generer l'etiquette

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
    url = f"http://pharmashopi.com/api/orders"
    r = requests.put(url, data=json.dumps(data), headers=headers)

# ----------------------------

def make_pdf(data, spacing=1):
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
            pdf.set_font("Arial", size=7)
        elif item == "Destinataire":
            pdf.set_font("Arial", size=10)
        pdf.cell(col_width, row_height * spacing, txt=item)
        pdf.ln(row_height * spacing)

    pdf.output(app.utilities.get_path("docs/etiquette_lettre_suivie.pdf"))

# ----------------------------

def add_to_list(idcmd, exp_nbr):
    entry = {str(idcmd): str(exp_nbr)}

    entry = DataFrame(entry.values(), index=entry.keys(), columns=['NumeroColis'])
    entry.index.name  ='NumeroCommande'

    date = datetime.datetime.today()
    file_name = 'lettre_suivie_' + date.strftime('%d-%b-%Y')

    path = app.utilities.get_path(f"docs/tracking_lettre_suivie/{file_name}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path, index_col=0, sep=';')
        df = df.append(entry, sort=True)
        df.to_csv(path, sep=';')
    else:
        entry.to_csv(path, sep=';')

# ----------------------------

def generer_etiquette(idcmd, finaliser, exp_nbr, mode_teste):
    """ Création de l'etiquette

    Parameters
    ----------
    idcmd : str
        Identification de la commande
    """

    try:
        cmd = app.utilities.get_request(f"api/orders/filter/id/{idcmd}")

        for key in cmd:
            cmd = cmd[key]

        parameters = get_info_lettre_suivie(cmd)

        logger.info(f"Parametres de l'etiquette : {parameters}")
        logger.new_formatter(mode="newline")

        make_pdf(parameters)

        if not mode_teste : 
            add_to_list(idcmd, exp_nbr)

        if finaliser == 1 and not mode_teste:
            setstatus(cmd['id'], '3', exp_nbr)
            print(f"La commande {idcmd} a changée de status\n")
            logger.info(f"Status de la commande {idcmd} : {app.utilities.get_status(idcmd)}")
            logger.new_formatter(mode="newline")

        print(f"Etiquette pour la commande {idcmd} générée. Son code d'expedition est {exp_nbr}\n\n")
        logger.info(f"Etiquette pour la commande {idcmd} générée. Son code d'expedition est {exp_nbr}")
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




