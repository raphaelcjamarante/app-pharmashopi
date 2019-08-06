# -*- coding: utf-8 -*-

import unittest

import app.process
import app.lettre_suivie
import app.mondial_relay

class Tests(unittest.TestCase):

    def test(self):

        # ------- picking --------
        sites = {"Pharmashopi": True, "Espace Contention": False}
        app.process.bonetpick(10, 30, sites, 3, "", 3, True)
        # ------- detection --------
        app.process.detection_arnaque(10, sites, 3, True)
        # ------- etiquette mondial --------
        app.mondial_relay.generer_etiquette(338264, 0, True)
        # ------- etiquette lettre --------
        app.lettre_suivie.generer_etiquette(338264, 0, 123, True)


if __name__ == '__main__':
    unittest.main()



