# -*- coding: utf-8 -*-

from barcode.writer import ImageWriter
import barcode
import datetime
import os
import unicodedata
import xlsxwriter

import app.log
import app.utilities

logger = app.log.setup_logger(__name__)


#------------------------------------------------------------
def cell_format(workbook, mode):
    """ Crée les celules xlsx

    Parameters
    ----------
    workbook : objet xlsx
        Fichier xlsx utilisé
    mode : str
        Selectionne le mode : picking ou bonprep

    Return
    ------
    cells : dict
        Dictionnaire avec les formats de celules
    """

    cells = {}

    cell_format2 = workbook.add_format({'text_wrap': True})
    cell_format2.set_border(7)
    cell_format2.set_align('center')
    cell_format2.set_align('vcenter')
    cells["2"] = cell_format2

    cell_format3 = workbook.add_format({'text_wrap': True})
    cell_format3.set_bold()
    cell_format3.set_border(7)
    cell_format3.set_align('center')
    cell_format3.set_align('vcenter')
    cells["3"] = cell_format3

    cell_format6 = workbook.add_format({'text_wrap': True})
    cell_format6.set_bold()
    cell_format6.set_border(7)
    cell_format6.set_font_size(17)
    cell_format6.set_align('center')
    cell_format6.set_align('vcenter')
    cells["6"] = cell_format6

    cell_format7 = workbook.add_format({'text_wrap': True})
    cell_format7.set_bold()
    cell_format7.set_border(7)
    cell_format7.set_font_size(6)
    cell_format7.set_align('center')
    cell_format7.set_align('vcenter')
    cells["7"] = cell_format7


    if mode == "picking":
        cell_format2bis = workbook.add_format({'text_wrap': True})
        cell_format2bis.set_border(7)
        cell_format2bis.set_align('center')
        cell_format2bis.set_align('vcenter')
        cell_format2bis.set_font_strikeout()
        cells["2bis"] = cell_format2bis

        cell_format3bis = workbook.add_format({'text_wrap': True})
        cell_format3bis.set_bold()
        cell_format3bis.set_border(7)
        cell_format3bis.set_align('center')
        cell_format3bis.set_align('vcenter')
        cell_format3bis.set_font_strikeout()
        cells["3bis"] = cell_format3bis

        cell_format4 = workbook.add_format({'text_wrap': True})
        cell_format4.set_bold()
        cell_format4.set_underline()
        cell_format4.set_border(7)
        cell_format4.set_align('center')
        cell_format4.set_align('vcenter')
        cells["4"] = cell_format4

        cell_format6bis = workbook.add_format({'text_wrap': True})
        cell_format6bis.set_bold()
        cell_format6bis.set_border(7)
        cell_format6bis.set_font_size(17)
        cell_format6bis.set_align('center')
        cell_format6bis.set_align('vcenter')
        cell_format6bis.set_font_strikeout()
        cells["6bis"] = cell_format6bis


    if mode == "bonprep":
        cell_format11 = workbook.add_format({'text_wrap': True})
        cell_format11.set_bold()
        cell_format11.set_border(7)
        cells["11"] = cell_format11

        cell_format33 = workbook.add_format({'text_wrap': True})
        cell_format33.set_bold()
        cell_format33.set_border(7)
        cell_format33.set_align('center')
        cell_format33.set_align('vcenter')
        cells["33"] = cell_format33

        cell_format4 = workbook.add_format({'text_wrap': True})
        cell_format4.set_font_size(10)
        cell_format4.set_border(7)
        cell_format4.set_align('vcenter')
        cells["4"] = cell_format4

        total_format = workbook.add_format({'text_wrap': True})
        total_format.set_border(7)
        total_format.set_align('right')
        total_format.set_align('vcenter')
        cells["total"] = total_format

        cell_format9 = workbook.add_format({'text_wrap': True})
        cell_format9.set_bold()
        cell_format9.set_border(7)
        cell_format9.set_font_size(13)
        cell_format9.set_align('center')
        cell_format9.set_align('vcenter')
        cells["9"] = cell_format9

    return cells


