import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import os
import datetime
import aiohttp
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()
import shutil
import ctypes.util
import subprocess
import imageio_ffmpeg
import pytz

# --- Web Server for Keep Alive (Railway Requirement) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def keep_alive_task():
    """Pings the web server every 5 minutes to prevent sleep."""
    url = f"http://0.0.0.0:{os.getenv('PORT', 8080)}"
    # In production, use the actual Railway URL if available
    railway_url = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    if railway_url:
        url = f"https://{railway_url}"
        
    print(f"⏰ Starting keep-alive pinger for: {url}")
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url) as resp:
                    pass # Just ping
            except:
                pass
            await asyncio.sleep(300) # Ping every 5 minutes

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌍 Web server started on port {port}")
    
    # Start the pinger
    asyncio.create_task(keep_alive_task())

# Configuration
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN is missing! Make sure to add it in Railway Variables.")
else:
    print("✅ Token found, starting bot...")

import ctypes.util

# Debug: Check Environment
print(f"Current Directory: {os.getcwd()}")
print(f"Files in dir: {os.listdir('.')}")

# --- Robust FFmpeg Finder ---
def find_ffmpeg():
    # 1. Try shutil.which (PATH) - Prioritize system FFmpeg (Docker)
    path = shutil.which("ffmpeg")
    if path:
        return path

    # 2. Try imageio-ffmpeg (Fallback)
    try:
        path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"✅ Found FFmpeg via imageio-ffmpeg: {path}")
        return path
    except Exception as e:
        print(f"⚠️ imageio-ffmpeg failed: {e}")
    
    # 3. Try common Linux/Nix paths
    common_paths = [
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/bin/ffmpeg",
        "/nix/var/nix/profiles/default/bin/ffmpeg",
    ]
    for p in common_paths:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
            
    # 4. Search in current directory
    if os.path.exists("ffmpeg.exe"): return os.path.abspath("ffmpeg.exe")
    if os.path.exists("ffmpeg"): return os.path.abspath("ffmpeg")
    
    return None

FFMPEG_PATH = find_ffmpeg()
print(f"✅ FOUND FFmpeg at: {FFMPEG_PATH}")

if not FFMPEG_PATH:
    print("⚠️ WARNING: FFmpeg not found in any standard location!")

# --- Robust Opus Finder & Loader ---
def load_opus():
    if discord.opus.is_loaded():
        print("✅ Opus is already loaded.")
        return

    print("Attempting to load Opus...")
    
    # 1. Try ctypes.util.find_library
    try:
        lib = ctypes.util.find_library("opus")
        if lib:
            discord.opus.load_opus(lib)
            print(f"✅ Loaded Opus via find_library: {lib}")
            return
    except Exception as e:
        print(f"⚠️ find_library failed: {e}")

    # 2. Try common Linux/Nix paths (Railway/Nixpacks specific)
    common_lib_paths = [
        "/usr/lib/libopus.so",
        "/usr/lib/libopus.so.0",
        "/usr/local/lib/libopus.so",
        "/lib/libopus.so",
    ]
    
    # Search in Nix store
    import glob
    nix_matches = glob.glob("/nix/store/*-libopus-*/lib/libopus.so.0")
    if nix_matches:
        common_lib_paths.extend(nix_matches)

    for lib_path in common_lib_paths:
        try:
            discord.opus.load_opus(lib_path)
            print(f"✅ Loaded Opus manually from: {lib_path}")
            return
        except:
            pass
            
    # 3. Try direct names
    for lib in ["libopus.so.0", "libopus.so", "libopus-0.dll"]:
        try:
            discord.opus.load_opus(lib)
            print(f"✅ Loaded Opus via direct name: {lib}")
            return
        except:
            pass
            
    print("❌ Could not load Opus. Voice will likely fail.")

# Load Opus at startup
load_opus()

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# Global variable to control the welcome bot
bot_active = True
# Variable to track if welcome is paused due to prayer
prayer_pause = False

# --- Welcome Feature ---

# (Removed setup_ranks command)

# --- Role View & Select Menu ---
# (Removed RoleSelect and RoleView classes)

