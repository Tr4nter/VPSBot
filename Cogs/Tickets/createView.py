from hashlib import new
import os
from btcpay import BTCPayClient
from dotenv import load_dotenv

import discord
from discord import SelectOption, interactions
from discord.interactions import Interaction
from discord.ui import View
from discord.utils import get

from jsonutils import save_json
from jsonutils import get_json

import uuid

import datetime
from utils import admin

load_dotenv()


ticketDataPath = 'ticketdata.json'
botDataPath = 'botdata.json'
storeDataPath = 'storedata.json'
promocodeDataPath = 'promocodes.json'


print(os.environ.get('SERVERIP'))
print(os.environ.get('PRIVATE_CRYPTO'))
print(os.environ.get('BITTOKEN'))
bitserverclient = BTCPayClient(host=os.environ.get("SERVERIP"), pem=os.environ.get('PRIVATE_CRYPTO'), tokens={'merchant':os.environ.get('BITTOKEN')}, insecure=True)

class promoCodeModal(discord.ui.Modal, title="Promocode"):
    rom = discord.ui.TextInput(label="Promocode", required=False)
    val: dict = None

    async def on_submit(self, interaction: discord.Interaction) -> None:
        promocodeData = get_json(promocodeDataPath)
        promocode = self.rom.value
        if not promocode in promocodeData: await interaction.response.send_message("Wrong code", ephemeral=True, delete_after=5)
        if promocodeData[promocode]["Type"] == "literal":
            await interaction.response.send_message(f'Successful, you will receive a ${promocodeData[promocode]["Value"]} discount', ephemeral=True, delete_after=5)
        else:
            await interaction.response.send_message(f'Successful, you will receive a {promocodeData[promocode]["Value"]}% discount', ephemeral=True, delete_after=5)


        self.val = promocodeData[promocode]





