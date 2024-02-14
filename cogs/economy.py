import voltage, json, random, pymongo
from voltage.ext import commands
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

with open("json/config.json", "r") as f:
    config = json.load(f)

DBclient = MongoClient(config["MONGOURI"])

db = DBclient["beta"]
userdb = db["users"]
serverdb = db["servers"]

def add_user(user: voltage.User, isbot:bool=False): # long ass fucking function to add users to the database if they dont exist yet. but it works..
  if userdb.find_one({"userid": user.id}):
    return "User already exists."
  id = 1
  for i in userdb.find({}):
    id += 1
  try:
    userdb.insert_one({
        "_id": id,
        "username": user.name,
        "userid": user.id,
        "levels": {
            "xp": 0,
            "level": 1
        },
        "economy": {
            "wallet": 0,
            "bank": 0,
            "data": {
                "inventory": {
                    "bank_loan": 1
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
        "status": {
            "beta": False,
            "familyfriendly": False,
            "premium": False,
            "admin": False,
            "isBot": isbot,
            "banned": False
        }
    })
    return "Added"
  except Exception as e:
    return f"Sorry, An Error Occured!\n\n```\n{e}\n```"


def setup(client) -> commands.Cog:

    eco = commands.Cog("Economy", "Wanna get rich! TOO BAD.")

    @eco.command(description="View your balance.", aliases=["bal", 'b', 'money', 'mybal'], name="balance")
    async def bal(ctx):
        if not userdb.find_one({"userid": ctx.author.id}):
            await ctx.send(
                "You dont have a bank account registered in our database! Would you like me to create one?"
            )
            message = await client.wait_for("message", check=lambda message: message.author.id != client.user.id, timeout=15)
            if any(x in message.content.lower() for x in ["yes", "y", "yea", "yeah", "yup"]):
                return await ctx.send(add_user())
            else:
                return await ctx.send("Oh... Hevermind then!")
        else:
            items = 0
            userdata = userdb.find_one({"userid": ctx.author.id})
            try:
                items = userdata['economy']['data']["inventory"]
                itemlist = {}
                for item in items:
                    itemlist[item] = {
                        "name": item,
                        "amount": items[item]
                    }
                itemstuff = """"""
                for item in itemlist:
                    itemstuff = itemstuff + f"**{item}:** *x{itemlist[item]['amount']}*\n"
                
            except:
                items = []
            if len(items) == 0:
                items = ["You have no items :boohoo:"]
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"""
    **Wallet Balance:** 
    > {userdata['economy']["wallet"]}

    **Bank Balance:**
    > {userdata['wallet']['bank']}

    **Inventory:**
    > {itemstuff}
    """,
            )
            await ctx.send(content="[]()", embed=embed)

    @eco.command(
        description="25% chance to get **nothing** and 75% to get up to 250 coins!"
    )
    async def beg(ctx):
        amount = random.randint(1, 250)
        people = [
            "Jan From Revolt",
            "ks",
            "Cesiyi",
            "Fatal From Revolt",
            "Delta2571",
            "Rick Astley",
            "Shrek",
            "Jesus",
            "Dank Memer",
            "Mr Mosby",
            "Wendy",
            "Barry McKocner",
            "Jordan Peele",
            "Harry Balzac",
            "Kevin Hart",
            "Kim Jong Un",
            "Drake",
            "Kamala Harris",
            "Chris Peanuts",
            "A honey badger",
            "Revolt Dog",
            "Rihanna",
            "Mr. Clean",
            "Satan",
            "ayylien",
            "Selena Gomez",
            "Harry",
            "Elizabeth Warren",
            "Dawn Keebals",
            "Billie Eyelash",
            "Joe Montana",
            "Mr. Ja-cough",
            "Your step-sister",
            "Chuck Norris",
            "Your drunk self",
            "Dr. Phil",
            "Default Jonesy",
            "Cardi B",
            "Sans",
            "Peter Dinklage",
            "Nicki Minaj",
            "Dwight Shrute",
            "Timmy",
            "Demi Lovato",
            "Donald Glover",
            "That fart you've been holding in",
            "Paula Deen",
            "Lady Gaga",
            "Oprah",
            "Elon Musk",
            "Taylor Swift",
            "Melmsie's Beard",
            "Justin Bieber",
            "Toby Turner",
            "That girl whose bed you woke up in last night and you're too afraid to ask her name because you might come off as rude",
            "AirPod Jerk",
            "Your mom",
            "Mike Hoochie",
            "Mike Ock",
            "Spoopy Skelo",
            "Chungus",
            "Flo from Progressive",
            "That tiktok star that shows a little too much butt",
            "Sir Cole Jerkin",
            "T series",
            "Jennifer Lopez",
            "Barack Obama",
            "Cersei Lannister",
            "Carole Baskin",
            "Gordon Ramsay",
            "Thanos",
            "Emilia Clarke",
            "B Simpson",
            "Bongo cat",
            "Keanu Reeves",
            "Mr. Beast",
            "Annoying Ass Clown",
            "That lion from the kids movie that vaguely resembles the story of Jesus Christ",
            "That imposter who was too scared to murder you just because he didn't want to look sus",
            "TikTok Moron",
            "Alotta Fagina",
            "Joe",
        ]
        badline = [
            "be gone",
            "coin.exe has stopped working",
            "I only give money to my mommy",
            "go ask someone else",
            "Well, let's ask another person",
            "I share money with **no-one**",
            "the atm is out of order, sorry",
            "nuh-uh, no coins for **you**",
            "ew no",
            "Back in my day we worked for a living",
            "I would not share with the likes of **you**",
            "honestly why are you even begging, get a job",
            "ew get away",
            "can you not",
            "nah, would rather not feed your gambling addiction",
            "I need my money to buy airpods",
            "ur too stanky",
            "ur not stanky enough",
            "Oh hell nah",
            "stop begging",
            "Sure take this nonexistent coin",
            "no coins for you",
            "there. is. no. coins. for. you.",
            "You get **nothing**",
            "no u",
            "Get a job you hippy",
            "No way, you'll just use it to buy drugs",
            "I give people **nothing**",
            "get the heck/censored out of here, you demon!",
            "I would sooner spend money on taxes than giving you anything",
            "get lost u simp",
            "get out of here, moron, get clapped on!",
            "I don't share with the n-words",
            "pull urself up by your bootstraps scrub",
            "HeRe In AmErIcA wE dOnT dO cOmMuNiSm",
            "Imagine begging in 2022, gofundme is where it is at",
        ]
        percentage = random.randint(1, 100)
        if not userdb.find_one({"userid": ctx.author.id}):
            await ctx.send(
                "You dont have a bank account registered in our database! I can resgister you now, is that okay? *(Yes/No)*"
            )
            message = await client.wait_for("message", check=lambda message: message.author.id != client.user.id, timeout=15)
            if any(x in message.content.lower() for x in ["yes", "y", "yea", "yeah", "yup"]):
                return await ctx.send(add_user())
            else:
                return await ctx.send("Oh... Hevermind then!")
        if percentage > 25:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"{random.choice(people)} gave you `{amount}` coins! Now get a job you bum.",
                color="#00FF00",
            )
            userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": amount}})
            return await ctx.send(content="[]()", embed=embed)
        else:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f'"{random.choice(badline)}" -{random.choice(people)}',
                color="#FF0000",
            )
            return await ctx.send(content="[]()", embed=embed)

    @eco.command(description="Go to work u bum **requires Resume**")
    async def work(ctx):
        amount = random.randint(500, 1000)
        if not userdb.find_one({"userid": ctx.author.id}):
            await ctx.send(
                "You dont have a bank account registered in our database! I can resgister you now, is that okay? *(Yes/No)*"
            )
            message = await client.wait_for("message", check=lambda message: message.author.id != client.user.id, timeout=15)
            if any(x in message.content.lower() for x in ["yes", "y", "yea", "yeah", "yup"]):
                return await ctx.send(add_user())
            else:
                return await ctx.send("Oh... Hevermind then!")
        else:
            userdata = userdb.find_one({"userid": ctx.author.id})
        if userdata['economy']['data']['job'] == "Unemployed":
            return await ctx.send("You're unemployed, get a job u bum!")
        elif "Resume" in userdata['economy']['data']["inventory"]:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"You worked as a {userdata['economy']['data']['job']} and made `{amount}`!",
                color="#00FF00",
            )
            await ctx.send(content="[]()", embed=embed)
            userdb.update_one(
                {"userid": ctx.author.id}, {"$inc": {"economy.wallet": amount}}
            )
        else:
            return await ctx.send(
                "You need a `resume` to work, your not workin' here bub."
            )

    @eco.command(name="leaderboard",aliases=["lb", "ranking"], description="Check out the richest users in all of Mecha!")
    async def leaderboard(ctx):
        lb = []
        count = 0
        for doc in userdb.find().sort([("economy.wallet", pymongo.DESCENDING)]).limit(10):
            count += 1
            lb.append(f"**#{count}** -> {doc['username']}: {doc['economy']['wallet']}")
        await ctx.send(
            '\n'.join(lb)
        )

    @eco.command(
        aliases=["apply", "getjob", "joblist", "gj", "workas", "howjob"]
    )
    async def job(ctx, job=None):
        if job is None:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description="""
**Available Jobs:**

> Teacher
> Twitch Streamer
> Youtuber
> Revolt Mod
> Developer
> Porn Star
        
""",
            )
            return await ctx.send(content="[]()", embed=embed)
        if userdb.find_one({"userid": ctx.author.id}):
            userdata = db.find_one({"userid": ctx.author.id})
        elif not userdb.find_one({"userid": ctx.author.id}):
            await ctx.send(
                "You dont have a bank account registered in our database! I can resgister you now, is that okay? *(Yes/No)*"
            )
            message = await client.wait_for(
                "message", check=lambda message: message.author.id != client.user.id, timeout=15
            )
            
        if "Unemployed" == userdata['economy']['data']["job"]:
            if "Resume" in userdata['economy']['data']["inventory"]:
                if job.lower() in [
                    "teacher",
                    "twitch streamer",
                    "youtuber",
                    "revolt mod",
                    "developer",
                    "porn star",
                ]:
                    if job.lower() == "revolt mod":
                        job = "Revolt Mod"
                    elif job.lower() == "twitch streamer":
                        job = "Twitch Streamer"
                    elif job.lower() == "porn star":
                        job = "Porn Star"
                    userdb.update_one(
                        {"userid": ctx.author.id},
                        {
                            "$set": {
                                "economy.data.job": job
                            }
                        }
                    )
                    return await ctx.send(
                        f"You are now working as a `{job.capitalize()}`!"
                    )
            elif "Resume" not in userdata['economy']['data']["inventory"]:
                return await ctx.send("You need a resume to get a job! Buy a resume!")
        else:
            return await ctx.send("You already have a job!")

    @eco.command(aliases=["sh", "buy"])
    async def shop(ctx, item=None):
        if item is None:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description="""
**Available items for sale:**
  
Playboy Magazine - `1000`
Resume - `250`
        
""",
            )
            return await ctx.send(content="[]()", embed=embed)
        else:
            userdata = userdb.find_one({"userid": ctx.author.id})
            if item.lower() in [
                "r",
                "resume",
                "application",
                "jobform",
                "resum",
                "res",
                "form",
            ]:
                if userdata['economy']["wallet"] < 250:
                    return await ctx.send("ur too poor, nerd.")
                else:
                    if "Resume" in userdata['economy']['data']["inventory"]:
                        return await ctx.send(
                            "You already have a resume! You don't need another!"
                        )
                    userdb.update_one(
                        {"userid": ctx.author.id}, {"$inc": {"wallet": -250}, "$push": {"inventory": {"Resume":1}}}
                    )
                    return await ctx.send("You bought a `resume` for `250` coins!")
            if item.lower() in [
                "pb",
                "playboi",
                "playboy",
                "magazine",
                "magasine",
                "playb",
                "pboy",
            ]:
                if userdata['economy']["wallet"] < 1000:
                    return await ctx.send("ur too poor, nerd.")
                else:
                    if "Playboy" in userdata['economy']['data']["inventory"]:
                        return await ctx.send(
                            "You already have a magazine! You don't need another!"
                        )
                    userdb.update_one(
                        {"userid": ctx.author.id}, {"$inc": {"wallet": -1000}, "$push": {"inventory": {"Playboy":1}}}
                    )
                    return await ctx.send(
                        "You bought a `Playboy Magazine` for `1000` coins!"
                    )

    return eco