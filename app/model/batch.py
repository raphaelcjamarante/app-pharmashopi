# -*- coding: utf-8 -*-

import app.model.commande

class Batch():
    """Represents the batch of orders selected for the picking via GUI

    Attributes
    ----------
    cmds : dict
        Dict of Commande objects with their id as key
    prods_info : dict
        Dict of dicts with general info on the products {best_reference: {Product object, requested quantity, robot stock}}

    Methods
    -------
    get_total_quantity(self)
        Gets the total quantity of all products in the batch, excluding the delivery method
    get_range(self)
        Gets a string with the first and last orders, by id number, in the batch
    make_products_dict(self, mode_teste)
        Makes prods_info
    """
    
    def __init__(self, cmds, mode_teste):
        self.cmds = {}
        for key in cmds:
            self.cmds[key] = app.model.commande.Commande(cmds[key])
        self.make_products_dict(mode_teste)

    # ------------------------------------------

    def get_total_quantity(self):
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
        list_prods = [self.cmds[k1].products[k2] 
                      for k1 in self.cmds 
                      for k2 in self.cmds[k1].products 
                      if self.cmds[k1].products[k2].reference != ""]
        list_prods = sorted(list_prods, key=lambda k: k.brand_name)

        self.prods_info = {}
        for prod in list_prods:
            ref = prod.get_best_reference()
            if mode_teste:
                robot_stock = '1'
            else:
                robot_stock = app.robot.robot_stock(ref)
            if ref not in self.prods_info:
                self.prods_info[ref] = {'product': prod, 'total_qte': prod.quantity, 'robot_stock': robot_stock}
            else:
                self.prods_info[ref]['total_qte'] += prod.quantity
