# -*- coding: utf-8 -*-

import socket
import time

import app.utilities

ip_robot = app.utilities.get_config_data()['ip_robot']

#------------------------------------------------------------
def retrait(idarticle, qte, idrequest, sortie):
    """ Request de retrait pour l'article et la quantité souhaités

    Parameters
    ----------
    idarticle : int
        Reference de l'article
    qte : int
        Quantité souhaité
    idrequest : int
        Id request
    sortie : int
        Choisit la sortie du robot
    """

    datahello = """<WWKS Version="2.0" TimeStamp="2013-04-16T11:14:00Z">
  <HelloRequest Id="1001">
    <Subscriber Id="100" >
      <Capability Name="KeepAlive"/>
      <Capability Name="Status"/>
      <Capability Name="Input"/>
      <Capability Name="InitiateInput"/>
      <Capability Name="ArticleMaster"/>
      <Capability Name="StockDelivery"/>
      <Capability Name="StockInfo"/>
      <Capability Name="Output"/>
      <Capability Name="TaskInfo"/>
      <Capability Name="TaskCancel"/>
      <Capability Name="Configuration"/>
      <Capability Name="StockLocationInfo"/>
    </Subscriber>
  </HelloRequest>
</WWKS>"""

    datarequest = """<WWKS Version="2.0" TimeStamp="2018-09-24T11:14:16Z">
    <OutputRequest Id="""'"' + str(idrequest) + '"' + """ Source="1001" Destination="999">
        <Details Priority="Normal" OutputDestination=""" + '"' + str(sortie) + '"' + """/>
        <Criteria ArticleId=""" + '"' + str(idarticle) + '"' + """ Quantity=""" + '"'+ str(qte) + '"' + """ />
    </OutputRequest>
</WWKS>"""

    v = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    v.connect((ip_robot, 6050))
    v.send(datahello.encode())
    v.recv(1024)
    v.send(datarequest.encode())
    chainerecu = v.recv(1024)
    v.close()


#------------------------------------------------------------
def robot_stock(idarticle):
    """ Verification de stock du robot pour l'article souhaité

    Parameters
    ----------
    idarticle : int
        Reference de l'article

    Return
    ------
    quantite_f : str
        Quantite en stock dans le robot
    """

    datahello = """<WWKS Version="2.0" TimeStamp="2018-09-24T11:14:16Z">
      <HelloRequest Id="1001">
        <Subscriber Id="100" >
        </Subscriber>
      </HelloRequest>
    </WWKS>"""

    datastock = """<WWKS Version="2.0" TimeStamp="2013-04-16T11:14:00Z">
        <StockInfoRequest Id="1003" Source="1001" Destination="999" IncludePacks="True">
            <Criteria ArticleId=""" + '"' + str(idarticle) + '"' + """/>
        </StockInfoRequest>
        </WWKS>"""

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_robot, 6050))
    s.send(datahello.encode())
    s.recv(1024)
    s.send(datastock.encode())

    time.sleep(1)
    chaine = s.recv(1024).decode('utf-8')
    if chaine.find("Quantity") != -1:
        quantite_f = chaine[str(chaine).find("Quantity")+10 : str(chaine).find("Quantity")+13]
        if quantite_f != "":
            while quantite_f[-1] not in ["1","2","3","4","5","6","7","8","9","0"]:
                quantite_f = quantite_f[:-1]
            time.sleep(2)
            s.close()
            return quantite_f
        else :
            s.close()
            return "0"
    else:
        s.close()
        return "0"