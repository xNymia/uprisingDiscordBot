from typing import Optional
import discord
from discord import app_commands, Embed
from discord.ext import commands
from utilities import getPlayer, getParticipation, createParticipationDataFrame, welcomeMessage, getGuildMembers, getPlayerByID, isFriend, purgeMember
from pprint import pprint
from datetime import datetime, timezone
import requests, json
import pandas as pd
from icecream import ic
import dataframe_image as dfi

STATIC_ALBION_DATA = {
    "uprisingGuildID" : "kEZ3m2YoR8OFHLSNRttjjw",
    "allianceID" : "0jtSqRJJTomBFZ6gR6oOhA",
    "ZVZ_BUILDS_IMAGE" : "https://media.discordapp.net/attachments/1166384778761752597/1169094432830804019/ZvZ_Build_Kingmaker_2.png"
}
DISCORD_MEMBERS_ROLE = 938924221554389014
DISCORD_ALLIANCE_ROLE = 1162315056562847845

class botCommands(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.db

    @app_commands.command(description="A test command")
    @app_commands.checks.has_role("Officers")
    async def hello(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(f'Hi, {interaction.user.mention} 2')


    @app_commands.command(description="Check Participation")
    @app_commands.choices(choices=[
        app_commands.Choice(name='General', value='general'),
        app_commands.Choice(name='CTA', value='cta'),
    ])
    @app_commands.checks.has_role("Officers")
    async def particiption(self, interaction: discord.Interaction, choices: app_commands.Choice[str]) -> None:

        await interaction.response.defer()

        typePlayerCount = {
            'general' : 2,
            'cta' : 5
        }
        result = getParticipation(14, typePlayerCount[choices.value])
        df = createParticipationDataFrame(result)
        dfi.export(df, 'pap.png')
        image = discord.File('pap.png')

        guildMembers = [x['albionIGN'] for x in self.db.getAllMembers()]
        partMembers = [x['name'] for x in result]
        missingPlayers = [x for x in guildMembers if x not in partMembers]

        embed = discord.Embed(
            title=f"Users not seen in this content",
            color=discord.Color.red()
        )
        embed.add_field(name="Players", value=", ".join(missingPlayers), inline=False)

        await interaction.followup.send(f'Participation - last 14 days - {choices.value}', file=image, embed=embed)


    @app_commands.command(description="Manually remove a member with IGN")
    @app_commands.checks.has_role("Officers")
    async def removeuser(self, interaction: discord.Interaction, ign: str) -> None:
        result = purgeMember(ign, self.db.discordUsers, "albionIGN")
        if result:
            await interaction.response.send_message("Member Purged")
            return
        await interaction.response.send_message("Purge Failed")

    @app_commands.command(description="Register with The Uprising guild bot")
    @app_commands.describe(nick="Your Albion Ingame Name")
    async def register(self, interaction: discord.Interaction, nick: str) -> str:

        if interaction.channel_id != 1163806135439065140:
            await interaction.response.send_message("This command can only be used in the 'Registration' Channel", ephemeral=True)
            return

        if not nick:
            await interaction.response.send_message("Youve gotta add a nickname dipshit")
            return

        await interaction.response.defer()

        playerData = getPlayer(nick)
        
        if not playerData:
            await interaction.followup.send(f"You probably spelt that wrong, are you sure {nick} is right?")
            return

        if self.db.doesUserExist(str(interaction.user.id), playerData["Id"]):
            await interaction.followup.send('User already exists, contact leadership')
            return

        userData = {
            "discordId" : str(interaction.user.id),
            "albionIGN" : playerData["Name"],
            "albionID" : playerData["Id"],
            "albionGuild" : playerData['GuildName'],
            "guildID" : playerData["GuildId"],
            "createTime" : datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "updateTime" : datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            "warnings": {
                "first": {
                    "comment": "",
                    "date": ""
                },
                "second": {
                    "comment": "",
                    "date": ""
                }
            }
        }

        async def handle_registration(interaction, role_name):
            
            await self.assignrole(interaction.user, role_name)
            await interaction.user.remove_roles(interaction.guild.get_role(1168180603531825233))

            embed = Embed()
            embed.title = f'User {interaction.user.name} Registration'
            embed.description = 'A new user was registered with the bot' 
            embed.color = discord.Color.red()
            embed.set_author(name='TheUprising')
            embed.add_field(name="Discord ID", value=userData["discordId"], inline=False)
            embed.add_field(name="Albion Name", value=userData["albionIGN"], inline=False)
            embed.add_field(name="Albion Guild", value=userData["albionGuild"], inline=False)

            self.db.insertUser(userData)

            try:
                await interaction.user.edit(nick=userData["albionIGN"])
            except Exception as e:
                ic(e)
                pass
            
            try:
                await interaction.followup.send(embed=embed)
            except Exception as e:
                ic(e)

        if playerData['GuildId'] == STATIC_ALBION_DATA["uprisingGuildID"]:
            await handle_registration(interaction, DISCORD_MEMBERS_ROLE)
            return

        if playerData['AllianceId'] == STATIC_ALBION_DATA["allianceID"]:
            await interaction.followup.send('Alliance Registration is currently disabled')
            #await handle_registration(interaction, DISCORD_ALLIANCE_ROLE)
            return

        # else not member
        await interaction.followup.send('You do not appear to be in guild or alliance.')
        await self.bot.adminLog(f'**WARNING** - {interaction.user} tried to register with nickname {nick} but arent in the alliance or guild')


    @app_commands.command(description="Welcome a new member")
    async def welcome(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(welcomeMessage(interaction=interaction))
    
    async def assignrole(self, user, role):
        await user.add_roles(self.bot.guilds[0].get_role(role))


    @app_commands.command(description="Newbie finder")
    @app_commands.checks.has_role("Officers")
    async def findthenewbies(self, interaction: discord.Interaction) -> None:

        await interaction.response.defer()

        gameGuildMembers = getGuildMembers()
        for member in gameGuildMembers:

            pve = member['LifetimeStatistics']['PvE']['Total']
            pvp = member['KillFame']

            if pve > 30000000:
                continue
            if pvp > 5000000:
                continue

            userDB = self.db.discordUsers.find_one({"albionID":member['Id']})
            if userDB:
                discordID = self.bot.guilds[0].get_member(int(userDB['discordId']))
            else:
                await self.bot.adminLog(f"{member['Name']} not registered")
                continue

            await self.bot.adminLog(f"{member['Name']} with {pvp:,d} PvP Fame and {pve:,d} PvE Fame - Discord User: {discordID.mention}")
            await discordID.add_roles(self.bot.guilds[0].get_role(1154086002277765171))

        await interaction.followup.send("Newbies Identified - Added Tag")


    @app_commands.command(description="check memebers")
    @app_commands.checks.has_role("Officers")
    async def checkmembers(self, interaction: discord.Interaction) -> None:

        if interaction.channel.id not in [1114796834167201853,1116965083914969128]:
            await interaction.response.send_message("Please do this in an officer channel")
            return

        await interaction.response.defer()

        gameGuildMembers = getGuildMembers()
        discordRoleMembers = self.bot.guilds[0].get_role(DISCORD_MEMBERS_ROLE).members
        everyoneRole = self.bot.guilds[0].get_role(935404714995118080)

        def isRegisteredWithBot(type: str, id: str|int) -> bool|tuple:
            registrationData = self.db.discordUsers.find_one({type:str(id)})
            if registrationData:
                return True, registrationData
            return False

        def guildMemberInDiscord(discordID: int):
            if self.bot.guilds[0].get_member(discordID):
                return True
            return False

        def isDiscordMemberInGuild(albionID: str):
            for member in gameGuildMembers:
                if member['Id'] == albionID:
                    return True
                
            return False

        ingameNoRegister=[]
        ingameNoDiscord=[]
        discordMemberNoRegister=[]
        discordMemberNoGuild=[]

        for member in gameGuildMembers:
            regData = isRegisteredWithBot("albionID", member['Id'])
            if not regData:
                ingameNoRegister.append(member['Name'])
                continue
                # User is in guild but not registered in discord
            if not guildMemberInDiscord(int(regData[1]['discordId'])):
                ingameNoDiscord(regData[1]['albionIGN'])
                continue
                # User is registered with the bot but not in discord, somehow.

        for member in discordRoleMembers:
            if isFriend(member.id):
                continue

            regData = isRegisteredWithBot("discordId", member.id)
            if not regData:
                discordMemberNoRegister.append(member)
                continue
                # User is in discord with member tag but not registered with the bot
            if not isDiscordMemberInGuild(regData[1]['albionID']):
                discordMemberNoGuild.append(member)
                continue
                # User is in discord with member tag but not in guild

        embed = Embed()
        embed.title = f'User Report'
        embed.color = discord.Color.red()
        embed.add_field(name="Discord Members Not in Guild - **SPY LIST**", value=', '.join([member.mention for member in discordMemberNoGuild]), inline=False)
        embed.add_field(name="Discord Members Not Registered - **PURGE**", value=', '.join([member.mention for member in discordMemberNoRegister]), inline=False)
        embed.add_field(name="Ingame Members Not Registered", value=', '.join(ingameNoRegister), inline=False)
        embed.add_field(name="Ingame Members registered, but not in discord.... somehow", value=', '.join(ingameNoDiscord), inline=False)
   

        async def purge(memberList: list, interaction: discord.Interaction) -> None:
            for member in memberList:
                result = await member.edit(roles=[everyoneRole])
                if result:
                    await interaction.channel.send(f'{member.name or member.nick or member.global_name} has been purged')
                else: 
                    await interaction.channel.send(f'{member.name or member.nick or member.global_name} purge failed')


        class Buttons(discord.ui.View):
            @discord.ui.button(label='PURGE', style=discord.ButtonStyle.danger)
            async def purge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                button.disabled=True
                await interaction.followup.edit_message(view=self, message_id=interaction.message.id)
                await purge(discordMemberNoRegister, interaction)
                await interaction.followup.send(content="Purge Complete")

        await interaction.followup.send(embed=embed, view=Buttons())

    @app_commands.command(description="Show Alliance ZvZ Builds")
    async def zvzbuilds(self, interaction: discord.Interaction):
        await interaction.response.send_message(STATIC_ALBION_DATA['ZVZ_BUILDS_IMAGE'])






async def setup(bot):
    await bot.add_cog(botCommands(bot))



