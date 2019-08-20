# -*- coding: utf-8 -*-

import unittest

import app.docs
import app.filters
import app.labels
import app.process
import app.utilities
import app.model.batch

class TestsUnit(unittest.TestCase):

    def test_filtrage_picking(self):
        nbrcmds = 5
        nbrmedic = 30
        site_filter = "/filter/store_id/pharmashopi"

        livraison = ""
        cmds = app.filters.filtrage_picking(nbrcmds, nbrmedic, site_filter, livraison="")
        assert len(cmds.keys()) <= nbrcmds

        livraison = ["Colissimo", "Mondial Relay", "Lettre suivie"]
        for item in livraison:
            cmds = app.filters.filtrage_picking(nbrcmds, nbrmedic, site_filter, livraison=item)
            assert len(cmds.keys()) <= nbrcmds
            for key in cmds:
                shipping_name = cmds[key]['shipping']['method_name']
                assert item in shipping_name

    #def test_filtrage_arnaque(self):

    def test_picking(self):
        mode_teste = True
        sortie = 3
        cmds = app.utilities.get_request(f"api/orders/filter/status/1/filter/orderby/date_created/asc/limit/5")
        batch = app.model.batch.Batch(cmds, mode_teste)
        
        app.process.picking(batch, sortie, mode_teste)

    def test_docs(self):
        mode_teste = True
        livraison = ''
        cmds = app.utilities.get_request(f"api/orders/filter/status/1/filter/orderby/date_created/asc/limit/5")
        batch = app.model.batch.Batch(cmds, mode_teste)

        app.docs.picking_doc(batch, livraison)
        app.docs.bonprep_doc(batch.cmds, livraison)

class TestsIntegrated(unittest.TestCase):

    def test_picking(self):
        nbrcmds = 5
        nbrmedic = 30
        sortie = 3
        sites = {"Pharmashopi": True, "Espace Contention": False}
        livraison = ['', 'Colissimo', 'Mondial Relay', 'Lettre suivie']
        nbrjours = 3
        mode_teste = True

        for item in livraison:
            app.process.bonetpick(nbrcmds, nbrmedic, sites, sortie, item, nbrjours, mode_teste)

        nbrcmds = 0
        app.process.bonetpick(nbrcmds, nbrmedic, sites, sortie, '', nbrjours, mode_teste)
        

    def test_detection(self):
        nbrcmds = 10
        sites = {"Pharmashopi": True, "Espace Contention": False}
        nbrjours = 3
        mode_teste = True
        mode_detection = ['batch', 'single']
        id_cmd = 357000

        app.process.detection_arnaque(nbrcmds, sites, nbrjours, mode_teste, mode_detection[0])
        app.process.detection_arnaque(nbrcmds, sites, nbrjours, mode_teste, mode_detection[1], id_cmd)


    def test_labels(self):

        id_cmd = 338264

        # ------- etiquette mondial --------
        app.labels.generer_etiquette(id_cmd, 0, 'Mondial Relay', True)


        # ------- etiquette lettre --------
        app.labels.generer_etiquette(id_cmd, 0, 'Lettre suivie', True, 123)

#-----------------------------------------------------------

if __name__ == '__main__':
    unittest.main()