#------------------------------------------------------------
def picking_doc(listeProd, totalquantity, range_cmds, livraison):
    """ Fait la documentation du picking

    Parameters
    ----------
    listeProd : list
        Liste de dictionnaires de chaque produit
    totalquantity : int
        Quantité totale de articles dans toutes les commandes d'un batch
    range_cmds : str
        String avec les nombres de la premiere et de la derniere commande
    """

    try:
        workbook = xlsxwriter.Workbook(app.utilities.get_path("docs/Picking.xlsx"))
        workbook.close()
    except Exception:
        logger.error("Fichier Picking.xlsx est ouvert. Fermez-le.")
        logger.new_formatter("newline")
        raise

    print("Écriture Picking.xlsx...")
    print("******************************************\n")

    workbook = xlsxwriter.Workbook(app.utilities.get_path("docs/Picking.xlsx"))

    cf = cell_format(workbook, "picking")

    worksheet = workbook.add_worksheet()
    worksheet.set_margins(0.2, 0.2, 0.2, 0.2)
    worksheet.set_column(0, 0, 3)
    worksheet.set_column(1, 1, 4)
    worksheet.set_column(2, 2, 7)
    worksheet.set_column(3, 3, 14)
    worksheet.set_column(4, 4, 12)
    worksheet.set_column(5, 5, 37)
    worksheet.set_column(6, 6, 7)
    worksheet.set_column(7, 7, 7)

    path = app.utilities.get_path("docs/images/pharmashopi.png")
    worksheet.insert_image('A3', path, {'x_scale': 0.5, 'y_scale': 0.5})

    now = datetime.datetime.now()

    worksheet.merge_range('B6:D7', f"Type livraison : {livraison}", cf["3"])

    worksheet.write(2, 5, now.strftime("%A %d %b %Y"), cf["4"])
    worksheet.write(3, 5, f"Heure : {now.strftime('%H:%M:%S')}", cf["4"])
    worksheet.write(4, 5, "Bon de preparations : ", cf["4"])
    worksheet.write(5, 5, range_cmds, cf["3"])
    worksheet.write(6, 5, f"{str(totalquantity)} produits", cf["3"])

    worksheet.write(8, 1, 'Qte', cf["3"])
    worksheet.write(8, 2, 'Stock', cf["3"])
    worksheet.write(8, 3, 'Code barres', cf["3"])
    worksheet.write(8, 4, 'Marque', cf["3"])
    worksheet.write(8, 5, 'Article', cf["3"])
    worksheet.write(8, 6, 'Options', cf["3"])
    worksheet.write(8, 7, 'Prix(ht)', cf["3"])

    row = 10
    col = 0

    for prod in listeProd:
        if int(prod["robot_stock"]) < int(prod["quantity"])  :
            worksheet.write(row, col, prod["robot_stock"], cf["2"])
            worksheet.write(row, col + 1, prod["quantity"], cf["6"])
            worksheet.write(row, col + 3, prod["reference"], cf["3"])
            worksheet.write(row, col + 5, prod["name"], cf["2"])
        else:
            worksheet.write(row, col, prod["robot_stock"], cf["2bis"])
            worksheet.write(row, col + 1, prod["quantity"], cf["6bis"])
            worksheet.write(row, col + 3, prod["reference"], cf["3bis"])
            worksheet.write(row, col + 5, prod["name"], cf["2bis"])

        worksheet.write_string(row, col + 2, prod["stock"], cf["2"])
        worksheet.write(row, col + 4, prod["brand_name"], cf["2"])
        worksheet.write(row, col + 6, prod["options"], cf["7"])
        worksheet.write(row, col + 7, prod["price"], cf["2"])
        row += 1

    workbook.close()

    logger.info("Picking.xlsx écrit")
    logger.new_formatter("newline")


