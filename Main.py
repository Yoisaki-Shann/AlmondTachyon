import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# Load Token
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)

# Remove default help to use our custom one
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"✅ Main System Logged in as {bot.user}")

# --- CUSTOM HELP COMMAND ---
@bot.command()
async def help(ctx):
    """ Shows the custom help menu """
    
    # Create the Embed
    embed = discord.Embed(
        title="🐎 Almond Tachuon Academy Club Tracker",
        description="**Konichiwa** 🥕\nI track our Club's performance, fan growth, and member activity. \n All Hail Eternity",
        color=0x00BFA5 # Uma Musume Green-ish Teal
    )
    
    # --- PUBLIC COMMANDS ---
    public_cmds = (
        "> `!members [club]`\n"
        "🏆 **Live Leaderboard**\n"
        "Show current ranking. Use `lunasoul` or `umaclover` to switch clubs.\n"
        "*(Ex: `!members`, `!members umaclover`)*\n\n"
        
        "> `!ClubStatus [club]`\n"
        "📈 **Club Report**\n"
        "Show Total Fans, Daily Output, and Monthly Estimates.\n\n"
        
        "> `!profile [name]`\n"
        "👤 **Personal Stats**\n"
        "Check Rank, Fans, and Weekly Growth for yourself or a friend.\n"
        "*(Ex: `!profile`, `!profile @Kuro`, `!profile Silence`)*"
    )
    embed.add_field(name="📊 **Public Statistics**", value=public_cmds, inline=False)
    
    # --- STAFF COMMANDS (Visible only to Mods) ---
    # Import the check function
    from utils import is_manager
    
    if is_manager(ctx):
        staff_cmds = (
            "> `!memberStatus [club]`\n"
            "🕒 **Login Check**\n"
            "See who is Online, Offline, or Inactive.\n\n"
            
            "> `!link @User [club] Name`\n"
            "🔗 **Connect User**\n"
            "Link a Discord user to an In-Game Name.\n"
            "*(Ex: `!link @Kuro umaclover SilenceSuzuka`)*\n\n"
            
            "> `!weekly`\n"
            "💾 **Sunday Save**\n"
            "Manually trigger the Weekly CSV Save & Reset for **ALL** clubs."
            "Mods and staff can use this to save manually (Triggered at 20:00 sunday automated).\n\n"
        )
        embed.add_field(name="🔒 **Staff / Mod Operations**", value=staff_cmds, inline=False)
    
    # Footer
    embed.set_footer(text="✨ Automated Tracking every Sunday at 20:00")
    
    await ctx.send(embed=embed)

async def load_extensions():
    # Load files from the Cogs folder
    await bot.load_extension("Cogs.Public")
    await bot.load_extension("Cogs.Staff")

@bot.event
async def on_command_error(ctx, error):
    
    # 1. Check if the error is because they lack Permissions (is_manager failed)
    if isinstance(error, commands.CheckFailure):
        # Create a red "Access Denied" box
        embed = discord.Embed(
            title="⛔ Access Denied",
            description="You do not have permission to use this command.\n**Required:** Mod, Staff, Officer, or Admin.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
    # 2. Check if the command doesn't exist (Optional: Prevents console spam)
    elif isinstance(error, commands.CommandNotFound):
        pass # Do nothing if they type !wrongcommand
        
    # 3. Print any other real errors to the console (for debugging)
    else:
        print(f"❌ Error in {ctx.command}: {error}")
        # Optional: Tell the user something went wrong
        await ctx.send(f"⚠️ **Bot Error:** `{error}`")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")

