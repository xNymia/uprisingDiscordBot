from pymongo import MongoClient, errors

class databaseManager:
    def __init__(self):
        try:
            self.conn = MongoClient('mongodb://localhost')
        except errors as e:
            print(f"Error connecting to database: {e}")
            exit(1)

        self.DB = self.conn.uprisingDatabase
        self.guildTracking = self.DB.guildTracking
        self.discordUsers = self.DB.discordUsers


    def guildTrackingHandler(self, guild) -> None:
        [self.guildTracking.insert_one(x) for x in guild]

    def doesUserExist(self, id, albionid) -> bool:
        if (self.discordUsers.find_one({"discordId":id}) or self.discordUsers.find_one({"albionID":albionid})):
            return True
        return False

    def getAllMembers(self):
        return self.discordUsers.find({})

    def insertUser(self, user: str) -> bool:
        self.discordUsers.insert_one(user)
        return True

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()