# -*- coding: utf-8 -*-

from app.interface import picking, detection, labels, config
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QListWidget, QMainWindow, 
                             QMessageBox, QTabWidget, QVBoxLayout, QWidget)
import app.utilities
import sys

# ------------------------------------------------------------

class MainWindow(QMainWindow):
    """Main window of the application

    Attributes
    ----------
    children : list
        Widgets created directly under in the 'hierarchy'
    mode_teste : bool
        Control of testing mode

    Methods
    -------
    fermer_app(self)
        Closes the app correctly
    """

    def __init__(self):
        super().__init__()
        self.children = []
        self.mode_teste = True # set default to True when developping and to False when in production to avoid confusion

        self.setWindowTitle("Module Automatique Pharmashopi")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(app.utilities.get_path("docs/images/icon.png")))

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
        
        tab_manager = TabsWidget(self.mode_teste)
        self.children.append(tab_manager)
        self.setCentralWidget(tab_manager)

        self.show()

    # ----------- Actions ---------------------

    def fermer_app(self):
        choix = QMessageBox.question(self, 'Fermer', "Sortir de l'application?", QMessageBox.Yes | QMessageBox.No)
        if choix == QMessageBox.Yes:
            sys.exit()


# ------------------------------------------------------------

class TabsWidget(QWidget):
    """Tabs manager

    Attributes
    ----------
    children : list
        Widgets created directly under in the 'hierarchy'
    mode_teste : bool
        Control of testing mode
    """

    def __init__(self, mode_teste):
        super().__init__()
        self.children = []
        self.mode_teste = mode_teste

        layout = QVBoxLayout()

        tabs = QTabWidget()
        tab_home = picking.Picking(self.mode_teste)
        tab_detection = detection.Detection(self.mode_teste)
        tab_etiquettes = labels.Etiquettes(self.mode_teste)
        tab_config = config.Config(self.mode_teste)
        self.children.extend([tab_home, tab_detection, tab_etiquettes, tab_config])

        tabs.addTab(tab_home, "Picking")
        tabs.addTab(tab_detection, "Détection d'Arnaque")
        tabs.addTab(tab_etiquettes, "Etiquettes")
        tabs.addTab(tab_config, "Configurations")

        layout.addWidget(tabs)
        self.setLayout(layout)


# ------------------------------------------------------------

def run():
    app = QApplication([])
    gui = MainWindow()
    sys.exit(app.exec_())