#------------------------------------------------------------
def bonprep_doc(cmds, infoBonprep):
    """ Fait la documentation des bons de preparation

    Parameters
    ----------
    cmds : dict
        Dictionnaire de commandes complet
    infoBonprep : dict
        Dictionnaire avec les info pour les bons de preparation
    """

    try:
        workbook = xlsxwriter.Workbook(app.utilities.get_path("docs/BonCommande.xlsx"))
        workbook.close()
    except Exception:
        logger.error("Fichier BonCommande.xlsx est ouvert. Fermez-le.")
        logger.new_formatter("newline")
        raise

    print("Écriture BonCommande.xlsx...")
    print("******************************************\n")

    workbook = xlsxwriter.Workbook(app.utilities.get_path("docs/BonCommande.xlsx"))

    cf = cell_format(workbook, "bonprep")

    ean_index = 0

    ordreCmds = list(infoBonprep.keys())
    ordreCmds.sort()

    for idcmd in ordreCmds:
        cmd = cmds[idcmd]
        infoClient = cmd["customer_info"]
        livraison = cmd["delivery_address"]
        payement = cmd["payment"]["method_name"]
        date = cmd["date_created"][2:4] + cmd["date_created"][5:7] + cmd["date_created"][8:10]
        strdate = f"{cmd['date_created'][8:10]} - {cmd['date_created'][5:7]} - {cmd['date_created'][0:4]}"

        EAN = barcode.get_barcode_class('ean13')
        ean = EAN(str(idcmd) + date, writer=ImageWriter())
        path = app.utilities.get_path("docs/barcodes/ean13" + str(ean_index))
        filename = ean.save(path)

        worksheet = workbook.add_worksheet()
        worksheet.set_margins(0.2, 0.2, 0.2, 0.2)
        worksheet.set_column(0, 0, 4)
        worksheet.set_column(1, 1, 5)
        worksheet.set_column(2, 2, 13.5)
        worksheet.set_column(3, 3, 11.5)
        worksheet.set_column(4, 4, 30)
        worksheet.set_column(5, 5, 6.5)
        worksheet.set_column(6, 6, 7)
        worksheet.set_column(7, 7, 6)
        worksheet.set_column(8, 8, 6)

        path = app.utilities.get_path("docs/images/pharmashopi.png")
        worksheet.insert_image('B2', path, {'x_scale': 0.45, 'y_scale': 0.45})
        path = app.utilities.get_path("docs/barcodes/ean13" + str(ean_index) + ".png")
        worksheet.insert_image('G2', path, {'x_scale': 0.25, 'y_scale': 0.25})
        ean_index += 1

        worksheet.merge_range('A7:C8', 'Commande : ' + str(idcmd), cf["9"])
        worksheet.merge_range('A9:C9', 'Numero client : ' + str(infoClient["id"]), cf["3"])
        worksheet.merge_range('A10:C10', 'Date : ' + strdate, cf["3"])
        worksheet.merge_range('A11:C12', str(unicodedata.normalize('NFD', payement)), cf["3"])
        worksheet.merge_range('A13:C14', infoBonprep[idcmd]["total_quantity"] + " articles", cf["9"])

        worksheet.merge_range('F7:I7', "Adresse de livraison: ", cf["3"])
        name = unicodedata.normalize('NFD', infoClient["name"]) + '\n'
        company = unicodedata.normalize('NFD', livraison["company"]) + '\n'
        if livraison["name"] != infoClient["name"]:
            company = unicodedata.normalize('NFD', livraison["name"]) + '\n'
        street = unicodedata.normalize('NFD', livraison["street_address"]) + '\n'
        city = unicodedata.normalize('NFD', livraison["city"]) + ", "
        postcode = unicodedata.normalize('NFD', livraison["postcode"]) + '\n'
        country = unicodedata.normalize('NFD', livraison["country"]) + '\n'
        telephone = unicodedata.normalize('NFD', livraison["phone"]) +'\n'
        if telephone == "\n":
            telephone = unicodedata.normalize('NFD', infoClient["phone"]) +'\n'
        email = str(unicodedata.normalize('NFD', infoClient["email"]))
        chaineadresse = name + company + street + city + postcode + country + telephone + email
        worksheet.merge_range('F8:I14', chaineadresse, cf["4"])

        row = 16
        info_sante = app.utilities.get_sante(idcmd)
        for key in info_sante:
            worksheet.merge_range(f"A{str(row)}:I{str(row)}", unicodedata.normalize('NFD', info_sante[key]), cf["11"])
            row += 1

        row += 1
        worksheet.write(row, 0, 'Qte', cf["33"])
        worksheet.write(row, 1, 'Notes', cf["33"])
        worksheet.write(row, 2, 'Code barres', cf["33"])
        worksheet.write(row, 3, 'Marque', cf["33"])
        worksheet.write(row, 4, 'Article', cf["33"])
        worksheet.write(row, 5, 'Options', cf["33"])
        worksheet.write(row, 6, 'Poids', cf["33"])
        worksheet.write(row, 7, 'Prix u HT', cf["33"])
        worksheet.write(row, 8, 'Total TTC', cf["33"])

        row += 1
        col = 0

        listeProd = infoBonprep[idcmd]["list_prod"]

        for prod in listeProd:
            if (prod["reference"] != ""):
                worksheet.write(row, col, prod["quantity"], cf["6"])
            worksheet.write(row, col + 1,  " ", cf["2"])
            worksheet.write(row, col + 2, prod["reference"], cf["3"])
            worksheet.write(row, col + 3, prod["brand_name"], cf["2"])
            worksheet.write(row, col + 4, prod["name"], cf["2"])
            worksheet.write(row, col + 5, prod["options"], cf["7"])
            worksheet.write(row, col + 6, prod["weight"], cf["2"])
            worksheet.write(row, col + 7, prod["ht"], cf["2"])
            worksheet.write(row, col + 8, str(round(float(prod["final_price"]) * int(prod["quantity"]), 2)), cf["2"])
            row += 1

        totalht = infoBonprep[idcmd]["totalht"]
        totalttc = infoBonprep[idcmd]["totalttc"]
        worksheet.write(row + 2, 7, totalht, cf["total"])
        worksheet.write(row + 4, 7, totalttc, cf["total"])
        worksheet.write(row + 3, 7, str(round(float(totalttc) - float(totalht), 2)), cf["total"])

        worksheet.merge_range(f"F{str(row + 3)}:G{str(row + 3)}", "Total HT: ", cf["3"])
        worksheet.merge_range(f"F{str(row + 4)}:G{str(row + 4)}", "TVA: ", cf["3"])
        worksheet.merge_range(f"F{str(row + 5)}:G{str(row + 5)}", "Total TTC: ", cf["3"])
    
    workbook.close()

    logger.info("BonCommande.xlsx écrit")
    logger.new_formatter("newline")