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
    
def checkIfOwner(interaction: discord.Interaction) -> bool:
    if interaction.user.id == interaction.guild.owner.id: #type: ignore
        return True
    else:
        return False
    
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

# Setup command
@bot.tree.command(name="setup", description="Setup the bot")
@commands.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction) -> None:
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
                if interaction.channel.id == config.get(str(interaction.guild_id), "botsettingschannel"): #type: ignore
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
async def filter(interaction: discord.Interaction, object: str, val: str) -> None:
    await reply(interaction, "This command will be added in a later update, sorry for the inconvienience!")
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
async def on_ready() -> None:
    print(f"Bot is ready. Logged in as {bot.user}")
    try:
        synced: list = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed syncing commands, Error: {e}")

bot.run(BOT_TOKEN)