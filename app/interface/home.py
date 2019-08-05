# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, 
                             QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QRadioButton, QSpinBox, 
                             QStackedWidget, QTabWidget, QVBoxLayout, QWidget)
from PyQt5.QtCore import Qt

import app.log
import app.process
import app.utilities

logger = app.log.setup_logger(__name__)

#------------------------------------------------------------
class home(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []

        main_layout = QVBoxLayout()

        # ----------

        label = QLabel()
        label.setText("BIENVENUE SUR LE MODULE AUTOMATIQUE DE GESTION DE COMMANDES DE PHARMASHOPI !")
        label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(label)

        # ----------

        b_start = QPushButton("Démarrer")
        b_start.clicked.connect(self.demarrer_bonetpick)
        main_layout.addWidget(b_start)

        # ----------

        main_layout.addStretch()

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

        form_params.addRow(label,hbox)

        # ----------
        label = QLabel()
        label.setText("Selectionnez le filtre du type de livraison : ")

        self.cb_livraison = QComboBox()
        self.cb_livraison.setEditable(True);
        self.cb_livraison.lineEdit().setReadOnly(True);
        self.cb_livraison.lineEdit().setAlignment(Qt.AlignCenter);
        self.cb_livraison.addItems(["", "Colissimo", "Mondial Relay", "Lettre suivie"])
        self.cb_livraison.setCurrentIndex(0)

        form_params.addRow(label, self.cb_livraison)

        # ----------

        label = QLabel()
        label.setText("Nombre de commandes à imprimer : ")

        self.sb_nbrcmds = QSpinBox()
        self.sb_nbrcmds.setValue(25)

        form_params.addRow(label, self.sb_nbrcmds)

        # ----------

        label = QLabel()
        label.setText("Nombre maximal de produits par commande : ")

        self.sb_nbrmedic = QSpinBox()
        self.sb_nbrmedic.setValue(30)

        form_params.addRow(label, self.sb_nbrmedic)

        # ----------

        label = QLabel()
        label.setText("Sortie robot : ")

        self.sb_sortie = QSpinBox()
        self.sb_sortie.setValue(3)
        self.sb_sortie.setMinimum(1)
        self.sb_sortie.setMaximum(5)

        form_params.addRow(label, self.sb_sortie)

        # ----------

        gb_params = QGroupBox("Paramètres")
        gb_params.setLayout(form_params)
        main_layout.addWidget(gb_params)


        # ----------

        b_open_file = QPushButton("Ouvrir Documents")
        b_open_file.clicked.connect(self.open_file)
        main_layout.addWidget(b_open_file)

        # ----------

        main_layout.addStretch()

        # ----------

        b_reset = QPushButton("Reset")
        b_reset.clicked.connect(self.reset)
        main_layout.addWidget(b_reset)

        # ----------

        self.setLayout(main_layout)


    # ----------- Actions ---------------------

    def open_file(self):
        app.utilities.open_file('docs/Picking.xlsx')
        app.utilities.open_file('docs/BonCommande.xlsx')

    # --------------------------
    def reset(self):
        msg = "Réinitialiser les paramètres par défaut? Les modifications ne seront pas sauvegardées."
        choix = QMessageBox.question(self, 'Reset', msg, QMessageBox.Yes | QMessageBox.No)
        if choix == QMessageBox.Yes:
            self.cb_site_1.setChecked(True)
            self.cb_site_2.setChecked(False)
            self.cb_livraison.setCurrentIndex(0)
            self.sb_commandes.setValue(25)
            self.sb_produits.setValue(30)
            self.sb_robot.setValue(3)
            
    # --------------------------
    def demarrer_bonetpick(self):
        msg = "Vérifiez que les fichiers Picking et BonCommande sont fermés.\n\nContinuer?"
        choix = QMessageBox.warning(self, 'Continuer Procedure', msg, QMessageBox.Yes | QMessageBox.No)
        if choix == QMessageBox.Yes:
            sites = {"Pharmashopi": self.cb_site_1.isChecked(), "Espace Contention": self.cb_site_2.isChecked()}
            nbrjours = 3 #self.parent_widget.tabs.widget(1).sb_nbrjours.value()
            app.process.bonetpick(self.sb_nbrcmds.value(), self.sb_nbrmedic.value(), sites, self.sb_sortie.value(),
                                  self.cb_livraison.currentText(), nbrjours, self.mode_teste)
