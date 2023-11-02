from typing import Any, Coroutine
import discord
from discord import app_commands
from discord.ext import commands, tasks
from pprint import pprint
from datetime import time, timezone, datetime
from utilities import getGuildMembers
from icecream import ic

class autoTasks(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.db

        
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.guildDBUpdate.start()

    # Pull guild from Albion API
    @tasks.loop(time=time(0,0,0,0, tzinfo=timezone.utc))
    async def guildDBUpdate(self) -> None:
        guildMembers = getGuildMembers()
        for x in guildMembers:
            x['timestamp'] = str(datetime.today().date())
        self.db.guildTrackingHandler(guildMembers)
        await self.bot.adminLog("Updated Guild Member Database")


    @tasks.loop( time=[time(17,0,0,0, tzinfo=timezone.utc), time(20,0,0,0, tzinfo=timezone.utc)])
    async def ctaannouncer(self) -> None:
        message= f"{self.bot.guilds[0].get_role(938924221554389014).mention}\n\nCTA is approaching - This is likely **mandatory** content. Time to wind down what you are doing and get ready to go to the K I N G M A K E R i.\n\nAttendance will be taken."
        await self.bot.guilds[0].get_channel(1114795409504739380).send(message)






async def setup(bot):
    await bot.add_cog(autoTasks(bot))
