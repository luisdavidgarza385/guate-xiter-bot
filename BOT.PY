import discord
from discord.ext import commands, tasks
import json
import time
import os
from collections import defaultdict

# =========================
# 🔐 TOKEN SEGURO
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")

# =========================
# 🤖 BOT
# =========================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# 💾 DATABASE JSON
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
# 🧠 ANTI-SPAM + XP
# =========================
user_messages = defaultdict(list)
xp = defaultdict(int)
level = defaultdict(int)
muted = {}

# =========================
# 🚀 READY
# =========================
@bot.event
async def on_ready():
    print(f"Bot activo como {bot.user}")

    try:
        unmute_loop.start()
    except:
        pass

# =========================
# 🧠 ANTI-SPAM + XP
# =========================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)
    now = time.time()

    # ================= ANTI-SPAM =================
    user_messages[uid].append(now)
    user_messages[uid] = [t for t in user_messages[uid] if now - t < 5]

    if len(user_messages[uid]) > 5:
        muted[uid] = now

        role = discord.utils.get(message.guild.roles, name="Muted")

        if role:
            try:
                await message.author.add_roles(role)
            except:
                pass

        await message.channel.send(
            f"🧠 Anti-spam: {message.author.mention} muteado"
        )

    # ================= XP SYSTEM =================
    xp[uid] += 5

    if xp[uid] >= (level[uid] + 1) * 100:
        level[uid] += 1

        await message.channel.send(
            f"📈 {message.author.mention} subió a nivel {level[uid]} 🔥"
        )

    await bot.process_commands(message)

# =========================
# 🔓 UNMUTE LOOP
# =========================
@tasks.loop(seconds=30)
async def unmute_loop():
    now = time.time()

    for uid, t in list(muted.items()):
        if now - t > 300:
            muted.pop(uid, None)

# =========================
# 👋 WELCOME + AUTOROLE + ANTI RAID
# =========================
@bot.event
async def on_member_join(member):
    gid = str(member.guild.id)

    # ================= ANTI RAID =================
    now = time.time()

    data["joins"].setdefault(gid, [])
    data["joins"][gid].append(now)

    data["joins"][gid] = [
        t for t in data["joins"][gid]
        if now - t < 10
    ]

    if len(data["joins"][gid]) > 5:
        channel = discord.utils.get(
            member.guild.text_channels,
            name="logs"
        )

        if channel:
            await channel.send("🛡️ Anti-raid activado")

        return

    # ================= AUTOROLE =================
    role_id = (
        data["autoroles"]["bot"]
        if member.bot
        else data["autoroles"]["user"]
    )

    if role_id:
        role = member.guild.get_role(role_id)

        if role:
            try:
                await member.add_roles(role)
            except:
                pass

    # ================= WELCOME =================
    channel = discord.utils.get(
        member.guild.text_channels,
        name="welcome"
    )

    if channel:
        embed = discord.Embed(
            title="🔥 Bienvenido 🔥",
            description=f"{member.mention}",
            color=0xff0000
        )

        await channel.send(embed=embed)

# =========================
# 📊 LOGS
# =========================
async def log(guild, msg):
    channel = discord.utils.get(
        guild.text_channels,
        name="logs"
    )

    if channel:
        await channel.send(msg)

@bot.event
async def on_message_delete(message):
    if message.guild:
        await log(
            message.guild,
            f"🗑️ {message.author}: {message.content}"
        )

@bot.event
async def on_message_edit(before, after):
    if before.guild:
        await log(
            before.guild,
            f"✏️ {before.author}: {before.content} → {after.content}"
        )

@bot.event
async def on_member_remove(member):
    await log(member.guild, f"👋 salió {member}")

# =========================
# ⚠️ WARNS
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
        await ctx.send("✅ Sin warns")
        return

    texto = "\n".join(
        [f"{i+1}. {w}" for i, w in enumerate(warns_list)]
    )

    await ctx.send(f"⚠️ Warns de {member.mention}\n{texto}")

# =========================
# 🎭 AUTOROLE
# =========================
@bot.command()
async def setautorole(ctx, tipo, role: discord.Role):
    tipo = tipo.lower()

    if tipo not in ["user", "bot"]:
        await ctx.send("❌ usa user o bot")
        return

    data["autoroles"][tipo] = role.id

    save(data)

    await ctx.send("✅ guardado")

# =========================
# 🧹 CLEAR
# =========================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)

    await ctx.send(
        f"🧹 {amount} mensajes eliminados",
        delete_after=3
    )

# =========================
# 🗑️ DELETE CHANNEL
# =========================
@bot.command()
@commands.has_permissions(manage_channels=True)
async def delchannel(ctx):
    await ctx.channel.delete()

# =========================
# 🚨 LOCKDOWN
# =========================
@bot.command()
async def lockdown(ctx):
    overwrite = ctx.channel.overwrites_for(
        ctx.guild.default_role
    )

    overwrite.send_messages = False

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.send("🔒 lock")

@bot.command()
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(
        ctx.guild.default_role
    )

    overwrite.send_messages = True

    await ctx.channel.set_permissions(
        ctx.guild.default_role,
        overwrite=overwrite
    )

    await ctx.send("🔓 unlock")

# =========================
# 🖼️ AVATAR
# =========================
@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author

    await ctx.send(member.display_avatar.url)

# =========================
# 📊 INFO + ONLINE
# =========================
@bot.command()
async def info(ctx):
    g = ctx.guild

    online = sum(
        1 for m in g.members
        if m.status != discord.Status.offline
    )

    bots = sum(
        1 for m in g.members
        if m.bot
    )

    await ctx.send(
        f"""
📊 INFO SERVER

👥 Miembros: {g.member_count}
🟢 Online: {online}
🤖 Bots: {bots}
💬 Canales: {len(g.channels)}
👑 Roles: {len(g.roles)}
"""
    )

@bot.command()
async def online(ctx):
    online = sum(
        1 for m in ctx.guild.members
        if m.status != discord.Status.offline
    )

    await ctx.send(f"🟢 Online: {online}")

# =========================
# 📈 RANK
# =========================
@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author

    uid = str(member.id)

    await ctx.send(
        f"""
📈 Rank de {member}

XP: {xp[uid]}
Nivel: {level[uid]}
"""
    )

# =========================
# 👑 VERIFICACIÓN
# =========================
class Verify(discord.ui.View):

    @discord.ui.button(
        label="Verificar",
        style=discord.ButtonStyle.green
    )
    async def verify_button(self, interaction, button):

        role = discord.utils.get(
            interaction.guild.roles,
            name="Verificado"
        )

        if role:
            await interaction.user.add_roles(role)

            await interaction.response.send_message(
                "✔ verificado",
                ephemeral=True
            )

@bot.command()
async def verify(ctx):
    await ctx.send(
        "👑 Presiona para verificarte",
        view=Verify()
    )

# =========================
# 📌 PANEL
# =========================
class Panel(discord.ui.View):

    @discord.ui.button(
        label="Info",
        style=discord.ButtonStyle.blurple
    )
    async def info_button(self, interaction, button):

        g = interaction.guild

        online = sum(
            1 for m in g.members
            if m.status != discord.Status.offline
        )

        await interaction.response.send_message(
            f"""
📊 PANEL SERVER

👥 Miembros: {g.member_count}
🟢 Online: {online}
👑 Roles: {len(g.roles)}
💬 Canales: {len(g.channels)}
""",
            ephemeral=True
        )

@bot.command()
async def panel(ctx):
    await ctx.send(
        "📌 Panel del servidor",
        view=Panel()
    )

# =========================
# 🚀 START
# =========================
bot.run(TOKEN)