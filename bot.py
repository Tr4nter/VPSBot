import os
import asyncio
from Cogs.Tickets.Ticket import createTicket
from Cogs.Tickets.createView import bitserverclient

from discord.ext.commands.context import Context
from discord.ext.commands.bot import Bot
import discord
from discord import app_commands
from discord.ext import commands, tasks

from typing import List 
import datetime

from jsonutils import save_json
from jsonutils import get_json
from utils import deliveryCheck
from utils import admin


from dotenv import load_dotenv
load_dotenv()

token = os.environ.get('TOKEN')
storeDataPath = 'storedata.json'
ticketDataPath = 'ticketdata.json'
finishedDataPath = 'finished.json'
panelDataPath = 'paneldata.json'

extensions = ['Cogs.Tickets.Ticket', 'Cogs.StoreList.StoreList', 'Cogs.FinishedOrders.FinishedOrders', 'Cogs.Promocode.Promocode', 'Cogs.Panel.Panel']

client: Bot = commands.Bot(command_prefix='!' ,intents=discord.Intents.all())


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

def clearData(user: str, clearChannel=False):
    loopData = get_json(ticketDataPath)
    if user in loopData["Tickets"]:
        loopData["Tickets"][user]["currentInvoice"] = None
        loopData["Tickets"][user]["currentProduct"] = None
        loopData["Tickets"][user]["currentRegion"] = None
        if clearChannel:
            print(loopData["Tickets"][user])
            del loopData["Tickets"][user]["ticketChannel"]
        save_json(loopData, ticketDataPath)


@tasks.loop(seconds=1)
async def loopa():
    global currentListOfOrders
    finishedData = get_json(finishedDataPath)
    loopData = get_json(ticketDataPath)
    temp = []
    userList = [i for i in loopData["Tickets"]]
    for user in loopData["Tickets"]:

        currentInvoice = loopData["Tickets"][user]['currentInvoice']
        if not currentInvoice: continue
        if currentInvoice.startswith("paypal"): temp.append(user); continue
        inv = bitserverclient.get_invoice(invoice_id=currentInvoice)
        if inv["status"] == "confirmed": temp.append(user)
        if user in processing: continue
        currentExpiration = int((inv["expirationTime"]-inv["currentTime"])/1000)
        try:
            channel = await client.fetch_channel(loopData["Tickets"][user]["ticketChannel"])
            message = await channel.fetch_message(loopData["Tickets"][user]["currentMessage"])
            await message.edit(content=f"Expiring in {currentExpiration} seconds")
        except Exception as e: pass


        if loopData["Tickets"][user]["currentInvoice"] == None: continue
        
        if inv["status"] == "expired":
            message = await channel.fetch_message(loopData["Tickets"][user]["currentMessage"])
            await message.edit(content=f"Expired")
            clearData(user)
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
            await forwardChannel.send(f'Purchase request: {loopData["Tickets"][user]["currentProduct"]}\nRegion:{loopData["Tickets"][user]["currentRegion"]}\nID: {loopData["Tickets"][user]["currentInvoice"]}')
            processing.append(user)
    currentListOfOrders = [i for i in userList if i in temp]


# @client.tree.interaction_check
@client.tree.command(name="deliver", guild=discord.Object(id=1163826007501979670))
async def deliver(ctx: discord.Interaction, id: str, ip: str, username: str, password: str):
    if ctx.user.id != os.environ.get("ADMIN") and ctx.user.id != int(confirmer): return
    await ctx.response.defer()
    loopData = get_json(ticketDataPath)
    # content = ' '.join(content)
    for user in loopData["Tickets"]:
        if id == loopData["Tickets"][user]["currentInvoice"]:
            # channel = await client.fetch_channel(loopData["Tickets"][user]["ticketChannel"])
            channel = await client.fetch_user(confirmer)
            if not channel: await ctx.channel.send("Error|Channel not found, please hold this delivery"); return
            confirmMessage = await channel.send(f"ID: {id}\nIP: {ip}\nUser: {username}\nPass:{password}")
            await confirmMessage.add_reaction("✅")
            await confirmMessage.add_reaction("❌")

            finishedData = get_json(finishedDataPath)
            finishedData[loopData["Tickets"][user]["currentProduct"]] += 1

            save_json(finishedData, finishedDataPath)
            try:
                message = await channel.fetch_message(loopData["Tickets"][user]["currentMessage"])
                await message.edit(content=f"Delivered")
            except Exception: pass


            await ctx.followup.send("Success")
            return