# --- Text Command Fallback (Emergency Solution) ---
# (Removed setup command)

# --- Security: Admin Code ---
ADMIN_CODE = os.getenv("ADMIN_CODE", "th1") # Default code if not set

@bot.command(name="fix")
@commands.has_permissions(administrator=True)
async def fix_duplicates(ctx, code: str = None):
    """Smart fix for duplicates. Usage: !fix <code>"""
    if code != ADMIN_CODE:
        await ctx.send("🔒 عذراً، الكود غير صحيح! لا يمكنك استخدام هذا الأمر.")
        return

    await ctx.send("🔧 جاري إصلاح التكرار (مسح نسخ السيرفر الزائدة)...")
    
    try:
        # 1. Clear Guild-specific commands ONLY (Removes the duplicate layer)
        bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        
        # 2. Re-sync Global to ensure originals are there
        synced = await bot.tree.sync()
        
        await ctx.send(f"✅ تم الإصلاح! تم حذف النسخ المكررة والإبقاء على {len(synced)} أمر أساسي.\n(سوي Refresh للديسكورد الآن - Ctrl+R)")
        
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {e}")

@bot.tree.command(name="sync", description="تحديث أوامر البوت يدوياً (للمشرفين فقط)")
@app_commands.describe(code="كود الأمان")
async def sync_commands(interaction: discord.Interaction, code: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return
    
    if code != ADMIN_CODE:
        await interaction.response.send_message("🔒 عذراً، كود الأمان غير صحيح!", ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    try:
        synced = await bot.tree.sync()
        await interaction.followup.send(f"✅ تم تحديث {len(synced)} أمر بنجاح!")
    except Exception as e:
        await interaction.followup.send(f"❌ حدث خطأ: {e}")

@bot.tree.command(name="debug", description="فحص مشاكل الصوت (للمشرفين فقط)")
@app_commands.describe(code="كود الأمان")
async def debug_bot(interaction: discord.Interaction, code: str):
    """Checks environment variables and files."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    if code != ADMIN_CODE:
        await interaction.response.send_message("🔒 عذراً، كود الأمان غير صحيح!", ephemeral=True)
        return

    report = "🔍 **تقرير الفحص:**\n"
    
    # 1. FFmpeg
    report += f"- **مسار FFmpeg المستخدم:** `{FFMPEG_PATH}`\n"
    if FFMPEG_PATH:
        try:
            result = subprocess.run([FFMPEG_PATH, "-version"], capture_output=True, text=True)
            version = result.stdout.splitlines()[0] if result.stdout else "Unknown"
            report += f"- **النسخة:** `{version}`\n"
        except Exception as e:
            report += f"- **خطأ في التشغيل:** `{e}`\n"
    else:
        report += "- **FFmpeg:** ❌ غير موجود نهائياً\n"
        report += f"- **PATH Env:** `{os.environ.get('PATH')}`\n"
    
    # 2. Opus
    report += f"- **Opus Loaded:** {'✅ نعم' if discord.opus.is_loaded() else '❌ لا'}\n"
    
    # 3. Audio Files
    files = [f for f in os.listdir('.') if f.endswith('.mp3')]
    report += f"- **ملفات الصوت:** {', '.join(files) if files else '❌ لا يوجد'}\n"

    await interaction.response.send_message(report, ephemeral=True)

@bot.tree.command(name="stop", description="إيقاف الترحيب مؤقتاً (للمشرفين فقط)")
@app_commands.describe(code="كود الأمان")
async def stop_bot(interaction: discord.Interaction, code: str):
    """Stops the bot from welcoming users."""
    global bot_active
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    if code != ADMIN_CODE:
        await interaction.response.send_message("🔒 عذراً، كود الأمان غير صحيح!", ephemeral=True)
        return

    bot_active = False
    await interaction.response.send_message("تم إيقاف الترحيب مؤقتاً 🛑")

@bot.tree.command(name="start", description="تفعيل الترحيب من جديد (للمشرفين فقط)")
@app_commands.describe(code="كود الأمان")
async def start_bot(interaction: discord.Interaction, code: str):
    """Resumes the bot welcoming users."""
    global bot_active
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    if code != ADMIN_CODE:
        await interaction.response.send_message("🔒 عذراً، كود الأمان غير صحيح!", ephemeral=True)
        return

    bot_active = True
    await interaction.response.send_message("تم تفعيل الترحيب من جديد ✅")

@bot.tree.command(name="say", description="جعل البوت يرسل رسالة في روم محدد (للمشرفين فقط)")
@app_commands.describe(channel="الروم الذي تريد الإرسال فيه", message="الرسالة التي تريد إرسالها", image="صورة مرفقة (اختياري)", code="كود الأمان")
async def say_command(interaction: discord.Interaction, message: str, code: str, channel: discord.TextChannel = None, image: discord.Attachment = None):
    """Makes the bot send a message to a channel."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    if code != ADMIN_CODE:
        await interaction.response.send_message("🔒 عذراً، كود الأمان غير صحيح!", ephemeral=True)
        return

    target_channel = channel or interaction.channel
    
    try:
        # Check bot permissions in target channel
        permissions = target_channel.permissions_for(interaction.guild.me)
        if not permissions.send_messages:
             await interaction.response.send_message(f"عذراً، لا أملك صلاحية الكتابة في روم {target_channel.mention} 🚫", ephemeral=True)
             return

        files = []
        if image:
            files.append(await image.to_file())

        await target_channel.send(content=message, files=files)
        await interaction.response.send_message(f"تم إرسال الرسالة بنجاح إلى {target_channel.mention} ✅", ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"حدث خطأ أثناء الإرسال: {e}", ephemeral=True)

# --- Game Role Selector (Self-Service) ---

class RoleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Rocket League", emoji="🚗", value="role_rocket", description="سيارات وكرة قدم"),
            discord.SelectOption(label="FiveM", emoji="👮‍♂️", value="role_fivem", description="حياة واقعية GTA V"),
            discord.SelectOption(label="Call of Duty", emoji="💀", value="role_cod", description="حروب وإطلاق نار"),
            discord.SelectOption(label="Minecraft", emoji="🪓", value="role_minecraft", description="بناء ومغامرات"),
            discord.SelectOption(label="Fortnite", emoji="🔫", value="role_fortnite", description="باتل رويال"),
            discord.SelectOption(label="Overwatch", emoji="�", value="role_overwatch", description="أبطال وقدرات"),
        ]
        super().__init__(placeholder="اختر ألعابك من هنا... | Select your games...", min_values=0, max_values=len(options), custom_id="role_select_menu")

    async def callback(self, interaction: discord.Interaction):
        # Defer immediately
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        all_values = [opt.value for opt in self.options]
        
        added = []
        removed = []
        
        for value in all_values:
            # Find the option to get the label (Role Name)
            option = next(opt for opt in self.options if opt.value == value)
            role_name = option.label # The role name is the label (e.g. "Fortnite")
            
            # Find or Create Role
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                try:
                    role = await guild.create_role(name=role_name, mentionable=True)
                except:
                    continue # Skip if can't create
            
            # Check logic
            if value in self.values:
                # Selected -> Add
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role)
                    added.append(role_name)
            else:
                # Not Selected -> Remove
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    removed.append(role_name)

        msg = ""
        if added: msg += f"✅ تمت إضافة: {', '.join(added)}\n"
        if removed: msg += f"❌ تمت إزالة: {', '.join(removed)}\n"
        if not msg: msg = "لم يتم تغيير أي شيء."
        
        await interaction.followup.send(msg, ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())

