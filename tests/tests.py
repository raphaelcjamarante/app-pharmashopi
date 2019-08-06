# -*- coding: utf-8 -*-

import unittest

import app.process
import app.lettre_suivie
import app.mondial_relay
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

        idcmd = 338264

        # ------- etiquette mondial --------
        app.mondial_relay.generer_etiquette(idcmd, 0, True)


        # ------- etiquette lettre --------
        app.lettre_suivie.generer_etiquette(idcmd, 0, 123, True)

#-----------------------------------------------------------

if __name__ == '__main__':
    unittest.main()


