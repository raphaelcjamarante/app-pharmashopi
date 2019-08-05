# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, 
                             QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QProgressBar,
                             QPushButton, QRadioButton, QSpinBox, QStackedWidget, QTabWidget, QVBoxLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QIcon)

import pandas as pd
import requests

import app.process
import app.utilities

cle_api = app.utilities.get_config_data()['cle_api']

#------------------------------------------------------------
class detection(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []

        main_layout = QVBoxLayout()

        button_start = QPushButton("Démarrer")
        button_start.clicked.connect(self.demarrer_detection)
        main_layout.addWidget(button_start)

        #self.progress = QProgressBar(self)

        # ----------

        form_params = QFormLayout()

        label = QLabel()
        label.setText("Selectionnez le(s) site(s) à rechercher : ")

        self.cb_site_1 = QCheckBox("Pharmashopi")
        self.cb_site_1.setChecked(True)
        self.cb_site_2 = QCheckBox("Espace Contention")
        self.cb_site_2.setChecked(False)

        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self.cb_site_1)
        hbox.addWidget(self.cb_site_2)

        form_params.addRow(label, hbox)

        # ----------

        label = QLabel()
        label.setText("Nombre de commandes souhaité pour la détection : ")

        self.sb_nbrcmds = QSpinBox()
        self.sb_nbrcmds.setMaximum(1000)
        self.sb_nbrcmds.setValue(100)
        
        form_params.addRow(label, self.sb_nbrcmds)

        # ----------

        label = QLabel()
        label.setText("Nombre de jours pour examiner des commandes multiples : ")

        self.sb_nbrjours = QSpinBox()
        self.sb_nbrjours.setValue(3)
        
        form_params.addRow(label, self.sb_nbrjours)

        # ----------

        gb_params = QGroupBox("Paramètres")
        gb_params.setLayout(form_params)
        main_layout.addWidget(gb_params)

        # ----------

        self.list_depts = QListWidget()
        self.make_list_depts()

        button_save = QPushButton("Sauvegarder Modifications")
        button_save.clicked.connect(self.save)
        button_cancel = QPushButton("Annuler Modifications")
        button_cancel.clicked.connect(self.cancel)
        hbox = QHBoxLayout()
        hbox.addWidget(button_save)
        hbox.addWidget(button_cancel)

        vbox_depts = QVBoxLayout()
        vbox_depts.addWidget(self.list_depts)
        vbox_depts.addLayout(hbox)

        # ----------

        gb_depts = QGroupBox("Départements Risque")
        gb_depts.setLayout(vbox_depts)

        # ----------

        self.list_prods = QListWidget()
        self.make_list_prods()

        button_add = QPushButton("Ajouter")
        button_add.clicked.connect(self.add)
        button_del = QPushButton("Supprimer")
        button_del.clicked.connect(self.delete)
        hbox = QHBoxLayout()
        hbox.addWidget(button_add)
        hbox.addWidget(button_del)

        vbox_prods = QVBoxLayout()
        vbox_prods.addWidget(self.list_prods)
        vbox_prods.addLayout(hbox)

        # ----------

        gb_prods = QGroupBox("Produits Risque")
        gb_prods.setLayout(vbox_prods)

        # ----------

        hbox = QHBoxLayout()
        hbox.addWidget(gb_depts)
        hbox.addWidget(gb_prods)
        main_layout.addLayout(hbox)


        # ----------

        self.setLayout(main_layout)

    # ----------- Actions ---------------------

    def demarrer_detection(self):
        choix = QMessageBox.question(self, 'Continuer Procedure', "Continuer?", QMessageBox.Yes | QMessageBox.No)
        if choix == QMessageBox.Yes:
            #self.progress.setValue(10)
            sites = {"Pharmashopi": self.cb_site_1.isChecked(), "Espace Contention": self.cb_site_2.isChecked()}
            app.process.detection_arnaque(self.sb_nbrcmds.value(), sites, self.sb_nbrjours.value(), self.mode_teste)
            #self.progress.setValue(10)

    # --------------------------
    def save(self):
        path = app.utilities.get_path("docs/arnaque/depts_risque.csv")
        depts_risque = pd.read_csv(path, index_col='code')
        for i in range(len(self.list_depts)):
            code = self.list_depts.item(i).text().split()[0]
            risque = self.list_depts.item(i).checkState()
            depts_risque.loc[int(code),'risque'] = bool(risque)
        depts_risque.to_csv(path)

    # --------------------------
    def cancel(self):
        self.make_list_depts()

    # --------------------------
    def add(self):
        dialog = dialog_add_prod(self.mode_teste)
        self.children.append(dialog)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            new_prod = dialog.get_inputs()
            path = app.utilities.get_path("docs/arnaque/prods_risque.csv")
            prods_risque = pd.read_csv(path, index_col='id')
            prods_risque.loc[new_prod['id']] = [new_prod['brand_name'], new_prod['name']]
            prods_risque.sort_values(by='brand_name', inplace=True)
            prods_risque.to_csv(path)
            self.make_list_prods()

    # --------------------------
    def delete(self):
        prod = self.list_prods.selectedItems()
        if prod:
            msg = "Procéder et supprimer le produit sélectionné?"
            choix = QMessageBox.question(self, 'Delete Product', msg, QMessageBox.Yes | QMessageBox.No)
            if choix == QMessageBox.Yes:
                id_prod = prod[0].text().split(" - ")[0]
                path = app.utilities.get_path("docs/arnaque/prods_risque.csv")
                prods_risque = pd.read_csv(path, index_col='id')
                prods_risque.drop(int(id_prod), inplace=True)
                prods_risque.to_csv(path)
                self.make_list_prods()
        else:
            QMessageBox.information(self, 'Delete Product', "Aucun produit selectionné", QMessageBox.Ok)

    # --------------------------
    def make_list_prods(self):
        self.list_prods.clear()
        path = app.utilities.get_path("docs/arnaque/prods_risque.csv")
        prods_risque = pd.read_csv(path, index_col='id')
        for id_prod,marque,nom in zip(prods_risque.index, prods_risque['brand_name'], prods_risque['name']):
            self.list_prods.addItem(f"{str(id_prod)} - {str(marque)} - {str(nom)}")

    # --------------------------
    def make_list_depts(self):
        self.list_depts.clear()
        path = app.utilities.get_path("docs/arnaque/depts_risque.csv")
        depts_risque = pd.read_csv(path, index_col='code')
        for index, dept, risque in zip(depts_risque.index, depts_risque['department'], depts_risque['risque']):
            cb_dept = QListWidgetItem()
            cb_dept.setCheckState(Qt.Checked if risque else Qt.Unchecked)
            cb_dept.setText(f"{str(index)} - {str(dept)}")
            self.list_depts.addItem(cb_dept)

