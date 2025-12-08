import discord
from discord.ext import commands
import typing
# Import CLUB_FILENAMES so we can use the pretty names
from utils import (
    read_browser_and_sort, load_json, get_filenames, 
    resolve_club_id, CLUB_FILENAMES
)

class Public(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- 1. MEMBERS LIST ---
    @commands.command(aliases=['member'])
    async def members(self, ctx, club_name_or_id: str = "main"):
        """ Shows the full Live Leaderboard (Embedded) """
        
        # 1. Resolve Club
        club_id = resolve_club_id(club_name_or_id)
        if club_id is None:
            return await ctx.send(f"❌ Unknown Club: **{club_name_or_id}**")

        pretty_name = CLUB_FILENAMES.get(club_id, f"Club {club_id}")
        port = 9222 if club_id == 1 else 9223
        
        # Temporary "Loading" message
        loading_msg = await ctx.send(f"🕵️ Reading stats for **{pretty_name}**...")
        
        # 2. Scrape Data
        club_title_from_web, raw_data = read_browser_and_sort(port)
        
        if club_title_from_web is None:
            return await ctx.send(f"❌ {raw_data}")

        files = get_filenames(club_id)
        bindings = load_json(files['bind'])
        
        header_name = club_title_from_web if club_title_from_web != "Club" else pretty_name
        
        # 3. Build the Text Block
        description_text = ""
        
        for i, p in enumerate(raw_data):
            name = p['name']
            fans = p['fans']
            
            # --- FANCY FORMATTING ---
            # Add medals for Top 3
            if i == 0: rank_icon = "🥇"
            elif i == 1: rank_icon = "🥈"
            elif i == 2: rank_icon = "🥉"
            else: rank_icon = f"`#{i+1}`" # Monospace font for other numbers
            
            # Link Check
            if name in bindings:
                display_name = f"<@{bindings[name]}>"
            else:
                display_name = f"{name}"
            
            # Line Format: 🥇 @Kuro: **150,000,000**
            line = f"{rank_icon} {display_name}: **{fans:,}**\n"
            
            description_text += line

        # 4. Create Embed
        embed = discord.Embed(
            title=f"🏆 {header_name} Leaderboard",
            description=description_text,
            color=discord.Color.gold()
        )
        
        # Add footer with total count
        embed.set_footer(text=f"Total Members: {len(raw_data)}/30 | Updated: just now")
        
        # 5. Send (and delete loading message)
        await loading_msg.delete()
        await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    # --- 2. PLAYER STATS ---
    @commands.command()
    async def profile(self, ctx, target: typing.Union[discord.Member, str] = None):
        """ Stats for one person (Checks All Clubs) """
        if target is None: target = ctx.author

        # Check Club 1 (Port 9222)
        found = await self.check_club(ctx, target, 1, 9222)
        if found: return

        # Check Club 2 (Port 9223)
        found = await self.check_club(ctx, target, 2, 9223)
        
        if not found:
            await ctx.send(f"❌ Could not find that player in any active club.")

    async def check_club(self, ctx, target, club_num, port):
        files = get_filenames(club_num)
        bindings = load_json(files['bind'])
        
        possible_search_terms = []
        target_user_display = "Not Linked"

        # 1. Identify what we are searching for
        if isinstance(target, discord.Member) or isinstance(target, discord.User):
            # If they tagged a user, we MUST find the name in bindings first
            target_user_display = target.mention
            for name, uid in bindings.items():
                if uid == target.id:
                    possible_search_terms.append(name)
            
            if not possible_search_terms: return False # User is not linked in this club
        else:
            # If they typed a string ("yoisaki"), we use that as the search term
            possible_search_terms.append(target)
            
            # Also check if this string is a binding key, and if so, add other aliases
            if target in bindings:
                target_uid = bindings[target]
                for name, uid in bindings.items():
                    if uid == target_uid and name != target:
                        possible_search_terms.append(name)

        # 2. Scrape Data
        club_title_from_web, raw_data = read_browser_and_sort(port)
        if not club_title_from_web: return False

        # 3. Find Player in the List (Case-Insensitive)
        player_data = None
        rank = 0
        
        for i, p in enumerate(raw_data):
            # Check if ANY search term is inside the name
            for term in possible_search_terms:
                if term.lower() in p['name'].lower():
                    player_data = p
                    rank = i + 1
                    break
            if player_data:
                break
        
        if player_data:
            # 4. NOW we check for the Link using the REAL name found in game
            real_name = player_data['name'] # e.g. "YoiSaki"
            
            # Check exact match in bindings
            if real_name in bindings:
                target_user_display = f"<@{bindings[real_name]}>"
            else:
                # Double check case-insensitive binding
                for b_name, b_id in bindings.items():
                    if b_name.lower() == real_name.lower():
                        target_user_display = f"<@{b_id}>"
                        break
            
            # 5. Calculate Stats
            weekly_file = load_json(files['json'])
            gain = player_data['fans'] - weekly_file.get(real_name, player_data['fans'])
            if gain < 0: gain = 0

            club_name = CLUB_FILENAMES.get(club_num, f"Club {club_num}")

            embed = discord.Embed(title=f"📊 Stats1: {real_name}", color=discord.Color.blue())
            embed.add_field(name="🏆 Rank", value=f"#{rank} ({club_name})", inline=True)
            embed.add_field(name="✨ Total Fans", value=f"{player_data['fans']:,}", inline=True)
            embed.add_field(name="📅 Earned This Week", value=f"+{gain:,}", inline=False)
            embed.add_field(name="🔗 Discord", value=target_user_display, inline=False)
            embed.set_footer(text=f"Club: {club_title_from_web}")
            
            await ctx.send(embed=embed)
            return True
            
        return False

    # --- 3. CLUB STATUS ---
    @commands.command(aliases=['clubstats'])
    async def ClubStatus(self, ctx, club_ref: str = "main"):
        """ Shows Total Fans, Averages, and Monthly Estimates. """
        
        club_id = resolve_club_id(club_ref)
        if not club_id: return await ctx.send(f"❌ Unknown Club: {club_ref}")

        club_name = CLUB_FILENAMES.get(club_id, f"Club {club_id}")

        port = 9222 if club_id == 1 else 9223
        await ctx.send(f"📊 Analyzing **{club_name}**...")
        
        club_title_from_web, raw_data = read_browser_and_sort(port)
        if not club_title_from_web: return await ctx.send(f"❌ {raw_data}")

        # Calc Stats
        total_fans = sum(p['fans'] for p in raw_data)
        total_daily = sum(p['daily'] for p in raw_data)
        member_count = len(raw_data)
        monthly_est = total_daily * 30
        
        embed = discord.Embed(title=f"📈 Club Report: {club_name}", color=discord.Color.gold())
        
        embed.add_field(name="👥 Members", value=f"{member_count}/30", inline=True)
        embed.add_field(name="✨ Total Fans", value=f"{total_fans:,}", inline=True)
        embed.add_field(name="🔥 Daily Output", value=f"+{total_daily:,} /day", inline=True)
        embed.add_field(name="📅 Monthly Estimate", value=f"~{monthly_est:,} fans", inline=True)
        
        # Footer uses the official name from the game
        embed.set_footer(text=f"Official Name: {club_title_from_web}")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Public(bot))