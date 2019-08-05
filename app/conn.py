# -*- coding: utf-8 -*-

import requests

def connexion():
    """Connexion automatique au backoffice. Utilisé pour faire le web scraping.
    Problème : sessionAdminSSL doit être pris à la main ; backoffice ne permet pas un processus completement automatique
    """
    login_data = [{"login": "xxx", "pass": "xxx"}]

    headers =  {"Cookie": "sessionAdminSSL=xxx"}

    login_url = "https://www.pharmashopi.com/superadmin/admin_login_admin.php"

    session = requests.Session()

    session.post(login_url, data=login_data, headers=headers)

    #TODO : test if successfully logged in

    return (session, headers)