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
from utils import check, ctxcheck, productList
import os
ticketDataPath = 'ticketdata.json'



class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot


    @app_commands.command(name='set_ticket_category')
    @app_commands.guilds(discord.Object(id=int(os.environ.get("STORESERVERID"))))
    @app_commands.check(check)
    async def set_ticket_category(self, interaction: Interaction, category: discord.CategoryChannel):
        ticketData = get_json('settings.json')

        ticketData["ticketCategory"] = category.id
        save_json(ticketData, ticketDataPath)
        await interaction.response.send_message(f"Successfully set {category.mention} to be a ticket category", ephemeral=True)


    @commands.check(ctxcheck)
    @commands.command()
    async def set_forward_channel(self, ctx, channel: discord.TextChannel):
        ticketData = get_json('settings.json')

        ticketData["forwardChannel"] = channel.id
        save_json(ticketData, ticketDataPath)
        # await interaction.response.send_message(f"Successfully set {category.mention} to be a ticket category", ephemeral=True)



    @app_commands.command(name='close_ticket')
    @app_commands.guilds(discord.Object(id=int(os.environ.get("STORESERVERID"))))

    @app_commands.check(check)
    async def close_ticket(self, interaction: Interaction, ticket_channel: TextChannel):
        ticketData = interaction.client.ticketCollections.find() 
        async for userData in ticketData:
            if not "ticketChannel" in userData: continue
            if userData["ticketChannel"] == ticket_channel.id:
                try:
                    channel = await self.bot.fetch_channel(ticket_channel.id)
                except discord.errors.NotFound: return
                try:
                    processing.append(userData["_id"])
                    message = await channel.fetch_message(userData["currentMessage"])
                    await message.edit(content=f"Order closed")
                    processing.remove(userData["_id"])
                except Exception as e: print(e)
                await clearData(userData["_id"])
                return


    @app_commands.command(name='send_button')
    @app_commands.guilds(discord.Object(id=int(os.environ.get("STORESERVERID"))))

    @app_commands.check(check)
    async def send_button(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)


        guild: Guild = interaction.guild

        ticketData = get_json('settings.json')
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

        interactionMessage = await interaction.channel.send(view=createTicket(await productList(interaction.client)))
        ticketData["ticketCreateMessage"] = interactionMessage.id
        ticketData["ticketCreateMessageChannel"] = interaction.channel.id

        save_json(ticketData, ticketDataPath)

        await interaction.followup.send("DONE", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ticket(bot))




