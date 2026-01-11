import discord
from discord.ext import commands

import os
from dotenv import load_dotenv

import json

import configparser

#Get values from variables

BOT_TOKEN: str = ""
PUBLIC_KEY: str = ""

try:
    open(".env", "r")
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN") #type: ignore
    PUBLIC_KEY = os.getenv("PUBLIC_KEY") #type: ignore
except FileNotFoundError:
    print("Please add a .env file to the same directory as this and add BOT_TOKEN and PUBLIC_KEY in the .env file.")
    
    choice: str = input("Would you like me (this program) to help you make the .env file or just raise FileNotFoundError? Options: 1/2: ")

    if choice == "1":
        BOT_TOKEN = input("Enter the BOT_TOKEN: ")
        PUBLIC_KEY = input("Enter the PUBLIC_KEY: ")

        with open(".env", "w") as env:
            env.write(f'BOT_TOKEN="{BOT_TOKEN}"\n')
            env.write(f'PUBLIC_KEY="{PUBLIC_KEY}"')

        print("Made .env file successfully!")
    else:
        print("Exiting program due to FileNotFoundError")
        raise(FileNotFoundError)
    
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
banned_words: list = []
filter = False
banned_wordsPATH = ""
global owner
owner: int = int(config.get("DEFAULT", "owner", fallback="0"))
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
def makeSlashCommand(name: str, description: str, functioon) -> None:
     @bot.tree.command(name=name, description=description)
     async def command(interaction: discord.Interaction):
          await functioon(interaction)

#Check if message was sent be owner
def checkIfOwner(interaction: discord.Interaction) -> bool:
    global owner
    member: discord.member = interaction.user #type: ignore

    if owner != 0:
        owner = interaction.guild.owner.id #type: ignore
        print("Defined owner")

    if member.id == owner: #type: ignore
        return True
    else:
        return False
    
def checkIfSettingsChannel(interaction: discord.Interaction) -> bool:
    if int(config.get("DEFAULT", "settingsChannelID")) == interaction.channel_id:
        return True
    else:
        return False

#For easily replying to messages
async def reply(interaction: discord.Interaction, text: str) -> None:
    if interaction.response.is_done() == False:    
        await interaction.response.send_message(text)
    else:
        await interaction.followup.send(text)

#Making the hello function
async def hello(interaction: discord.Interaction) -> None:
    await reply(interaction, "Hi!")

#Making the dreaded test function
async def test(interaction: discord.Interaction) -> None:
    await reply(interaction, "I can't remove this command or this bot will break!")

#Making the clear function
@bot.tree.command(name="cleanup", description="Cleans up the channel or the number of messages")
async def clear(interaction: discord.Interaction, object: str, val: str) -> None:
    print("Ran this command")
    if checkIfOwner(interaction) == False:
        print("Not owner!")
        return None
    
    if object == "channel":
        if val == "~":
            delChannel = interaction.channel
            # delChannelPerms = interaction.channel.overwrites
            # delChannelName = interaction.channel.name
            # delChannelCatagory = interaction.channel.category

            newChannel = await interaction.channel.clone() #type: ignore
            await delChannel.delete() #type: ignore
        else:
            delChannel = discord.utils.get(interaction.guild.channels, name=val) #type: ignore

            newChannel = await delChannel.clone() #type: ignore
            await delChannel.delete() #type: ignore

            await reply(interaction, f"Cleared {val} channel")

    elif object == "messages":
        try:
            try:
                await interaction.response.defer(ephemeral=True)

                amount: int = int(val)

                if amount <= 0:
                    raise ValueError

                await interaction.channel.purge(limit=int(val)) #type: ignore
                await reply(interaction, "Deleted messages.")
            except ValueError:
                await reply(interaction, "Make sure to put the value as an integer more than 0!")
        except Exception as e:
            print("Maybe the interaction got deleted?")
            print(f"IDK man, take the exception {e}")

    else:
        await reply(interaction, f"No object {object} found!")


