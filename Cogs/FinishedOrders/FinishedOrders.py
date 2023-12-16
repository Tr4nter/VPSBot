from typing import List
import discord
from discord import Guild, SelectOption, TextChannel
from discord.interactions import Interaction
from discord.message import Message
from discord.ui import Select, View
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions
from discord import app_commands
from discord.utils import get

from jsonutils import save_json
from jsonutils import get_json
import os
from utils import check, ctxcheck

finishedDataPath = 'finished.json'
storeDataPath = 'storedata.json'

async def fincheck(interaction: discord.Interaction):
    storeData = interaction.client.storeCollections.find()
    async for k in storeData:
        finishedData = await interaction.client.finishedCollections.find_one({"_id": k["_id"]})
        if not finishedData:
            await interaction.client.finishedCollections.insert_one({"_id": k["_id"], "Count": 0})
    return interaction.user.id == 672514949184225310 or interaction.user.id == 861763675915288576

async def labelAutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    storeData = interaction.client.finishedCollections.find()
    try:
        return [app_commands.Choice(name=k["_id"], value=k["_id"]) async for k in storeData]
    except Exception as e: print(e)

class FinishedOrders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @app_commands.command(name='view_finished')
    @app_commands.guilds(discord.Object(id=int(os.environ.get("STORESERVERID"))))

    @app_commands.check(fincheck)
    async def view_finished(self, interaction: Interaction):
        finishedData = interaction.client.finishedCollections.find()
        guild = interaction.guild

        listStr = "```"
        current = 0
        async for k in finishedData:
            count = k["Count"]
            storeData = await interaction.client.storeCollections.find_one({"_id": k["_id"]})
            current+=count*storeData["Price"]
            listStr += f"{k['_id']}:   {k['Count']}| Total of product: ${k['Count']*storeData['Price']}\n"

        listStr += f"\nTotal of all: ${current}"
        listStr += "```"
        await interaction.response.send_message(listStr, ephemeral=True)


    @app_commands.command(name='change_finished')
    @app_commands.guilds(discord.Object(id=int(os.environ.get("STORESERVERID"))))

    @app_commands.autocomplete(labels=labelAutoComplete)
    @app_commands.check(fincheck)
    async def change_finished(self, interaction: Interaction, labels: str, amount: int):
        finishedData = await interaction.client.finishedCollections.find_one({"_id": labels}) 
        finishedData["Count"] = amount
        await interaction.client.finishedCollections.update_one({"_id": labels}, {"$set":finishedData})
        await interaction.response.send_message('success', ephemeral=True)



    @app_commands.command(name='increase_finished')
    @app_commands.guilds(discord.Object(id=int(os.environ.get("STORESERVERID"))))

    @app_commands.autocomplete(labels=labelAutoComplete)
    @app_commands.check(fincheck)
    async def increase_finished(self, interaction: Interaction, labels: str):
        await interaction.client.finishedCollections.update_one({"_id": labels}, {"$inc": {"Count": 1}})
        await interaction.response.send_message('success', ephemeral=True)



    @app_commands.command(name='decrease_finished')
    @app_commands.guilds(discord.Object(id=int(os.environ.get("STORESERVERID"))))

    @app_commands.autocomplete(labels=labelAutoComplete)
    @app_commands.check(check)
    async def decrease_finished(self, interaction: Interaction, labels: str):
        finishedData = await interaction.client.finishedCollections.find_one({"_id": labels}) 
        if finishedData["Count"] > 0:
            await interaction.client.finishedCollections.update_one({"_id": labels}, {"$inc": {"Count": -1}})
            await interaction.response.send_message('success', ephemeral=True)
            return
        await interaction.response.send_message('value is 0', ephemeral=True)



async def setup(bot):
    await bot.add_cog(FinishedOrders(bot))
