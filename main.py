import discord
from pprint import pprint
from discord import app_commands
from discord.ext import tasks, commands
from database import databaseManager
from dotenv import dotenv_values
from icecream import ic
from utilities import purgeMember
import os
import logging

logHandler = logging.getLogger('discord')
secrets = dotenv_values(".env")
LOG_CHANNEL = 1116965083914969128
TOKEN = secrets["TOKEN"]
GUILDID = discord.Object(id=935404714995118080)
INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.guilds = True
INTENTS.message_content = True
CURRENT_COGS = []

class botClient(commands.Bot):

    def __init__(self,*, command_prefix: str, intents: discord.Intents):
        super().__init__(command_prefix, intents=INTENTS)     
        self.db = databaseManager()
        

    async def setup_hook(self):
        await self.loadCogs()
        await self.tree.sync(guild=None)
        self.tree.copy_global_to(guild=GUILDID)



    async def loadCogs(self) -> None:
        for filename in os.listdir(f"./cogs/."):
            if filename.endswith(".py"):
                await self.load_extension(f'cogs.{filename[:-3]}')
                logHandler.info(f'Loaded Cog: {filename[:-3]}')


    async def adminLog(self, message: str) -> None:      
        await self.get_channel(LOG_CHANNEL).send(message)
   
    
# Instanciation
uprisingBot = botClient(command_prefix='$', intents=INTENTS)


# Ready Trigger
@uprisingBot.event
async def on_ready() -> None:
    logHandler.info(f'Logged in as {uprisingBot.user} (ID: {uprisingBot.user.id})')
    print('------')

@uprisingBot.event
async def on_interaction(interaction) -> None:
    try:
        logHandler.info(f'{interaction.user} ran command {interaction.command.name}')
    except AttributeError:
        logHandler.info(f'Button was pressed!')

@uprisingBot.event
async def on_member_join(member):
    await member.add_roles(member.guild.get_role(1168180603531825233))
    logHandler.info(f'Added Lurker Role to {member.nick or member.name or member.global_name}')

@uprisingBot.event
async def on_member_remove(member):
    memberRole = member.guild.get_role(938924221554389014)
    if memberRole in member.roles:
        result = await purgeMember(member.id, uprisingBot.db.discordUsers, "discordId")
        if result:
            logHandler.info(f"{member.id} left server with member role - Purged DB entry")
        else:
            logHandler.error(f"{member.name or member.nick or member.global_name} Database Purge Failed")


# Reload Cog Command
@uprisingBot.tree.command()
@app_commands.checks.has_role("Officers")
@app_commands.choices(cog=[
    app_commands.Choice(name='Commands', value='commands'),
    app_commands.Choice(name='Tasks', value='tasks'),
    app_commands.Choice(name='Events', value='events'),
])
async def reload(interaction: discord.Interaction, cog: app_commands.Choice[str]) -> None:

    await uprisingBot.reload_extension(f'cogs.{cog.value}')
    await interaction.response.send_message(f'Reloading cog: {cog.value}', ephemeral=True)


try:
    uprisingBot.run(TOKEN)
finally:
    #uprisingBot.db.discordUsers.delete_many({"discordId": "98075883549519872"})
    uprisingBot.db.close()