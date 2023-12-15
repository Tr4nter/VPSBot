from Cogs.Tickets.createView import createTicket
from bot import clearData, processing

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
ticketDataPath = 'ticketdata.json'


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot


    @app_commands.command(name='set_ticket_category')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check)
    async def set_ticket_category(self, interaction: Interaction, category: discord.CategoryChannel):
        ticketData = get_json(ticketDataPath)

        ticketData["ticketCategory"] = category.id
        save_json(ticketData, ticketDataPath)
        await interaction.response.send_message(f"Successfully set {category.mention} to be a ticket category", ephemeral=True)


    @commands.check(ctxcheck)
    @commands.command()
    async def set_forward_channel(self, ctx, channel: discord.TextChannel):
        ticketData = get_json(ticketDataPath)

        ticketData["forwardChannel"] = channel.id
        save_json(ticketData, ticketDataPath)
        # await interaction.response.send_message(f"Successfully set {category.mention} to be a ticket category", ephemeral=True)



    @app_commands.command(name='close_ticket')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check)
    async def close_ticket(self, interaction: Interaction, ticket_channel: TextChannel):
        ticketData = get_json(ticketDataPath)
        for user in ticketData["Tickets"]:
            if not "ticketChannel" in ticketData["Tickets"][user]: continue
            if ticketData["Tickets"][user]["ticketChannel"] == ticket_channel.id:
                try:
                    userObject = await interaction.guild.fetch_member(user)
                    channel = await self.bot.fetch_channel(ticket_channel.id)
                except discord.errors.NotFound: return
                try:
                    processing.append(user)
                    message = await channel.fetch_message(ticketData["Tickets"][user]["currentMessage"])
                    await message.edit(content=f"Order closed")
                    processing.remove(user)
                except Exception as e: print(e)
                clearData(user)
                return


    @app_commands.command(name='send_button')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check)
    async def send_button(self, interaction: Interaction):
        await interaction.response.defer()

        guild: Guild = interaction.guild

        ticketData = get_json(ticketDataPath)
        if ticketData["ticketCreateMessage"] != 0:
            channel: TextChannel = await guild.fetch_channel(ticketData["ticketCreateMessageChannel"])
            message = None 
            if channel:
                try:
                    message: Message = await channel.fetch_message(ticketData["ticketCreateMessage"])
                except:
                    pass
             
            if channel and message:
                await message.delete()

        interactionMessage = await interaction.channel.send(view=createTicket())

        ticketData["ticketCreateMessage"] = interactionMessage.id
        ticketData["ticketCreateMessageChannel"] = interaction.channel.id

        save_json(ticketData, ticketDataPath)


async def setup(bot):
    ticketData = get_json(ticketDataPath)
    if "ticketCreateMessage" not in ticketData:
        ticketData = {}
        ticketData["ticketCreateMessage"] = 0
        ticketData["ticketCreateMessageChannel"] = 0
        ticketData["ticketCategory"] = 0
        ticketData["forwardChannel"] = 0
        ticketData["Tickets"] = {}
        
        save_json(ticketData, ticketDataPath)
    await bot.add_cog(Ticket(bot))




