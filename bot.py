import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

import json

import configparser

#Get values from variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_KEY = os.getenv("PUBLIC_KEY")

#Define Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

#Define bot
bot = commands.Bot(command_prefix="/", intents=intents)

#Read properties
config = configparser.ConfigParser()
config.read('config.properties')

#Pre-Make Variables
banned_words = []
filter = False
banned_wordsPATH = ""
global owner

#For filtering, put values in variables
if config.get('DEFAULT', 'filtering') == "True":
    banned_wordsPATH = config.get('DEFAULT', 'bannedWordsFile')
    try:
        with open(banned_wordsPATH, 'r') as bw:
            banned_words = json.load(bw)
    except FileNotFoundError:
        print(f"There is not a file at {banned_wordsPATH}")
    filter = True

#I left this
#Space because
#If I didn't my
#Brain would
#Fry

#A easier function for making slash commands
def makeSlashCommand(name, description, function):
     @bot.tree.command(name=name, description=description)
     async def command(interaction: discord.Interaction):
          await function(interaction)

#For easily replying to messages
async def reply(interaction: discord.Interaction, text):
    await interaction.response.send_message(text)

#Making the hello function
async def hello(interaction: discord.Interaction):
    await reply(interaction, "Hi!")

#Making the dreaded test function
async def test(interaction: discord.Interaction):
    await reply(interaction, "I can't remove this command or this bot will break!")

#Making the Setup Bot function
async def setup(interaction: discord.Interaction):    
    global owner
    owner = interaction.guild.owner

    botMember = interaction.guild.me

    if interaction.user != owner:
        await reply(interaction, "YOU do NOT enough permissions to run THIS command!")
        return

    await reply(interaction, "Setting up bot...")


    if discord.utils.get(interaction.guild.channels, name='bot-settings'):
        await interaction.followup.send("Why did you run setup if channel already exists?")
        return

    perms = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    if interaction.channel.permissions_for(botMember).manage_channels == True:
        settingsChannel = await interaction.guild._create_channel('bot-settings', channel_type=discord.ChannelType.text,overwrites=perms)
        await interaction.followup.send(f"Now you have the ability to completely and utterly destory me at {settingsChannel.mention}", ephemeral=True)
        await interaction.followup.send("Succesfully enabled you to destroy the bot!")
    else:
        await interaction.followup.send("Hey I don't have manage channel permissions!")

#Make the commands
makeSlashCommand("hello", "Say hi!", hello)
makeSlashCommand("test", "I HATE YOU discord_example_app!!!", test)
makeSlashCommand("setupbot", "Set the bot up so that you can destroy it!", setup)

#Main stuff
@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} commands synced")
    except Exception as e:
        print(f"Error occured when syncing commands: {e}")

#Debug
print(banned_words, banned_wordsPATH, filter)
#Run the bot, you can remove this if you like wasting ur time
bot.run(BOT_TOKEN)