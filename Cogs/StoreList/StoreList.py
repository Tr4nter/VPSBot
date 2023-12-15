from typing import List
from utils import check
import discord
from discord import app_commands
from discord.ext import commands

from jsonutils import save_json
from jsonutils import get_json

from Cogs.Tickets.createView import createTicket

storeDataPath = 'storedata.json'
ticketDataPath = 'ticketdata.json'




async def remove_itemAutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    storeData = get_json(storeDataPath)
    return [app_commands.Choice(name=k, value=k) for k in storeData['items']]
    

class StoreList(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot


    @app_commands.command(name="add_item", description="Make a shop item")
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check) # Eqv to @command.before_invoke in this context
    async def add_item(self, interaction: discord.Interaction, label: str, price_in_usd: int):
        ticketData = get_json(ticketDataPath)
        label = label.strip()
        storeData = get_json(storeDataPath)

        if label not in storeData["items"]:
            storeData["items"][label] = price_in_usd
        save_json(storeData, storeDataPath)
        await interaction.response.send_message(f"Successfully added {label} with the price of ${price_in_usd}", ephemeral=True)
        try:
            ticketCreateChannel = await self.bot.fetch_channel(ticketData["ticketCreateMessageChannel"])
            print(ticketCreateChannel)
        except:
            return
        
        try:
            message = await ticketCreateChannel.fetch_message(ticketData["ticketCreateMessage"])
            await message.edit(view=createTicket())
        except:
            return



    @app_commands.command(name="remove_item", description="Make a shop item")
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.autocomplete(labels=remove_itemAutoComplete)
    @app_commands.check(check) # Eqv to @command.before_invoke in this context
    async def remove_item(self, interaction: discord.Interaction, labels: str):
        ticketData = get_json(ticketDataPath)
        storeData = get_json(storeDataPath)
        guild = interaction.guild

        del storeData["items"][labels]
        save_json(storeData, storeDataPath)

        await interaction.response.send_message(f"Successfully removed {labels}", ephemeral=True)
        try:
            ticketCreateChannel = await self.bot.fetch_channel(ticketData["ticketCreateMessageChannel"])
        except:
            return
        
        try:
            message = await ticketCreateChannel.fetch_message(ticketData["ticketCreateMessage"])
            await message.edit(view=createTicket())
        except:
            return


    @app_commands.command(name="list_items", description="Make a shop item")
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check) # Eqv to @command.before_invoke in this context
    async def list_items(self, interaction: discord.Interaction):
        storeData = get_json(storeDataPath)
        guild = interaction.guild
        guildId = guild.id

        listStr = "```"
        for k,v in storeData['items'].items():
            listStr += f"{k}:   ${v}\n"


        listStr += "```"
        await interaction.response.send_message(listStr, ephemeral=True)


async def setup(bot):
    storeData = get_json(storeDataPath)
    if 'items' not in storeData:
        storeData["items"] = {}
    save_json(storeData, storeDataPath)
    await bot.add_cog(StoreList(bot))
