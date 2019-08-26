# -*- coding: utf-8 -*-

import app.utilities
import unicodedata

class Product():
    """Represents a product of an order
    
    Attributes
    ----------
    id : str
    reference : str
    stock_reference : str
    name : str
    quantity : int
    final_price : float
        Price of product
    tax_rate : float
    taxed_price : float
        Price of product with tax rate
    weight : float
        Weight of product in kg
    brand_name : str
    options : dict of Option objects
    ean : str
    stock_total_quantity : str
    stock : Stock object
        Stock of the appropriate type of the product, selected via the attribute stock_reference

    Methods
    -------
    get_more_info(self, id_prod)
        Complements the attributes when the product is not the delivery service
    get_options(self)
        Get string of options of the product
    get_stocks(self)
        Gets string of the distribution of the product in 3 different stocks (local, BIOX, PSL)
    get_best_reference(self)
        Gets the best reference to track the right product
    """

    def __init__(self, prod):

        self.id = prod['id']
        self.reference = prod['reference']
        self.stock_reference = prod['stock_reference']
        self.name = prod['name']
        self.quantity = int(prod['quantity'])

        self.final_price = float(prod['final_price'])
        self.tax_rate = float(prod['tax_rate'])
        self.taxed_price = self.final_price + (self.final_price * self.tax_rate / 100)

        self.weight = float(prod['weight'])
        self.brand_name = prod['brand_name']

        self.options = {}
        if 'options' in prod:
            for key in prod['options']:
                self.options[key] = Option(prod['options'][key])

        if self.reference != '':
            self.get_more_info(self.id)

    # ------------------------------------------

    def get_more_info(self, id_prod):
        prod = app.utilities.get_request(f"api/products/filter/id/{id_prod}")

        for key in prod:
            prod = prod[key]

        self.ean = prod['ean']
        self.stock_total_quantity = prod['stock_total_quantity']

        if self.stock_reference in prod['stock']:
            self.stock = Stock(prod['stock'][self.stock_reference])    

    # ------------------------------------------

    def get_options(self):
        opt_list = []
        for key in self.options:
            opt_list.append(self.options[key].get_option())
        return '\n'.join(opt_list)

    # ------------------------------------------

    def get_stocks(self):
        stocks = self.stock_total_quantity

        other_stocks = {}
        if hasattr(self, 'stock'):
            other_stocks = self.stock.get_stock()
        for key in other_stocks:
            if other_stocks[key] != '':
                stocks = stocks + f" | {key}: {other_stocks[key]}"
        return stocks

    # ------------------------------------------

    def get_best_reference(self):
        if hasattr(self, 'stock') and self.options != {}:
            return self.stock.ean
        elif hasattr(self, 'ean') and self.ean != '':
            return self.ean
        else:
            return self.reference


# ----------------------------------------------

class Option():
    """Represents an option of the product

    Attributes
    ----------
    name : str
    value_name : str

    Methods
    -------
    get_option(self)
        Gets the formatted string of the option
    """

    def __init__(self, option):
        self.name = unicodedata.normalize('NFD', option['option_name'])
        self.value_name = unicodedata.normalize('NFD', option['option_value_name'])

    # ------------------------------------------

    def get_option(self):
        return self.name + " : " + self.value_name


# --------------------------------------------

class Stock():
    """Represents a stock of the product

    Attributes
    ----------
    reference : str
    ean : str
    entries : dict of StockEntry objects

    Methods
    -------
    get_stock(self)
        Gets a dict with the quantity of the product in different stocks
    """

    def __init__(self, stock):
        self.reference = stock['stock_reference']
        self.ean = stock['stock_ean']
        self.entries = {}
        if 'stock_entries' in stock:
            for key in stock['stock_entries']:
                self.entries[key] = StockEntry(stock['stock_entries'][key])

    # ------------------------------------------

    def get_stock(self):
        stock = {}
        for key in self.entries:
            stock.update(self.entries[key].get_entry())
        return stock


# --------------------------------------------

class StockEntry():
    """Represents an entry of a stock

    Attributes
    ----------
    quantity : str
    supplier_id : str

    Methods
    -------
    get_entry(self)
        Gets the quantity of two specific stocks (BIOX and PSL)
    """

    def __init__(self, entry):
        self.quantity = entry['stock_entry_quantity']
        self.supplier_id = entry['stock_entry_supplier_id']

    # ------------------------------------------

    def get_entry(self):
        entry = {'BIOX': '', 'PSL': ''}
        if self.supplier_id == "21":
            entry['BIOX'] = self.quantity
        elif self.supplier_id == "38":
            entry['PSL'] = self.quantity
        return entry




