import voltage, json, random, pymongo, time, datetime, asyncio, motor
import motor.motor_asyncio
from functools import wraps
from voltage.ext import commands
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

sep = "\n"

def strfdelta(tdelta, fmt):
    d = {"days": tdelta.days}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)

def limiter(cooldown: int, *, on_ratelimited = None, key = None):
  cooldowns = {}
  getter = key or (lambda ctx, *_1, **_2: ctx.author.id)
  def wrapper(callback):
    @wraps(callback)
    async def wrapped(ctx, *args, **kwargs):
      k = getter(ctx, *args, **kwargs)
      v = (time.time() - cooldowns.get(k, 0))
      if v < cooldown and 0 > v:
        if on_ratelimited:
          return await on_ratelimited(ctx, -v, *args, **kwargs)
        return
      cooldowns[k] = time.time() + cooldown
      return await callback(ctx, *args, **kwargs)
    return wrapped
  return wrapper 

with open("json/config.json", "r") as f:
    config = json.load(f)

DBclient = motor.motor_asyncio.AsyncIOMotorClient(config['MONGOURI'])

db = DBclient["beta"]
userdb = db["users"]
serverdb = db["servers"]

joblist = [
    "Professional Couch Potato",
    "Chief Meme Officer",
    "Wizard of Light Bulb Moments",
    "Underwater Basket Weaver",
    "Pet Psychic",
    "Digital Overlord",
    "Head Cheese Maker",
    "Rogue Pizza Taster",
    "Freelance Scapegoat",
    "Beer Sommelier",
    "Crayon Evangelist",
    "Director of First Impressions",
    "Space Lawyer",
    "Extreme Unicyclist"
]
short_forms = [job[:3].lower() for job in joblist]

def match_job_to_short_form(job_name, short_forms, joblist):
    """
    Return the full job name that corresponds to the given short form.

    :param job_name: The short form of a job.
    :param short_forms: A list of short forms derived from the joblist.
    :param joblist: A list of job names.
    :return: The full job name that corresponds to the short form.
    """
    try:
        index = short_forms.index(job_name[:3].lower())
        return joblist[index]
    except ValueError:
        return "Job not found."

async def add_user(user: voltage.User, isbot:bool=False): # long ass fucking function to add users to the database if they dont exist yet. but it works..
  if (await userdb.find_one({"userid": user.id})):
    return "User already exists."
  try:
    await userdb.insert_one({
        "_id": userdb.count_documents({}) + 1,
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
            "1":{
              "message": f"Welcome to Mecha, {user.name}!{sep}To get started, type `m!help` in this server to get started!",
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
            "afk": {}
        }
    })
    return "Added"
  except Exception as e:
    return f"Sorry, An Error Occured!{sep}{sep}```{sep}{e}{sep}```"


async def parse_amount(ctx, amount, bank=False):
    user = (await userdb.find_one({"userid": ctx.author.id}))
    if bank:
        econ = user["economy"]["bank"]
        try:
            if "%" in amount:
                if float(amount.replace("%", "")) > 100 and float(amount.replace("%", "")) <= 0:
                    embed = voltage.SendableEmbed(
                        description="You can only withdraw up to 100%!",
                        color="#FF0000",
                        title="Error"
                    )
                    return await ctx.reply(embed=embed)
                return econ * (float(amount.replace("%", "")) / 100)
            elif amount.lower() in ["a", "all", "everything", "max"]:
                amount = user["economy"]["bank"]
                return amount
            elif "k" in amount.lower() or "thousand" in amount.lower():
                return 1000 * int(amount.replace("k", "").replace("thousand", "").replace(" ", ""))
            elif "m" in amount.lower() or "mil" in amount.lower() or "million" in amount.lower():
                return 1000000 * int(amount.replace("m", "").replace("mil", "").replace("million", "").replace(" ", ""))
            else:
                return int(amount.replace(" ", ""))
        except ValueError:
            print(f"Error parsing amount: {amount}")
            embed = voltage.SendableEmbed(
                description="Invalid amount!",
                color="#FF0000",
                title="Error"
            )
            await ctx.reply(embed=embed)
            return None

    user = await userdb.find_one({"userid": ctx.author.id})
    try:
        suffixes = {
            'k': 1000,
            'thousand': 1000,
            'm': 1000000,
            "mil": 1000000,
            "million": 1000000,
            'h': 100,
            'hundred': 100,
            'hundredthousand': 100000,
            'th': 100000
        }
        if "%" in amount:
            if float(amount.replace("%", "")) > 100 and float(amount.replace("%", "")) <= 0:
                embed = voltage.SendableEmbed(
                    description="You can only withdraw up to 100%!",
                    color="#FF0000",
                    title="Error"
                )
                return await ctx.reply(embed=embed)
            return user['economy']['wallet'] * (float(amount.replace("%", "")) / 100)
        elif amount.lower() in ["a", "all", "everything", "max"]:
            amount = user["economy"]["wallet"]
            return amount
        for suffix, multiplier in suffixes.items():
            if suffix in amount.lower():
                amount = int(amount.replace(suffix, '')) * multiplier
                break
        else:
            amount = int(amount)
            return amount
    except ValueError:
        embed = voltage.SendableEmbed(
            description="Amount must be an integer or use k, m, h, or th suffixes for thousand, million, hundred, or hundred thousand respectively!",
            color="#FF0000",
            title="Error"
        )
        await ctx.reply(embed=embed)
        return None