class createTicket(View):


    def __init__(self, productList):
        super().__init__(timeout=None)


        self.productSelection = discord.ui.Select(custom_id="productSelection", options=productList, placeholder="Select product...")
        self.productSelection.callback = self.productSelectionSelectCallback

        self.paymentMethod = discord.ui.Select(custom_id="paymentMethod", options=
        [
            SelectOption(label="BTC", description="BTC as a payment method", value='BTC'),
            SelectOption(label="LTC", description="LTC as a payment method", value='LTC'),
            SelectOption(label="PayPal", description="PayPal as a payment method", value='PayPal')

        ], placeholder="Select payment method...")
        self.paymentMethod.callback = self.paymentMethodSelectCallback

        self.serverRegion = discord.ui.Select(custom_id="serverLocation", options=
        [
            SelectOption(label="US", description="Server location in US", value='US'),
            SelectOption(label="EU", description="Server location in EU", value='EU'),

        ], placeholder="Select server region...")
        self.serverRegion.callback = self.serverRegionSelectCallback

        self.buyButton = discord.ui.Button(label="Create buy order",custom_id="buyButton")
        self.buyButton.callback = self.buyButtonCallback

        self.promoCodeButton = discord.ui.Button(label="Enter a promocode", custom_id="promoCodeButton")
        self.promoCodeButton.callback = self.promoCodeButtonCallback

        
        self.add_item(self.productSelection)
        self.add_item(self.paymentMethod)
        self.add_item(self.serverRegion)
        self.add_item(self.promoCodeButton)
        self.add_item(self.buyButton)

        self.users = {}

    async def productSelectionSelectCallback(self, interaction: Interaction):
        if str(interaction.user.id) not in self.users:
            self.users[str(interaction.user.id)] = {}
        user = interaction.user
        userId = user.id
    
        data = interaction.data
        self.users[str(interaction.user.id)]["currentProduct"] = data['values'][0]
        await interaction.response.send_message('Success', delete_after=0, ephemeral=True)


    async def serverRegionSelectCallback(self, interaction: Interaction):
        if str(interaction.user.id) not in self.users:
            self.users[str(interaction.user.id)] = {}
        user = interaction.user
        userId = user.id
    
        data = interaction.data
        self.users[str(interaction.user.id)]["currentRegion"] = data['values'][0]
        await interaction.response.send_message('Success', delete_after=0, ephemeral=True)


    async def paymentMethodSelectCallback(self, interaction: Interaction):
        if str(interaction.user.id) not in self.users:
            self.users[str(interaction.user.id)] = {}
        user = interaction.user
        userId = user.id

        data = interaction.data
        self.users[str(interaction.user.id)]["currentPayment"] = data['values'][0]
        await interaction.response.send_message('Success', delete_after=0, ephemeral=True)


    async def promoCodeButtonCallback(self, interaction: discord.Interaction):
        if str(interaction.user.id) not in self.users:
            self.users[str(interaction.user.id)] = {}
        self.users[str(interaction.user.id)]["Modal"] = promoCodeModal()

        await interaction.response.send_modal(self.users[str(interaction.user.id)]["Modal"])
        
         


    async def buyButtonCallback(self, interaction: discord.Interaction):
        if str(interaction.user.id) not in self.users:
            self.users[str(interaction.user.id)] = {}
        ticketData = await interaction.client.ticketCollections.find_one({"_id": interaction.user.id})
        guild = interaction.guild
        
        formData = self.users[str(interaction.user.id)]

        user = interaction.user
        userId = user.id

        if not 'currentPayment' in formData:
            await interaction.response.send_message("Please select a payment",ephemeral=True, delete_after=3)
            return
        if not 'currentProduct' in formData:
            await interaction.response.send_message("Please select a product",ephemeral=True, delete_after=3)
            return
        if not 'currentRegion' in formData:
            await interaction.response.send_message("Please select a region",ephemeral=True, delete_after=3)
            return
        if not ticketData:
            await interaction.client.ticketCollections.insert_one({"_id": userId, "currentInvoice": None, "currentProduct": None, "currentRegion": None, "currentMessage": None})
        ticketData = await interaction.client.ticketCollections.find_one({"_id": userId})

        if ticketData["currentInvoice"]:
            await interaction.response.send_message("You've already have an order going on, please resolve it before making another order.", ephemeral=True, delete_after=3)
            return

        storeData = await interaction.client.storeCollections.find_one({"_id": formData["currentProduct"]})
        settings = get_json("settings.json")
        category = get(guild.categories, id=settings["ticketCategory"])
        if "ticketChannel" not in ticketData:
            channel = await category.create_text_channel(name=f"{user.name}")
            await channel.set_permissions(interaction.guild.default_role, read_messages=False)
            await interaction.client.ticketCollections.update_one({"_id": userId}, {"$set": {"ticketChannel": channel.id}})
        else:
            channel = await interaction.guild.fetch_channel(ticketData["ticketChannel"])

        await channel.set_permissions(user, read_messages=True, send_messages=True)

        crypto = False
        new_invoice = None
        deductedPrice = storeData["Price"]
        if deductedPrice <= 0: await interaction.response.send_message("Error",ephemeral=True, delete_after=5) 
        if 'Modal' in formData and formData['Modal'].val:
            if formData['Modal'].val["Type"] == "literal":
                deductedPrice -= formData['Modal'].val["Value"]
            else:
                deductedPrice = (deductedPrice / 100)*(formData['Modal'].val["Value"])
        price = 0
        await channel.send(f"Buy order for {formData['currentProduct']}, Region: {formData['currentRegion']}")
        if formData['currentPayment']== "BTC":
            new_invoice = bitserverclient.create_invoice({"price": deductedPrice, "currency": "USD"})
            price = new_invoice["btcPrice"]
            crypto = True
        elif formData['currentPayment']== "LTC":
            rate = bitserverclient.get_rate(currency="USD", crypto="LTC")
            new_invoice = bitserverclient.create_invoice({"price": deductedPrice/rate, "currency": "LTC"})
            price = new_invoice["price"]
            crypto = True
        if crypto and new_invoice:
            ticketData["currentInvoice"] = new_invoice['id']

            await channel.send(f'Please send exactly\n{price} {formData["currentPayment"]}\nto this address\n{new_invoice["addresses"][formData["currentPayment"]]}')
            ticketData["currentMessage"] = (await channel.send("Expiring in: ...")).id
        else:
            orderId = "paypal"+str(uuid.uuid4()).split("-")[-1]

            ticketData["currentInvoice"] = orderId
            await channel.send(f"<@{admin}> PayPal order, please wait for admin's response., ID={orderId}, Price={deductedPrice}")


        ticketData["currentProduct"] = formData['currentProduct']
        ticketData["currentRegion"] = formData['currentRegion']
        await interaction.client.ticketCollections.update_one({"_id": userId}, {"$set": ticketData})


        


        