@bot.tree.command(name="setup_ranks", description="إنشاء قائمة اختيار رتب الألعاب")
@app_commands.describe(code="كود الأمان", channel="الروم (اختياري)")
async def setup_ranks(interaction: discord.Interaction, code: str, channel: discord.TextChannel = None):
    # Defer immediately to prevent timeout
    await interaction.response.defer(ephemeral=True)

    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    if code != ADMIN_CODE:
        await interaction.followup.send("🔒 عذراً، كود الأمان غير صحيح!", ephemeral=True)
        return

    target = channel or interaction.channel
    if not target.permissions_for(interaction.guild.me).send_messages:
        await interaction.followup.send("🚫 لا أستطيع الإرسال في هذا الروم.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🎮 اختر ألعابك | Choose Your Games",
        description="اختر الألعاب التي تلعبها للحصول على رتبتها.\nSelect the games you play to get their roles.",
        color=discord.Color.gold()
    )
    if interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    await target.send(embed=embed, view=RoleView())
    await interaction.followup.send("✅ تم إنشاء قائمة الألعاب بنجاح.", ephemeral=True)

# --- Fallback Text Command ---
@bot.command(name="setup_ranks")
@commands.has_permissions(administrator=True)
async def setup_ranks_text(ctx, code: str = None):
    """Text command fallback: !setup_ranks <code>"""
    if code != ADMIN_CODE:
        await ctx.send("🔒 الكود غير صحيح أو مفقود! الاستخدام: `!setup_ranks <code>`")
        return

    embed = discord.Embed(
        title="🎮 اختر ألعابك | Choose Your Games",
        description="اختر الألعاب التي تلعبها للحصول على رتبتها.\nSelect the games you play to get their roles.",
        color=discord.Color.gold()
    )
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)

    await ctx.send(embed=embed, view=RoleView())
    await ctx.message.delete() # Clean up command

