from typing import List
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get


from jsonutils import save_json
from jsonutils import get_json
from utils import check

promocodeDataPath = 'promocodes.json'

async def promocode_AutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    promoData = interaction.client.promocodeCollections.find()
    return [app_commands.Choice(name=k, value=k) async for k in promoData]

class Promocode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(name='create_promocode')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.choices(type_of_promo=[app_commands.Choice(name='literal', value='literal'),app_commands.Choice(name='percentage', value='percentage')])
    @app_commands.check(check)
    async def create_promocode(self, interaction: discord.Interaction, promocode: str, type_of_promo: str, amount: int):
        amount = amount if type_of_promo == "literal" else max(min(amount, 99), 1)
        await interaction.client.promocodeCollections.insert_one({"Type":type_of_promo,"Value":amount if type_of_promo == "literal" else max(min(amount, 99), 1)})
        await interaction.response.send_message("Success", ephemeral=True)



    @app_commands.command(name='list_promocode')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check)
    async def list_promocode(self, interaction):
        await interaction.response.defer(ephemeral=True)
        promoData = interaction.client.promocodeCollections.find()
        res = "```"
        async for prom in promoData:
            tempres = f'{prom}: Type:{promoData["Type"]} | Value:{promoData["Value"]}'
            if len(res+tempres)>= 2048:
                await interaction.followup.send(res+'```', ephemeral=True)
                res = '```'
            res+=tempres
        await interaction.followup.send(res+'```', ephemeral=True)



    @app_commands.command(name='remove_promocode')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check)
    @app_commands.autocomplete(promocode=promocode_AutoComplete)
    async def remove_promocode(self, interaction: discord.Interaction, promocode: str):
        await interaction.client.promocodeCollections.delete_one({"_id": promocode})
        await interaction.response.send_message("Success", ephemeral=True)



async def setup(bot):
    await bot.add_cog(Promocode(bot))
