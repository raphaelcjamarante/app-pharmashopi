# -*- coding: utf-8 -*-

import unicodedata

import app.utilities

class Product():
    def __init__(self, prod):
        self.id = prod['id']
        self.reference = prod['reference']
        self.stock_reference = prod['stock_reference']
        self.name = prod['name']
        self.quantity = int(prod['quantity'])

        self.final_price = float(prod['final_price'])
        self.tax_rate = float(prod['tax_rate'])
        self.taxed_price = self.final_price + (self.final_price * self.tax_rate / 100)

        self.date_added = prod['date_added']
        self.weight = float(prod['weight'])
        self.brand_name = prod['brand_name']

        self.options = {}
        if 'options' in prod:
            for key in prod['options']:
                self.options[key] = Option(prod['options'][key])

        # excludes delivery 'product'
        if self.reference != '':
            self.get_more_info(self.id)

    # ------------------------------------------

    def get_more_info(self, id_prod):
        prod = app.utilities.get_request(f"api/products/filter/id/{id_prod}")

        for key in prod:
            prod = prod[key]

        self.ean = prod['ean']
        self.stock_total_quantity = prod['stock_total_quantity']

        #if self.stock_reference in prod['stock']:
        self.stock = Stock(prod['stock'][self.stock_reference])
        #else:
        #    for key in prod['stock']:
        #        self.stock = Stock(prod['stock'][key])        

    # ------------------------------------------

    def get_options(self):
        opt_list = []
        for key in self.options:
            opt_list.append(self.options[key].get_option())
        #if len(opt_list) == 0:
        #    return " "
        return '\n'.join(opt_list)

    # ------------------------------------------

    def get_stocks(self):
        stocks = self.stock_total_quantity
        other_stocks = self.stock.get_stock()
        for key in other_stocks:
            if other_stocks[key] != '':
                stocks = stocks + f" | {key}: {other_stocks[key]}"
        return stocks

    # ------------------------------------------

    def get_best_reference(self):
        if self.options != {}:
            return self.stock.ean
        elif hasattr(self, 'ean') and self.ean != '':
            return self.ean
        else:
            return self.reference


# --------------------------------------------

class Option():
    def __init__(self, option):
        self.id = option['option_id']
        self.value_id = option['option_value_id']
        self.name = unicodedata.normalize('NFD', option['option_name'])
        self.value_name = unicodedata.normalize('NFD', option['option_value_name'])

    # ------------------------------------------

    def get_option(self):
        return self.name + " : " + self.value_name



# --------------------------------------------

class Stock():
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