@bot.tree.command(name="ajrr", description="تشغيل مقطع الأجر (صلي على محمد) في جميع الرومات الصوتية النشطة")
async def ajrr_command(interaction: discord.Interaction):
    """Plays ajrr.mp3 in ALL active voice channels."""
    
    guild = interaction.guild
    audio_file = "ajrr.mp3"
    
    if not os.path.exists(audio_file):
        await interaction.response.send_message("⚠️ عذراً، ملف الصوت `ajrr.mp3` غير موجود في البوت.", ephemeral=True)
        return

    # Find ALL channels with people (No bots)
    active_channels = [
        vc for vc in guild.voice_channels 
        if len(vc.members) > 0 and any(not m.bot for m in vc.members)
    ]

    if not active_channels:
        await interaction.response.send_message("⚠️ ما فيه أحد في الرومات الصوتية حالياً!", ephemeral=True)
        return

    await interaction.response.send_message(f"جاري نشر الأجر في **{len(active_channels)}** رومات... 🕌✨", ephemeral=True)

    # Loop through all channels
    for v_channel in active_channels:
        try:
            # Force disconnect if stuck
            if guild.voice_client:
                await guild.voice_client.disconnect()
            
            print(f"Joining {v_channel.name} for AJRR...")
            
            # Connect
            vc = await v_channel.connect(self_deaf=True)
            
            # Play
            executable = FFMPEG_PATH if FFMPEG_PATH else "ffmpeg"
            vc.play(discord.FFmpegPCMAudio(source=audio_file, executable=executable))
            
            # Wait until done
            while vc.is_playing():
                await asyncio.sleep(1)
            
            await asyncio.sleep(0.5) # Quick pause
            await vc.disconnect()
            
        except Exception as e:
            print(f"Error in ajrr command for {v_channel.name}: {e}")
            if guild.voice_client:
                await guild.voice_client.disconnect()
    
    await interaction.followup.send("✅ تم الانتهاء من نشر الأجر في جميع الرومات.", ephemeral=True)

@bot.event
async def on_message(message):
    # Don't reply to self
    if message.author == bot.user:
        return
    
    # Process other commands (needed for prefix commands like !force_sync)
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    # Check if bot is active (and not paused for prayer)
    if not bot_active or prayer_pause:
        return

    # Ignore bots
    if member.bot:
        return

    # Check if user joined a channel
    if after.channel is not None and before.channel != after.channel:
        voice_channel = after.channel
        
        # Check permissions
        permissions = voice_channel.permissions_for(member.guild.me)
        if not permissions.connect or not permissions.speak:
            print(f"Missing permissions in {voice_channel.name}")
            return

        try:
            # Connect
            vc = await voice_channel.connect(self_deaf=True)
            
            # Look for audio file
            if os.path.exists("welcome.mp3"):
                print("Found welcome.mp3, attempting to play...")
                try:
                    vc.play(discord.FFmpegPCMAudio("welcome.mp3"))
                    print("Playing started successfully.")
                except Exception as e:
                    print(f"❌ Error playing audio: {e}")
                
                # Wait while playing
                while vc.is_playing():
                    await asyncio.sleep(1)
                
                await asyncio.sleep(1)
            else:
                print(f"Error: 'welcome.mp3' file not found! Current dir files: {os.listdir('.')}")

            # Disconnect
            await vc.disconnect()
            
        except discord.errors.ClientException:
            pass
        except Exception as e:
            print(f"An error occurred: {e}")
            if member.guild.voice_client:
                await member.guild.voice_client.disconnect()

