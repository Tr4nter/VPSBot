from typing import List
from utils import check
import discord
from discord import app_commands
from discord.ext import commands

from jsonutils import save_json
from jsonutils import get_json

import os
from Cogs.Tickets.createView import createTicket

storeDataPath = 'storedata.json'
ticketDataPath = 'ticketdata.json'




async def remove_itemAutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    storeData = interaction.client.storeCollections.find()
    return [app_commands.Choice(name=k["_id"], value=k["_id"]) async for k in storeData]
    

class StoreList(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot


    @app_commands.command(name="add_item", description="Make a shop item")
    @app_commands.guilds(discord.Object(id=os.environ.get("STORESERVERID")))

    @app_commands.check(check) # Eqv to @command.before_invoke in this context
    async def add_item(self, interaction: discord.Interaction, label: str, price_in_usd: int):
        settings = get_json('settings.json')
        label = label.strip()
        storeData = await interaction.client.storeCollections.find_one({"_id": label})

        if not storeData:
            await interaction.client.storeCollections.insert_one({"_id": label, "Price": price_in_usd})
            await interaction.response.send_message(f"Successfully added {label} with the price of ${price_in_usd}", ephemeral=True)
        try:
            ticketCreateChannel = await self.bot.fetch_channel(settings["ticketCreateMessageChannel"])
        except:
            return
        
        try:
            message = await ticketCreateChannel.fetch_message(settings["ticketCreateMessage"])
            await message.edit(view=createTicket())
        except:
            return



    @app_commands.command(name="remove_item", description="Make a shop item")
    @app_commands.guilds(discord.Object(id=os.environ.get("STORESERVERID")))

    @app_commands.autocomplete(labels=remove_itemAutoComplete)
    @app_commands.check(check) # Eqv to @command.before_invoke in this context
    async def remove_item(self, interaction: discord.Interaction, labels: str):
        storeData = await interaction.client.storeCollections.delete_one({"_id": labels})

        await interaction.response.send_message(f"Successfully removed {labels}", ephemeral=True)
        settings = get_json('settings.json')
        try:
            ticketCreateChannel = await self.bot.fetch_channel(settings["ticketCreateMessageChannel"])
        except:
            return
        
        try:
            message = await ticketCreateChannel.fetch_message(settings["ticketCreateMessage"])
            await message.edit(view=createTicket())
        except:
            return


    @app_commands.command(name="list_items", description="Make a shop item")
    @app_commands.guilds(discord.Object(id=os.environ.get("STORESERVERID")))

    @app_commands.check(check) # Eqv to @command.before_invoke in this context
    async def list_items(self, interaction: discord.Interaction):
        storeData = interaction.client.storeCollections.find()
        guild = interaction.guild

        listStr = "```"
        async for k in storeData:
            listStr += f"{k['_id']}:   ${k['Price']}\n"


        listStr += "```"
        await interaction.response.send_message(listStr, ephemeral=True)


async def setup(bot):
    await bot.add_cog(StoreList(bot))
