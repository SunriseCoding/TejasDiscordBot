import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

import json

import configparser

import asyncio

# Get Bot credentials for discord
global BOT_TOKEN
global PUBLIC_KEY
BOT_TOKEN: str = ""
PUBLIC_KEY: str = ""

# Make sure banned_words.json exists
try:
    open("banned_words.json", "r")
except FileNotFoundError:
    with open("banned_words.json", "w") as ban:
        ban.write("")

# Make sure config.properties exists
try:
    open("config.properties", "r")
except FileNotFoundError:
    with open("config.properties", "w") as conf:
        conf.write("")

try:
    open(".env", "r")
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN") #type: ignore
    PUBLIC_KEY = os.getenv("PUBLIC_KEY") #type: ignore
except FileNotFoundError:
    print("No .env found, starting .env file creation wizard.")
    BOT_TOKEN = input("Enter BOT_TOKEN: ")
    PUBLIC_KEY = input("Enter PUBLIC_KEY: ")
    with open(".env", "w") as env:
        env.write(f'BOT_TOKEN="{BOT_TOKEN}"\n')
        env.write(f'PUBLIC_KEY="{PUBLIC_KEY}"')

    print(".env file successfully written! Proceeding...")

# Define Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Define bot
bot = commands.Bot(command_prefix="/", intents=intents)

# Read the config file
config = configparser.ConfigParser()
config.read('config.properties')

# Reply function
async def reply(interaction: discord.Interaction, text: str, ephemeral: bool = False) -> None:
    if interaction.response.is_done() == False:
        await interaction.response.send_message(text, ephemeral=ephemeral)
        return None
    else:
        await interaction.followup.send(text, ephemeral=ephemeral)
        return None
    
# Check if owner function
def checkIfOwner(interaction: discord.Interaction) -> bool:
    if interaction.user.id == interaction.guild.owner.id: #type: ignore
        return True
    else:
        return False

# Check if allowed function
async def checkIfAllowed(interaction: discord.Interaction) -> bool:
    guildID = interaction.guild_id
    adminRoleID: int = int(config.get(str(guildID), "adminRoleID", fallback="0"))

    roles: list = interaction.user.roles #type: ignore

    hasAdminRole: bool = False

    await reply(interaction, "Checking for privileges...", True)

    for i in roles:
        if i.id == adminRoleID or i.name == adminRoleID:
            hasAdminRole = True

    if checkIfOwner(interaction) == True or hasAdminRole == True:
        return True
    else:
        return False
    
# Check if the channel is the settings channel
def checkIfSettingsChannel(interaction: discord.Interaction) -> bool:
    if interaction.channel_id == int(config.get(str(interaction.guild_id), "botsettingschannel", fallback="0")):
        return True
    else:
        return False