# --- Prayer Times Feature (Voice Only) ---

PRAYER_DATA = {
    "Fajr": {
        "ar": "الفجر",
        "msg": "قال رسول الله ﷺ: «ركعتا الفجر خير من الدنيا وما فيها»."
    },
    "Dhuhr": {
        "ar": "الظهر",
        "msg": "قال رسول الله ﷺ: «وقت تفتح فيه أبواب السماء، فأحب أن يصعد لي فيه عمل صالح»."
    },
    "Asr": {
        "ar": "العصر",
        "msg": "قال الله تعالى: ﴿حَافِظُوا عَلَى الصَّلَوَاتِ وَالصَّلَاةِ الْوُسْطَىٰ﴾."
    },
    "Maghrib": {
        "ar": "المغرب",
        "msg": "تذكر قول الله تعالى: ﴿وَأَقِمِ الصَّلَاةَ طَرَفَيِ النَّهَارِ وَزُلَفًا مِنَ اللَّيْلِ﴾."
    },
    "Isha": {
        "ar": "العشاء",
        "msg": "قال رسول الله ﷺ: «من صلى العشاء في جماعة فكأنما قام نصف الليل»."
    }
}

async def send_prayer_notifications(guild, prayer_name_en):
    """Sends text notifications to specific channels."""
    try:
        # Get Arabic name and message
        prayer_info = PRAYER_DATA.get(prayer_name_en, {"ar": prayer_name_en, "msg": "حي على الصلاة، حي على الفلاح."})
        prayer_ar = prayer_info["ar"]
        prayer_msg = prayer_info["msg"]
        
        notification_text = f"حان الآن موعد صلاة **{prayer_ar}** حسب توقيت الرياض 🕌\n\n✨ {prayer_msg}\n\n@everyone"

        # 1. General Chat (Keep message)
        chat_channel = discord.utils.get(guild.text_channels, name="chat")
        if chat_channel and chat_channel.permissions_for(guild.me).send_messages:
            await chat_channel.send(notification_text, delete_after=1200)

        # 2. Athkar Chat (Delete after 20 mins)
        athkar_channel = discord.utils.get(guild.text_channels, name="اذكار")
        if athkar_channel and athkar_channel.permissions_for(guild.me).send_messages:
            await athkar_channel.send(notification_text, delete_after=1200)
            
    except Exception as e:
        print(f"Notification error in {guild.name}: {e}")

async def play_prayer_audio(guild, prayer_name_en):
    """Finds active voice channels and plays the prayer audio."""
    # Determine audio file
    audio_file = f"{prayer_name_en.lower()}.mp3"
    if not os.path.exists(audio_file):
        audio_file = "adhan.mp3"
    
    if not os.path.exists(audio_file):
        print(f"Audio file not found for {prayer_name_en}")
        return False

    # Find all voice channels with members (excluding bots)
    active_voice_channels = [
        vc for vc in guild.voice_channels 
        if len(vc.members) > 0 and any(not m.bot for m in vc.members)
    ]

    if not active_voice_channels:
        return False

    for v_channel in active_voice_channels:
        try:
            # Disconnect if connected elsewhere
            if guild.voice_client:
                await guild.voice_client.disconnect()
            
            print(f"Joining {v_channel.name} for {prayer_name_en}...")
            
            # Connect
            vc = await v_channel.connect(self_deaf=True)
            
            # Play
            print(f"Attempting to play {audio_file} in {v_channel.name}...")
            if not os.path.exists(audio_file):
                print(f"❌ File not found right before playing: {audio_file}")
            
            try:
                vc.play(discord.FFmpegPCMAudio(audio_file))
                print(f"Playback started for {audio_file}")
            except Exception as e:
                 print(f"❌ FFmpeg Playback Error: {e}")

            while vc.is_playing():
                await asyncio.sleep(1)
            await asyncio.sleep(1)
            
            await vc.disconnect()
        except Exception as e:
            print(f"Voice prayer error in {v_channel.name}: {e}")
            if guild.voice_client:
                await guild.voice_client.disconnect()
    
    return True

