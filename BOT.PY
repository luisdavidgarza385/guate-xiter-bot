import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from collections import defaultdict
from datetime import timedelta

# =========================
# 🔐 TOKEN (FIX REAL)
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

# 🔥 FIX: evita crash si no hay token
if not TOKEN:
    raise ValueError("❌ No se encontró DISCORD_TOKEN en variables de entorno")

# =========================
# 🤖 INTENTS
# =========================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.presences = True

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
            "autoroles": {"user": None, "bot": None}
        }

def save():
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load()

# =========================
# 📊 SYSTEMS
# =========================
xp = defaultdict(int)
level = defaultdict(int)

# =========================
# 🚀 READY
# =========================
@bot.event
async def on_ready():
    print(f"Bot activo como {bot.user}")

    try:
        await bot.tree.sync()
        print("Slash commands listos")
    except Exception as e:
        print("Slash error:", e)

# =========================
# 👋 WELCOME (NO TOCADO)
# =========================
@bot.event
async def on_member_join(member):

    role_id = data["autoroles"].get("bot") if member.bot else data["autoroles"].get("user")

    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role, reason="Autorole system")
            except Exception as e:
                print("Autorole error:", e)

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
# 📊 INFO (FIX ONLINE REAL)
# =========================
@bot.command()
async def info(ctx):
    g = ctx.guild

    online = sum(
        1 for m in g.members
        if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
    )

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
    online = sum(
        1 for m in ctx.guild.members
        if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
    )
    await ctx.send(f"🟢 Online: {online}")

# =========================
# ⚠️ WARN SYSTEM
# =========================
@bot.command()
async def warn(ctx, member: discord.Member, *, reason="sin razón"):
    uid = str(member.id)

    data["warns"].setdefault(uid, [])
    data["warns"][uid].append(reason)

    save()

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
# 🎭 AUTOROLE
# =========================
@bot.command()
async def setautorole(ctx, tipo, role: discord.Role):

    tipo = tipo.lower()

    if tipo not in ["user", "bot"]:
        return await ctx.send("❌ usa user o bot")

    data["autoroles"][tipo] = role.id
    save()

    await ctx.send("✅ Autorole guardado")

# =========================
# 🧹 CLEAR
# =========================
@bot.command()
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"🧹 {amount} eliminados", delete_after=3)

# =========================
# 🔒 LOCK / UNLOCK
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
# 👑 VERIFY
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
        online = sum(
            1 for m in g.members
            if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
        )

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
# 💀 SLASH COMMANDS
# =========================
@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "sin razón"):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Baneado {member}")

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):
    await member.kick()
    await interaction.response.send_message(f"👢 Kick {member}")

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):

    await member.timeout(
        discord.utils.utcnow() + timedelta(minutes=minutes)
    )

    await interaction.response.send_message(f"⏱️ Muted {member}")

@bot.tree.command(name="info")
async def info_slash(interaction: discord.Interaction):
    g = interaction.guild

    online = sum(
        1 for m in g.members
        if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
    )

    await interaction.response.send_message(
        f"👥 {g.member_count}\n🟢 {online}\n👑 {len(g.roles)}"
    )

# =========================
# 🚀 RUN
# =========================
bot.run(TOKEN)