#------------------------------------------------------------
class dialog_add_prod(QDialog):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []

        self.setWindowTitle("Ajouter Produit de Risque")
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowIcon(QIcon(app.utilities.get_path("docs/images/icon.png")))

        layout = QFormLayout()

        self.id_prod = QLineEdit()
        layout.addRow(QLabel("Id Produit"), self.id_prod)
        self.marque_prod = QLineEdit()
        layout.addRow(QLabel("Marque Produit"), self.marque_prod)
        self.nom_prod = QLineEdit()
        layout.addRow(QLabel("Nom Produit"), self.nom_prod)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.setLayout(layout)

    # ----------- Actions ---------------------
    def accept(self):
        if (self.id_prod.text() != "") and (self.marque_prod.text() != "") and (self.nom_prod.text() != ""):
            prods = app.utilities.get_request(f"api/products/filter/id/{self.id_prod.text()}?key={cle_api}")

            if prods:
                return super().accept()
            else:
                QMessageBox.critical(self, 'Error', "Id invalide", QMessageBox.Ok)
        else:
            QMessageBox.critical(self, 'Error', "Paramètres Invalides", QMessageBox.Ok)

    def get_inputs(self):
        return {"id": self.id_prod.text(), "brand_name": self.marque_prod.text(), "name": self.nom_prod.text()}