#Making the filter function
@bot.tree.command(name="filter", description="Change filter settings")
async def filterfunc(interaction: discord.Interaction, type: str, val: str) -> None:
    global filter
    global banned_words
    global banned_wordsPATH

    owner = interaction.guild.owner.id #type: ignore

    if checkIfSettingsChannel(interaction) == False:
        await reply(interaction, f"Sorry, YOU **NEED** ELEVATED PRIVILEGES FOR THIS COMMAND!!! _whispers {interaction.user.global_name} is an idiot_")
        return None

    if interaction.user == owner or discord.utils.get(interaction.user.roles, name="admin"): #type: ignore
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
            
            banned_words.append(val) #type: ignore

            with open(banned_wordsPATH, 'w') as f:
                json.dump(banned_words, f, indent=4)

        elif type.lower() == "remove":
            if val in banned_words:
                try:
                    banned_words.remove(val) #type: ignore
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
    elif type.lower() != "on" or type.lower() != "off" or type.lower() != "append" or type.lower() != "remove":
        print(f"{interaction.user.name} is stupid as there is no type called {type}")

#Making the Setup Bot function v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v-v
async def setup(interaction: discord.Interaction):    
    global owner
    global botMember
    owner = interaction.guild.owner.id #type: ignore

    botMember = interaction.guild.me #type: ignore

    if int(config.get("DEFAULT", "owner", fallback="0")) != owner:
        config.set("DEFAULT", "owner", str(owner))
        with open("config.properties", "w") as conf:
            config.write(conf)

    if checkIfOwner(interaction) == False:
        await reply(interaction, "YOU do NOT enough permissions to run THIS command!")
        return

    await reply(interaction, "Setting up bot...")


    if discord.utils.get(interaction.guild.channels, name='bot-settings'): #type: ignore
        await interaction.followup.send("Why did you run setup if channel already exists?")
        adminPerms = discord.Permissions(
            permissions=8
        )

        member: discord.member = interaction.user #type: ignore

        #If channel is already made, make the admin role
        adminRoleName = discord.utils.get(interaction.guild.roles, name="admin") #type: ignore
        confAdminRoleID = int(config.get("DEFAULT", "adminRoleID", fallback=0))
        adminRoleID = 0

        if confAdminRoleID != 0:
            try:
                adminRoleID = await interaction.guild.fetch_role(confAdminRoleID) #type: ignore
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
                adminRole = await interaction.guild.create_role(reason=None, name="admin", permissions=adminPerms) #type: ignore
                config.set("DEFAULT", "adminRoleID", str(adminRole.id))
                with open("config.properties", 'w') as cfg:
                    config.write(cfg)
                await interaction.followup.send("Made admin role!")
            else:
                await interaction.followup.send("Please allow me to manage roles!")

        return

    #Make the permissions for the settings channel
    perms = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), #type: ignore
        interaction.guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True) #type: ignore
    }

    #Make the settings channel
    if interaction.channel.permissions_for(botMember).manage_channels == True: #type: ignore
        settingsChannel = await interaction.guild.create_text_channel('bot-settings', overwrites=perms) #type: ignore
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
    adminRoleName = discord.utils.get(interaction.guild.roles, name="admin") #type: ignore
    confAdminRoleID = int(config.get("DEFAULT", "adminRoleID", fallback=0))
    adminRoleID = 0

    if confAdminRoleID != 0:
        try:
            adminRoleID = await interaction.guild.fetch_role(confAdminRoleID) #type: ignore
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
            adminRole = await interaction.guild.create_role(reason=None, name="admin", permissions=adminPerms) #type: ignore
            config.set("DEFAULT", "adminRoleID", str(adminRole.id))
            with open("config.properties", 'w') as cfg:
                config.write(cfg)
            await interaction.followup.send("Made admin role!")
        else:
            await interaction.followup.send("Please allow me to manage roles!")

#end of setup function x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-


#Make the commands
makeSlashCommand("hello", "Say hi!", hello) #type: ignore
makeSlashCommand("test", "I HATE YOU discord_example_app!!!", test) #type: ignore
makeSlashCommand("setupbot", "Set the bot up so that you can destroy it!", setup) #type: ignore

#Main stuff
@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} commands synced")
        print(f"Commands synced are: {synced}")
    except Exception as e:
        print(f"Error occured when syncing commands: {e}")

#Debug
print(banned_words, banned_wordsPATH, filter)
#Run the bot, you can remove this if you like wasting ur time
bot.run(BOT_TOKEN)