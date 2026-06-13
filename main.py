from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import discord
import json
import time
import os
import io

load_dotenv()

variables:dict = json.load(open("./vars.json", "r"))

engine_kingdom_guild_id:int = variables["engine_kingdom_guild_id"]
tracked_user_id:int       = variables["tracked_user_id"]
log_channel_id:int        = variables["log_channel_id"]
role_ping_id:int          = variables["role_ping_id"]
banner_cmd_guild_id:int   = variables["banner_cmd_guild_id"]
banner_log_channel_id:int = variables["banner_log_channel_id"]
banner_admins:list        = variables["banner_admins"]
banner_allowed_roles:list = variables["banner_allowed_roles"]
banner_delay_hours:int    = variables["banner_delay_hours"]
honeypot_channel_id:int   = variables["honeypot_channel_id"]
honeypot_immune_roles:list = variables["honeypot_immune_roles"]

db:dict = json.load(open("./db.json", "r"))

last_msg_id:int         = db["last_msg_id"]
online:bool             = db["online"]
track:bool              = db["track"]
banner_change_date:int  = db["banner_change_date"]
banner_changer_id:int   = db["banner_changer_id"]
banner_changer_name:str = db["banner_changer_name"]
banner_banned:list      = db["banner_banned"]

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
-# <@&{role_ping_id}> - $time$
"""

HONEYPOT_MSG = """
Hola $username$, tu cuenta ha sido expulsada temporalmente de **$guild_name$** debido a que ha sido comprometida (enviando imágenes, enlaces o mensajes sospechosos). Asegura tu cuenta antes de volver por favor.

