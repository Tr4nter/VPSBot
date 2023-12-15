import btcpay.crypto
from btcpay import BTCPayClient

prim = btcpay.crypto.generate_privkey()
client = BTCPayClient.create_client(host="http://localhost:14142",code='zF7fS2C')
print(client.pem)
invoces = client.get_invoices()
print(20/client.get_rate(currency="USD", crypto="LTC"))
# new_invoice = client.create_invoice({"price": 20, "currency": "LTC"})
# print(new_invoice)

