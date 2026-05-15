from dotenv import load_dotenv
import asyncio
import discord
import json
import time
import os

load_dotenv()

# change zeez
TRACKED_USER_ID = 518021652471349250
LOG_CHANNEL_ID = 1501730488631693415
ROLE_PING_ID = 1501730555782496369
TOKEN = os.getenv("TOKEN")

ONLINE_MSG = f"""
# :white_check_mark: ¡Los Servidores han vuelto!
:flag_us: The Servers are back!
:flag_br: Os Servidores voltaram!
-# <@&{ROLE_PING_ID}> - $time$
"""

OFFLINE_MSG = f"""
# <:EK_bad_servers:1502482565968302080> ¡Los Servidores están offline!
:flag_us: The Servers are offline!
:flag_br: Os Servidores estão offline!
<<<<<<< HEAD
-# <@&{ROLE_PING_ID}> - $time$
=======
-#  <@&{ROLE_PING_ID}> - $time$
>>>>>>> 29c56e8e2cf9854d1353cae103445f7b0625c3d4
"""

# actual code
async def offline_to_online():
    global online
    global last_msg_id
    online = True
    await client.change_presence(
        status=discord.Status.online
    )
    try:
        await client.get_channel(LOG_CHANNEL_ID).get_partial_message(last_msg_id).delete()
        await asyncio.sleep(1)
    except:
        pass
    new_msg = await client.log_channel.send(ONLINE_MSG.replace("$time$", f"<t:{int(time.time())}:R>"))
    last_msg_id = new_msg.id
    db.update({
        "last_msg_id": last_msg_id,
        "online":online
    })
    json.dump(db, open("./db.json", "w"), indent=4)

async def online_to_offline():
    global online
    global last_msg_id
    online = False
    await client.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game("Servers are down, welp")
    )
    try:
        await client.get_channel(LOG_CHANNEL_ID).get_partial_message(last_msg_id).delete()
        await asyncio.sleep(1)
    except:
        pass
    new_msg = await client.log_channel.send(OFFLINE_MSG.replace("$time$", f"<t:{int(time.time())}:R>"))
    last_msg_id = new_msg.id
    db.update({
        "last_msg_id": last_msg_id,
        "online":online
    })
    json.dump(db, open("./db.json", "w"), indent=4)

class Client(discord.Client):
    async def on_ready(self):
        global online
        print(f"{self.user.name} online")
        self.log_channel:discord.TextChannel = self.get_channel(LOG_CHANNEL_ID)
        member = self.log_channel.guild.get_member(TRACKED_USER_ID)
        if member.status.name != "offline" and not online:
            await offline_to_online()
        elif member.status.name == "offline" and online:
            await online_to_offline()

    async def on_presence_update(self, before:discord.Member, after:discord.Member):
        global online
        
        if self.log_channel and before.id == TRACKED_USER_ID:
            if before.status.name != "offline" and after.status.name == "offline" and online:
                await online_to_offline()
                
            elif before.status.name == "offline" and after.status.name != "offline" and not online:
                await offline_to_online()


intents = discord.Intents.default()
intents.presences = True
intents.members = True

client = Client(intents=intents)
client.log_channel = None

db:dict = json.load(open("./db.json", "r"))
last_msg_id = db["last_msg_id"]
online = db["online"]

client.run(TOKEN)
