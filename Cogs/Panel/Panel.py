from typing import List
import time
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
    panelData = get_json('settings.json')
    if not interaction.user.get_role(panelData["buyerRole"]): return False
    return True

    
async def panel_AutoComplete(interaction, current: str) -> List[app_commands.Choice[str]]:

    panelData = interaction.client.panelCollections.find({"Owner":str(interaction.user.id)})
    if not panelData: return 
    return [app_commands.Choice(name=f'ID:{k["_id"]}|Product:{k["Product"]}|Region:{k["Region"]}', value=str(k["_id"])) async for k in panelData]

    


class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @app_commands.command(name='set_buyer_role')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(check)
    async def set_buyer_role(self, interaction: discord.Interaction, role: discord.Role):

        paneldata = get_json('settings.json')
        paneldata["buyerRole"] = role.id
        save_json(paneldata, 'settings.json')
        await interaction.response.send_message('Success', ephemeral=True)


    @app_commands.command(name='view_machines')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(panelCheck)
    async def view_machines(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        panelData = interaction.client.panelCollections.find({"Owner": str(user_id)}) 
        cur = ""
        async for machineData in panelData:
            machine_id = machineData["_id"]
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
        machineData = await interaction.client.panelCollections.find_one({"_id": machine_id})
        content = f'```IP:{machineData["IP"]}\nUser:{machineData["User"]}\nPass:{machineData["Pass"]}```'
        await interaction.response.send_message(content,ephemeral=True)


    @app_commands.command(name='remove_machine')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(panelCheck)
    @app_commands.autocomplete(machine_id=panel_AutoComplete)
    async def remove_machine(self, interaction: discord.Interaction, machine_id: str):
        machineData = await interaction.client.panelCollections.find_one({"_id": machine_id})
        if datetime.datetime.now().timestamp() > machineData["Expiration"]:
            await interaction.client.panelCollections.delete_one({"_id": machine_id})
            await interaction.response.send_message(f"Successfully deleted {machine_id}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Machine still has warranty, cant delete", ephemeral=True)



    @app_commands.command(name='request_reboot')
    @app_commands.guilds(discord.Object(id=1163825960399949884))
    @app_commands.check(panelCheck)
    @app_commands.autocomplete(machine_id=panel_AutoComplete)
    async def request_reboot(self, interaction: discord.Interaction, machine_id: str):
        user_id = interaction.user.id
        settings = get_json("settings.json")

        rebootRequests = await interaction.client.rebootRequests.find_one({"_id": user_id})
        if not rebootRequests:
            await interaction.client.rebootRequests.insert_one({"_id": user_id, "machines": []})
        rebootRequests = await interaction.client.rebootRequests.find_one({"_id": user_id})

        machineData = await interaction.client.panelCollections.find_one({"_id": machine_id})
        if not machineData:
            await interaction.response.send_message("Could not find machine", ephemeral=True); return
        forwardChannel = await self.bot.fetch_channel(settings["forwardChannel"])
        if datetime.datetime.now().timestamp() < machineData["Expiration"]:
            await interaction.client.rebootRequests.update_one({"_id":user_id}, {"$push": {"machines": machine_id}})
            await interaction.response.send_message("Sent reboot request", ephemeral=True)

            await forwardChannel.send(f'Reboot request for {machine_id}\nIP:{machineData["IP"]}\nUsername:{machineData["User"]}\nPass:{machineData["Pass"]}')

        else:
            await interaction.response.send_message("Warranty expired", ephemeral=True)




async def setup(bot):
    
    await bot.add_cog(Panel(bot))
