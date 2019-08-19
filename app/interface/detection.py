# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, 
                             QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QPushButton, 
                             QSpinBox, QVBoxLayout, QWidget)
import app.process
import app.utilities
import pandas as pd

# ------------------------------------------------------------

class Detection(QWidget):
    """Scam detection tab

    Attributes
    ----------
    children : list
        Widgets created directly under in the 'hierarchy'
    mode_teste : bool
        Control of testing mode
    cb_site_1 : QCheckBox
        Selection of site to make the requests (pharmashopi)
    cb_site_2 : QCheckBox
        Selection of site to make the requests (espace contention)
    sb_nbrcmds : QSpinBox
        Selection of number of orders
    sb_nbrjours : QSpinBox
        Selection of minimum number of days that make multiple orders by one client suspicious
    list_depts : QListWidget
        Selection of french departments considered risky
    list_prods : QListWidget
        Selection of products considered risky

    Methods
    -------
    demarrer_detection(self)
        Initializes only the detection process
    save(self)
        Saves to file the changes in the risky departments
    cancel(self)
        Cancels changes to the risky departments, restoring the default
    add(self)
        Adds product to list of risky product
    delete(self)
        Deletes product from list of risky product
    make_list_prods(self)
        Reads file and creates list of risky product
    make_list_depts(self)
        Reads file and creates list of risky departments
    """

    def __init__(self, mode_teste):
        super().__init__()
        self.children = []
        self.mode_teste = mode_teste

        main_layout = QVBoxLayout()

        button_start = QPushButton("Démarrer")
        button_start.clicked.connect(lambda: self.demarrer_detection('batch'))
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
        self.sb_nbrcmds.setMinimum(1)
        self.sb_nbrcmds.setMaximum(1000)
        self.sb_nbrcmds.setValue(100)
        
        form_params.addRow(label, self.sb_nbrcmds)

        # ----------

        label = QLabel()
        label.setText("Nombre de jours pour examiner des commandes multiples : ")

        self.sb_nbrjours = QSpinBox()
        self.sb_nbrjours.setMinimum(1)
        self.sb_nbrjours.setMaximum(5)
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

        form_single_detection = QFormLayout()

        label = QLabel()
        label.setText("Id Commande : ")
        self.le_id_cmd = QLineEdit()
        form_single_detection.addRow(label, self.le_id_cmd)

        button_start_single = QPushButton("Démarrer")
        button_start_single.clicked.connect(lambda: self.demarrer_detection('single'))

        hbox = QHBoxLayout()
        hbox.addLayout(form_single_detection)
        hbox.addWidget(button_start_single)

        gb_single_detection = QGroupBox("Detection Singulaire")
        gb_single_detection.setLayout(hbox)
        main_layout.addWidget(gb_single_detection)

        # ----------

        self.setLayout(main_layout)

    # ----------- Actions ---------------------

    def demarrer_detection(self, mode_detection):
        choix = QMessageBox.question(self, 'Continuer Procedure', "Continuer?", QMessageBox.Yes | QMessageBox.No)
        if choix == QMessageBox.Yes:
            sites = {"Pharmashopi": self.cb_site_1.isChecked(), "Espace Contention": self.cb_site_2.isChecked()}
            if mode_detection == 'batch':
                app.process.detection_arnaque(self.sb_nbrcmds.value(), sites, self.sb_nbrjours.value(), 
                                              self.mode_teste, mode_detection)
            else:
                app.process.detection_arnaque(self.sb_nbrcmds.value(), sites, self.sb_nbrjours.value(), 
                                              self.mode_teste, mode_detection, self.le_id_cmd.text())

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
        dialog = DialogAddProd(self.mode_teste)
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


# ------------------------------------------------------------

class DialogAddProd(QDialog):
    """Dialog to add new product to list

    Attributes
    ----------
    children : list
        Widgets created directly under in the 'hierarchy'
    mode_teste : bool
        Control of testing mode
    id_prod : QLineEdit
        Id of product to be added
    marque_prod : QLineEdit
        Brand of product to be added
    nom_prod : QLineEdit
        Name of product to be added

    Methods
    -------
    accept(self)
        Verifies parameters before adding to list
    get_inputs(self)
        Extracts input info of the new product
    """

    def __init__(self, mode_teste):
        super().__init__()
        self.children = []
        self.mode_teste = mode_teste

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
            prods = app.utilities.get_request(f"api/products/filter/id/{self.id_prod.text()}")

            if prods:
                return super().accept()
            else:
                QMessageBox.critical(self, 'Error', "Id invalide", QMessageBox.Ok)
        else:
            QMessageBox.critical(self, 'Error', "Paramètres Invalides", QMessageBox.Ok)

    # --------------------------

    def get_inputs(self):
        return {"id": self.id_prod.text(), "brand_name": self.marque_prod.text(), "name": self.nom_prod.text()}
