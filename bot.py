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
configSettingsChannelID = config.get('DEFAULT', 'settingsChannelID')

if configSettingsChannelID == "None":
    print("No ID Found for Settings Channel!")

#For filtering, put values in variables
if config.get('DEFAULT', 'filtering') == "True":
    banned_wordsPATH = config.get('DEFAULT', 'bannedwordsfile', fallback="banned_words.json")
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

#Check if message was sent be owner
def checkIfOwner(interaction: discord.Interaction):
    member: discord.member = interaction.user

    if member.id == owner.id:
        return True
    else:
        return False
    
def checkIfSettingsChannel(interaction: discord.Interaction):
    if int(config.get("DEFAULT", "settingsChannelID")) == interaction.channel_id:
        return True
    else:
        return False

#For easily replying to messages
async def reply(interaction: discord.Interaction, text):
    await interaction.response.send_message(text)

#Making the hello function
async def hello(interaction: discord.Interaction):
    await reply(interaction, "Hi!")

#Making the dreaded test function
async def test(interaction: discord.Interaction):
    await reply(interaction, "I can't remove this command or this bot will break!")

#Making the filter function
@bot.tree.command(name="filter", description="Change filter settings")
async def filterfunc(interaction: discord.Interaction, type: str, val: str):
    global filter
    global banned_words
    global banned_wordsPATH

    owner = interaction.guild.owner

    if checkIfSettingsChannel(interaction) == False:
        return

    if interaction.user == owner or discord.utils.get(interaction.user.roles, name="admin"):
        if type.lower() == "on":
            filter = True
            config.set("DEFAULT", "filtering", "True")

            with open("config.properties", 'w') as conf:
                config.write(conf)

            await reply(interaction, "Message filter is now on")
        elif type.lower() == "off":
            filter = False
            config.set("DEFAULT", "filtering", "False")

            with open("config.properties", 'w') as conf:
                config.write(conf)

            await reply(interaction, "Message filter is now off")
        elif type.lower() == "append":
            if config.get("DEFAULT", "filtering") != "True":
                await reply(interaction, "Please enable filtering and restart me!")
                return
            
            await reply(interaction, f"Adding word to {banned_wordsPATH}...")

            try:
                with open(banned_wordsPATH, "r") as f:
                    banned_words = json.load(f)
            except FileNotFoundError:
                await interaction.followup.send(f"File not found at current path: {banned_wordsPATH}. Resorting to config.properties re-read. Make sure you have enabled filtering and you may run this command again")
                banned_wordsPATH = config.get("DEFAULT", "bannedwordsfile", fallback="banned_words.json")
            
            banned_words.append(val)

            with open(banned_wordsPATH, 'w') as f:
                json.dump(banned_words, f, indent=4)

        elif type.lower() == "remove":
            if val in banned_words:
                try:
                    banned_words.remove(val)
                    with open(banned_wordsPATH, 'w') as f:
                        json.dump(banned_words, f)
                    
                    await reply(interaction, f"Removed {val} from file {banned_wordsPATH}")
                except ValueError:
                    await reply(interaction, f"{val} not found in {banned_wordsPATH}")
            else:
                await reply(interaction, f"{val} not found in {banned_wordsPATH}")

        elif type.lower() == "show":
            await reply(interaction, f"Here is the list to banned words: {banned_words}")

        else:
            await reply(interaction, f"No type called {type}")
    else:
        print(f"{interaction.user.name}")

#Making the Setup Bot function v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v
async def setup(interaction: discord.Interaction):    
    global owner
    global botMember
    owner = interaction.guild.owner

    botMember = interaction.guild.me

    if checkIfOwner(interaction) == False:
        await reply(interaction, "YOU do NOT enough permissions to run THIS command!")
        return

    await reply(interaction, "Setting up bot...")


    if discord.utils.get(interaction.guild.channels, name='bot-settings'):
        await interaction.followup.send("Why did you run setup if channel already exists?")
        adminPerms = discord.Permissions(
            permissions=8
        )

        member: discord.member = interaction.user
        #If channel is already made, make the admin role
        adminRoleName = discord.utils.get(interaction.guild.roles, name="admin")
        confAdminRoleID = int(config.get("DEFAULT", "adminRoleID", fallback=0))
        adminRoleID = 0

        if confAdminRoleID != 0:
            try:
                adminRoleID = await interaction.guild.fetch_role(confAdminRoleID)
            except:
                adminRoleID = 0
        else:
            await interaction.followup.send("Oops! Looks like I can't find this role, now you should delete this 'FAKE' admin role and run /setup again!")
            adminRoleID = 0

        if adminRoleName and adminRoleID != 0:
            await interaction.followup.send("Admin role already exists!")
            if config.get("DEFAULT", "adminRoleID") == "0":
                await interaction.followup.send("Actually, it does exist but I don't have the ID, can you delete that admin role and run /setupbot again?")
        else:
            if botMember.guild_permissions.manage_roles == True:
                adminRole = await interaction.guild.create_role(reason=None, name="admin", permissions=adminPerms)
                config.set("DEFAULT", "adminRoleID", str(adminRole.id))
                with open("config.properties", 'w') as cfg:
                    config.write(cfg)
                await interaction.followup.send("Made admin role!")
            else:
                await interaction.followup.send("Please allow me to manage roles!")

        return

    #Make the permissions for the settings channel
    perms = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    #Make the settings channel
    if interaction.channel.permissions_for(botMember).manage_channels == True:
        settingsChannel = await interaction.guild.create_text_channel('bot-settings', overwrites=perms)
        config.set("DEFAULT", "settingsChannelID", str(settingsChannel.id))
        with open("config.properties", 'w') as cfg:
            config.write(cfg)
        await interaction.followup.send(f"Now you have the ability to completely and utterly destory me at {settingsChannel}", ephemeral=True)
        await interaction.followup.send("Succesfully enabled you to destroy the bot!")
    else:
        await interaction.followup.send("Hey I don't have manage channel permissions!")

    adminPerms = discord.Permissions(
        permissions=8
    )

    #Make the admin role
    adminRoleName = discord.utils.get(interaction.guild.roles, name="admin")
    confAdminRoleID = int(config.get("DEFAULT", "adminRoleID", fallback=0))
    adminRoleID = 0

    if confAdminRoleID != 0:
        try:
            adminRoleID = await interaction.guild.fetch_role(confAdminRoleID)
        except:
            adminRoleID = 0
    else:
        await interaction.followup.send("Oops! Looks like I can't find this role, now you should delete this 'FAKE' admin role and run /setup again!")
        adminRoleID = 0

    if adminRoleName and adminRoleID != 0:
        await interaction.followup.send("Admin role already exists!")
        if config.get("DEFAULT", "adminRoleID") == "0":
            await interaction.followup.send("Actually, it does exist but I don't have the ID, can you delete that admin role and run /setupbot again?")
    else:
        if botMember.guild_permissions.manage_roles == True:
            adminRole = await interaction.guild.create_role(reason=None, name="admin", permissions=adminPerms)
            config.set("DEFAULT", "adminRoleID", str(adminRole.id))
            with open("config.properties", 'w') as cfg:
                config.write(cfg)
            await interaction.followup.send("Made admin role!")
        else:
            await interaction.followup.send("Please allow me to manage roles!")

#end of setup function x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-


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
        bot.tree.remove_command("togglefilter")
    except Exception as e:
        print(f"Error occured when syncing commands: {e}")

#Debug
print(banned_words, banned_wordsPATH, filter)
#Run the bot, you can remove this if you like wasting ur time
bot.run(BOT_TOKEN)