# Setup command
@bot.tree.command(name="setup", description="Setup the bot")
@commands.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction) -> None:
    try: 
        interaction.guild.id #type: ignore
    except AttributeError:
        await reply(interaction, "This is a server only command")
    
    await interaction.response.defer(thinking=True, ephemeral=False)

    botMember = interaction.guild.me #type: ignore
    guildID: int = interaction.guild_id #type: ignore

    if checkIfOwner(interaction) == False:
        await reply(interaction, "Only the owner can run this command!")
        return None
    
    # setup: str = config.get(str(interaction.guild_id), "setup", fallback="False")

    if config.has_section(str(guildID)) == True:
        await reply(interaction, "Bot has already been setup. Aborting...", True)
        return None
    
    await reply(interaction, "Setting up bot...", True)

    config.add_section(str(guildID))

    with open("config.properties", "w") as conf:
        config.write(conf)
    
    await reply(interaction, "Initialized settings section. Continuing", True)
    
    config.set(str(guildID), "filter", "False")

    with open("config.properties", "w") as conf:
        config.write(conf)

    roles: list = await interaction.guild.fetch_roles() #type: ignore

    hasAdminRole: list = [False, "0"]

    await reply(interaction, "Checking for pre-existing roles name admin...", True)

    for i in roles:
        if i.name == "admin" or i.name == "Admin":
            hasAdminRole = [True, i.id, i]
    
    if hasAdminRole[0] == True:
        await reply(interaction, "Detected role named admin, making it the admin role...", True)
        config.set(str(guildID), "adminRoleID", str(hasAdminRole[1]))
        await reply(interaction, "Successfully added Admin role to the settings of this guild", True)
    else:
        if botMember.guild_permissions.manage_roles == True:
            await reply(interaction, "Making new admin role.", True)
            adminRole = await interaction.guild.create_role(reason="Ran /setup", name="Admin", permissions=discord.Permissions(permissions=8)) #type: ignore
            config.set(str(guildID), "adminRoleID", str(adminRole.id))
            
        else:
            await reply(interaction, "Please grant the manage roles permission, aborting...")
            config.remove_section(str(guildID))
            with open("config.properties", "w") as conf:
                config.write(conf)

            return None
        
    
    with open("config.properties", "w") as conf:
        config.write(conf)
        
    await reply(interaction, "Successfully added admin role to the settings of this guild!", True)

    adminRole = await interaction.guild.fetch_role(int(config.get(str(guildID), "adminRoleID"))) #type: ignore

    await reply(interaction, "Making the bot-settings channel...", True)

    if botMember.guild_permissions.manage_channels == True:
        permsBotSettingsChannel = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), #type: ignore
        interaction.guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True), #type: ignore
        adminRole: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        botSettingsChannel: discord.TextChannel = await interaction.guild.create_text_channel("bot-settings", reason="Ran /setup command", overwrites=permsBotSettingsChannel) #type: ignore

        await reply(interaction, "Successfully made the bot-settings channel, adding to the settings of this guild", True)

        config.set(str(guildID), "botSettingsChannel", str(botSettingsChannel.id))

        with open("config.properties", "w") as conf:
            config.write(conf)

        await reply(interaction, "Successfully added the bot-settings channel to the settings of this guild", True)

        await reply(interaction, "Initializing the filter section...", True)

        banned_words: dict = {}

        with open("banned_words.json", "r") as f:
            banned_words = json.load(f)

        banned_words[str(interaction.guild_id)] = []

        with open("banned_words.json", "w") as f:
            json.dump(banned_words, f)

        await reply(interaction, "Setup finished!", True)

        return None
    else:
        await reply(interaction, "Please grant the manage channels permission, aborting...")
        config.remove_section(str(guildID))
        with open("config.properties", "w") as conf:
            config.write(conf)

        return None

# End of /setup command -x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x

# Cleanup command
@bot.tree.command(name="cleanup", description="Cleans up messages or the channel")
async def cleanup(interaction: discord.Interaction, object: str, val: str = "0") -> None:
    try: 
        interaction.guild.id #type: ignore
    except AttributeError:
        await reply(interaction, "This is a server only command")
    
    await interaction.response.defer(thinking=True, ephemeral=False)

    if object == "messages":
        if await checkIfAllowed(interaction) == True:
            try:
                lmt: int = int(val)
            except ValueError:
                await reply(interaction, "Please enter a number greater than 0 in val!")
                return None

            await interaction.channel.purge(limit=lmt+1) #type: ignore

            channel: int = interaction.channel_id #type: ignore

            await bot.get_channel(channel).send(f"Successfully deleted {val} messages!") #type: ignore

            return None
        else:
            await reply(interaction, "Only the owner of the guild can use this command")
            return None
        
    elif object == "channel" or object == "channels":
        if checkIfOwner(interaction) == True:
            if val == "~":
                if interaction.channel.id == int(config.get(str(interaction.guild_id), "botsettingschannel")): #type: ignore
                    await reply(interaction, "Can't delete that channel!")
                    return None

                delChannelName: str = interaction.channel.name #type: ignore
                await interaction.channel.clone() #type: ignore
                await interaction.channel.delete() #type: ignore

                await reply(interaction, f"Successfully cleared the channel {delChannelName}")

                return None
            else:
                channels = await interaction.guild.fetch_channels() #type: ignore
                channelID: int = 0
                for i in channels:
                    if i.name == val and type(i) == discord.TextChannel:
                        channelID = i.id
                        break
                else:
                    await reply(interaction, f"There is no channel named {val}. Aborting...")
                    return None
                
                if channelID == int(config.get(str(interaction.guild_id), "botsettingschannel")): #type: ignore
                    await reply(interaction, "Can't delete that channel!")
                    return None

                oldChannel: discord.TextChannel = await interaction.guild.fetch_channel(channelID) #type: ignore
                await oldChannel.clone()
                await oldChannel.delete()

                await reply(interaction, f"Cleared channel {val}")
                return None
        else:
            await reply(interaction, "Only the owner can run this command")
            return None
    
    else:
        await reply(interaction, f"No object name {object}")
        return None
    
