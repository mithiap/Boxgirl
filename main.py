from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import discord
import json
import time
import os

load_dotenv()

variables:dict = json.load(open("./vars.json", "r"))
tracked_user_id = variables["tracked_user_id"]
log_channel_id = variables["log_channel_id"]
role_ping_id = variables["role_ping_id"]
TOKEN = os.getenv("TOKEN")

# ==================== change zeez ====================
ONLINE_MSG = f"""
# :white_check_mark: ¡Los Servidores han vuelto!
:flag_us: The Servers are back!
:flag_br: Os Servidores voltaram!
-# <@&{role_ping_id}> - $time$
"""

OFFLINE_MSG = f"""
# <:EK_bad_servers:1502482565968302080> ¡Los Servidores están offline!
:flag_us: The Servers are offline!
:flag_br: Os Servidores estão offline!
-#  <@&{role_ping_id}> - $time$
"""

# actual code

def update_db():
    global last_msg_id
    global online
    global track
    db.update({
        "last_msg_id": last_msg_id,
        "online":online,
        "track": track
    })
    json.dump(db, open("./db.json", "w"), indent=4)

def update_vars():
    global tracked_user_id
    global log_channel_id
    global role_ping_id

    variables:dict = json.load(open("./vars.json", "r"))
    tracked_user_id = variables["tracked_user_id"]
    log_channel_id = variables["log_channel_id"]
    role_ping_id = variables["role_ping_id"]

async def offline_to_online():
    global online
    global last_msg_id
    online = True
    await client.change_presence(
        status=discord.Status.online
    )
    try:
        await client.get_channel(log_channel_id).get_partial_message(last_msg_id).delete()
        await asyncio.sleep(1)
    except:
        pass
    new_msg = await client.log_channel.send(ONLINE_MSG.replace("$time$", f"<t:{int(time.time())}:R>"))
    last_msg_id = new_msg.id
    update_db()

async def online_to_offline():
    global online
    global last_msg_id
    online = False
    await client.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game("Servers are down, welp")
    )
    try:
        await client.get_channel(log_channel_id).get_partial_message(last_msg_id).delete()
        await asyncio.sleep(1)
    except:
        pass
    new_msg = await client.log_channel.send(OFFLINE_MSG.replace("$time$", f"<t:{int(time.time())}:R>"))
    last_msg_id = new_msg.id
    update_db()

class Client(commands.Bot):
    async def on_ready(self):
        global online
        print(f"{self.user.name} online")
        self.log_channel:discord.TextChannel = self.get_channel(log_channel_id)
        member = self.log_channel.guild.get_member(tracked_user_id)
        await self.tree.sync()
        if member.status.name != "offline" and not online:
            await offline_to_online()
        elif member.status.name == "offline" and online:
            await online_to_offline()

    async def on_presence_update(self, before:discord.Member, after:discord.Member):
        global online
        global track
        
        if track:
            if self.log_channel and before.id == tracked_user_id:
                if before.status.name != "offline" and after.status.name == "offline" and online:
                    await online_to_offline()

                elif before.status.name == "offline" and after.status.name != "offline" and not online:
                    await offline_to_online()
    
    async def on_message(self, msg):
        pass

intents = discord.Intents.default()
intents.presences = True
intents.members = True

client = Client("", intents=intents)
client.log_channel = None

@client.tree.command(name="toggle", description="Enable or disable tracking the EK-Bot's status")
async def toggle_track(interaction:discord.Interaction):
    global track
    if interaction.user.guild_permissions.administrator:
        if track:
            track = False
            await interaction.response.send_message(":warning: Tracking has been **disabled**.")
        else:
            track = True
            await interaction.response.send_message(":white_check_mark: Tracking has been **enabled**.")
        update_db()
    else:
        await interaction.response.send_message(f""":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.""", ephemeral=True)

@client.tree.command(name="update", description="Update the variables from vars.json without needing to restart the bot")
async def update_vars_cmd(interaction:discord.Interaction):
    update_vars()
    if interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(":white_check_mark: Variables updated!")
    else:
        await interaction.response.send_message(f""":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.""", ephemeral=True)

@client.tree.command(name="catch-up", description="Check EK-Bot's status and update the message accordingly")
async def catch_up_cmd(interaction:discord.Interaction):
    global online
    if interaction.user.guild_permissions.administrator:
        member = client.log_channel.guild.get_member(tracked_user_id)
        if member.status.name != "offline" and not online:
            await offline_to_online()
            await interaction.response.send_message(":white_check_mark: EK-Bot is now online, I've updated my message.")
        elif member.status.name == "offline" and online:
            await online_to_offline()
            await interaction.response.send_message(":white_check_mark: EK-Bot is now offline, I've updated my message.")
        else:
            await interaction.response.send_message(":warning: EK-Bot's status is the same as the last update, no changes were made.")
    else:
        await interaction.response.send_message(f""":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.""", ephemeral=True)

db:dict = json.load(open("./db.json", "r"))
last_msg_id = db["last_msg_id"]
online = db["online"]
track = db["track"]

client.run(TOKEN)
