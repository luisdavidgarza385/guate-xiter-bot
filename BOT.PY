import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from collections import defaultdict
from datetime import timedelta
import datetime

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
        print("Error slash:", e)

# =========================
# 👋 WELCOME + AUTOROLE
# =========================
@bot.event
async def on_member_join(member):

    tipo = "bot" if member.bot else "user"
    role_id = data["autoroles"].get(tipo)

    if role_id:
        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                print("Autorole error:", e)

    channel = member.guild.get_channel(1500703841518223375)

    if channel:
        embed = discord.Embed(
            title="🔥 BIENVENIDO A GUATE XITER 🔥",
            description=f"""
Welcome {member.mention} to **MIEMBROS GUATE XITER!**

🔥 Bienvenido a Guate Xiter 🔥  
Aquí no somos solo un clan… somos familia 💯  
Nos apoyamos, subimos juntos y hacemos mrd a todo 😈  

🚀 Subir TODO  
🏆 Llegar al TOP  
💀 Dominar  

🔥 Siempre activos  
⚔️ Siempre competitivos  
🤝 Siempre en equipo  

💀 Guate Xiter no es un clan… es otro nivel.
""",
            color=0xff0000
        )

        embed.set_image(
            url="https://i.postimg.cc/nV2JGZmr/file-00000000c9ec71f59259d589e645e4e1.png"
        )

        await channel.send(embed=embed)

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
        f"""📊 INFO
👥 Miembros: {g.member_count}
🟢 Online: {online}
🤖 Bots: {sum(m.bot for m in g.members)}
💬 Canales: {len(g.channels)}
👑 Roles: {len(g.roles)}"""
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
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "sin razón"):

    uid = str(member.id)

    data["warns"].setdefault(uid, [])
    data["warns"][uid].append(reason)
    save()

    await interaction.response.send_message(f"⚠️ Warn a {member}")

# =========================
# ⚠️ WARNS
# =========================
@bot.tree.command(name="warns")
async def warns(interaction: discord.Interaction, member: discord.Member):

    uid = str(member.id)
    warns_list = data["warns"].get(uid, [])

    if not warns_list:
        return await interaction.response.send_message("✅ Sin warns")

    text = "\n".join([f"{i+1}. {w}" for i, w in enumerate(warns_list)])

    await interaction.response.send_message(f"⚠️ Warns:\n{text}")

# =========================
# 🎭 AUTOROLE
# =========================
class RoleSelect(discord.ui.Select):
    def __init__(self, roles, tipo):
        self.tipo = tipo

        options = [
            discord.SelectOption(label=r.name, value=str(r.id))
            for r in roles[:25]
        ]

        super().__init__(placeholder=f"Selecciona rol {tipo}", options=options)

    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        data["autoroles"][self.tipo] = role_id
        save()

        await interaction.response.send_message(
            f"✅ Autorole {self.tipo}: <@&{role_id}>",
            ephemeral=True
        )

class RoleView(discord.ui.View):
    def __init__(self, roles, tipo):
        super().__init__()
        self.add_item(RoleSelect(roles, tipo))

@bot.tree.command(name="setautorole")
async def setautorole(interaction: discord.Interaction, tipo: str):

    tipo = tipo.lower()

    if tipo not in ["user", "bot"]:
        return await interaction.response.send_message("❌ usa user o bot")

    view = RoleView(interaction.guild.roles, tipo)

    await interaction.response.send_message(
        f"🎭 Selecciona autorole {tipo}",
        view=view
    )

# =========================
# 🧹 CLEAR (FIX)
# =========================
@bot.tree.command(name="clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):

    await interaction.response.defer(ephemeral=True)

    await interaction.channel.purge(limit=amount)

    await interaction.followup.send(f"🧹 Eliminados {amount}")

# =========================
# 🔒 LOCK
# =========================
@bot.tree.command(name="lock")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False

    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    await interaction.response.send_message("🔒 lock")

# =========================
# 🔓 UNLOCK
# =========================
@bot.tree.command(name="unlock")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True

    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    await interaction.response.send_message("🔓 unlock")

# =========================
# 🖼️ AVATAR
# =========================
@bot.tree.command(name="avatar")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):

    member = member or interaction.user

    await interaction.response.send_message(member.display_avatar.url)

# =========================
# 📈 RANK
# =========================
@bot.tree.command(name="rank")
async def rank(interaction: discord.Interaction, member: discord.Member = None):

    member = member or interaction.user
    uid = str(member.id)

    await interaction.response.send_message(
        f"📈 XP: {xp[uid]} | Nivel: {level[uid]}"
    )

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

@bot.tree.command(name="verify")
async def verify(interaction: discord.Interaction):

    await interaction.response.send_message("👑 Verifícate", view=Verify())

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

        await interaction.response.send_message(
            f"👥 {g.member_count}\n🟢 {online}",
            ephemeral=True
        )

@bot.tree.command(name="panel")
async def panel(interaction: discord.Interaction):

    await interaction.response.send_message("📌 Panel", view=Panel())

# =========================
# 💀 MODERACIÓN
# =========================
@bot.tree.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "sin razón"):

    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 baneado {member}")

@bot.tree.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member):

    await member.kick()
    await interaction.response.send_message(f"👢 kick {member}")

@bot.tree.command(name="timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int):

    await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes))

    await interaction.response.send_message("⏱️ timeout aplicado")

# =========================
# 🚀 RUN
# =========================
bot.run(TOKEN)