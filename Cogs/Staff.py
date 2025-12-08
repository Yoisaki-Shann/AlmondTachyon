import discord
from discord.ext import commands, tasks
import os
from datetime import datetime
from utils import (
    is_manager, load_json, save_json, save_weekly_csv, 
    read_browser_and_sort, get_filenames, resolve_club_id,
    CLUB_FILENAMES, perform_background_refresh 
)

# Safety check for ID
channel_id_env = os.getenv('REPORT_CHANNEL_ID')
REPORT_CHANNEL_ID = int(channel_id_env) if channel_id_env else 0

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("🕒 Staff Module Loaded. Starting Timers...") # <--- DEBUG PRINT
        
        # 1. Start the Weekly Sunday Report Timer
        self.scheduled_weekly_report.start()
        
        # 2. Start the 5-Minute Refresh Timer
        self.background_browser_refresher.start() 
        print("✅ Auto-Refresher Started!") # <--- DEBUG PRINT

    # --- 🔄 AUTO REFRESHER (Check every 1 hour) ---
    @tasks.loop(hours=1) 
    async def background_browser_refresher(self):
        print("⏱️ Timer Tick: Refreshing Browsers now...") # <--- DEBUG PRINT
        
        # Loop through all configured clubs
        for c_id in CLUB_FILENAMES.keys():
            port = 9222 if c_id == 1 else 9223
            try:
                # Call the function from utils.py
                perform_background_refresh(port)
            except Exception as e:
                print(f"❌ Error refreshing Port {port}: {e}")

    @background_browser_refresher.before_loop
    async def before_refresh(self):
        print("⏳ Waiting for bot to be ready before refreshing...")
        await self.bot.wait_until_ready()

    # --- 1. MEMBER STATUS ---
    @commands.command()
    @commands.check(is_manager)
    async def memberStatus(self, ctx, club_ref: str = "main"):
        club_id = resolve_club_id(club_ref)
        if not club_id: return await ctx.send(f"❌ Unknown Club: {club_ref}")

        club_name = CLUB_FILENAMES.get(club_id, f"Club {club_id}")
        port = 9222 if club_id == 1 else 9223
        
        await ctx.send(f"🕒 Checking **{club_name}** login status...")
        
        club_title_from_web, raw_data = read_browser_and_sort(port)
        if not club_title_from_web: return await ctx.send(f"❌ {raw_data}")

        msg = f"🕒 **Last Login: {club_name}** 🕒\n"
        for i, p in enumerate(raw_data):
            login = p['login']
            if "minute" in login or "hour" in login: icon = "🟢"
            elif "1 day" in login: icon = "🟡"
            else: icon = "🔴"
            
            line = f"{i+1}. **{p['name']}**: {login} {icon}\n"
            if len(msg) + len(line) > 1900:
                await ctx.send(msg)
                msg = ""
            msg += line
        if msg: await ctx.send(msg)

    # --- 2. LINK ---
    @commands.command()
    @commands.check(is_manager) 
    async def link(self, ctx, member: discord.Member, club_ref: str = "main", *, in_game_name: str):
        club_id = resolve_club_id(club_ref)
        if not club_id: return await ctx.send(f"❌ Invalid Club: {club_ref}")

        club_name = CLUB_FILENAMES.get(club_id, f"Club {club_id}")
        files = get_filenames(club_id)
        bindings = load_json(files['bind'])
        in_game_name = in_game_name.strip()
        bindings[in_game_name] = member.id
        save_json(files['bind'], bindings)
        await ctx.send(f"🔗 Linked **{in_game_name}** to {member.mention} in **{club_name}**!")
        
    # --- 3. UNLINK ---   
    @commands.command()
    @commands.check(is_manager)
    async def unlink(self, ctx, club_ref: str = "main", *, in_game_name: str):
        club_id = resolve_club_id(club_ref)
        if not club_id: return await ctx.send(f"❌ Invalid Club: {club_ref}")

        club_name = CLUB_FILENAMES.get(club_id, f"Club {club_id}")
        files = get_filenames(club_id)
        bindings = load_json(files['bind'])
        
        if in_game_name in bindings:
            del bindings[in_game_name]
            save_json(files['bind'], bindings)
            await ctx.send(f"🗑️ Unlinked **{in_game_name}** in **{club_name}**!")
        else:
            await ctx.send(f"❌ **{in_game_name}** is not linked in **{club_name}**.")
            
    # --- 4. WEEKLY MANUAL ---
    @commands.command()
    @commands.check(is_manager)
    async def weekly(self, ctx):
        await ctx.send("📅 **Saving Weekly Reports for ALL Clubs...**")
        for c_id, c_name in CLUB_FILENAMES.items():
            port = 9222 if c_id == 1 else 9223
            await self.run_report_for_club(ctx, c_id, port, c_name)
        await ctx.send("✅ **All Clubs Saved!**")

    # --- 5. AUTOMATIC WEEKLY LOOP ---
    @tasks.loop(minutes=1)
    async def scheduled_weekly_report(self):
        now = datetime.now()
        if now.weekday() == 6 and now.hour == 20 and now.minute == 0:
            if REPORT_CHANNEL_ID == 0: return
            channel = self.bot.get_channel(REPORT_CHANNEL_ID)
            if channel:
                print("🤖 Running Auto Report...")
                for c_id, c_name in CLUB_FILENAMES.items():
                    port = 9222 if c_id == 1 else 9223
                    await self.run_report_for_club(channel, c_id, port, c_name)

    async def run_report_for_club(self, ctx_or_channel, club_num, port, pretty_name):
        club_title_from_web, current_data = read_browser_and_sort(port)
        if not club_title_from_web:
            await ctx_or_channel.send(f"❌ Error: Could not read **{pretty_name}** (Port {port})")
            return
        files = get_filenames(club_num)
        last_week = load_json(files['json'])
        save_weekly_csv(files['csv'], current_data, last_week)
        new_snapshot = {p['name']: p['fans'] for p in current_data}
        save_json(files['json'], new_snapshot)
        await ctx_or_channel.send(f"✅ **{pretty_name}** Data Saved!")

    @scheduled_weekly_report.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Staff(bot))