async def buy_item(ctx, item:str, price:int, amount:int): # this sucks but it works
    if (await userdb.find_one({"userid": ctx.author.id})):
        if amount < 1:
            return await ctx.reply("Amount must be greater than 0!")
        userdata = (await userdb.find_one({"userid": ctx.author.id}))
        if userdata['economy']['wallet'] < price:
            return await ctx.reply("You don't have enough money to purchase this!")
        if item in userdata['economy']['data']['inventory']:
            await userdb.bulk_write([
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -price}}),
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {f"economy.data.inventory.{item.lower()}": amount}})
            ])
        else:
            await userdb.bulk_write([
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {f"economy.data.inventory.{item.lower()}": amount}}),
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -price}})
            ])
        return await ctx.reply(f"You bought **{item.capitalize()}** for **{price}** coins!")

async def apply_job(ctx, job:str):
    if (await userdb.find_one({"userid": ctx.author.id})):
        userdata = (await userdb.find_one({"userid": ctx.author.id}))
        if "resume" in userdata['economy']['data']['inventory']:
            jobname = match_job_to_short_form(job.lower(), short_forms, joblist)
            if random.randint(1, 100) < 75:
                await userdb.update_one({"userid": ctx.author.id}, {"$set": {"economy.data.job": jobname}})
                embed = voltage.SendableEmbed(
                    title="Application Accepted",
                    description=f"You were accepted for **{jobname.capitalize()}**!",
                    colour="#198754"
                )
                return await ctx.reply(embed=embed)
            else:
                await userdb.bulk_write([
                    pymongo.UpdateOne({"userid": ctx.author.id}, {"$set": {"economy.data.job": "unemployed"}}),
                    pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": 250}})
                ])
                embed = voltage.SendableEmbed(
                    title="Application Rejected",
                    description=f"### :01HQ9JZ0Q1FMAKF6Y4Z2TZ58ZG:{sep}You were rejected for **{jobname.capitalize()}**{sep}You have received `250` coins as compensation!{sep}You are now unemployed..",
                    colour="#FF033E"
                )
                return await ctx.reply(embed=embed)
        else:
            return await ctx.reply("You don't have a resume to apply for a job with! Purchase a resume for `250` coins by using `m!buy resume`")
    else:
        return await ctx.reply("You don't have an account registered with me!")

