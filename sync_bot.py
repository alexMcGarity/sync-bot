from typing import List
import discord
import csv
import logging
import config

TOKEN = config.TOKEN

#role that the bot will assign
role_name = "Registered Club Member"

#intents
intents = discord.Intents.default()
intents.presences = False
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
nameList: List[str] = []
#reads the csv file and returns a list of Registered Club Members
def get_names():
    with open('./OrganizationRoster.csv', 'r+') as csvfile:
        #skip 3 lines
        for i in range(3):
            next(csvfile)
        #read the csv file
        reader = csv.DictReader(csvfile)
        names = list()
        for row in reader:
            names.append(row["First Name"]+" "+row["Last Name"])
        csvfile.close()
        return names

#prints to console if the bot is ready
@client.event
async def on_ready():
    #role that the bot will assign
    global role_name
    role_name = "Registered Club Member"
    print(f'We have logged in as {client.user}')


#bot will respond to messages from a user with the manage_roles permission with a csv file attachment
@client.event
async def on_message(message: discord.Message):
    global role_name
    if message.author == client.user:
        return
    if message.author.guild_permissions.manage_roles and message.attachments[0].content_type == "text/csv; charset=utf-8":
        guild = client.get_guild(message.guild.id)
        guild_members = guild.members
        role = discord.utils.get(guild.roles, name=role_name)
        await message.channel.send(f'{message.author.mention} has uploaded a CSV file.')
        await message.attachments[0].save(message.attachments[0].filename)
        #delete the message
        await message.delete()
        #list of people with the role
        WithRole = []
        for user in guild_members:
            if role in user.roles:
                WithRole.append(user)
        #build list of people who have the role and have a correct name
        formatted_users = []
        for user in WithRole:
            display_name = str(user.display_name)
            if len(display_name.split())<2:
                pass
            else:
                formatted_users.append(display_name.split()[0] + " " + display_name.split()[1][0:1])
        lowercase_users = [x.lower() for x in formatted_users]
        #list of people in the csv file adjusted for first name last initial format
        csvnames = get_names()

        #list of people in the csv file that are not in the role
        NotInRole = []
        for name in csvnames:
            if name.split()[0].lower() + " " + name.split()[1][0:1].lower() in lowercase_users:
                pass
            else:
                NotInRole.append(name)

        #puts the people in the csv file that are not in the role into the role
        for name in NotInRole:
            for user in guild_members:
                if len(user.display_name.split(' '))>1 and name.split()[0].lower() + " " + name.split()[1][0:1].lower() == user.display_name.split(' ')[0].lower() + " " + user.display_name.split(' ')[1][0:1].lower():
                    await user.add_roles(discord.utils.get(guild.roles, name=role_name))
                    await message.channel.send(f'{user.mention} has been added to the {role_name} role.')
                    NotInRole.remove(name)
                    WithRole.append(user)
        await message.channel.send(f"Sync Bot has finished adding users to the {role_name} role.")
        await message.channel.send(f"**To get added to the {role_name} role please format your server display name to be firstname, space, last initial as it appears in OrgLink.**")
        await message.channel.send("names in the csv that are not in the discord or were not formatted according to the csv:")

        #prints the names in the csv file that are not in the discord or were not formatted according to the csv in groups of 20
        for i in range(0, len(NotInRole), 20):
            await message.channel.send(NotInRole[i:i+20])
        #creates new list of names from csvnames that is lowercase
        lowercase_csvnames = [x.split(" ")[0].lower()+" "+x.split(" ")[1][0:1].lower() for x in csvnames]
        #removes the role from people who are in the role but not in the csv file
        for user in WithRole:
            display_name = str(user.display_name)
            if len(display_name.split(' '))<2 or display_name.split(' ')[0].lower()+ " " + display_name.split(' ')[1][0:1].lower() not in lowercase_csvnames:
                await user.remove_roles(role)
                await message.channel.send(f'{user.mention} has been removed from the {role_name} role.')

client.run(TOKEN, log_handler=handler)