async def reboot_AutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    panelData = get_json(panelDataPath)
    res = []
    for user in panelData["RebootRequest"]:
        for machine_id in panelData["RebootRequest"][user]:
            res.append(machine_id)
    return [app_commands.Choice(name=k, value=k) for k in res]


@client.tree.command(name="confirm_reboot", guild=discord.Object(id=1163826007501979670))
@app_commands.autocomplete(machine_id=reboot_AutoComplete)
async def confirm_reboot(ctx: discord.Interaction, machine_id: str):
    if ctx.user.id != os.environ.get("ADMIN") and ctx.user.id != int(confirmer): return
    loopData = get_json(ticketDataPath)
    user = 0
    panelData = get_json(panelDataPath)
    for user_id in panelData["RebootRequest"]:
        if machine_id in panelData["RebootRequest"][user_id]:
            user = user_id
            break

    if user == 0: return
    userData = loopData["Tickets"][user]
    try:
        panelData["RebootRequest"][str(user)].remove(machine_id)
        save_json(panelData, panelDataPath)
    except: pass
    
    ticketChannel = await client.fetch_channel(userData["ticketChannel"])
    await ticketChannel.send(f'{machine_id} has finished with rebooting')
    await ctx.response.send_message("Success")


# @client.tree.interaction_check(deliveryCheck)
@client.tree.command(name="get_queue", guild=discord.Object(id=1163826007501979670))
async def get_queue(interaction: discord.Interaction):
    if interaction.user.id != os.environ.get("ADMIN") and interaction.user.id != int(confirmer): return
    panelData = get_json(panelDataPath)
    loopData = get_json(ticketDataPath)
    res = "```"
    for user_id in panelData["RebootRequest"]:
        for machine_id in panelData["RebootRequest"][user_id]:
            machineData = panelData["Users"][user_id][machine_id]
            temp = f'**REBOOT**|{machine_id}|IP:{machineData["IP"]}|Username:{machineData["User"]}|Pass:{machineData["Pass"]}\n'
            if len(res + temp) >= 2048:
                await interaction.channel.send(res + "```")
                res = "```"
            res += temp
    for user in currentListOfOrders:
        temp = f'**Purchase**|{loopData["Tickets"][user]["currentProduct"]}|Region:{loopData["Tickets"][user]["currentRegion"]}|ID: {loopData["Tickets"][user]["currentInvoice"]}\n'
        if len(res + temp) >= 2048:
            await interaction.channel.send(res + "```")
            res = "```"
        res += temp
    await interaction.channel.send(res+"```")



@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    loopData = get_json(ticketDataPath)
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
    user = 0
    userData = {}
    for v in loopData["Tickets"]:
        if str(id) == loopData["Tickets"][v]["currentInvoice"]: user = v; userData = loopData["Tickets"][v]; break

    if user == 0: return

    if emote == "✅":
        ticketChannel = await client.fetch_channel(userData["ticketChannel"])
        await ticketChannel.send(message.content)
        panelData = get_json(panelDataPath)
        if str(user) not in panelData["Users"]:
            panelData["Users"][str(user)] = {}


        expirationObj = datetime.datetime.now() + datetime.timedelta(days=20)
        panelData["Users"][str(user)][str(id)] = {}
        panelData["Users"][str(user)][str(id)]["Product"] = userData["currentProduct"]
        panelData["Users"][str(user)][str(id)]["Region"] = userData["currentRegion"]
        panelData["Users"][str(user)][str(id)]["Expiration"] = expirationObj.timestamp()
        panelData["Users"][str(user)][str(id)]["IP"] = ip
        panelData["Users"][str(user)][str(id)]["User"] = username
        panelData["Users"][str(user)][str(id)]["Pass"] =   password 
        save_json(panelData, panelDataPath)

        await ticketChannel.send(f"Warranty expires <t:{int(expirationObj.timestamp())}:R>")
        clearData(user)

        try:
            processing.remove(user)
        except: pass
    else:
        forwardChannel = await client.fetch_channel(loopData["forwardChannel"])
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



