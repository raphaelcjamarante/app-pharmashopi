# -*- coding: utf-8 -*-

import unittest

import app.process
import app.labels
import app.filters

class TestsUnit(unittest.TestCase):

    def test_filtrage_picking(self):
        nbrcmds = 5
        nbrmedic = 30
        site_filter = "/filter/store_id/pharmashopi"
        livraison = ""
        cmds = app.filters.filtrage_picking(nbrcmds, nbrmedic, site_filter, livraison="")
        assert len(cmds.keys()) == nbrcmds

        #TODO : assert all are one livraison

class TestsIntegrated(unittest.TestCase):

    def test_picking(self):

        sites = {"Pharmashopi": True, "Espace Contention": False}
        app.process.bonetpick(5, 30, sites, 3, "", 3, True)
        #app.process.bonetpick(5, 30, sites, 3, "Colissimo", 3, True)
        #app.process.bonetpick(5, 30, sites, 3, "Mondial Relay", 3, True)
        #app.process.bonetpick(5, 30, sites, 3, "Lettre suivie", 3, True)
        app.process.bonetpick(0, 30, sites, 3, "", 3, True)
        

    def test_detection(self):

        sites = {"Pharmashopi": True, "Espace Contention": False}
        app.process.detection_arnaque(10, sites, 3, True)

    def test_labels(self):

        id_cmd = 338264

        # ------- etiquette mondial --------
        app.labels.generer_etiquette(id_cmd, 0, 'Mondial Relay', True)


        # ------- etiquette lettre --------
        app.labels.generer_etiquette(id_cmd, 0, 'Lettre suivie', True, 123)

#-----------------------------------------------------------

if __name__ == '__main__':
    unittest.main()


