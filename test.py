import btcpay.crypto
from btcpay import BTCPayClient

prim = btcpay.crypto.generate_privkey()
client = BTCPayClient.create_client(host="http://localhost:14142",code='ayT3Rvn')
print(client.pem)
invoces = client.get_invoices()
print(20/client.get_rate(currency="USD", crypto="LTC"))
new_invoice = client.create_invoice({"price": 20, "currency": "LTC"})
print(new_invoice)

# import motor.motor_asyncio
# import json
# from jsonutils import *
# import asyncio
# mongoclient = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
# mainDB = mongoclient.shitposterbot
# finishedCollections = mainDB.finishedCollections
# panelCollections = mainDB.panelCollections
# promocodeCollections = mainDB.promocodeCollections
# storeCollections = mainDB.storeCollections
# ticketCollections = mainDB.ticketCollections
# rebootRequests = mainDB.rebootRequests


# data = get_json("paneldata.json")
# async def test():
#     for k, v in data["RebootRequest"].items():
#         await rebootRequests.insert_one({"_id": k, "machines": v})


# asyncio.run(test())