@bot.command(name="force_sync")
@commands.has_permissions(administrator=True)
async def force_sync_text(ctx):
    """Syncs commands using a text command (prefix !)."""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ تم تحديث {len(synced)} أمر slash بنجاح!")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {e}")

@bot.tree.command(name="test_notification", description="تجربة التنبيهات الكتابية للصلاة (للمشرفين فقط)")
@app_commands.choices(prayer=[
    app_commands.Choice(name="الفجر", value="Fajr"),
    app_commands.Choice(name="الظهر", value="Dhuhr"),
    app_commands.Choice(name="العصر", value="Asr"),
    app_commands.Choice(name="المغرب", value="Maghrib"),
    app_commands.Choice(name="العشاء", value="Isha")
])
@app_commands.describe(code="كود الأمان")
async def test_notification(interaction: discord.Interaction, prayer: app_commands.Choice[str], code: str):
    """Manually triggers the text notification for testing."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    if code != ADMIN_CODE:
        await interaction.response.send_message("🔒 عذراً، كود الأمان غير صحيح!", ephemeral=True)
        return

    # Acknowledge the command immediately
    prayer_info = PRAYER_DATA.get(prayer.value, {"ar": prayer.name})
    await interaction.response.send_message(f"جاري إرسال تنبيهات الصلاة لـ **{prayer_info['ar']}**... 📨", ephemeral=True)
    
    await send_prayer_notifications(interaction.guild, prayer.value)
    
    await interaction.followup.send("✅ تم الإرسال.", ephemeral=True)

@bot.tree.command(name="test_prayer", description="تجربة الأذان: يدخل فوراً وبدون إعدادات (للمشرفين فقط)")
@app_commands.choices(prayer=[
    app_commands.Choice(name="الفجر", value="Fajr"),
    app_commands.Choice(name="الظهر", value="Dhuhr"),
    app_commands.Choice(name="العصر", value="Asr"),
    app_commands.Choice(name="المغرب", value="Maghrib"),
    app_commands.Choice(name="العشاء", value="Isha")
])
@app_commands.describe(code="كود الأمان")
async def test_prayer(interaction: discord.Interaction, prayer: app_commands.Choice[str], code: str):
    """Manually triggers the prayer voice notification immediately."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    if code != ADMIN_CODE:
        await interaction.response.send_message("🔒 عذراً، كود الأمان غير صحيح!", ephemeral=True)
        return

    # Acknowledge the command immediately
    prayer_info = PRAYER_DATA.get(prayer.value, {"ar": prayer.name})
    await interaction.response.send_message(f"جاري الدخول للرومات للأذان لصلاة **{prayer_info['ar']}**... 🚀", ephemeral=True)
    
    prayer_name_en = prayer.value
    guild = interaction.guild

    # Send notifications manually for testing
    await send_prayer_notifications(guild, prayer_name_en)
    
    # 1. Prepare Audio
    audio_file = f"{prayer_name_en.lower()}.mp3"
    if not os.path.exists(audio_file):
        audio_file = "adhan.mp3" # Fallback
    
    if not os.path.exists(audio_file):
        await interaction.followup.send(f"⚠️ ملف الصوت غير موجود: {audio_file}", ephemeral=True)
        return

    # 2. Find ALL channels with people (No bots)
    active_channels = [
        vc for vc in guild.voice_channels 
        if len(vc.members) > 0 and any(not m.bot for m in vc.members)
    ]

    if not active_channels:
        await interaction.followup.send("⚠️ ما فيه أحد في الرومات الصوتية حالياً!", ephemeral=True)
        return

    # 3. Join them one by one forcefully
    for v_channel in active_channels:
        try:
            # Force disconnect if stuck
            if guild.voice_client:
                await guild.voice_client.disconnect()
            
            # Connect
            vc = await v_channel.connect(self_deaf=True)
            
            # Play
            abs_path = os.path.abspath(audio_file)
            print(f"Test Prayer: Playing {abs_path}...")
            
            if not os.path.exists(abs_path):
                 await interaction.followup.send(f"⚠️ الملف غير موجود في المسار: {abs_path}", ephemeral=True)
                 return

            try:
                # Explicitly use found FFMPEG_PATH
                executable = FFMPEG_PATH if FFMPEG_PATH else "ffmpeg"
                vc.play(discord.FFmpegPCMAudio(source=abs_path, executable=executable, options="-vn"))
                print(f"Playback started for {audio_file} using {executable}")
            except Exception as e:
                print(f"❌ Test Prayer Error: {e}")
                await interaction.followup.send(f"⚠️ خطأ في تشغيل الصوت: {e}", ephemeral=True)
            
            # Wait until done
            while vc.is_playing():
                await asyncio.sleep(1)
            
            await asyncio.sleep(0.5) # Quick pause
            await vc.disconnect()
            
        except Exception as e:
            print(f"Error in {v_channel.name}: {e}")
            if guild.voice_client:
                await guild.voice_client.disconnect()
    
    await interaction.followup.send("✅ تم الانتهاء من الأذان في جميع الرومات.", ephemeral=True)

