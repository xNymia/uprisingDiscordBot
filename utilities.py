import requests
import json
import pandas as pd
from icecream import ic

def getGuildMembers() -> list:
    uprisingGuildID = "kEZ3m2YoR8OFHLSNRttjjw"
    url = f"https://gameinfo.albiononline.com/api/gameinfo/guilds/{uprisingGuildID}/members"
    response = json.loads(requests.get(url).text)
    return response

def getPlayer(nick: str) -> dict:
    url = f'https://gameinfo.albiononline.com/api/gameinfo/search?q={nick}'
    players = json.loads(requests.get(url).text)['players']
    for player in players:
        if player['KillFame'] == 0:
            continue
        else:
            return player

def getPlayerByID(id: int) -> dict:
    url = f'https://gameinfo.albiononline.com/api/gameinfo/players/{id}'
    return json.loads(requests.get(url).text)

def getParticipation(interval, min) -> list:
    url = f"https://api.albionbattles.com/player?guildSearch=The-Uprising&interval={interval}&minGP={min}"
    response = json.loads(requests.get(url).text)
    return response

def createParticipationDataFrame(data) -> object:
    df = pd.DataFrame(data)
    df.set_index('name', inplace=True)
    df.drop('itemsUsed', axis=1, inplace=True)
    df.drop('totalDamage', axis=1, inplace=True)
    df.drop('totalHealing', axis=1, inplace=True)
    df.drop('totalFame', axis=1, inplace=True)
    df.drop('battleID', axis=1, inplace=True)
    df.drop('totalRange', axis=1, inplace=True)
    df.drop('totalSupport', axis=1, inplace=True)
    df.drop('totalTank', axis=1, inplace=True)
    df.drop('totalHealer', axis=1, inplace=True)
    df.drop('totalMelee', axis=1, inplace=True)
    df.drop('totalBattleMount', axis=1, inplace=True)
    df.drop('totalKillContribution', axis=1, inplace=True)


    df.rename(columns={
        'battleNumber':'Battle Participation',
        'totalDeath':'Total Deaths',
        'totalKills':'Total Kills',
        'averageIP':'Average IP',
        'lastActivity':'Last Activity',
    }, inplace=True)

    df.sort_values(by=['Battle Participation'], inplace=True, ascending=False)
    return df

def welcomeMessage(interaction) -> str:
    return f'''
Welcome to The Uprising!

Now that you have been accepted there are a few steps you need to take:

- Read the {interaction.guild.get_channel(938926115790131210).mention} again
- Go to the {interaction.guild.get_channel(1163806135439065140).mention} channel and use the `/register` command
 - After registering you can change your discord handle to whatever you want
- Join the alliance discord: https://discord.gg/4uwEBPBbEa and request permissions in the request channel
- Start to participate in guild content!

        '''

def isFriend(id) -> bool:
    friends = [
        136455855817228288, # Freeze
        376049408522977281, # Asilith
        146702284510724096, # Hex
        534923622934904842, # Gwen
        207365417830711296, # rachaelneco
        1017670331235831860, # Tribby
        918742931584741457, # Frosty
    ]

    if id in friends: 
        return True
    else:
        return False
    
def purgeMember(member, discordUsers, type) -> str:
    result = discordUsers.delete_one({
            type : str(member)
        }
    )
    if result.acknowledged:
        return True
    else: 
        return False

    

    
