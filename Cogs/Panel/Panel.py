from typing import List
import discord
from discord import app_commands
from discord.ext import commands

from jsonutils import save_json
from jsonutils import get_json
from utils import check

import datetime
panelDataPath = 'paneldata.json'
ticketDataPath = 'ticketdata.json'


async def panelCheck(interaction: discord.Interaction):
    panelData = get_json(panelDataPath)
    if not interaction.user.get_role(panelData["buyerRole"]): return False
    return True

    
async def panel_AutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:
    panelData = get_json(panelDataPath)
    if not str(interaction.user.id) in panelData["Users"]: return []
    users = panelData["Users"][str(interaction.user.id)]
    return [app_commands.Choice(name=f'ID:{k}|Product:{users[k]["Product"]}|Region:{users[k]["Region"]}', value=k) for k in panelData["Users"][str(interaction.user.id)]]

    


class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @app_commands.command(name='set_buyer_role')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check)
    async def set_buyer_role(self, interaction: discord.Interaction, role: discord.Role):

        paneldata = get_json(panelDataPath)
        paneldata["buyerRole"] = role.id
        save_json(paneldata, panelDataPath)
        await interaction.response.send_message('Success', ephemeral=True)


    @app_commands.command(name='view_machines')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(panelCheck)
    async def view_machines(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        panelData = get_json(panelDataPath)
        user_id = interaction.user.id
        cur = ""
        for machine_id in panelData["Users"][str(user_id)]:
            machineData = panelData["Users"][str(user_id)][machine_id]
            tick = datetime.datetime.now().timestamp()
            nextStr = f'**ID**: {machine_id}|**Product**: {machineData["Product"]}|**Region**: {machineData["Region"]}|'
            nextStr += f'**Warranty**: {"Active" if tick < machineData["Expiration"] else "Expired"}\n'
            if len(cur+nextStr) >= 2048:
                await interaction.followup.send(cur, ephemeral=True)
                cur = ""
            cur += nextStr

        await interaction.followup.send(cur, ephemeral=True)


    @app_commands.command(name='view_machine_info')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(panelCheck)
    @app_commands.autocomplete(machine_id=panel_AutoComplete)
    async def view_machine_info(self, interaction: discord.Interaction, machine_id: str):
        panelData = get_json(panelDataPath)
        user_id = interaction.user.id
        machineData = panelData["Users"][str(user_id)][machine_id]
        content = f'```IP:{machineData["IP"]}\nUser:{machineData["User"]}\nPass:{machineData["Pass"]}```'
        await interaction.response.send_message(content,ephemeral=True)


    @app_commands.command(name='remove_machine')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(panelCheck)
    @app_commands.autocomplete(machine_id=panel_AutoComplete)
    async def remove_machine(self, interaction: discord.Interaction, machine_id: str):
        panelData = get_json(panelDataPath)
        user_id = interaction.user.id
        machineData = panelData["Users"][str(user_id)][machine_id]
        if datetime.datetime.now() > machineData["Expiration"]:
            del panelData["Users"][str(user_id)][machine_id]
            save_json(panelData, panelDataPath)
            await interaction.response.send_message(f"Successfully deleted {machine_id}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Machine still has warranty, cant delete", ephemeral=True)



    @app_commands.command(name='request_reboot')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(panelCheck)
    @app_commands.autocomplete(machine_id=panel_AutoComplete)
    async def request_reboot(self, interaction: discord.Interaction, machine_id: str):
        panelData = get_json(panelDataPath)
        user_id = interaction.user.id
        machineData = panelData["Users"][str(user_id)][machine_id]
        ticketData = get_json(ticketDataPath)

        if str(user_id) not in panelData["RebootRequest"]:
            panelData["RebootRequest"][str(user_id)] = []

        forwardChannel = await self.bot.fetch_channel(ticketData["forwardChannel"])
        if datetime.datetime.now().timestamp() < machineData["Expiration"]:
            panelData["RebootRequest"][str(user_id)].append(machine_id)
            await interaction.response.send_message("Sent reboot request", ephemeral=True)

            machineData = panelData["Users"][str(user_id)][machine_id]
            await forwardChannel.send(f'Reboot request for {machine_id}\nIP:{machineData["IP"]}\nUsername:{machineData["User"]}\nPass:{machineData["Pass"]}')

        else:
            await interaction.response.send_message("Warranty expired", ephemeral=True)
        save_json(panelData, panelDataPath)




async def setup(bot):
    paneldata = get_json(panelDataPath)
    if not "buyerRole" in paneldata:
        paneldata["buyerRole"] = ""
        paneldata["Users"] = {}
        paneldata["RebootRequest"] = {}
    save_json(paneldata, panelDataPath)
    await bot.add_cog(Panel(bot))
