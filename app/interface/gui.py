# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QRadioButton, 
                             QSpinBox, QStackedWidget, QTabWidget, QVBoxLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QIcon)

import PyQt5.QtCore
import sys

from app.interface import home, detection, labels, config
import app.utilities


#------------------------------------------------------------
class main_window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.children = []

        self.setWindowTitle("Module Automatique Pharmashopi")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(app.utilities.get_path("../../docs/images/icon.png")))

        # change default value to True when developping to avoid running the program for real
        self.mode_teste = True

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        editMenu = mainMenu.addMenu('Edit')
        viewMenu = mainMenu.addMenu('View')
        searchMenu = mainMenu.addMenu('Search')
        toolsMenu = mainMenu.addMenu('Tools')
        helpMenu = mainMenu.addMenu('Help')

        extractAction = QAction("Exit", self)
        extractAction.setShortcut("Ctrl+Q")
        extractAction.triggered.connect(self.fermer_app)
        fileMenu.addAction(extractAction)

        extractAction = QAction("Mode Teste", self, checkable=True)
        extractAction.setShortcut("Ctrl+M")
        extractAction.setChecked(self.mode_teste)
        extractAction.triggered.connect(lambda state: app.utilities.change_mode(self, state, self.children))
        toolsMenu.addAction(extractAction)

        extractAction = QAction("Open README.txt", self)
        extractAction.triggered.connect(lambda: app.utilities.open_file('README.txt'))
        helpMenu.addAction(extractAction)
        
        tab_manager = tabs_widget(self.mode_teste)
        self.children.append(tab_manager)
        self.setCentralWidget(tab_manager)

        self.show()

    # ----------- Actions ---------------------
    def fermer_app(self):
        choix = QMessageBox.question(self, 'Fermer', "Sortir de l'application?", QMessageBox.Yes | QMessageBox.No)
        if choix == QMessageBox.Yes:
            sys.exit()

#------------------------------------------------------------
class tabs_widget(QWidget):
    def __init__(self, mode_teste):
        super().__init__()
        self.mode_teste = mode_teste
        self.children = []

        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        tab_home = home.home(self.mode_teste)
        tab_detection = detection.detection(self.mode_teste)
        tab_etiquettes = labels.etiquettes(self.mode_teste)
        tab_config = config.config(self.mode_teste)
        self.children.extend([tab_home, tab_detection, tab_etiquettes, tab_config])

        self.tabs.addTab(tab_home, "Home")
        self.tabs.addTab(tab_detection, "Détection d'Arnaque")
        self.tabs.addTab(tab_etiquettes, "Etiquettes")
        self.tabs.addTab(tab_config, "Configurations")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

#------------------------------------------------------------
def run():
    app = QApplication([])
    gui = main_window()
    sys.exit(app.exec_())


