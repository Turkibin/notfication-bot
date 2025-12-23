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

# --- Web Server for Keep Alive (Railway Requirement) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌍 Web server started on port {port}")

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
ffmpeg_path = shutil.which("ffmpeg")
print(f"FFmpeg path: {ffmpeg_path}")
if not ffmpeg_path:
    print("⚠️ WARNING: FFmpeg not found in PATH! Audio will not work.")

# Try to load Opus manually if needed (Common fix for Linux/Railway)
if not discord.opus.is_loaded():
    try:
        opus_lib = ctypes.util.find_library("opus")
        if opus_lib:
            discord.opus.load_opus(opus_lib)
            print(f"✅ Opus loaded successfully from {opus_lib}")
        else:
            print("⚠️ Could not find opus library via ctypes.")
            # Try common paths
            for lib in ["libopus.so.0", "libopus.so", "libopus-0.dll"]:
                try:
                    discord.opus.load_opus(lib)
                    print(f"✅ Opus loaded manually from {lib}")
                    break
                except:
                    pass
    except Exception as e:
        print(f"❌ Error loading opus: {e}")

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

@bot.tree.command(name="debug", description="فحص مشاكل الصوت (للمشرفين فقط)")
async def debug_bot(interaction: discord.Interaction):
    """Checks environment variables and files."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    report = "🔍 **تقرير الفحص:**\n"
    
    # 1. FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    report += f"- **FFmpeg:** {'✅ موجود' if ffmpeg_path else '❌ غير موجود'}\n"
    report += f"- **مسار FFmpeg:** `{ffmpeg_path}`\n"
    
    # 2. Opus
    report += f"- **Opus Loaded:** {'✅ نعم' if discord.opus.is_loaded() else '❌ لا'}\n"
    
    # 3. Audio Files
    files = [f for f in os.listdir('.') if f.endswith('.mp3')]
    report += f"- **ملفات الصوت:** {', '.join(files) if files else '❌ لا يوجد'}\n"
    
    # 4. Try running FFmpeg
    try:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        report += f"- **FFmpeg Version:** `{result.stdout.splitlines()[0]}`\n"
    except Exception as e:
        report += f"- **FFmpeg Run Error:** `{e}`\n"

    await interaction.response.send_message(report, ephemeral=True)

@bot.tree.command(name="stop", description="إيقاف الترحيب مؤقتاً (للمشرفين فقط)")
async def stop_bot(interaction: discord.Interaction):
    """Stops the bot from welcoming users."""
    global bot_active
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    bot_active = False
    await interaction.response.send_message("تم إيقاف الترحيب مؤقتاً 🛑")

@bot.tree.command(name="start", description="تفعيل الترحيب من جديد (للمشرفين فقط)")
async def start_bot(interaction: discord.Interaction):
    """Resumes the bot welcoming users."""
    global bot_active
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    bot_active = True
    await interaction.response.send_message("تم تفعيل الترحيب من جديد ✅")

@bot.tree.command(name="say", description="جعل البوت يرسل رسالة في روم محدد (للمشرفين فقط)")
@app_commands.describe(channel="الروم الذي تريد الإرسال فيه", message="الرسالة التي تريد إرسالها", image="صورة مرفقة (اختياري)")
async def say_command(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None, image: discord.Attachment = None):
    """Makes the bot send a message to a channel."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
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
            vc = await voice_channel.connect()
            
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
            vc = await v_channel.connect()
            
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

@bot.tree.command(name="test_prayer", description="تجربة الأذان: يدخل فوراً وبدون إعدادات (للمشرفين فقط)")
@app_commands.choices(prayer=[
    app_commands.Choice(name="الفجر", value="Fajr"),
    app_commands.Choice(name="الظهر", value="Dhuhr"),
    app_commands.Choice(name="العصر", value="Asr"),
    app_commands.Choice(name="المغرب", value="Maghrib"),
    app_commands.Choice(name="العشاء", value="Isha")
])
async def test_prayer(interaction: discord.Interaction, prayer: app_commands.Choice[str]):
    """Manually triggers the prayer voice notification immediately."""
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("عذراً، هذا الأمر للمشرفين فقط 🚫", ephemeral=True)
        return

    # Acknowledge the command immediately
    await interaction.response.send_message(f"جاري الدخول للرومات للأذان لصلاة **{prayer.name}**... 🚀", ephemeral=True)
    
    prayer_name_en = prayer.value
    guild = interaction.guild
    
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
            vc = await v_channel.connect()
            
            # Play
            abs_path = os.path.abspath(audio_file)
            print(f"Test Prayer: Playing {abs_path}...")
            
            if not os.path.exists(abs_path):
                 await interaction.followup.send(f"⚠️ الملف غير موجود في المسار: {abs_path}", ephemeral=True)
                 return

            try:
                # Explicitly use 'ffmpeg' command, assuming it's in PATH (nixpacks installs it)
                # If not found, we might need to find where nixpacks puts it, but usually it's in PATH.
                # Adding options='-vn' is good practice for audio only.
                vc.play(discord.FFmpegPCMAudio(source=abs_path, executable="ffmpeg", options="-vn"))
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
    
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M")
    
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
                                await play_prayer_audio(guild, prayer)
                            
                            # Wait a bit to prevent double triggering within the same minute
                            await asyncio.sleep(60) 
    except Exception as e:
        print(f"Prayer task error: {e}")

@bot.event
async def on_ready():
    # Start web server
    await start_web_server()

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    if not prayer_task.is_running():
        prayer_task.start()

    print(f'Logged in as {bot.user.name}')
    print('Bot is ready to welcome and pray!')

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"Error starting bot: {e}")
