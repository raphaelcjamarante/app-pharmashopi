# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, 
                             QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QRadioButton, QSpinBox, 
                             QStackedWidget, QTabWidget, QVBoxLayout, QWidget)

from PyQt5.QtCore import Qt

import app.lettre_suivie
import app.log
import app.mondial_relay
import app.utilities

logger = app.log.setup_logger(__name__)

#------------------------------------------------------------
class etiquettes(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []

        main_layout = QVBoxLayout()
        labels = label_stack(self.mode_teste)
        self.children.append(labels)
        main_layout.addWidget(labels)
        self.setLayout(main_layout)

#------------------------------------------------------------
class label_stack(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []

        main_layout = QVBoxLayout()

        # ----------

        label = QLabel()
        label.setText("Choisir le type d'etiquette")
        label.setAlignment(Qt.AlignCenter)

        stack_options = QListWidget()
        stack_options.insertItem(0, 'Mondial Relay')
        stack_options.insertItem(1, 'Lettre suivie')
        stack_options.insertItem(2, 'Colissimo')

        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(stack_options)

        # ----------
        
        stack_mondial = mondial_relay(self.mode_teste)
        stack_lettre = lettre_suivie(self.mode_teste)
        stack_colissimo = colissimo(self.mode_teste)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(stack_mondial)
        self.stack.addWidget(stack_lettre)
        self.stack.addWidget(stack_colissimo)

        for i in range(self.stack.count()):
            self.children.append(self.stack.widget(i))

        # ----------
        
        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.stack)
        main_layout.addLayout(hbox)

        # ----------

        self.setLayout(main_layout)
        stack_options.currentRowChanged.connect(self.display)

        
    # ----------- Actions ---------------------
    def display(self, i):
        self.stack.setCurrentIndex(i)

#------------------------------------------------------------
class mondial_relay(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []

        main_layout = QVBoxLayout()

        # ----------

        main_layout.addStretch()

        # ----------
        vbox_params = QVBoxLayout()
        
        # ---------- not usable (yet) due to back-office limitation
        label = QLabel()
        label.setText("Finaliser la commande")
        label.setAlignment(Qt.AlignCenter)
        #vbox_params.addWidget(label)

        self.rb_1 = QRadioButton()
        self.rb_1.setText("Oui")
        self.rb_1.setChecked(False)
        self.rb_2 = QRadioButton()
        self.rb_2.setText("Non")
        self.rb_2.setChecked(True)

        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self.rb_1)
        hbox.addWidget(self.rb_2)
        #vbox_params.addLayout(hbox)
        
        # ----------

        label = QLabel()
        label.setText("Scannez le code-barres de la commande")
        label.setAlignment(Qt.AlignCenter)
        vbox_params.addWidget(label)

        self.le = QLineEdit()
        self.le.textChanged.connect(self.text_changed)
        vbox_params.addWidget(self.le)

        # ----------

        gb_params = QGroupBox("Paramètres")
        gb_params.setLayout(vbox_params)
        main_layout.addWidget(gb_params)

        # ----------

        b_open_file = QPushButton("Ouvrir Etiquette")
        b_open_file.clicked.connect(lambda: app.utilities.open_file('docs/etiquette_mondial_relay.pdf'))
        main_layout.addWidget(b_open_file)

        # ----------

        b_open_log = QPushButton("Ouvrir Tracking Log")
        b_open_log.clicked.connect(lambda: app.utilities.open_file('docs/tracking_mondial_relay'))
        main_layout.addWidget(b_open_log)

        # ----------

        main_layout.addStretch()

        # ----------

        self.setLayout(main_layout)

    # ----------- Actions ---------------------
    def text_changed(self, text):
        if len(text) == 13:
            if self.rb_1.isChecked() ^ self.rb_2.isChecked():
                app.mondial_relay.generer_etiquette(text[:6], self.rb_1.isChecked(), self.mode_teste)
                self.le.setText("")

#------------------------------------------------------------
class lettre_suivie(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []

        main_layout = QVBoxLayout()

        # ----------

        main_layout.addStretch()

        # ----------
        vbox_params = QVBoxLayout()
        
        # ---------- not usable (yet) due to back-office limitation
        label = QLabel()
        label.setText("Finaliser la commande")
        label.setAlignment(Qt.AlignCenter)
        #vbox_params.addWidget(label)

        self.rb_1 = QRadioButton()
        self.rb_1.setText("Oui")
        self.rb_1.setChecked(False)
        self.rb_2 = QRadioButton()
        self.rb_2.setText("Non")
        self.rb_2.setChecked(True)

        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self.rb_1)
        hbox.addWidget(self.rb_2)
        #vbox_params.addLayout(hbox)
        
        # ----------
        
        label = QLabel()
        label.setText("Mode lettre")
        label.setAlignment(Qt.AlignCenter)
        vbox_params.addWidget(label)

        self.rb_suivie = QRadioButton()
        self.rb_suivie.setText("Suivie")
        self.rb_suivie.setChecked(True)
        self.rb_suivie.toggled.connect(self.rb_suivie_clicked)
        self.rb_simple = QRadioButton()
        self.rb_simple.setText("Simple")
        self.rb_simple.setChecked(False)
        self.rb_simple.toggled.connect(self.rb_simple_clicked)

        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignCenter)
        hbox.addWidget(self.rb_suivie)
        hbox.addWidget(self.rb_simple)
        vbox_params.addLayout(hbox)
        
        # ----------

        label = QLabel()
        label.setText("Scannez le code-barres de la lettre suivie")
        label.setAlignment(Qt.AlignCenter)
        vbox_params.addWidget(label)

        self.le_lettre = QLineEdit()
        vbox_params.addWidget(self.le_lettre)

        # ----------
        
        label = QLabel()
        label.setText("Scannez le code-barres de la commande")
        label.setAlignment(Qt.AlignCenter)
        vbox_params.addWidget(label)

        self.le_commande = QLineEdit()
        vbox_params.addWidget(self.le_commande)

        # ----------

        self.le_lettre.textChanged.connect(self.both_texts_changed)
        self.le_commande.textChanged.connect(self.both_texts_changed)

        # ----------

        gb_params = QGroupBox("Paramètres")
        gb_params.setLayout(vbox_params)
        main_layout.addWidget(gb_params)

        # ----------

        b_open_file = QPushButton("Ouvrir Etiquette")
        b_open_file.clicked.connect(lambda: app.utilities.open_file('docs/etiquette_lettre_suivie.pdf'))
        main_layout.addWidget(b_open_file)

        # ----------

        b_open_log = QPushButton("Ouvrir Dossier Tracking Log")
        b_open_log.clicked.connect(lambda: app.utilities.open_file('docs/tracking_lettre_suivie'))
        main_layout.addWidget(b_open_log)

        # ----------

        main_layout.addStretch()

        # ----------

        self.setLayout(main_layout)

    # ----------- Actions ---------------------
    def both_texts_changed(self):
        code_cmd = self.le_commande.text()
        code_lettre = self.le_lettre.text()
        if (len(code_cmd) == 13) and (len(code_lettre) == 13) :
            if self.rb_1.isChecked() ^ self.rb_2.isChecked():
                app.lettre_suivie.generer_etiquette(code_cmd[:6], self.rb_1.isChecked(), code_lettre, self.mode_teste)
                if self.rb_suivie.isChecked():
                    self.le_lettre.setText("")
                self.le_commande.setText("")

    def rb_suivie_clicked(self, enabled):
        if enabled:
            self.le_lettre.clear()
            self.le_lettre.setReadOnly(False)

    def rb_simple_clicked(self, enabled):
        if enabled:
            self.le_lettre.setText('Lettre simple')
            self.le_lettre.setReadOnly(True)

#------------------------------------------------------------
class colissimo(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []
        
        main_layout = QVBoxLayout()

        label = QLabel()
        label.setText("Pas encore implementé")
        label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(label)

        self.setLayout(main_layout)

