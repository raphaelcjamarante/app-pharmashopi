# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, 
                             QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QRadioButton, QSpinBox, 
                             QStackedWidget, QTabWidget, QVBoxLayout, QWidget)

from PyQt5.QtCore import Qt

from ast import literal_eval
from pandas import DataFrame
import pandas as pd

import app.interface
import app.log
import app.utilities

logger = app.log.setup_logger(__name__)

#------------------------------------------------------------
class config(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []
        self.config_data = app.utilities.get_config_data()

        main_layout = QVBoxLayout()

        b_save = QPushButton("Sauvegarder Modifications")
        b_save.clicked.connect(self.save_config)
        main_layout.addWidget(b_save)

        # ----------

        form_general = QFormLayout()

        label = QLabel()
        label.setText("Clé Shop Application API : ")
        self.le_cle_api = QLineEdit()
        self.le_cle_api.setText(self.config_data['cle_api'])
        form_general.addRow(label, self.le_cle_api)

        label = QLabel()
        label.setText("Adresse IP Robot : ")
        self.le_ip_robot = QLineEdit()
        self.le_ip_robot.setText(self.config_data['ip_robot'])
        form_general.addRow(label, self.le_ip_robot)

        b_open_log = QPushButton("Ouvrir Log")
        b_open_log.clicked.connect(lambda: app.utilities.open_file('docs/log.log'))
        b_reset_log = QPushButton("Vider Log")
        b_reset_log.clicked.connect(self.reset_log)

        hbox = QHBoxLayout()
        hbox.addWidget(b_open_log)
        hbox.addWidget(b_reset_log)
        form_general.addRow(hbox)

        gb_general = QGroupBox("Paramètres Générales")
        gb_general.setLayout(form_general)

        # ----------
        form_bonetpick = QFormLayout()

        label = QLabel()
        label.setText("XXX : ")
        self.le_x = QLineEdit()
        self.le_x.setText(self.config_data['x'])
        form_bonetpick.addRow(label, self.le_x)

        # last docs?
        # only docs?
        gb_bonetpick = QGroupBox("Paramètres du Picking")
        gb_bonetpick.setLayout(form_bonetpick)

        # ----------

        hbox_upper = QHBoxLayout()
        hbox_upper.addWidget(gb_general)
        hbox_upper.addWidget(gb_bonetpick)
        main_layout.addLayout(hbox_upper)

        # ----------
        form_detection = QFormLayout()


        detection_params = self.config_data["detection_params"]

        self.list_detection = QListWidget()
        for key in detection_params:
            cb_param = QListWidgetItem()
            cb_param.setCheckState(Qt.Checked if detection_params[key] else Qt.Unchecked)
            cb_param.setText(key)
            self.list_detection.addItem(cb_param)

        # disable client history (back-office limitation)
        self.list_detection.item(5).setFlags(Qt.NoItemFlags)

        form_detection.addWidget(self.list_detection)

        gb_detection = QGroupBox("Paramètres de la Détection d'Arnaque")
        gb_detection.setLayout(form_detection)

        # ----------
        vbox_labels = QVBoxLayout()

        form_mondial = QFormLayout()

        label = QLabel()
        label.setText("Enseigne Production : ")
        self.le_ens_prod = QLineEdit()
        self.le_ens_prod.setText(self.config_data['enseigne_production'])
        form_mondial.addRow(label, self.le_ens_prod)

        label = QLabel()
        label.setText("Clé Privée Production : ")
        self.le_cle_prod = QLineEdit()
        self.le_cle_prod.setText(self.config_data['cle_production'])
        form_mondial.addRow(label, self.le_cle_prod)

        label = QLabel()
        label.setText("Enseigne Testing : ")
        self.le_ens_test = QLineEdit()
        self.le_ens_test.setText(self.config_data['enseigne_testing'])
        form_mondial.addRow(label, self.le_ens_test)

        label = QLabel()
        label.setText("Clé Privée Testing : ")
        self.le_cle_test = QLineEdit()
        self.le_cle_test.setText(self.config_data['cle_testing'])
        form_mondial.addRow(label, self.le_cle_test)

        b_open_file = QPushButton("Ouvrir Doc de Paramètres Officiel")
        b_open_file.clicked.connect(lambda: app.utilities.open_file('docs/MondialRelay/ParametresSecurite.pdf'))
        form_mondial.addRow(b_open_file)

        gb_mondial = QGroupBox("Mondial Relay")
        gb_mondial.setLayout(form_mondial)

        vbox_labels.addWidget(gb_mondial)

        gb_labels = QGroupBox("Paramètres de la Génération d'Etiquettes")
        gb_labels.setLayout(vbox_labels)

        # ----------

        hbox_lower = QHBoxLayout()
        hbox_lower.addWidget(gb_detection)
        hbox_lower.addWidget(gb_labels)
        main_layout.addLayout(hbox_lower)

        # ----------

        self.setLayout(main_layout)

    # ----------- Actions ---------------------
    def save_config(self):
        config_data = {}

        config_data["cle_api"] = self.le_cle_api.text()
        config_data["ip_robot"] = self.le_ip_robot.text()
        config_data["x"] = self.le_x.text()

        detection_params = {}
        for i in range(self.list_detection.count()):
            key = self.list_detection.item(i).text()
            value = self.list_detection.item(i).checkState()
            detection_params[key] = bool(value)
        config_data["detection_params"] = detection_params

        config_data["enseigne_production"] = self.le_ens_prod.text()
        config_data["cle_production"] = self.le_cle_prod.text()
        config_data["enseigne_testing"] = self.le_ens_test.text()
        config_data["cle_testing"] = self.le_cle_test.text()

        df = DataFrame.from_dict(config_data, orient="index", columns=["value"])
        df.index.name = "parameter"

        df.to_csv(app.utilities.get_path("docs/config_data.csv"))

    # --------------------------
    def reset_log(self):
        choix = QMessageBox.question(self, 'Vider Log', "Voulez-vous vider le log?", QMessageBox.Yes | QMessageBox.No)
        if choix == QMessageBox.Yes:
            open(app.utilities.get_path("docs/log.log"), "w").close()

