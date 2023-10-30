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








async def setup(bot):
    await bot.add_cog(autoTasks(bot))
