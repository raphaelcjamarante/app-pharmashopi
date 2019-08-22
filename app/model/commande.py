# -*- coding: utf-8 -*-

import app.model.delivery
import app.model.product
import unicodedata

class Commande():
    """Represents one order from the batch

    Attributes
    ----------
    id : str
    language : str
    status : str
    date_created : str
    shipping : Shipping object
    payment : Payment object
    customer : Customer object
    delivery_address : DeliveryAddress object
    statuses_history : dict of StatusHistory objects
    products : dict of Product objects
        (key is different from id. It is the same as in the request)
    totalht : float
        Total cost without tax rate
    totalttc : float
        Total cost with tax rate

    Methods
    -------
    calculate_cost(self)
        Calculates the total cost of the order with and without the tax rate
    get_date_created(self, mode='string')
        Gets the date of creation in different formats
    get_sante(self)
        Gets the health information of the client linked to the order
    get_total_quantity(self)
        Gets the total quantity of all products in the order, excluding the delivery method
    """

    def __init__(self, cmd):

        print(f"Traitement de la commande : {cmd['id']}")

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
    """Represents the customer associated with an order
    """

    def __init__(self, info):
        self.id = info['id']
        self.name = unicodedata.normalize('NFD', info['name'])
        self.company = unicodedata.normalize('NFD', info['company'])
        self.city = unicodedata.normalize('NFD', info['city'])
        self.street_address = unicodedata.normalize('NFD', info['street_address'])
        self.postcode = info['postcode']
        self.country = unicodedata.normalize('NFD', info['country'])
        self.phone = info['phone']
        self.email = unicodedata.normalize('NFD', info['email'])

# --------------------------------------------

class Payment():
    """Represents the payment with an order
    """

    def __init__(self, payment):
        self.method_name = unicodedata.normalize('NFD', payment['method_name'])
        self.method_code = payment['method_code']

# --------------------------------------------

class StatusHistory():
    """Represents the history associated with an order
    
    Attributes
    ----------
    status_comments : str
        String containing the health information of the client

    Methods
    -------
    get_sante(self)
        Gets the parsed content of the health info in a list
    """

    def __init__(self, history):
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