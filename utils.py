import discord
import os
from btcpay import BTCPayClient
from discord.ext.commands import Context

from dotenv import load_dotenv
load_dotenv()
admin = os.environ.get("ADMIN")

async def check(interaction: discord.Interaction):
    return interaction.user.id == 672514949184225310 or interaction.user.id == 861763675915288576
    

async def ctxcheck(interaction: Context):
    return interaction.author.id == 672514949184225310 or interaction.author.id == 861763675915288576


async def deliveryCheck(interaction):
    return interaction.user.id == os.environ.get("CONFIRMER") 
