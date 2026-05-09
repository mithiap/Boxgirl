import discord
import json

# change zeez
TOKEN = "oootoken"
TRACKED_USER_ID = 518021652471349250 # Mithia
LOG_CHANNEL_ID = 1501730488631693415 # #status on ONT
ROLE_PING_ID = 1501730555782496369 # @status on ONT

online = True

class Client(discord.Client):
    async def on_ready(self):
        print(f"{self.user.name} online")
        self.log_channel:discord.TextChannel = self.get_channel(LOG_CHANNEL_ID)
    
    async def on_presence_update(self, before:discord.Member, after:discord.Member):
        global online
        global last_msg_id
        if self.log_channel and before.id == TRACKED_USER_ID:
            if before.status.name != "offline" and after.status.name == "offline" and online:
                online = False
                
                await self.change_presence(
                    status=discord.Status.dnd,
                    activity=discord.Game("Servers are down, welp")
                )
                try:
                    await self.log_channel.get_partial_message(last_msg_id).delete()
                except:
                    pass

                new_msg = await self.log_channel.send(f"# :warning: ¡Los Servidores están offline!\n:flag_us: The Servers went offline!\n:flag_br: Os Servidores ficaram offline!\n-# <@&{ROLE_PING_ID}>")
                last_msg_id = new_msg.id
                db.update({
                    "last_msg_id": last_msg_id,
                    "online":online
                })
                json.dump(db, open("./db.json", "w"), indent=4)
            
            elif before.status.name == "offline" and after.status.name != "offline" and not online:
                online = True
                
                await self.change_presence(
                            status=discord.Status.online,
                )
                try:
                    await self.log_channel.get_partial_message(last_msg_id).delete()
                except:
                    pass

                new_msg = await self.log_channel.send(f"# :white_check_mark: ¡Los servidores han vuelto!\n:flag_us: The Servers are back!\n:flag_br: Os Servidores voltaram!\n-# <@&{ROLE_PING_ID}>")
                last_msg_id = new_msg.id
                db.update({
                    "last_msg_id": last_msg_id,
                    "online":online
                })
                json.dump(db, open("./db.json", "w"), indent=4)
            

intents = discord.Intents.default()
intents.presences = True
intents.members = True

client = Client(intents=intents)

db:dict = json.load(open("./db.json", "r"))
last_msg_id = db["last_msg_id"]

client.run(TOKEN)