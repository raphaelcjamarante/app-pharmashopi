# -*- coding: utf-8 -*-

import app.model.commande

class Batch():
    def __init__(self, cmds, mode_teste):
        self.cmds = {}
        for key in cmds:
            self.cmds[key] = app.model.commande.Commande(cmds[key])
        self.make_products_dict(mode_teste)

    # ------------------------------------------

    def get_total_quantity(self):
        """ total quantity of products in a batch
        """
        return sum([self.cmds[key].get_total_quantity() for key in self.cmds])

    # ------------------------------------------

    def get_range(self):
        range_batch = ""
        ordre_cmds = list(self.cmds.keys())
        if ordre_cmds != []:
            range_batch = str (min(ordre_cmds)) + "  -->  " + str(max(ordre_cmds))
        return range_batch

    # ------------------------------------------

    def make_products_dict(self, mode_teste):
        """ dict with product, aggregated quantity if is the same, and robot stock
        """
        # excluding delivery 'products'
        list_prods = [self.cmds[k1].products[k2] 
                      for k1 in self.cmds 
                      for k2 in self.cmds[k1].products 
                      if self.cmds[k1].products[k2].reference != "" ]
        list_prods = sorted(list_prods, key=lambda k: k.brand_name)

        self.prods_info = {}
        for prod in list_prods:
            if mode_teste:
                robot_stock = '1'
            else:
                robot_stock = app.robot.robot_stock(prod.reference)

            ref = prod.get_best_reference()
            if ref not in self.prods_info:
                self.prods_info[ref] = {'product': prod, 'total_qte': prod.quantity, 'robot_stock': robot_stock}
            else:
                self.prods_info[ref]['total_qte'] += prod.quantity
