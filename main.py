from dotenv import load_dotenv
import discord
import json
import os

load_dotenv()

# change zeez
TOKEN = os.getenv("TOKEN")
TRACKED_USER_ID = 518021652471349250 # Mithia
LOG_CHANNEL_ID = 1501730488631693415 # #status on ONT
ROLE_PING_ID = 1501730555782496369 # @status on ONT

OFFLINE_MSG = f"""
# :warning: ¡Los servidores están offline!
:flag_us: The Servers went offline!
:flag_br: Os Servidores ficaram offline!
-# <@&{ROLE_PING_ID}>
"""

ONLINE_MSG = f"""
# :white_check_mark: ¡Los servidores han vuelto!
:flag_us: The Servers are back!
:flag_br: Os Servidores voltaram!
-# <@&{ROLE_PING_ID}>
"""

# actual code
async def offline_to_online():
    global online
    global last_msg_id
    online = True
    await client.change_presence(
        status=discord.Status.online
    )
    new_msg = await client.log_channel.send(ONLINE_MSG)
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
    new_msg = await client.log_channel.send(OFFLINE_MSG)
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