@bot.tree.command(name="filter", description="Filter the messages sent by players (WIP)")
async def filter(interaction: discord.Interaction, object: str, val: str = "0") -> None:
    #await reply(interaction, "This command will be added in a later update, sorry for the inconvienience!")
    await interaction.response.defer(thinking=True)

    try: 
        interaction.guild.id #type: ignore
    except AttributeError:
        await reply(interaction, "This is a server only command")

    if await checkIfAllowed(interaction) == False:
        await reply(interaction, "You are not eligible to use this command", True)
        return None
    
    if checkIfSettingsChannel(interaction) == False:
        await reply(interaction, "Please run this command on the bot-settings channel", True)
        return None
    
    if object == "on":
        config.set(str(interaction.guild_id), "filter", "True")

        with open("config.properties", "w") as conf:
            config.write(conf)

        await reply(interaction, "Filter in now on")
        return None
    elif object == "off":
        config.set(str(interaction.guild_id), "filter", "False")

        with open("config.properties") as conf:
            config.write(conf)

        await reply(interaction, "Filter in now off")
        return None
    elif object == "append":
        banned_words: dict = {}
        with open("banned_words.json", "r") as f:
            banned_words = json.load(f)

        try:
            banned_words[str(interaction.guild_id)].append(val)
        except KeyError:
            await reply(interaction, "An error occured, aborting...")
            await reply(interaction, "Tip: run the ```/setup``` command if you haven't")

            return None

        with open("banned_words.json", "w") as f:
            json.dump(banned_words, f)
            
        await reply(interaction, f"Appended {val} to banned_words.json")
        return None
    elif object == "remove":
        banned_words: dict = {}
        with open("banned_words.json", "r") as f:
            banned_words = json.load(f)

        try:
            banned_words[str(interaction.guild_id)].pop(banned_words[str(interaction.guild_id)].index(val))
        except ValueError or KeyError:
            await reply(interaction, "An error occured, aborting...")
            await reply(interaction, f"Tip: run the ```/setup``` command if you haven't or make sure that {val} exists in the banned_words list")

            return None

        with open("banned_words.json", "w") as f:
            json.dump(banned_words, f)
            
        await reply(interaction, f"Removed {val} from banned_words.json")
        return None
    elif object == "list":
        banned_words: dict = {}
        with open("banned_words.json", "r") as f:
            banned_words = json.load(f)

        try:
            bannedWords: list = banned_words[str(interaction.guild_id)]
            await reply(interaction, f"All the banned_words are: {bannedWords}")
            return None
        except KeyError:
            await reply(interaction, "An error occured, aborting...")
            await reply(interaction, "Tip: run the /setup command if you haven't")
            return None
    else:
        await reply(interaction, f"No object named {val} found.")
        return None

@bot.tree.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction) -> None:
    await reply(interaction, "Hello World!")
    return None

@bot.tree.command(name="test", description="I HATE YOU DISCORD EXAMPLE BOT!!!")
async def test(interaction: discord.Interaction) -> None:
    await reply(interaction, "If I remove this command from the code, the bot will break!")
    return None

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author == bot.user:
        return None
    
    try:
        message.guild.id #type: ignore
    except AttributeError:
        await message.reply("Hey, how are you? I am Tejas#9286 and I am a server management bot! \nUnfortunately, I am **NOT** an AI so I can't chat with you, so this is my default response to dms! :)")
        return None
    
    channel = message.channel

    if message.author == bot.user:
        return None
    
    if config.get(str(message.guild.id), "filter") == "False": #type: ignore
        await bot.process_commands(message)
        return None
    
    banned_words: list = []
    with open("banned_words.json", "r") as f:
        entireBanned_Words = json.load(f)

        try:
            banned_words = entireBanned_Words[str(message.guild.id)] #type: ignore
        except KeyError:
            await bot.process_commands(message)
            return None
        
    for word in banned_words:
        if word.lower() in message.content.lower():
            await message.reply("Can't send that message!")
            await message.delete()

            break
            #await channel.send("Can't send that message")
        else:
            asyncio.timeout(0.01)

    await bot.process_commands(message)
    

@bot.event
async def on_ready() -> None:
    print(f"Bot is ready. Logged in as {bot.user}")
    try:
        synced: list = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed syncing commands, Error: {e}")

bot.run(BOT_TOKEN)