@tasks.loop(minutes=1)
async def prayer_task():
    # Hardcoded Location: Riyadh, SA
    city = "Riyadh"
    country = "SA"
    
    # Force Riyadh Timezone
    tz = pytz.timezone('Asia/Riyadh')
    now = datetime.datetime.now(tz)
    current_time = now.strftime("%H:%M")
    
    print(f"Checking prayer time... Current Riyadh Time: {current_time}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=4") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    timings = data["data"]["timings"]
                    
                    prayers_en = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
                    
                    for prayer in prayers_en:
                        if timings[prayer] == current_time:
                            print(f"It's {prayer} time! Checking guilds...")
                            for guild in bot.guilds:
                                # Run voice and text notifications concurrently
                                await asyncio.gather(
                                    play_prayer_audio(guild, prayer),
                                    send_prayer_notifications(guild, prayer)
                                )
                            
                            # Wait a bit to prevent double triggering within the same minute
                            await asyncio.sleep(60) 
    except Exception as e:
        print(f"Prayer task error: {e}")

@bot.event
async def on_ready():
    # Start web server
    await start_web_server()

    print(f'Logged in as {bot.user.name}')
    
    # --- IMMEDIATE FORCE SYNC (Old Reliable Way) ---
    # No clearing, no complex logic. Just sync everything NOW.
    print("🔄 Starting immediate command sync...")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands globally!")
    except Exception as e:
        print(f"⚠️ Global sync error: {e}")

    # --- CLEANUP DUPLICATES (The Safe Way) ---
    # We remove guild-specific commands so only the Global ones remain.
    # This fixes duplicates without wiping the bot.
    for guild in bot.guilds:
        try:
            bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"🧹 Cleared local duplicate commands for: {guild.name}")
        except Exception as e:
            print(f"❌ Failed to clear duplicates for {guild.name}: {e}")

    # Register the persistent view for roles so it works after restart
    bot.add_view(RoleView()) 
    print("✅ RoleView registered.")

    # --- Auto-Send Rank Panel ---
    # (Removed auto-send rank panel)

    # Sync commands to all guilds immediately (Instant Update)
    # for guild in bot.guilds:
    #     try:
    #         bot.tree.copy_global_to(guild=guild)
    #         await bot.tree.sync(guild=guild)
    #         print(f"✅ Synced commands to guild: {guild.name}")
    #     except Exception as e:
    #         print(f"❌ Failed to sync to {guild.name}: {e}")

    if not prayer_task.is_running():
        prayer_task.start()

    print('Bot is ready to welcome and pray!')

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error starting bot: {e}")
