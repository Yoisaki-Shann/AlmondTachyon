import discord
from discord.ext import commands, tasks
from datetime import datetime
# IMPORT CLUB_FILENAMES HERE 👇
from utils import (
    is_manager, load_json, save_json, save_weekly_csv, 
    read_browser_and_sort, get_filenames, resolve_club_id,
    CLUB_FILENAMES 
)

REPORT_CHANNEL_ID = int(os.getenv('REPORT_CHANNEL_ID'))

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_weekly_report.start()

    # --- 1. MEMBER STATUS (ONLINE CHECK) ---
    @commands.command()
    @commands.check(is_manager)
    async def memberStatus(self, ctx, club_ref: str = "main"):
        """ (Mod Only) Shows Last Login times. """
        
        # 1. Resolve ID
        club_id = resolve_club_id(club_ref)
        if not club_id: return await ctx.send(f"❌ Unknown Club: {club_ref}")

        # 2. Get Pretty Name (The Fix)
        pretty_name = CLUB_FILENAMES.get(club_id, f"Club {club_id}")

        port = 9222 if club_id == 1 else 9223
        
        # 3. Use Pretty Name in Message
        await ctx.send(f"🕒 Checking **{pretty_name}** login status...")
        
        club_title_from_web, raw_data = read_browser_and_sort(port)
        if not club_title_from_web: return await ctx.send(f"❌ {raw_data}")

        # 4. Use Pretty Name in Header
        msg = f"🕒 **Last Login: {pretty_name}** 🕒\n"
        
        for i, p in enumerate(raw_data):
            login = p['login']
            # Icons
            if "minute" in login or "hour" in login: icon = "🟢"
            elif "1 day" in login: icon = "🟡"
            else: icon = "🔴"
            
            line = f"{i+1}. **{p['name']}**: {login} {icon}\n"
            
            if len(msg) + len(line) > 1900:
                await ctx.send(msg)
                msg = ""
            msg += line
            
        if msg: await ctx.send(msg)

    # --- 2. MANAGEMENT COMMANDS ---
    @commands.command()
    @commands.check(is_manager) 
    async def link(self, ctx, member: discord.Member, club_ref: str = "main", *, in_game_name):
        """ Link @User to Name """
        club_id = resolve_club_id(club_ref)
        if not club_id: return await ctx.send(f"❌ Invalid Club")

        # Get Pretty Name
        pretty_name = CLUB_FILENAMES.get(club_id, f"Club {club_id}")

        files = get_filenames(club_id)
        bindings = load_json(files['bind'])
        in_game_name = in_game_name.strip()
        bindings[in_game_name] = member.id
        save_json(files['bind'], bindings)
        
        await ctx.send(f"🔗 Linked **{in_game_name}** to {member.mention} in **{pretty_name}**!")
        
    # --- 3. UNLINK ---   
    @commands.command()
    @commands.check(is_manager)
    async def unlink(self, ctx, in_game_name: str, club_ref: str = "main"):
        """ Unlink Name """
        club_id = resolve_club_id(club_ref)
        if not club_id: return await ctx.send(f"❌ Invalid Club")

        # Get Pretty Name
        pretty_name = CLUB_FILENAMES.get(club_id, f"Club {club_id}")

        files = get_filenames(club_id)
        bindings = load_json(files['bind'])
        
        # Check if binding exists
        if in_game_name in bindings:
            del bindings[in_game_name]
            save_json(files['bind'], bindings)
            await ctx.send(f"🗑️ Unlinked **{in_game_name}** in **{pretty_name}**!")
        else:
            await ctx.send(f"❌ **{in_game_name}** is not linked in **{pretty_name}**.")
            
    @commands.command()
    @commands.check(is_manager)
    async def weekly(self, ctx):
        """ Manual Sunday Trigger """
        await ctx.send("📅 **Saving Weekly Reports for ALL Clubs...**")
        
        # Loop through all clubs defined in filenames
        for c_id, c_name in CLUB_FILENAMES.items():
            port = 9222 if c_id == 1 else 9223
            await self.run_report_for_club(ctx, c_id, port, c_name)
            
        await ctx.send("✅ **All Clubs Saved!**")

    # --- AUTOMATIC LOOP ---
    @tasks.loop(minutes=60)
    async def scheduled_weekly_report(self):
        now = datetime.now()
        # Sunday at 8 PM
        if now.weekday() == 6 and now.hour == 20:
            channel = self.bot.get_channel(REPORT_CHANNEL_ID)
            if channel:
                print("🤖 Running Auto Report...")
                # Loop through clubs automatically
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