import asyncio
import json
import time
import random

import motor
import pymongo
import revolt

from motor.motor_asyncio import AsyncIOMotorClient

with open("json/config.json", "r") as f:
    config = json.load(f)


class Database:
    def __init__(self, client):
        self.client = client

        self.db_client = AsyncIOMotorClient(config['MONGOURI'])
        self.db = self.db_client['beta']
        self.userdb = self.db['users']
        self.serverdb = self.db['servers']
        self.settingsdb = self.db['settings']
        self.cooldowns = self.db['cooldowns']

    async def server_update(self):
        _id = self.serverdb.count_documents({})
        for server in self.client.servers:
            if not self.serverdb.find_one({"serverid": server.id}):
                icon = server.icon.url if server.icon else None
                banner = server.banner.url if server.banner else None
                description = server.description

                serverdb.insert_one(
                    {
                        "_id": _id,
                        "serverid": server.id,
                        "name": server.name,
                        "owner": {
                            "id": server.owner.id,
                            "name": server.owner.name,
                            "discriminator": server.owner.discriminator
                        },
                        "created_at": f"{server.created_at}",
                        "meta": {
                            "description": description,
                            "banner": banner,
                            "icon": icon,
                        },
                        "member_count": len(server.members),
                        "role_count": len(server.roles),
                        "channel_count": len(server.channel_ids),
                        "category_count": len(server.categories)
                    }
                )

        print(f"Updated {_id} servers!")

    async def upd(self):
        doc = await self.userdb.find({}).to_list(length=None)
        for i in doc:
            try:
                if i['economy']['data']['inventory']['bank_loan']:
                    bank = i['economy']['data']['inventory']['bank_loan']
                    await self.userdb.update_one(
                        {'userid': i['userid']}, {'$unset': {'economy.data.inventory.bank_loan': 1}}
                    )
                    if bank < 0:
                        bank = 0
                        print("Bank loan capped at 10m")
                    await self.userdb.update_one(
                        {'userid': i['userid']}, {'$set': {'economy.data.inventory.Bank Loan': bank}}
                    )
                    print(f"Added {bank} bank notes to {i['username']}")
            except KeyError:
                pass

    async def cheater_beater(self):
        while True:
            doc = await self.userdb.find({}).to_list(length=None)
            for i in doc:
                try:
                    if i['economy']['bank'] > 200000000000 or i['economy']['wallet'] > 200000000000:
                        await self.userdb.update_one({'userid': i['userid']}, {'$set': {'economy.bank': 1000000}})
                        await self.userdb.update_one({'userid': i['userid']}, {'$set': {'economy.wallet': 0}})
                        print(f"{i['username']} is a stinkin' cheater, and has been reset as a result!")
                except Exception:
                    pass

            await asyncio.sleep(60 * 60)

    async def update_level(self, user: revolt.User):
        if await self.userdb.find_one({'userid': user.id}):
            user_data = await self.userdb.find_one({'userid': user.id})
            lvl = user_data['levels']['level']
            xp = user_data['levels']['xp']
            if 0 >= (5 * (lvl ^ 2) + (50 * lvl) + 100 - xp):
                amt = random.randint(0, 10000)
                o = 1
                for i in user_data['notifications']['inbox']:
                    o += 1
                await self.userdb.bulk_write(
                    [
                        pymongo.UpdateOne({'userid': user.id}, {'$inc': {'levels.level': 1}}),
                        pymongo.UpdateOne({'userid': user.id}, {'$set': {'levels.xp': 0}}),
                        pymongo.UpdateOne({'userid': user.id}, {'$inc': {'levels.totalxp': xp}}),
                        pymongo.UpdateOne({'userid': user.id}, {'$inc': {'economy.bank': 100 * lvl + amt}}),
                        pymongo.UpdateOne(
                            {'userid': user.id}, {
                                '$set': {
                                    f'notifications.inbox.{i}': {
                                        "message": f"Congratulations on leveling up to level {lvl + 1}!\nYou've received {100 * lvl + amt} coins as a reward!",
                                        "date": time.time(),
                                        "title": "Level Up!",
                                        "type": "level",
                                        "read": False
                                    }
                                }
                            }
                        ),
                    ]
                )
            return False
        else:
            return False

    async def check_xp(self, user: revolt.User):
        user_data = await self.userdb.find_one({'userid': user.id})
        if user_data:
            return user_data['levels']['xp']
        else:
            return 0

    async def add_user(
            self, user: revolt.User, isbot: bool = False
            ):  # long ass fucking function to add users to the database if they dont exist yet. but it works..
        if await self.userdb.find_one({"userid": user.id}):
            return "User already exists."

        try:
            await self.userdb.insert_one(
                {
                    "_id": (await self.userdb.count_documents({}) + 1),
                    "username": user.name,
                    "userid": user.id,
                    "levels": {
                        "xp": 0,
                        "level": 0,
                        "totalxp": 0,
                        "lastmessage": time.time()
                    },
                    "prefixes": ["m!"],
                    "economy": {
                        "wallet": 0,
                        "bank": 0,
                        "total": 0,
                        "daily": time.time(),
                        "monthly": time.time(),
                        "data": {
                            "inventory": {
                                "Bank Loan": 1
                            },
                            "job": "unemployed"
                        },
                        "buffs": {
                            "beginner_luck": 100
                        },
                        "debuffs": {},
                        "achievements": {
                            "early_user": True,
                            "beta_tester": True
                        }
                    },
                    "notifications": {
                        "inbox": {
                            "1": {
                                "message": f"Welcome to Mecha, {user.name}!\nTo get started, type `m!help` in this server to get started!",
                                "date": time.time(),
                                "title": "Welcome To Mecha!",
                                "type": "bot",
                                "read": False
                            }
                        }
                    },
                    "status": {
                        "developer": False,
                        "admin": False,
                        "moderator": False,
                        "friend": False,
                        "premium": False,
                        "bug": False,
                        "beta": False,
                        "familyfriendly": False,
                        "isBot": isbot,
                        "banned": False,
                        "afk": {

                        }
                    }
                }
            )
            return "Added"
        except Exception as e:
            return f"Sorry, An Error Occurred!\n\n```\n{e}\n```"

    async def update_stats(self, users, servers):
        if self.settingsdb.find_one({"_id": 1}):
            await self.settingsdb.update_one(
                {
                    "_id": 1,
                    "setting": "stats"
                },
                {
                    "$set": {
                        "users": users,
                        "servers": servers
                    }
                }
            )
        else:
            await self.settingsdb.insert_one(
                {
                    "_id": 1,
                    "setting": "stats",
                    "users": users,
                    "servers": servers
                }
            )

    async def ping_db(self):  # ping the database; never gonna use this, might need it, add it.
        try:
            await self.db_client.admin.command('ping')
            return "[+] Pinged your deployment. Successfully connected to MongoDB!"
        except Exception as e:
            return f"[-] ERROR!\n\n\n{e}"

    async def get_user(self, user: revolt.User):
        if user := (await self.userdb.find_one({"userid": user.id})):
            return user

    async def give_xp(self, user: revolt.User, xp: int):
        await self.userdb.update_one(
            {"userid": user.id},
            {"$inc": {"levels.xp": xp}}
        )

    async def get_prefix(self, message):
        user_data = await self.get_user(message.author)
        if user_data is not None:
            return user_data['prefixes']
        else:
            return ['m!']

    # USE THIS IF YOU NEED TO ADD NEW KEYS TO THE DATABASE
    async def do(self):
        while True:
            curs = self.userdb.find()
            async for user in curs:
                try:
                    ud = self.client.get_user(user['userid'])
                    if ud is None:
                        continue

                    await self.userdb.update_one(
                        {'userid': user['userid']},
                        {
                            '$set': {
                                "username": f"{ud.name}#{ud.discriminator}"
                            }
                        }
                    )
                except Exception:
                    pass

            await asyncio.sleep(60 * 60)

    async def update(self):  # This function can be replaced
        print("Started Update Loop")
        while True:
            documents = self.userdb.find()
            async for i in documents:
                total = int(i["economy"]["wallet"])
                total += int(i["economy"]["bank"])
                userdb.update_many(
                    {
                        "_id": i["_id"]
                    },
                    {
                        "$set": {
                            "economy.total": total
                        }
                    }
                )
            await asyncio.sleep(120)  # sleep for 2 minutes

    async def afk_check(self, message: revolt.Message):
        try:
            user_data = await self.get_user(message.author)
            if user_data:
                if user_data['status']['afk'][message.server.id]['afk']:
                    if user_data['status']['afk'][message.server.id]['lastseen'] + 2 < int(time.time()):
                        await self.userdb.update_one(
                            {"userid": message.author.id},
                            {"$set": {"status.afk.{}".format(message.server.id): {"afk": False}}}
                        )
                        embed = revolt.SendableEmbed(
                            title="AFK!",
                            description=f"Welcome back, {message.author.mention}!\nI've removed your AFK status!",
                            colour="#00ff00",
                            icon_url=message.author.avatar.url if message.author.avatar else None
                        )
                        msg = await message.reply(embed=embed)
                        await asyncio.sleep(5)
                        await msg.delete()
                    else:
                        return "TooEarly"
                else:
                    return "NotAfk"
            else:
                return "DoesntExist"
        except Exception:
            return

