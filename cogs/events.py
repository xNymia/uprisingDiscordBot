from typing import Any, Coroutine, List, Optional
import discord
from discord import app_commands
from discord.components import SelectOption
from discord.ext import commands, tasks
from pprint import pprint
from datetime import time, timezone, datetime

from discord.utils import MISSING
from utilities import getGuildMembers
from icecream import ic

class albionEvents(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.db




    @app_commands.command(description="Create An event")
    @app_commands.checks.has_role("Officers")
    async def create_event(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # create modal to select type of content
        # create new modal to get event details

        class Select(discord.ui.Select):
            def __init__(self) -> None:
                options = [
                    discord.SelectOption(label="option 1", description="option 1 description")
                ]
                super().__init__(placeholder='Select an option', min_values=1, max_values=1, options=options,)






        class SelectView(discord.ui.View):
            def __init__(self, *, timeout: float | None = 180):
                super().__init__(timeout=timeout)
                self.add_item(Select())


        await interaction.followup.send("options!", view=SelectView())


async def setup(bot):
    await bot.add_cog(albionEvents(bot))
