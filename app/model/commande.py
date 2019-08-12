# -*- coding: utf-8 -*-

import unicodedata

import app.model.delivery
import app.model.product

class Commande():
    def __init__(self, cmd):
        self.id = cmd['id']
        self.language = cmd['language']
        self.status = cmd['status']
        self.date_created = cmd['date_created']

        self.shipping = app.model.delivery.Shipping(cmd['shipping'])
        self.payment = Payment(cmd['payment'])
        self.customer = Customer(cmd['customer_info'])
        self.delivery_address = app.model.delivery.DeliveryAddress(cmd['delivery_address'], self.customer)

        self.statuses_history = {}
        for key in cmd['statuses_history']:
            self.statuses_history[key] = StatusHistory(cmd['statuses_history'][key])

        self.products = {}
        for key in cmd['products']:
            self.products[key] = app.model.product.Product(cmd['products'][key])

        self.calculate_cost()

    # ------------------------------------------

    def calculate_cost(self):
        self.totalht = 0
        self.totalttc = 0
        for key in self.products:
            product = self.products[key]
            quantity = product.quantity
            self.totalht += product.final_price * quantity
            self.totalttc += product.taxed_price * quantity

    # ------------------------------------------

    def get_date_created(self, mode='string'):
        if mode == 'barcode':
            return self.date_created[2:4] + self.date_created[5:7] + self.date_created[8:10]
        else:
            return f"{self.date_created[8:10]} - {self.date_created[5:7]} - {self.date_created[0:4]}"

    # ------------------------------------------

    def get_sante(self):
        # gets the most complete health info
        sante = []
        for key in self.statuses_history:
            tmp = self.statuses_history[key].get_sante()
            if len(tmp) > len(sante):
                sante = tmp
        return sante

    # ------------------------------------------

    def get_total_quantity(self):
        return sum([self.products[key].quantity for key in self.products if self.products[key].reference != ''])

# --------------------------------------------

class Customer():
    def __init__(self, info):
        self.id = info['id']
        self.name = unicodedata.normalize('NFD', info['name'])
        self.company = unicodedata.normalize('NFD', info['company'])
        self.city = unicodedata.normalize('NFD', info['city'])
        self.street_address = unicodedata.normalize('NFD', info['street_address'])
        self.suburb = unicodedata.normalize('NFD', info['suburb'])
        self.postcode = info['postcode']
        self.country = unicodedata.normalize('NFD', info['country'])
        self.phone = info['phone']
        self.email = unicodedata.normalize('NFD', info['email'])

# --------------------------------------------

class Payment():
    def __init__(self, payment):
        self.method_name = unicodedata.normalize('NFD', payment['method_name'])
        self.method_code = payment['method_code']

# --------------------------------------------

class StatusHistory():
    def __init__(self, history):
        self.status_history_id = history['status_history_id']
        self.status_id = history['status_id']
        self.status_date = history['status_date']
        self.status_comments = history['status_comments']

    # ------------------------------------------

    def get_sante(self):
        sante = []

        if self.status_comments != None and self.status_comments != '':
            sante = self.status_comments.split("<br />")
            sante = sante[1:-1]

            # special cases
            if len(sante) > 6 :
                sante = sante[-6:]

            sante = [item.replace("\r\n", "") for item in sante]
            sante = [unicodedata.normalize('NFD', item) for item in sante]

        return sante