def setup(client) -> commands.Cog:

    eco = commands.Cog("Economy", "Wanna get rich! TOO BAD.")

    async def create_account(ctx):
        await ctx.send("You dont have a bank account registered in our database! I can resgister you now, is that okay? *(Yes/No)*")
        try:
            message = await client.wait_for("message", check=lambda message: message.author.id != client.user.id, timeout=15)
        except asyncio.TimeoutError:
            return await ctx.send(f"{ctx.author.mention} | Timed out! Please try again!")
        if any(x in message.content.lower() for x in ["yes", "y", "yea", "yeah", "yup"]):
            return await ctx.send(await add_user(ctx.author))
        else:
            return await ctx.send("Oh... Nevermind then!")

    @eco.command(description="View your balance.", aliases=["bal", 'b', 'money', 'mybal'], name="balance")
    @limiter(5, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def bal(ctx, user:voltage.User=None):
        if not user:
            user = ctx.author
        if (await userdb.find_one({"userid": user.id})):
            items = 0
            userdata = (await userdb.find_one({"userid": user.id}))
            try:
                items = userdata['economy']['data']["inventory"]
                itemlist = {}
                itemstuff = []
                for item in items:
                    itemlist[item] = {
                        "name": item.capitalize(),
                        "amount": items[item]
                    }
                for item in itemlist:
                    itemstuff.append(f"**{item}:** *x{itemlist[item]['amount']}*")
            except:
                items = []
            if len(items) == 0:
                items = ["You have no items :boohoo:"]
            embed = voltage.SendableEmbed(title=f"{user.name}'s balance", icon_url=user.display_avatar.url, description=f"**Wallet Balance:**{sep}> \${round(userdata['economy']['wallet'], 2):,}{sep}{sep}**Bank Balance:**{sep}> \${round(userdata['economy']['bank'], 2):,}{sep}**Inventory:**{sep}> {f'{sep}> '.join(itemstuff)}", colour="#516BF2")
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                "You dont have a bank account registered in our database! Would you like me to create one?"
            )
            message = await client.wait_for("message", check=lambda message: message.author.id != client.user.id, timeout=15)
            if any(x in message.content.lower() for x in ["yes", "y", "yea", "yeah", "yup"]):
                return await ctx.send(await add_user(ctx.author))
            else:
                return await ctx.send("Oh... Nevermind then!")

    @eco.command(
        description="25% chance to get **nothing** and 75% to get up to 250 coins!"
    )
    @limiter(15, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def beg(ctx):
        amount = random.randint(1, 250)
        people = [
            "Lea From Revolt",
            "ks",
            "Cesiyi",
            "css",
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
            "TikTok Moron",
            "Alotta Fagina",
            "Joe",
            "Max",
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
            "Imagine begging in 2024, gofundme is where it is at",
        ]
        percentage = random.randint(1, 100)
        if not (await userdb.find_one({"userid": ctx.author.id})):
            await create_account(ctx)
        elif random.randint(1,200) == 1 or ctx.author.display_name.lower() == "mechahater":
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"YOU JUST GOT ROBBED! OH NO! THEY TOOK EVERYTHING IN YOUR WALLET WHADAFRICK!",
                colour = "#FF0000"
            )
            await userdb.update_one(
                {"userid": ctx.author.id},
                {"$set": {"economy.wallet": 0}},
            )
            return await ctx.reply(embed=embed)
        elif percentage > 25:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"{random.choice(people)} gave you `{round(amount, 2):,}` coins! Now get a job you bum.",
                color="#00FF00",
            )
            await userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": amount}})
            return await ctx.send(embed=embed)
        else:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f'"{random.choice(badline)}" -{random.choice(people)}',
                color="#FF0000",
            )
            return await ctx.send(embed=embed)

    @eco.command(description="Go to work u bum **requires Resume**")
    @limiter(60, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def work(ctx):
        amount = random.randint(500, 1000)
        if not (await userdb.find_one({"userid": ctx.author.id})):
            await create_account(ctx)
        else:
            userdata = (await userdb.find_one({"userid": ctx.author.id}))
        if userdata['economy']['data']['job'] == "unemployed":
            return await ctx.send("You're unemployed, get a job u bum!")
        elif "resume" in userdata['economy']['data']["inventory"]:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"You worked as a {userdata['economy']['data']['job']} and made `{amount}`!",
                color="#00FF00",
            )
            await ctx.send(embed=embed)
            await userdb.update_one(
                {"userid": ctx.author.id}, {"$inc": {"economy.wallet": amount}}
            )
        else:
            return await ctx.send(
                "You need a `resume` to work, your not workin' here bub."
            )

    @eco.command(name="richest",aliases=["richlist", "richrank"], description="Check out the richest users in all of Mecha!")
    @limiter(5, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def richest(ctx):
        lb = []
        count = 0
        d = userdb.find().sort([("economy.total", pymongo.DESCENDING)]).limit(10)
        for doc in (await d.to_list(length=10)):
            total = doc['economy']['wallet'] + doc['economy']['bank']
            count += 1
            if count <= 3:
                emoji = ["0", "🥇", "🥈", "🥉"]
                if len(doc['username']) <= 10:
                    lb.append(f"{'#' * count} **{emoji[count]}** {doc['username']}{sep}#### **\${round(total):,}**")
                elif len(doc['username']) > 10 and count == 1:
                    lb.append(f"{'###' * count} **{emoji[count]}** {doc['username']}{sep}#### **\${round(total):,}**")
                elif count == 3 and len(doc['username']) < 20:
                    lb.append(f"{'#' * count} **{emoji[count]}** {doc['username']}{sep}#### **\${round(total):,}**")
                else:
                    lb.append(f"{'#' * count + '#'} **{emoji[count]}** {doc['username']}{sep}#### **\${round(total):,}**")
            elif count == 4:
                lb.append(f"**#4** -> {doc['username']}: {round(total):,}")
            else:
                lb.append(f"**#{count}** -> {doc['username']}: {round(total):,}")
        embed = voltage.SendableEmbed(
            title = "View the Leaderboard (UPDATES EVERY 2 MINUTES!)",
            description='\n'.join(lb),
            color="#516BF2"
        )
        await ctx.send(
            embed=embed
        )

    @eco.command(description="Move money into your bank account!", name="deposit", aliases=['dep', 'tobank', 'dp', 'd'])
    @limiter(10, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def deposit(ctx, *, amount: str):
        if (await userdb.find_one({"userid": ctx.author.id})):
            amt = (await parse_amount(ctx, amount, False))
            if amt is None:
                print(amt)
                print(amount)
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Please enter a valid amount!",
                    color="#FF0000",
                )
                await ctx.reply(embed=embed)
                return
            elif amt < 0:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Please enter a valid amount!",
                    color="#FF0000",
                )
                return await ctx.reply(embed=embed)
            userdata = (await userdb.find_one({"userid": ctx.author.id}))["economy"]["wallet"]
            if userdata > 0:
                if amt > userdata:
                    await ctx.reply("You're trying to deposit more than you have in your wallet!")
                    return
                await userdb.bulk_write([
                    pymongo.UpdateOne(
                        {"userid": ctx.author.id},
                        {"$inc": {"economy.wallet": -amt, "economy.bank": amt}}
                    )
                ])
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"You deposited `${amt:,}` into your bank account! {sep}You have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['bank']:,}` in your bank account!",
                    color="#00FF00",
                )
                await ctx.reply(embed=embed)
            else:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Please enter a valid amount!",
                    color="#FF0000"
                )
                await ctx.reply(embed=embed)
        else:
            await create_account(ctx)
    
    # GAMBA GAMBA GAMBA
    
    @eco.command(name="coinflip", aliases=['cf', 'coin', 'flip'], description="Flip a coin!")
    @limiter(7, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def coinflip(ctx, bet:int=None, choice:str=None, user:voltage.User=None):
        if not bet or bet < 0:
            return await ctx.reply("Please enter a valid bet!")
        else:
            bet = int(bet)
        if not choice:
            return await ctx.reply("Please enter heads or tails!")
        elif choice.lower() not in ['heads', 'tails']:
            return await ctx.reply("Please enter heads or tails!")
        elif bet > (await userdb.find_one({"userid": ctx.author.id}))["economy"]["wallet"]:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"You don't have that much money in your wallet!{sep}*(lol poor fella)*",
                colour="#FF0000"
            )
            return await ctx.reply(embed=embed)
        elif (await userdb.find_one({"userid": ctx.author.id})):
            if not user:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"Flipping a coin for **\${bet:,}**... {sep}You now have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['wallet']-bet:,}` in your wallet!",
                    colour="#00FF00",
                    media = "https://media.tenor.com/images/60b3d58b8161ad9b03675abf301e8fb4/tenor.gif"
                )
                msg = await ctx.reply(embed=embed)
                await userdb.bulk_write([
                    pymongo.UpdateOne(
                        {"userid": ctx.author.id},
                        {"$inc": {"economy.wallet": -bet}}
                    )
                ])
                await asyncio.sleep(3)
                if random.choice(['heads', 'tails']) == choice.lower():
                    await userdb.bulk_write([
                        pymongo.UpdateOne(
                            {"userid": ctx.author.id},
                            {"$inc": {"economy.wallet": bet*2}}
                        )
                    ])
                    embed = voltage.SendableEmbed(
                        title=ctx.author.display_name,
                        icon_url=ctx.author.display_avatar.url,
                        description=f"You won **\${bet:,}**! {sep}You now have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['wallet']:,}` in your wallet!",
                        colour="#00FF00"
                    )
                    return await msg.edit(embed=embed)
                else:
                    embed = voltage.SendableEmbed(
                        title=ctx.author.display_name,
                        icon_url=ctx.author.display_avatar.url,
                        description=f"You lost **\${bet:,}**! {sep}You now have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['wallet']:,}` in your wallet!",
                        colour="#FF0000"
                    )
                    return await msg.edit(embed=embed)
            else:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"{ctx.author.display_name}, challenges {user.display_name} to a coinflip for **\${bet:,}*! {sep}Do you confirm? (15 seconds)",
                    colour="#00FF00"
                )
                await ctx.send(embed=embed, content=user.mention)
                try:
                    def check(msg):
                        return msg.author.id == user.id
                    msg = await client.wait_for("message", check=check, timeout=15)
                    if msg.content.lower() in ["yes", "y", "yea", "yeah", "yup"]:
                        if (await userdb.find_one({"userid": user.id})):
                            udata = (await userdb.find_one({"userid": user.id}))
                            if bet > udata["economy"]["wallet"]:
                                embed = voltage.SendableEmbed(
                                    title=ctx.author.display_name,
                                    icon_url=ctx.author.display_avatar.url,
                                    description=f"{user.display_name} doesn't have that much money in their wallet!{sep}*(lol poor fella)*",
                                    colour="#FF0000"
                                )
                                return await ctx.reply(embed=embed)
                            embed = voltage.SendableEmbed(
                                title=ctx.author.display_name,
                                icon_url=ctx.author.display_avatar.url,
                                description=f"Flipping a coin for **\${bet:,}**... {sep}You now have `${(await userdb.find_one({'userid': user.id}))['economy']['wallet']-bet:,}` in your wallet!",
                                media = "https://media.tenor.com/images/60b3d58b8161ad9b03675abf301e8fb4/tenor.gif",
                                colour="#00FF00"
                            )
                            await userdb.bulk_write([
                                pymongo.UpdateOne(
                                    {"userid": user.id},
                                    {"$inc": {"economy.wallet": -bet}}
                                ),
                                pymongo.UpdateOne(
                                    {"userid": ctx.author.id},
                                    {"$inc": {"economy.wallet": -bet}}
                                )
                            ])
                            await ctx.reply(embed=embed, content=user.mention)
                            if random.choice(['heads', 'tails']) == choice.lower():
                                await userdb.bulk_write([
                                    pymongo.UpdateOne(
                                        {"userid": ctx.author.id},
                                        {"$inc": {"economy.wallet": bet*2}}
                                    )
                                ])
                                embed = voltage.SendableEmbed(
                                    title=ctx.author.display_name,
                                    icon_url=ctx.author.display_avatar.url,
                                    description=f"{ctx.author.mention} won **\${bet:,}**! {sep}You now have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['wallet']:,}` in your wallet!",
                                    colour="#00FF00"
                                )
                                return await ctx.reply(embed=embed)
                            else:
                                await userdb.bulk_write([
                                    pymongo.UpdateOne(
                                        {"userid": user.id},
                                        {"$inc": {"economy.wallet": bet*2}}
                                    )
                                ])
                                embed = voltage.SendableEmbed(
                                    title=ctx.author.display_name,
                                    icon_url=ctx.author.display_avatar.url,
                                    description=f"{user.mention} won **\${bet:,}**! {sep}They now have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['wallet']:,}` in their wallet!",
                                    colour="#00FF00"
                                )
                                return await msg.reply(embed=embed)
                        else:
                            embed = voltage.SendableEmbed(
                                title=ctx.author.display_name,
                                icon_url=ctx.author.display_avatar.url,
                                description=f"{user.display_name} doesn't exist! {sep}You now have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['wallet']:,}` in your wallet!",
                                colour="#FF0000"
                            )
                            await ctx.reply(embed=embed)
                    elif msg.content.lower() in ["no", "n", "nah", "nope"]:
                        embed = voltage.SendableEmbed(
                            title=ctx.author.display_name,
                            icon_url=ctx.author.display_avatar.url,
                            description=f"Looks like {user.display_name} doesn't want to play with you. {sep}You now have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['wallet']:,}` in your wallet!",
                            colour="#FF0000"
                        )
                        return await ctx.reply(embed=embed)
                    else:
                        await ctx.send(msg.content)
                except asyncio.TimeoutError:
                    embed = voltage.SendableEmbed(
                        title=ctx.author.display_name,
                        icon_url=ctx.author.display_avatar.url,
                        description=f"{user.display_name} didn't respond in time! {sep}You now have `${(await userdb.find_one({'userid': ctx.author.id}))['economy']['wallet']:,}` in your wallet!",
                        colour="#FF0000"
                    )
                    return await ctx.reply(embed=embed)
        
    @eco.command(name="blackjack", aliases=["bj"], description="Play a game of blackjack!")
    @limiter(7, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def blackjack(ctx, *, bet:str):
        bet = await parse_amount(ctx, bet)
        if bet is None or bet <= 0:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"Please specify a valid bet!{sep}**Usage:** `{ctx.prefix}bj <bet>`",
                colour="#FF0000"
            )
            return await ctx.reply(embed=embed)
        elif bet > (await userdb.find_one({"userid": ctx.author.id}))["economy"]["wallet"]:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"You don't have that much money in your wallet!{sep}*(lol poor fella)*",
                colour="#FF0000"
            )
            return await ctx.reply(embed=embed)
        elif (await userdb.find_one({"userid": ctx.author.id})):
            await userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -bet}})
            deck = [
                'SA', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'SJ', 'SQ', 'SK',
                'HA', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'HJ', 'HQ', 'HK',
                'CA', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'CJ', 'CQ', 'CK',
                'DA', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'DJ', 'DQ', 'DK'
            ]
            random.shuffle(deck)

            def calculate_hand(hand):
                value = 0
                ace_count = 0
                for card in hand:
                    if card[1:] in ['J', 'Q', 'K']:
                        value += 10
                    elif card[1:] == 'A':
                        ace_count += 1
                        value += 11
                    else:
                        value += int(card[1:])
                while value > 21 and ace_count:
                    value -= 10
                    ace_count -= 1
                return value

            player_hand = [deck.pop(), deck.pop()]
            dealer_hand = [deck.pop(), deck.pop()]

            player_value = calculate_hand(player_hand)
            dealer_value = calculate_hand(dealer_hand)

            # Initial hand display
            embed = voltage.SendableEmbed(
                title=f"{ctx.author.display_name}'s blackjack game",
                description=f"Dealer's hand: {str(dealer_hand[0])} and ?{sep}Your hand: {' '.join(player_hand)} (Total: {player_value}){sep}`hit` or `stand`?",
                colour="#44ff44"
            )
            await ctx.reply(embed=embed)

            # Player's turn
            while True:
                if player_value == 21:
                    embed = voltage.SendableEmbed(
                        title=f"{ctx.author.display_name}'s blackjack game",
                        description=f"Blackjack! You win!",
                        colour="#198754"
                    )
                    await ctx.reply(embed=embed)
                    await userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": round(bet*2.5)}})
                    return
                elif player_value > 21:
                    embed = voltage.SendableEmbed(
                        title=f"{ctx.author.display_name}'s blackjack game",
                        description=f"You busted with a total of {player_value}. Dealer wins.",
                        colour="#dc3545"
                    )
                    await ctx.reply(embed=embed)
                    return
                action = await client.wait_for('message', check=lambda m: m.author == ctx.author and m.content.lower() in ['hit', 'stand', 'h', 's'], timeout=30)
                if any(x in action.content.lower() for x in ['hit', 'h', 'draw']):
                    player_hand.append(deck.pop())
                    player_value = calculate_hand(player_hand)
                    embed=voltage.SendableEmbed(
                        title=f"{ctx.author.display_name}'s blackjack game",
                        description=f"You drew a card: {str(player_hand[-1])}{sep}Your hand: {' '.join(player_hand)} (Total: {player_value}){sep}`hit` or `stand`?",
                        colour="#0d6efd"
                    )
                    await ctx.reply(embed=embed)
                else:
                    break

            # Dealer's turn
            embed = voltage.SendableEmbed(
                title=f"{ctx.author.display_name}'s blackjack game",
                description=f"It's the Dealer's turn.{sep}Dealer's hand: {' '.join(dealer_hand)} (Total: {dealer_value})",
                colour="#ffc107"
            )
            await ctx.send(embed=embed)
            while dealer_value < 17:
                dealer_hand.append(deck.pop())
                dealer_value = calculate_hand(dealer_hand)
                text = []
                text.append(f"Dealer drew a card: {dealer_hand[-1]}{sep}Dealer's hand: {' '.join(dealer_hand)} (Total: {dealer_value})")
                embed = voltage.SendableEmbed(
                    title=f"{ctx.author.display_name}'s blackjack game",
                    description='\n'.join(text),
                    colour="#ffc107"
                )
                await ctx.reply(embed=embed)

            # Determine winner
            if dealer_value > 21 or player_value > dealer_value:
                embed = voltage.SendableEmbed(
                    title=f"{ctx.author.display_name}'s blackjack game",
                    description=f"You won `${bet*2}`!{sep}Dealer busted with a total of {dealer_value}.{sep}Your hand: {' '.join(player_hand)} (Total: {player_value})",
                    colour="#198754"
                )
                await ctx.reply(embed=embed)
                await userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": bet*2}})
            elif dealer_value == player_value:
                embed = voltage.SendableEmbed(
                    title=f"{ctx.author.display_name}'s blackjack game",
                    description=f"It's a tie!",
                    colour="#ffc107"
                )
                await ctx.reply(embed=embed)
                await userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": bet}})
            else:
                embed = voltage.SendableEmbed(
                    title=f"{ctx.author.display_name}'s blackjack game",
                    description=f"Dealer wins with a total of {dealer_value}.{sep}Your hand: {' '.join(player_hand)} (Total: {player_value})",
                    colour="#dc3545"
                )
                await ctx.reply(embed=embed)
        else:
            await add_user(ctx.author)
            await ctx.send("Please try again!")
   
    @eco.command(description="Pay another user from your wallet!", name="pay", aliases=['transfer', 'sendmoney'])
    @limiter(10, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def pay(ctx, member:voltage.User, amount:str):
        parsed_amount = await parse_amount(ctx, amount)
        if parsed_amount is None:
            return await ctx.reply("Please enter a valid amount!")
        if parsed_amount <= 0:
            embed = voltage.SendableEmbed(
                title="Error!",
                description="Please enter a positive amount to pay.",
                colour="#dc3545"
            )
            await ctx.reply(embed=embed)
            return
        if ctx.author.id == member.id:
            embed = voltage.SendableEmbed(
                title="Error!",
                description="You cannot pay yourself!",
                colour="#dc3545"
            )
            await ctx.reply(embed=embed)
            return
        sender_data = await userdb.find_one({"userid": ctx.author.id})
        if sender_data and sender_data["economy"]["wallet"] >= amount:
            recipient_data = (await userdb.find_one({"userid": member.id}))
            if recipient_data:
                await userdb.bulk_write([
                    pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -amount}}),
                    pymongo.UpdateOne({"userid": member.id}, {"$inc": {"economy.wallet": -amount}}),
                    pymongo.UpdateOne({"userid": member.id}, {"$append": {"notifications.inbox": {
                        "title": f"Payment from {ctx.author.display_name}",
                        "message": f"{ctx.author.display_name} paid you {round(amount, 2):,} coins!",
                        "date": time.time(),
                        "read": False,
                        "type": "member"
                    }}}),
                ])
                embed = voltage.SendableEmbed(
                    title="Success!",
                    description=f"You have successfully paid {round(amount, 2):,} to {member.display_name}.",
                    colour="#198754"
                )
                await ctx.reply(embed=embed)
            else:
                embed = voltage.SendableEmbed(
                    title="Error!",
                    description="The recipient does not have an account. Please ask them to create one using `m!add`.",
                    colour="#dc3545"
                )
                await ctx.relpy(embed=embed)
        else:
            embed = voltage.SendableEmbed(
                title="Error!",
                description="You do not have enough funds in your wallet to make this payment.",
                colour="#dc3545"
            )
            await ctx.reply(embed=embed)
    
    @eco.command(description="Move money back into your wallet!", name="withdraw", aliases=['with', 'towallet', 'wd', 'w'])
    @limiter(10, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def withdraw(ctx, *, amount):
        if (await userdb.find_one({"userid": ctx.author.id})):
            userdata = await parse_amount(ctx, amount, True)
            if userdata >= 0:
                await userdb.bulk_write([
                    pymongo.UpdateOne(
                        {"userid": ctx.author.id},
                        {"$inc": {"economy.wallet": userdata, "economy.bank": -userdata}}
                    )
                ])
                amt = userdata
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"You withdrew `${round(amt, 2):,}` from your bank account! {sep}You have `${round((await userdb.find_one({'userid': ctx.author.id}))['economy']['bank'], 2):,}` in your bank account!",
                    color="#00FF00",
                )
                await ctx.reply(embed=embed)
            else:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Please enter a valid amount!",
                    color="#dc3545",
                )
                await ctx.reply(embed=embed)
        else:
            await create_account(ctx)

    @eco.command(name="monthly", description="Claim your monthly reward! (50,000 - 150,000 coins!)")
    async def monthly(ctx):
        if (await userdb.find_one({"userid": ctx.author.id})):
            if time.time() < (await userdb.find_one({"userid": ctx.author.id}))["economy"]["monthly"]:
                elapsed_time = int((await userdb.find_one({"userid": ctx.author.id}))['economy']['monthly'] - time.time())
                days, remainder = divmod(elapsed_time, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"Please wait `{str(days)+'d ' if days > 0 else ''}{str(hours) + 'h ' if hours > 0 else ''}{str(minutes) + 'm ' if minutes > 0 else ''}{str(seconds) + 's' if seconds > 0 else ''}` before claiming your monthly reward!",
                    color="#dc3545"
                )
                return await ctx.reply(embed=embed)
            else:
                amount = random.randint(50000, 150000)
                await userdb.bulk_write([
                    pymongo.UpdateOne(
                        {"userid": ctx.author.id},
                        {"$set": {"economy.monthly": time.time() + 2592000}}
                    ),
                    pymongo.UpdateOne(
                        {"userid": ctx.author.id},
                        {"$inc": {"economy.wallet": amount}}
                    )
                ])
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"You have claimed your monthly reward! {sep}You have received `${amount:,}`!",
                    color="#00FF00"
                )
                return await ctx.reply(embed=embed)
        else:
            await create_account(ctx)

    @eco.command(name="daily", aliases=["dailies", 'dr', 'claimdaily'], description="Claim your daily reward! (5,000 - 15,000 coins!)")
    async def daily(ctx):
        if (await userdb.find_one({"userid": ctx.author.id})):
            if time.time() < (await userdb.find_one({"userid": ctx.author.id}))["economy"]["daily"]:
                elapsed_time = int((await userdb.find_one({"userid": ctx.author.id}))['economy']['daily'] - time.time())
                days, remainder = divmod(elapsed_time, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"You already claimed your daily reward today!{sep}Come back in `{str(days)+'d ' if days > 0 else ''}{str(hours) + 'h ' if hours > 0 else ''}{str(minutes) + 'm ' if minutes > 0 else ''}{str(seconds) + 's' if seconds > 0 else ''}`!",
                    color="#dc3545"
                )
                return await ctx.reply(embed=embed)
            amount = random.randint(5000, 15000)
            await userdb.bulk_write(
                [
                    pymongo.UpdateOne(
                        {"userid": ctx.author.id},
                        {"$inc": {"economy.wallet": amount}}
                    ),
                    pymongo.UpdateOne(
                        {"userid": ctx.author.id},
                        {"$set": {"economy.daily": time.time() + 86400}}
                    )
                ]
            )
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"You claimed your daily reward of `${amount:,}`!",
                colour="#198754"
            )
            return await ctx.reply(embed=embed)
        else:
            await create_account(ctx)
            
    @eco.command(
        aliases=["apply", "getjob", "gj", "workas", "howjob"]
    )
    @limiter(5, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def job(ctx, job=None):
        if job is None:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"## **Available Jobs:**{sep}{f'{sep}> '.join(joblist)}",
            )
            return await ctx.send(embed=embed)
        elif any(x in job.lower() for x in short_forms):
            await apply_job(ctx, job)
        

    @eco.command(aliases=["sh", "buy"], description="Buy items from the shop!", name="shop")
    @limiter(5, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please try again in `{strfdelta(datetime.timedelta(seconds=delay), '{seconds}s')}`!"))
    async def shop(ctx, item:str=None, amount:int=1):
        if not item:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description="""
**Available items for sale:**
  
Playboy Magazine - `1000`
Resume - `250`
Golden Egg - `5000`
        
""",
            )
            return await ctx.send(content="[]()", embed=embed)
        else:
            if (await userdb.find_one({"userid": ctx.author.id})):
                if any(x in item.lower() for x in [
                    "r",
                    "resume",
                    "application",
                    "jobform",
                    "resum",
                    "res",
                    "form",
                    "resueme",
                ]):
                    await buy_item(ctx, "Resume", 250, amount)
                elif any(x in item.lower() for x in [
                    "gedd",
                    "gegg",
                    "goldenegg",
                    "goldegg",
                    "gold",
                    "egggold",
                    "egg",
                    "ge",
                ]):
                    await buy_item(ctx, "Golden Egg", 5000, amount)
                elif any(x in item.lower() for x in [
                    "pb",
                    "playboi",
                    "playboy",
                    "magazine",
                    "magasine",
                    "playb",
                    "pboy",
                ]):
                    await buy_item(ctx, "Playboy", 1000, amount)
            else:
                await create_account(ctx)

    async def slots_game(ctx, amount: int):
        if (await userdb.find_one({"userid": ctx.author.id})):
            user = await userdb.find_one({"userid": ctx.author.id})
            await userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -amount}})
            if user["economy"]["wallet"] < amount:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"You don't have enough money to bet {amount:,}!",
                    colour="#FF0000"
                )
                return await ctx.reply(embed=embed)
            elif amount < 100:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="You can't bet less than 100 coins!",
                    colour="#FF0000"
                )
                return await ctx.reply(embed=embed)

            emojis = {  # The emojis and their values
                "🗑️": 0,  # Trash Can
                "🍎": 1,  # Apple
                "🍊": 4,  # Orange
                "🍇": 8,  # Grapes
                "🍓": 2,  # Strawberry
                "🍒": 5,  # Cherry
                "🍉": 7,  # Watermelon
                "🍌": 10, # Banana
                "🥝": 12, # Kiwi
                "🍋": 15, # Lemon
                "🍈": 18, # Plum
                "🍅": 20, # Tomato
                "7️⃣": 50,  # 7
            }

            a = random.choice(list(emojis.keys()))
            b = random.choice(list(emojis.keys()))
            c = random.choice(list(emojis.keys()))

            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"You bet {amount:,}...{sep}{sep} | **{a}** | **{b}** | **{c}** |",
                colour="#FFD700"
            )
            msg = await ctx.reply(embed=embed)
            prize = 0
            if a == b == c == "7️⃣":
                prize = 25_000_000
            else:
                if a == b:
                    prize = emojis.get(a, 0) * 2 * amount
                elif a == c:
                    prize = emojis.get(a, 0) * amount
                elif b == c:
                    prize = emojis.get(b, 0) * amount
            if prize == 0:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description=f"You lost! {sep}{sep} | **{a}** | **{b}** | **{c}** |",
                    colour="#FF0000"
                )
                return await msg.edit(embed=embed)
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"**x{round(prize / amount)}!**{sep}You won `{prize:,}`!{sep}{sep} | **{a}** | **{b}** | **{c}** |",
                colour="#198754"
            )
            await msg.edit(embed=embed)
            await userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": prize}})
        else:
            await create_account(ctx)


    @eco.command(
        name="slots",
        aliases=["bet", "slts"],
        description="Bet on the slots machine!",
    )
    @limiter(30, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please try again in `{strfdelta(datetime.timedelta(seconds=delay), '{seconds}s')}`!"))
    async def slots(ctx, amount: str):
        parsed_amount = await parse_amount(ctx, amount)

        if parsed_amount is None:
            return await ctx.reply(
                "Invalid amount specified. Please specify an amount like `100` or `1k` or `1m`"
            )

        if parsed_amount > 100_000_000:
            return await ctx.reply(
                "You can't bet more than 100,000,000 coins!"
            )

        if parsed_amount > (await userdb.find_one({"userid": ctx.author.id}))["economy"]["wallet"]:
            return await ctx.reply(
                f"You don't have enough money to bet {parsed_amount:,}!"
            )

        await slots_game(ctx, parsed_amount)

        if (await userdb.find_one({"userid": ctx.author.id})) is None:
            await create_account(ctx)


    unusable_items = ["resume"]  # Add more items if needed

    async def useitem(ctx, item:str, amount:str="1"):
        am = int(await parse_amount(ctx, amount))
        if am < 1:
            embed = voltage.SendableEmbed(
                title="Error",
                description="Invalid amount specified. Please specify an amount like `100` or `1k` or `1m`",
                color="#FF0000"
            )
            return await ctx.reply(embed=embed)
        user = await userdb.find_one({"userid": ctx.author.id})
        if user is None:
            embed = voltage.SendableEmbed(
                title="Error",
                description="You dont have a bank account registered in our database! Would you like me to create one?",
                color="#FF0000",
            )
            return await ctx.send(embed=embed)
        items = user["economy"]["data"]["inventory"]
        if item not in items:
            embed = voltage.SendableEmbed(
                title="Error",
                description=f"You don't have {item}!",
                color="#FF0000",
            )
            return await ctx.send(embed=embed)
        elif items[item] < 1:
            embed = voltage.SendableEmbed(
                title="Error",
                description=f"You don't have enough {item}!",
                color="#FF0000",
            )
            return await ctx.send(embed=embed)
        elif item in unusable_items:
            embed = voltage.SendableEmbed(
                title="Error",
                description=f"You can't use {item}!",
                color="#FF0000",
            )
            return await ctx.send(embed=embed)
        
        # check what the item is
        if item == "playboy":
            if user["economy"]["data"]["inventory"]["playboy"] < 1:
                embed = voltage.SendableEmbed(
                    title="Error",
                    description=f"You don't have any {item}!",
                    color="#FF0000",
                )
                return await ctx.reply(embed=embed)
            if random.randint(1, 100) < 90:
                amt = (random.randint(1, 50) * user["levels"]["level"]) * round(am)
            else:
                amt = (random.randint(500, 1000) * user["levels"]["level"]) * round(am)
                
            await userdb.bulk_write([
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.data.inventory.playboy": -int(am)}}),
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": round(amt)}}),
            ])
            embed = voltage.SendableEmbed(
                title="Success",
                description=f"You used `x{round(am)}` **{item}**!{sep}You got ${round(amt):,} coins!",
                color="#00FF00",
            )
            return await ctx.send(embed=embed)
        elif item == "bank_loan" or item == "Bank Loan":
            for i in user["economy"]["data"]["inventory"]:
                if any(x in i for x in ["bank_loan", "Bank Loan"]) > 0: # Check if the item is in the inventory
                    amt = (random.randint(10000, 50000) * user["levels"]["level"]) * round(am)
                    await userdb.bulk_write([
                        pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.data.inventory.Bank Loan": -int(am)}}),
                        pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": amt}}),
                    ])
                    embed = voltage.SendableEmbed(
                        title="Success",
                        description=f"You used `x{round(am)}` **{item}**!{sep}You got ${amt:,} coins!",
                        color="#00FF00",
                    )
                    return await ctx.send(embed=embed)
                else:
                    embed = voltage.SendableEmbed(
                        title="Error",
                        description=f"You don't have any {item}!",
                        color="#FF0000",
                    )
                    return await ctx.reply(embed=embed)
        
    

    @eco.command(name="use", description="Use an item.", aliases=["eat", "drink", "useitem"])
    async def use(ctx, item, amount="1"):
        await useitem(ctx, item, amount)

    return eco