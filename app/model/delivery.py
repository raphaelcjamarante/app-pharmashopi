# -*- coding: utf-8 -*-

import unicodedata

class Shipping():
    """Represents the shipping associated with an order
    """

    def __init__(self, shipping):
        self.tracking_code = shipping['tracking_code']
        self.tracking_url = shipping['tracking_url']
        self.method_code = shipping['method_code']
        self.method_name = unicodedata.normalize('NFD', shipping['method_name'])
        if 'mondial_relay' in shipping:
            self.relay_id = shipping['mondial_relay']['relay_id']
            self.relay_country_code = shipping['mondial_relay']['relay_country_code']

# --------------------------------------------

class DeliveryAddress():
    """Represents the delivery address associated with an order
    
    Attributes
    ----------
    gender : str
    name : str
    company : str
        Business location of the delivery
    phone : str
        Phone, either of the delivery address or the customer
    street : str
    city : str
    postcode : str
    country : str
    country_code : str

    Methods
    -------
    get_complete_address(self)
        Gets the complete address string
    """

    def __init__(self, delivery, customer):
        self.gender = delivery['gender']
        self.name = unicodedata.normalize('NFD', customer.name)

        # treats special case : Mondial Relay
        if delivery['name'] != customer.name:
            self.company = unicodedata.normalize('NFD', delivery['name'])
        else:
            self.company = unicodedata.normalize('NFD', delivery['company'])

        if delivery['phone'] == '':
            self.phone = customer.phone
        else:
            self.phone = delivery['phone']

        self.street = unicodedata.normalize('NFD', delivery['street_address'])
        self.city = unicodedata.normalize('NFD', delivery['city'])
        self.postcode = delivery['postcode']
        self.country = unicodedata.normalize('NFD', delivery['country'])
        self.country_code = delivery['country_code']
        
        self.email = customer.email

    # ------------------------------------------

    def get_complete_address(self):
        return (self.name + '\n'
                + self.company + '\n'
                + self.street + '\n'
                + self.city + ", " + self.postcode + '\n'
                + self.country + '\n'
                + self.phone + '\n'
                + self.email)

