import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import time
import os
from collections import defaultdict

# =========================
# 🔐 TOKEN
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# 🤖 INTENTS (FIX TOTAL)
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
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
        return {
            "warns": {},
            "autoroles": {"user": None, "bot": None},
            "joins": {}
        }

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# =========================
# 📊 SYSTEMS
# =========================
xp = defaultdict(int)
level = defaultdict(int)
user_messages = defaultdict(list)
muted = {}

# =========================
# 🚀 READY
# =========================
@bot.event
async def on_ready():
    print(f"Bot activo como {bot.user}")

    try:
        await bot.tree.sync()
        print("Slash commands listos")
    except:
        pass

    try:
        unmute_loop.start()
    except:
        pass

# =========================
# 🧠 XP + ANTI SPAM
# =========================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    xp[uid] += 5

    if xp[uid] >= (level[uid] + 1) * 100:
        level[uid] += 1
        await message.channel.send(f"📈 {message.author.mention} subió a nivel {level[uid]} 🔥")

    await bot.process_commands(message)

# =========================
# 👋 WELCOME + AUTOROLE FIX
# =========================
@bot.event
async def on_member_join(member):

    # ===== AUTOROLE =====
    role_id = data["autoroles"]["bot"] if member.bot else data["autoroles"]["user"]

    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except:
                pass

    # ===== WELCOME (CANAL POR ID) =====
    channel = member.guild.get_channel(1500703841518223375)

    if channel:
        embed = discord.Embed(
            title="🔥 Bienvenido a Guate Xiter 🔥",
            description=f"""
Welcome {member.mention} to MIEMBROS GUATE XITER!

🔥 Somos familia 💯  
🚀 Aquí se sube todo  
🏆 Aquí se domina  
💀 Aquí no hay debilidad  

⚔️ Siempre activos  
🤝 Siempre en equipo  
""",
            color=0xff0000
        )

        embed.set_image(url="https://images-ext-1.discordapp.net/external/ch2lkaZJmmSwYBMyGG-Iqo2tZSdovpxc5kxVD6nheAo/https/i.postimg.cc/nV2JGZmr/file-00000000c9ec71f59259d589e645e4e1.png")

        await channel.send(content=member.mention, embed=embed)

# =========================
# 📊 INFO
# =========================
@bot.command()
async def info(ctx):
    g = ctx.guild

    online = sum(1 for m in g.members if m.status != discord.Status.offline)
    bots = sum(1 for m in g.members if m.bot)

    await ctx.send(f"""
📊 INFO SERVER

👥 Miembros: {g.member_count}
🟢 Online: {online}
🤖 Bots: {bots}
💬 Canales: {len(g.channels)}
👑 Roles: {len(g.roles)}
""")

@bot.command()
async def online(ctx):
    online = sum(1 for m in ctx.guild.members if m.status != discord.Status.offline)
    await ctx.send(f"🟢 Online: {online}")

# =========================
# ⚠️ WARN SYSTEM
# =========================
@bot.command()
async def warn(ctx, member: discord.Member, *, reason="sin razón"):
    uid = str(member.id)

    data["warns"].setdefault(uid, [])
    data["warns"][uid].append(reason)

    save(data)

    await ctx.send(f"⚠️ warn a {member.mention}")

@bot.command()
async def warns(ctx, member: discord.Member):
    uid = str(member.id)

    warns_list = data["warns"].get(uid, [])

    if not warns_list:
        return await ctx.send("✅ Sin warns")

    text = "\n".join([f"{i+1}. {w}" for i, w in enumerate(warns_list)])

    await ctx.send(f"⚠️ Warns de {member.mention}\n{text}")

# =========================
# 🎭 AUTOROLE SET
# =========================
@bot.command()
async def setautorole(ctx, tipo, role: discord.Role):

    tipo = tipo.lower()

    if tipo not in ["user", "bot"]:
        return await ctx.send("❌ usa user o bot")

    data["autoroles"][tipo] = role.id
    save(data)

    await ctx.send("✅ Autorole guardado")

# =========================
# 🧹 CLEAR
# =========================
@bot.command()
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 {amount} eliminados", delete_after=3)

# =========================
# 🔒 LOCKDOWN
# =========================
@bot.command()
async def lockdown(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 lock")

@bot.command()
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 unlock")

# =========================
# 🖼️ AVATAR
# =========================
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(member.display_avatar.url)

# =========================
# 📈 RANK
# =========================
@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)

    await ctx.send(f"""
📈 Rank de {member}

XP: {xp[uid]}
Nivel: {level[uid]}
""")

# =========================
# 👑 VERIFY (BUTTON)
# =========================
class Verify(discord.ui.View):

    @discord.ui.button(label="Verificar", style=discord.ButtonStyle.green)
    async def verify(self, interaction, button):

        role = discord.utils.get(interaction.guild.roles, name="Verificado")

        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("✔ verificado", ephemeral=True)

@bot.command()
async def verify(ctx):
    await ctx.send("👑 Verifícate", view=Verify())

# =========================
# 📌 PANEL
# =========================
class Panel(discord.ui.View):

    @discord.ui.button(label="Info", style=discord.ButtonStyle.blurple)
    async def info(self, interaction, button):

        g = interaction.guild
        online = sum(1 for m in g.members if m.status != discord.Status.offline)

        await interaction.response.send_message(f"""
📊 PANEL

👥 {g.member_count}
🟢 {online}
👑 {len(g.roles)}
💬 {len(g.channels)}
""", ephemeral=True)

@bot.command()
async def panel(ctx):
    await ctx.send("📌 Panel", view=Panel())

# =========================
# 🔓 LOOP
# =========================
@tasks.loop(seconds=30)
async def unmute_loop():
    pass

# =========================
# 🚀 RUN
# =========================
bot.run(TOKEN)