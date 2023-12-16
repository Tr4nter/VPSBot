import os
import asyncio
from Cogs.Tickets.Ticket import createTicket
from Cogs.Tickets.createView import bitserverclient

from discord.ext.commands.context import Context
from discord.ext.commands.bot import Bot
import discord
from discord import app_commands
from discord.ext import commands, tasks
import motor.motor_asyncio

from typing import List 
import datetime

from jsonutils import save_json
from jsonutils import get_json
from utils import deliveryCheck
from utils import admin


from dotenv import load_dotenv
load_dotenv()

token = os.environ.get('TOKEN')

extensions = ['Cogs.Tickets.Ticket', 'Cogs.StoreList.StoreList', 'Cogs.FinishedOrders.FinishedOrders', 'Cogs.Promocode.Promocode', 'Cogs.Panel.Panel']

mongoclient = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
mainDB = mongoclient.shitposterbot

class BotWithDatabase(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mainDB = mainDB
        if self.mainDB != None:
            self.finishedCollections = self.mainDB.finishedCollections
            self.panelCollections = self.mainDB.panelCollections
            self.promocodeCollections = self.mainDB.promocodeCollections
            self.storeCollections = self.mainDB.storeCollections
            self.ticketCollections = self.mainDB.ticketCollections
            self.rebootRequests = self.mainDB.rebootRequests

client: BotWithDatabase = BotWithDatabase(command_prefix='!' ,intents=discord.Intents.all())


async def checkAdmin(ctx: Context):
    return ctx.author.id == 672514949184225310
    # return ctx.member


async def loadCogs():
    for i in extensions:
        await client.load_extension(i)



paidSent = []
processing = []


currentListOfOrders = []

confirmer = os.environ.get("CONFIRMER")

async def clearData(user: int, clearChannel=False):
    loopData = await client.ticketCollections.find_one({"_id": user})
    if loopData:
        loopData["currentInvoice"] = None
        loopData["currentProduct"] = None
        loopData["currentRegion"] = None
        if clearChannel:
            del loopData["Tickets"][user]["ticketChannel"]
        await client.ticketCollections.update_one({"_id": user, "$set": loopData})


@tasks.loop(seconds=1)
async def loopa():
    global currentListOfOrders
    loopData = client.ticketCollections.find()
    temp = []
    userList = [i["_id"] async for i in loopData]
    async for userData in loopData:

        currentInvoice = userData['currentInvoice']
        if not currentInvoice: continue
        if currentInvoice.startswith("paypal"): temp.append(userData["_id"]); continue
        inv = bitserverclient.get_invoice(invoice_id=currentInvoice)
        if inv["status"] == "confirmed": temp.append(userData["_id"])
        if userData["_id"] in processing: continue
        currentExpiration = int((inv["expirationTime"]-inv["currentTime"])/1000)
        try:
            channel = await client.fetch_channel(userData["ticketChannel"])
            message = await channel.fetch_message(userData["currentMessage"])
            await message.edit(content=f"Expiring in {currentExpiration} seconds")
        except Exception as e: pass


        if userData["currentInvoice"] == None: continue
        
        if inv["status"] == "expired":
            message = await channel.fetch_message(userData["currentMessage"])
            await message.edit(content=f"Expired")
            await clearData(userData["_id"])
            await channel.send(f'{inv["id"]} invoice has expired\nPlease create another buy order to retry, this ticket channel will stay active.') 
        elif inv['status'] == "new":
            if channel.id in paidSent: paidSent.remove(channel.id)
        elif inv["status"] == "paid" and channel.id not in paidSent:
            await channel.send(f'{inv["id"]} invoice has received payment, please wait for it to be confirmed.') 
            paidSent.append(channel.id)
        elif inv["status"] == "confirmed":


            await channel.send(f'{inv["id"]} invoice has been confirmed, you will receive your product shortly.') 
            try:
                forwardChannel = await client.fetch_channel(loopData["forwardChannel"])
            except discord.errors.NotFound: continue
            await forwardChannel.send(f'Purchase request: {userData["currentProduct"]}\nRegion:{userData["currentRegion"]}\nID: {userData["currentInvoice"]}')
            processing.append(userData["_id"])
    currentListOfOrders = [i for i in userList if i in temp]


# @client.tree.interaction_check
@client.tree.command(name="deliver", guild=discord.Object(id=1163826007501979670))
async def deliver(ctx: discord.Interaction, id: str, ip: str, username: str, password: str):
    if ctx.user.id != os.environ.get("ADMIN") and ctx.user.id != int(confirmer): return
    await ctx.response.defer()
    loopData =  client.ticketCollections.find()
    # content = ' '.join(content)
    async for userData in loopData["Tickets"]:
        if id == userData["currentInvoice"]:
            # channel = await client.fetch_channel(loopData["Tickets"][user]["ticketChannel"])
            channel = await client.fetch_user(confirmer)
            if not channel: await ctx.channel.send("Error|Channel not found, please hold this delivery"); return
            confirmMessage = await channel.send(f"ID: {id}\nIP: {ip}\nUser: {username}\nPass:{password}")
            await confirmMessage.add_reaction("✅")
            await confirmMessage.add_reaction("❌")

            # finishedData = get_json(finishedDataPath)
            currentProduct = userData["currentProduct"]
            finishedData = await client.finishedCollections.find_one({"_id": currentProduct})
            await client.finishedCollections.update_one({"_id": currentProduct}, {"$inc": {"Count": 1}})

            try:
                message = await channel.fetch_message(userData["currentMessage"])
                await message.edit(content=f"Delivered")
            except Exception: pass


            await ctx.followup.send("Success")
            return

async def reboot_AutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    panelData = await client.rebootRequests.find_one({"_id": interaction.user.id})
    if not panelData: return []
    res = []
    for machine_id in panelData["machines"]:
        res.append(machine_id)
    return [app_commands.Choice(name=k, value=str(k)) for k in res]


@client.tree.command(name="confirm_reboot", guild=discord.Object(id=1163826007501979670))
@app_commands.autocomplete(machine_id=reboot_AutoComplete)
async def confirm_reboot(ctx: discord.Interaction, machine_id: str):
    if ctx.user.id != os.environ.get("ADMIN") and ctx.user.id != int(confirmer): return
    user = 0
    rebootRequests =  client.rebootRequests.find()
    async for userData in rebootRequests:
        if machine_id in userData["machines"]:
            user = userData["_id"]
            break

    if user == 0: return
    userData = await client.ticketCollections.find_one({"_id": user})
    rebootRequests = await client.rebootRequests.find_one({"_id": user})


    try:
        await client.rebootRequests.update_one({"_id": user}, {"$pull": {"machines": machine_id}})
    except: pass
    
    ticketChannel = await client.fetch_channel(userData["ticketChannel"])
    await ticketChannel.send(f'{machine_id} has finished with rebooting')
    await ctx.response.send_message("Success")


# @client.tree.interaction_check(deliveryCheck)
@client.tree.command(name="get_queue", guild=discord.Object(id=1163826007501979670))
async def get_queue(interaction: discord.Interaction):
    if interaction.user.id != os.environ.get("ADMIN") and interaction.user.id != int(confirmer): return
    rebootRequests = client.rebootRequests.find()
    res = "```"
    async for rebootRequest in rebootRequests:
        machineData = await client.panelCollections.find_one({"_id": machine_id})
        for machine_id in rebootRequest["machines"]:
            temp = f'**REBOOT**|{machine_id}|IP:{machineData["IP"]}|Username:{machineData["User"]}|Pass:{machineData["Pass"]}\n'
            if len(res + temp) >= 2048:
                await interaction.channel.send(res + "```")
                res = "```"
            res += temp
    loopData = await client.ticketCollections.find_one({"_id": str(interaction.user.id)})
    for user in currentListOfOrders:
        temp = f'**Purchase**|{loopData["currentProduct"]}|Region:{loopData["currentRegion"]}|ID: {loopData["currentInvoice"]}\n'
        if len(res + temp) >= 2048:
            await interaction.channel.send(res + "```")
            res = "```"
        res += temp
    await interaction.channel.send(res+"```")



@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    con = await client.fetch_user(confirmer)
    channel = con.dm_channel
    if not channel: channel = await con.create_dm()

    message = await channel.fetch_message(payload.message_id)
    if payload.channel_id != channel.id: return

    emote = payload.emoji.name
    if emote != "✅" and emote != "❌": return

    if con.id != payload.user_id:
        return

    data =[i.strip() for i in message.content.replace("\n", ":").split(":")]
    id = data[1]
    ip = data[3]
    username = data[5]
    password = data[7]
    userData = await client.ticketCollections.find_one({"currentInvoice": id})

    if userData["_id"] == "": return

    if emote == "✅":
        ticketChannel = await client.fetch_channel(userData["ticketChannel"])
        await ticketChannel.send(message.content)
        panelData = await client.panelCollections.find_one({"Owner": userData["_id"]})
        if not panelData:
            await client.panelCollections.insert_one({"_id":id, "Owner": userData["_id"]})
        panelData = await client.panelCollections.find_one({"_id": id})


        expirationObj = datetime.datetime.now() + datetime.timedelta(days=20)
        panelData["Product"] = userData["currentProduct"]
        panelData["Region"] = userData["currentRegion"]
        panelData["Expiration"] = expirationObj.timestamp()
        panelData["IP"] = ip
        panelData["User"] = username
        panelData["Pass"] =   password 
        await client.panelCollections.update_one({"_id": id}, {"$set": panelData})

        await ticketChannel.send(f"Warranty expires <t:{int(expirationObj.timestamp())}:R>")
        await clearData(userData["_id"])

        try:
            processing.remove(userData["_id"])
        except: pass
    else:
        setting = get_json("settings.json")
        forwardChannel = await client.fetch_channel(setting["forwardChannel"])
        await forwardChannel.send(f"{id} has failed, please try sending again")

@client.event 
async def on_ready():
   
    client.add_view(createTicket())
    await client.tree.sync(guild=discord.Object('1163825960399949884'))
    await client.tree.sync(guild=discord.Object('1163826007501979670'))
    print(f"{client.user} is ready")
    loopa.start()


asyncio.run(loadCogs())
client.run(token)



