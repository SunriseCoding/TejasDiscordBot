import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_KEY = os.getenv("PUBLIC_KEY")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

def makeSlashCommand(name, description, function):
     @bot.tree.command(name=name, description=description)
     async def command(interaction: discord.Interaction):
          await function(interaction)

async def reply(interaction: discord.Interaction, text):
    await interaction.response.send_message(text)

async def hello(interaction: discord.Interaction):
    await reply(interaction, "Hi!")

async def test(interaction: discord.Interaction):
    await reply(interaction, "I can't remove this command or this bot will break!")

makeSlashCommand("hello", "Say hi!", hello)
makeSlashCommand("test", "I HATE YOU discord_example_app!!!", test)
        
@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} commands synced")
    except Exception as e:
        print(f"Error occured when syncing commands: {e}")

bot.run(BOT_TOKEN)