https://discord.gg/enginekingdom
"""
# actual code

def update_db():
    global last_msg_id
    global online
    global track
    global banner_change_date
    global banner_changer_id
    global banner_changer_name
    global banner_banned

    db.update({
        "last_msg_id": last_msg_id,
        "online":online,
        "track": track,
        "banner_change_date": banner_change_date,
        "banner_changer_id": banner_changer_id,
        "banner_changer_name": banner_changer_name,
        "banner_banned": banner_banned
    })
    json.dump(db, open("./db.json", "w"), indent=4)

def update_vars():
    global engine_kingdom_guild_id
    global tracked_user_id
    global log_channel_id
    global role_ping_id
    global banner_cmd_guild_id
    global banner_log_channel_id
    global banner_admins
    global banner_allowed_roles
    global banner_delay_hours

    variables = json.load(open("./vars.json", "r"))
    engine_kingdom_guild_id = variables["engine_kingdom_guild_id"]
    tracked_user_id       = variables["tracked_user_id"]
    log_channel_id        = variables["log_channel_id"]
    role_ping_id          = variables["role_ping_id"]
    banner_cmd_guild_id   = variables["banner_cmd_guild_id"]
    banner_log_channel_id = variables["banner_log_channel_id"]
    banner_admins         = variables["banner_admins"]
    banner_allowed_roles  = variables["banner_allowed_roles"]
    banner_delay_hours    = variables["banner_delay_hours"]
    honeypot_channel_id   = variables["honeypot_channel_id"]
    honeypot_immune_roles = variables["honeypot_immune_roles"]

    if client and client.log_channel and client.log_channel.id != log_channel_id:
        client.log_channel = client.get_channel(log_channel_id)

async def offline_to_online():
    global online
    global last_msg_id
    online = True
    await client.change_presence(
        status=discord.Status.online,
        activity=(discord.CustomActivity(f"Banner by {banner_changer_name}") if banner_changer_name else None)
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
    global honeypot_channel_id
    global honeypot_immune_roles
    online = False
    await client.change_presence(
        status=discord.Status.dnd,
        activity=discord.CustomActivity("Servers are down, download levels instead")
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
        await self.tree.sync()
        await self.tree.sync(guild=discord.Object(id=banner_cmd_guild_id))
        if online:
            await client.change_presence(
                status=discord.Status.online,
                activity=(discord.CustomActivity(f"Banner by {banner_changer_name}") if banner_changer_name else None)
            )

    async def on_presence_update(self, before:discord.Member, after:discord.Member):
        global online
        global track
        if track:
            if self.log_channel and before.id == tracked_user_id:
                if before.status.name != "offline" and after.status.name == "offline" and online:
                    await online_to_offline()

                elif before.status.name == "offline" and after.status.name != "offline" and not online:
                    await offline_to_online()
    
    async def on_message(self, msg:discord.Message):
        if msg.author.bot or any(role.id in honeypot_immune_roles for role in msg.author.roles):
            return

        if msg.channel.id != honeypot_channel_id:
            return
        
        try:
            await msg.author.send(
                HONEYPOT_MSG.replace("$username$", msg.author.name).replace("$guild_name$", msg.guild.name)
            )
        except:
            pass

        try:
            await msg.delete()
        except:
            pass

        await msg.author.ban(
            reason="Cuenta hackeada (cayó en el bait de #the-thing) ban temporal.",
            delete_message_days=1
        )

        embed = discord.Embed(
            title="<:boxg:1502150406523064401> Logs ︱ Honeypot Triggered",
            description=f"{msg.author.name} (<@{msg.author.id}>) was banned! - <t:{int(time.time())}:f>\n\n`ID: {msg.author.id}`",
            color=0x00FF00
        )

        channel = self.get_channel(banner_log_channel_id)

        await channel.send(embed=embed)

        await asyncio.sleep(10)

        try:
            await msg.author.unban(reason="Baneo temporal del bait de #the-thing finalizado.")
        except:
            embed = discord.Embed(
                title="<:boxg:1502150406523064401> Logs ︱ Failed to unban user",
                description=f"Failed to automatically unban {msg.author.name} (<@{msg.author.id}>)! - <t:{int(time.time())}:f>\n\n`ID: {msg.author.id}`",
                color=0xFF0000
            )
        else:
            embed = discord.Embed(
                title="<:boxg:1502150406523064401> Logs ︱ User unbanned",
                description=f"Automatically unbanned {msg.author.name} (<@{msg.author.id}>) after 10 seconds! - <t:{int(time.time())}:f>\n\n`ID: {msg.author.id}`",
                color=0x00FF00
            )
        await channel.send(embed=embed)


intents = discord.Intents.default()
intents.presences = True
intents.members = True

client = Client("", intents=intents)
client.log_channel = None

# ======================= commands =======================

@client.tree.command(name="toggle", description="🔶 Enable or disable tracking EK-Bot")
@discord.app_commands.allowed_contexts(guilds = True)
async def toggle_track(interaction:discord.Interaction, enable:bool):
    global track
    if interaction.user.guild_permissions.administrator:
        if enable == False:
            track = False
            await client.change_presence(
                status=discord.Status.idle,
                activity=discord.CustomActivity("Tracking is currently off")
            )
            await interaction.response.send_message(":warning: Tracking has been **disabled**.")
        else:
            track = True
            await client.change_presence(
                status=discord.Status.online,
                activity=(discord.CustomActivity(f"Banner by {banner_changer_name}") if banner_changer_name else None)
            )
            await interaction.response.send_message(":white_check_mark: Tracking has been **enabled**.")
        update_db()
    else:
        await interaction.response.send_message(f":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.", ephemeral=True)

@client.tree.command(name="catch-up", description="🔶 Check EK-Bot's status and update the message accordingly")
@discord.app_commands.allowed_contexts(guilds = True)
async def catch_up_cmd(interaction:discord.Interaction):
    global online
    if interaction.user.guild_permissions.administrator:
        member = client.log_channel.guild.get_member(tracked_user_id)
        if member.status.name != "offline" and not online:
            await offline_to_online()
            await interaction.response.send_message(":white_check_mark: EK-Bot is now **online**, I've updated my message.")
        elif member.status.name == "offline" and online:
            await online_to_offline()
            await interaction.response.send_message(":white_check_mark: EK-Bot is now **offline**, I've updated my message.")
        else:
            await interaction.response.send_message(":warning: EK-Bot's status is the same as the last update, no changes were made.")
    else:
        await interaction.response.send_message(f":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.", ephemeral=True)

@client.tree.command(name="banner", description="Set the banner for the bot")
@discord.app_commands.describe(banner="Set the banner for the bot - Please choose a SMM:WE related image (max 10 MB)")
@discord.app_commands.allowed_contexts(guilds = True, dms = True)
async def set_banner_cmd(interaction:discord.Interaction, banner:discord.Attachment):
    global banner_change_date
    global banner_changer_id
    global banner_changer_name
    global banner_banned
    global banner_log_channel_id
    global online

    if interaction.guild:
        member = interaction.guild.get_member(interaction.user.id)
    else:
        guild = client.get_guild(engine_kingdom_guild_id)
        member = guild.get_member(interaction.user.id)

    if member.id in banner_admins or any(role.id in banner_allowed_roles for role in member.roles):
        
        if not member:
            await interaction.response.send_message(":x: Couldn't find you in Engine Kingdom.", ephemeral=True)
            return

        if member.id in banner_banned:
            await interaction.response.send_message(":x: You are banned from changing the banner.", ephemeral=True)
            return

        if member.id == banner_changer_id:
            await interaction.response.send_message(":x: You can't change the banner twice in a row.", ephemeral=True)
            return
    
        if not member.id in banner_admins:
            cooldown = int(time.time()) - banner_change_date
            if cooldown < 60 * 60 * banner_delay_hours: # 1 hour cooldown for non-admins
                await interaction.response.send_message(f":x: The banner can only be changed once every hour. You'll be able to change it <t:{int(time.time()) + (60 * 60 * banner_delay_hours)}:R>.", ephemeral=True)
                return

        if not banner.content_type or not banner.content_type.startswith("image/"):
            await interaction.response.send_message(":x: Please upload a valid image file.", ephemeral=True)
            return
    
        if banner.size > 10 * 1024 * 1024:
            await interaction.response.send_message(":x: The image file size must be less than 10 MB.", ephemeral=True)
            return

        try:
            await interaction.response.defer()
            img_bytes = await banner.read()
            await client.user.edit(banner=img_bytes)

            if online:
                await client.change_presence(
                    status=discord.Status.online,
                    activity=(discord.CustomActivity(f"Banner by {member.name}") if member.name else None)
                )

            banner_log_channel = client.get_channel(banner_log_channel_id)
    
            image_stream = io.BytesIO(img_bytes)

            filename = banner.filename.replace(" ", "").replace("_", "")
            file = discord.File(fp=image_stream, filename=filename)

            embed = discord.Embed(title="<:boxg:1502150406523064401> Logs ︱ Banner Updated", description=f"{member.name} (<@{member.id}>) changed my banner! - <t:{int(time.time())}:f>\n\n`ID: {member.id}`", color=0x5B0BAA)
            
            embed.set_image(url="attachment://"+filename)

            await banner_log_channel.send(embed=embed, file=file)

            if not member.id in banner_admins:
                banner_change_date = int(time.time())
                banner_changer_id = member.id
            banner_changer_name = member.name
            update_db()
            await interaction.followup.send(":white_check_mark: Banner updated successfully! Check it out!")
        except Exception as e:
                await interaction.followup.send(f":x: Failed to update banner: `{e}`", ephemeral=True)
    else:
        await interaction.response.send_message(f":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.", ephemeral=True)


# ======================= these are for our server only so no need to make too fancy =======================

@client.tree.command(name="update", description="📦 Update the variables from vars.json without needing to restart the bot", guild=discord.Object(id=banner_cmd_guild_id))
@discord.app_commands.allowed_contexts(guilds = True)
async def update_vars_cmd(interaction:discord.Interaction):
    update_vars()
    if interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(":white_check_mark: Variables updated!")
    else:
        await interaction.response.send_message(f":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.", ephemeral=True)

@client.tree.command(name="banner-ban", description="📦 Ban a user from changing the banner", guild=discord.Object(id=banner_cmd_guild_id))
@discord.app_commands.allowed_contexts(guilds = True)
async def banner_ban_cmd(interaction:discord.Interaction, user_id:str):
    global banner_banned
    if interaction.user.id in banner_admins:
        user = client.get_user(int(user_id))
        if not user:
            await interaction.response.send_message(f":x: User not found.")
            return
        if user.id not in banner_banned:
            banner_banned.append(user.id)
            update_db()
            await interaction.response.send_message(f":white_check_mark: {user.name} has been banned from changing the banner.")
        else:
            await interaction.response.send_message(f":warning: {user.name} is already banned from changing the banner.")
    else:
        await interaction.response.send_message(f":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.", ephemeral=True)

@client.tree.command(name="banner-unban", description="📦 Unban a user from changing the banner", guild=discord.Object(id=banner_cmd_guild_id))
@discord.app_commands.allowed_contexts(guilds = True)
async def banner_unban_cmd(interaction:discord.Interaction, user_id:str):
    global banner_banned
    if interaction.user.id in banner_admins:
        user = client.get_user(int(user_id))
        if not user:
            await interaction.response.send_message(f":x: User not found.")
            return
        if user.id in banner_banned:
            banner_banned.remove(user.id)
            update_db()
            await interaction.response.send_message(f":white_check_mark: {user.name} has been unbanned from changing the banner.")
        else:
            await interaction.response.send_message(f":warning: {user.name} is not banned from changing the banner.")
    else:
        await interaction.response.send_message(f":no_entry: You don't have permission to use this command\n-# Are you trying to make an account? use **</setup:1199514841363255340>**.", ephemeral=True)

client.run(TOKEN)
