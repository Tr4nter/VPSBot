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
from utils import check, ctxcheck

finishedDataPath = 'finished.json'
storeDataPath = 'storedata.json'

async def fincheck(interaction: discord.Interaction):
    storeData = get_json(storeDataPath)
    finishedData = get_json(finishedDataPath)
    for v in storeData['items']:
        if not v in finishedData:
            finishedData[v] = 0
    save_json(finishedData, finishedDataPath)
    return interaction.user.id == 672514949184225310 or interaction.user.id == 861763675915288576

async def labelAutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    storeData = get_json(storeDataPath)
    return [app_commands.Choice(name=k, value=k) for k in storeData['items']]

class FinishedOrders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @app_commands.command(name='view_finished')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(fincheck)
    async def view_finished(self, interaction: Interaction):
        finishedData = get_json(finishedDataPath)
        storeData = get_json(storeDataPath)
        guild = interaction.guild
        guildId = guild.id

        listStr = "```"
        current = 0
        for k,v in finishedData.items():
            current+=v*storeData['items'][k]
            listStr += f"{k}:   {v}| Total of product: ${v*storeData['items'][k]}\n"

        listStr += f"\nTotal of all: ${current}"
        listStr += "```"
        await interaction.response.send_message(listStr, ephemeral=True)


    @app_commands.command(name='change_finished')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.autocomplete(labels=labelAutoComplete)
    @app_commands.check(fincheck)
    async def change_finished(self, interaction: Interaction, labels: str, amount: int):
        finishedData = get_json(finishedDataPath)
        finishedData[labels] = amount
        save_json(finishedData, finishedDataPath)
        await interaction.response.send_message('success', ephemeral=True)



    @app_commands.command(name='increase_finished')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.autocomplete(labels=labelAutoComplete)
    @app_commands.check(fincheck)
    async def increase_finished(self, interaction: Interaction, labels: str):
        finishedData = get_json(finishedDataPath)
        finishedData[labels] += 1
        save_json(finishedData, finishedDataPath)
        await interaction.response.send_message('success', ephemeral=True)



    @app_commands.command(name='decrease_finished')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.autocomplete(labels=labelAutoComplete)
    @app_commands.check(check)
    async def decrease_finished(self, interaction: Interaction, labels: str):
        finishedData = get_json(finishedDataPath)
        if finishedData[labels] > 0:
            finishedData[labels] -= 1
            save_json(finishedData, finishedDataPath)
            await interaction.response.send_message('success', ephemeral=True)
            return
        await interaction.response.send_message('value is 0', ephemeral=True)



async def setup(bot):
    finishedData = get_json(finishedDataPath)
    storeData = get_json(storeDataPath)
    for v in storeData['items']:
        if not v in finishedData:
            finishedData[v] = 0
    save_json(finishedData, finishedDataPath)
    await bot.add_cog(FinishedOrders(bot))
