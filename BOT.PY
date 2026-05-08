import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from collections import defaultdict
import datetime
import asyncio

# =========================
# 🔐 TOKEN
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ No se encontró DISCORD_TOKEN")

# =========================
# 🤖 INTENTS
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# 💾 DATA
# =========================
FILE = "data.json"

def load():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {"warns": {}, "autoroles": {"user": None, "bot": None}}

def save():
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# =========================
# 📊 SYSTEMS
# =========================
xp = defaultdict(int)
level = defaultdict(int)
spam = defaultdict(list)
join_tracker = []

LOG_CHANNEL_ID = 1500703841518223375

# =========================
# 🚀 STATUS BOT
# =========================
async def status_loop():
    await bot.wait_until_ready()

    while not bot.is_closed():

        total = sum(g.member_count for g in bot.guilds)

        online = sum(
            1 for g in bot.guilds
            for m in g.members
            if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
        )

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{total} miembros | {online} online"
        )

        await bot.change_presence(status=discord.Status.online, activity=activity)

        await asyncio.sleep(60)

# =========================
# 🚀 READY
# =========================
@bot.event
async def on_ready():
    print(f"Bot activo como {bot.user}")
    await bot.tree.sync()
    bot.loop.create_task(status_loop())

# =========================
# 🛡️ ANTI RAID
# =========================
@bot.event
async def on_member_join(member):

    now = datetime.datetime.utcnow().timestamp()
    join_tracker.append(now)
    join_tracker[:] = [t for t in join_tracker if now - t < 10]

    if len(join_tracker) >= 5:
        for c in member.guild.text_channels:
            await c.set_permissions(member.guild.default_role, send_messages=False)

    # AUTOROLE
    tipo = "bot" if member.bot else "user"
    role_id = data["autoroles"].get(tipo)

    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            await member.add_roles(role)

    # LOG JOIN
    log = member.guild.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(f"📥 JOIN: {member}")

    # WELCOME
    channel = member.guild.get_channel(LOG_CHANNEL_ID)

    if channel:
        embed = discord.Embed(
            title="🔥 BIENVENIDO A GUATE XITER CHEATS 🔥",
            description="""
🔥 Bienvenido a Guate Xiter 🔥  
Aquí no somos solo un clan… somos familia 💯  
Nos apoyamos, subimos juntos y hacemos mrd 😈  

🚀 Subir TODO  
🏆 Llegar al TOP  
💀 Dominar  

⚔️ Siempre competitivos  
🤝 Siempre en equipo  

💀 GUATE XITER ES OTRO NIVEL 💀
""",
            color=0xff0000
        )

        embed.set_image(url="https://i.postimg.cc/nV2JGZmr/file-00000000c9ec71f59259d589e645e4e1.png")
        await channel.send(embed=embed)

# =========================
# 📊 XP + ANTI SPAM + ANTI LINK
# =========================
@bot.event
async def on_message(message):

    if message.author.bot:
        return

    uid = str(message.author.id)

    xp[uid] += 5
    if xp[uid] % 100 == 0:
        level[uid] += 1

    now = datetime.datetime.utcnow().timestamp()

    spam[uid].append(now)
    spam[uid] = [t for t in spam[uid] if now - t < 5]

    if len(spam[uid]) > 5:
        await message.delete()
        return

    if "http" in message.content or "discord.gg" in message.content:
        await message.delete()
        return

    await bot.process_commands(message)

# =========================
# 📢 LOGS COMPLETOS
# =========================
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    ch = message.guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"🧹 DELETE: {message.author} → {message.content}")

@bot.event
async def on_message_edit(before, after):
    ch = before.guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"✏ EDIT: {before.author}\n{before.content} ➜ {after.content}")

@bot.event
async def on_member_ban(guild, user):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"🔨 BAN: {user}")

@bot.event
async def on_member_remove(member):
    ch = member.guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"👢 LEAVE/KICK: {member}")

@bot.event
async def on_voice_state_update(member, before, after):
    ch = member.guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(f"🎤 VOICE: {member}")

# =========================
# 📊 INFO
# =========================
@bot.tree.command(name="info")
async def info(interaction: discord.Interaction):

    g = interaction.guild

    online = sum(
        1 for m in g.members
        if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
    )

    await interaction.response.send_message(
        f"👥 Miembros: {g.member_count}\n🟢 Online: {online}\n🤖 Bots: {sum(m.bot for m in g.members)}"
    )

# =========================
# 🟢 ONLINE
# =========================
@bot.tree.command(name="online")
async def online(interaction: discord.Interaction):

    online = sum(
        1 for m in interaction.guild.members
        if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
    )

    await interaction.response.send_message(f"🟢 Online: {online}")

# =========================
# ⚠️ WARN
# =========================
@bot.tree.command(name="warn")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):

    uid = str(member.id)
    data["warns"].setdefault(uid, [])
    data["warns"][uid].append(reason)
    save()

    await interaction.response.send_message(f"⚠️ Warn a {member}")

# =========================
# 👑 VERIFY
# =========================
class Verify(discord.ui.View):

    @discord.ui.button(label="Verificar", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button):

        role = discord.utils.get(interaction.guild.roles, name="Verificado")

        if not role:
            return await interaction.response.send_message("❌ No existe rol Verificado", ephemeral=True)

        await interaction.user.add_roles(role)
        await interaction.response.send_message("✔ Verificado", ephemeral=True)

@bot.tree.command(name="verify")
async def verify(interaction: discord.Interaction):
    await interaction.response.send_message("👑 Verifícate", view=Verify())

# =========================
# 🖼️ AVATAR
# =========================
@bot.tree.command(name="avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):

    member = member or interaction.user

    embed = discord.Embed(title="Avatar", color=0xff0000)
    embed.set_image(url=member.display_avatar.with_format("png").with_size(1024))

    await interaction.response.send_message(embed=embed)

# =========================
# 📈 RANK
# =========================
@bot.tree.command(name="rank")
async def rank(interaction: discord.Interaction, member: discord.Member = None):

    member = member or interaction.user
    uid = str(member.id)

    await interaction.response.send_message(f"📈 XP: {xp[uid]} | Nivel: {level[uid]}")

# =========================
# 🚀 RUN
# =========================
bot.run(TOKEN)