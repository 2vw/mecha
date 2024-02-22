import voltage, json, random, pymongo, time, datetime
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

DBclient = MongoClient(config["MONGOURI"])

db = DBclient["beta"]
userdb = db["users"]
serverdb = db["servers"]

joblist = [
    "Professional Couch Potato",
    "Chief Meme Officer",
    "Wizard of Light Bulb Moments",
    "Underwater Basket Weaver",
    "Pet Psychic",
    "Chief Happiness Officer",
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
            "level": 0,
            "totalxp": 0,
            "lastmessage": time.time()
        },
        "prefixes": [],
        "economy": {
            "wallet": 0,
            "bank": 0,
            "total": 0,
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
    return f"Sorry, An Error Occured!{sep}{sep}```{sep}{e}{sep}```"

async def buy_item(ctx, item:str, price:int): # this sucks but it works
    if userdb.find_one({"userid": ctx.author.id}):
        userdata = userdb.find_one({"userid": ctx.author.id})
        if userdata['economy']['wallet'] < price:
            return await ctx.reply("You don't have enough money to purchase this!")
        if item in userdata['economy']['data']['inventory']:
            userdb.bulk_write([
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -price}}),
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {f"economy.data.inventory.{item.lower()}": 1}})
            ])
        else:
            userdb.bulk_write([
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {f"economy.data.inventory.{item.lower()}": 1}}),
                pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -price}})
            ])
        return await ctx.reply(f"You bought **{item.capitalize()}** for **{price}** coins!")

async def apply_job(ctx, job:str):
    if userdb.find_one({"userid": ctx.author.id}):
        userdata = userdb.find_one({"userid": ctx.author.id})
        if "resume" in userdata['economy']['data']['inventory']:
            if random.randint(1, 100) < 75:
                jobname = match_job_to_short_form(job, short_forms, joblist)
                userdb.update_one({"userid": ctx.author.id}, {"$set": {"economy.data.job": jobname}})
                return await ctx.reply(f"You applied for **{jobname.capitalize()}** and were accepted!")
            else:
                userdb.bulk_write([
                    pymongo.UpdateOne({"userid": ctx.author.id}, {"$set": {"economy.data.job": "unemployed"}}),
                    pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": 250}})
                ])
                return await ctx.reply(f"You applied for **{job.capitalize()}** and were rejected! You've been compensated with `250` coins! (If you previously had a job you were fired!)")
        else:
            return await ctx.reply("You don't have a resume to apply for a job with! Purchase a resume for `250` coins by using `m!buy resume`")
    else:
        return await ctx.reply("You don't have an account registered with me!")

def setup(client) -> commands.Cog:

    eco = commands.Cog("Economy", "Wanna get rich! TOO BAD.")

    async def create_account(ctx):
        await ctx.send("You dont have a bank account registered in our database! I can resgister you now, is that okay? *(Yes/No)*")
        message = await client.wait_for("message", check=lambda message: message.author.id != client.user.id, timeout=15)
        if any(x in message.content.lower() for x in ["yes", "y", "yea", "yeah", "yup"]):
            return await ctx.send(add_user(ctx.author))
        else:
            return await ctx.send("Oh... Nevermind then!")

    @eco.command(description="View your balance.", aliases=["bal", 'b', 'money', 'mybal'], name="balance")
    @limiter(5, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def bal(ctx, user:voltage.User=None):
        if not user:
            user = ctx.author
        if userdb.find_one({"userid": user.id}):
            items = 0
            userdata = userdb.find_one({"userid": user.id})
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
            embed = voltage.SendableEmbed(title=f"{user.name}'s balance", icon_url=user.display_avatar.url, description=f"**Wallet Balance:**{sep}> ${userdata['economy']['wallet']:,}{sep}{sep}**Bank Balance:**{sep}> ${userdata['economy']['bank']:,}{sep}**Inventory:**{sep}> {f'{sep}> '.join(itemstuff)}", colour="#516BF2")
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                "You dont have a bank account registered in our database! Would you like me to create one?"
            )
            message = await client.wait_for("message", check=lambda message: message.author.id != client.user.id, timeout=15)
            if any(x in message.content.lower() for x in ["yes", "y", "yea", "yeah", "yup"]):
                return await ctx.send(add_user(ctx.author))
            else:
                return await ctx.send("Oh... Nevermind then!")

    @eco.command(
        description="25% chance to get **nothing** and 75% to get up to 250 coins!"
    )
    @limiter(15, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
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
            "Imagine begging in 2024, gofundme is where it is at",
        ]
        percentage = random.randint(1, 100)
        if not userdb.find_one({"userid": ctx.author.id}):
            await create_account(ctx)
        if random.randint(1,200) == 1 or ctx.author.display_name.lower() == "mechahater":
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"YOU JUST GOT ROBBED! OH NO! THEY TOOK EVERYTHING IN YOUR WALLET WHADAFRICK!",
                colour = "#FF0000"
            )
            userdb.update_one(
                {"userid": ctx.author.id},
                {"$set": {"economy.wallet": 0}},
            )
            return await ctx.reply(embed=embed)
        if percentage > 25:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"{random.choice(people)} gave you `{amount:,}` coins! Now get a job you bum.",
                color="#00FF00",
            )
            userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": amount}})
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
        if not userdb.find_one({"userid": ctx.author.id}):
            await create_account(ctx)
        else:
            userdata = userdb.find_one({"userid": ctx.author.id})
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
            userdb.update_one(
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
        for doc in userdb.find().sort([("economy.total", pymongo.DESCENDING)]).limit(10):
            total = doc['economy']['wallet'] + doc['economy']['bank']
            count += 1
            if count <= 3:
                emoji = ["0", "🥇", "🥈", "🥉"]
                lb.append(f"{'#' * count} **{emoji[count]}** {doc['username']}{sep}#### **${total:,}**")
            elif count == 4:
                lb.append(f"**#4** -> {doc['username']}: {total:,}")
            else:
                lb.append(f"**#{count}** -> {doc['username']}: {total:,}")
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
    async def deposit(ctx, amount):
        if userdb.find_one({"userid": ctx.author.id}):
            userdata = userdb.find_one({"userid": ctx.author.id})["economy"]["wallet"]
            if userdata > 0:
                if not amount.isdigit():
                    if any(x in amount.lower() for x in ["all", 'max', 'everything', 'maximum', 'a']):
                        userdb.bulk_write([
                            pymongo.UpdateOne(
                                {"userid": ctx.author.id},
                                {"$inc": {"economy.wallet": -userdata, "economy.bank": userdata}}
                            )
                        ])
                        embed = voltage.SendableEmbed(
                            title=ctx.author.display_name,
                            icon_url=ctx.author.display_avatar.url,
                            description=f"You deposited **all** your money into your bank account! {sep}You have `${userdb.find_one({'userid': ctx.author.id})['economy']['bank']:,}` in your bank account!",
                            color="#00FF00",
                        )
                        await ctx.reply(embed=embed)
                elif int(amount) < userdata:
                    userdb.bulk_write([
                        pymongo.UpdateOne(
                            {"userid": ctx.author.id},
                            {"$inc": {"economy.wallet": -int(amount), "economy.bank": int(amount)}}
                        )
                    ])
                    amt = int(amount)
                    embed = voltage.SendableEmbed(
                        title=ctx.author.display_name,
                        icon_url=ctx.author.display_avatar.url,
                        description=f"You deposited `${amt:,}` into your bank account! {sep}You have `${userdb.find_one({'userid': ctx.author.id})['economy']['bank']:,}` in your bank account!",
                        color="#00FF00",
                    )
                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply("You're trying to deposit more than you have in your wallet!")
            else:
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Please enter a valid amount!",
                    color="#FF0000",
                )
                await ctx.reply(embed=embed)
        else:
            await create_account(ctx)
    
    @eco.command(name="blackjack", aliases=["bj"], description="Play a game of blackjack!")
    @limiter(7, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def blackjack(ctx, bet:int=None):
        if not bet or not bet.is_integer() or bet < 0:
            return await ctx.reply("Please enter a valid bet!")
        elif bet > userdb.find_one({"userid": ctx.author.id})["economy"]["wallet"]:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"You don't have that much money in your wallet!{sep}*(lol poor fella)*",
                colour="#FF0000"
            )
            return await ctx.reply(embed=embed)
        elif userdb.find_one({"userid": ctx.author.id}):
            userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -bet}})
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
                    userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": round(bet*2.5)}})
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
                    description=f"You win!{sep}Dealer busted with a total of {dealer_value}.{sep}Your hand: {' '.join(player_hand)} (Total: {player_value})",
                    colour="#198754"
                )
                await ctx.reply(embed=embed)
                userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": bet*2}})
            elif dealer_value == player_value:
                embed = voltage.SendableEmbed(
                    title=f"{ctx.author.display_name}'s blackjack game",
                    description=f"It's a tie!",
                    colour="#ffc107"
                )
                await ctx.reply(embed=embed)
                userdb.update_one({"userid": ctx.author.id}, {"$inc": {"economy.wallet": bet}})
            else:
                embed = voltage.SendableEmbed(
                    title=f"{ctx.author.display_name}'s blackjack game",
                    description=f"Dealer wins with a total of {dealer_value}.{sep}Your hand: {' '.join(player_hand)} (Total: {player_value})",
                    colour="#dc3545"
                )
                await ctx.reply(embed=embed)
        else:
            add_user(ctx.author)
            await ctx.send("Please try again!")
   
    @eco.command(description="Pay another user from your wallet!", name="pay", aliases=['transfer', 'sendmoney'])
    @limiter(10, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def pay(ctx, member: voltage.Member, amount:int):
        if not str(amount).isinstance(int):
            return await ctx.reply("Please enter a valid amount!")
        if amount <= 0:
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
        sender_data = userdb.find_one({"userid": ctx.author.id})
        if sender_data and sender_data["economy"]["wallet"] >= amount:
            recipient_data = userdb.find_one({"userid": member.id})
            if recipient_data:
                userdb.bulk_write([
                    pymongo.UpdateOne({"userid": ctx.author.id}, {"$inc": {"economy.wallet": -amount}}),
                    pymongo.UpdateOne({"userid": member.id}, {"$inc": {"economy.wallet": -amount}}),
                    pymongo.UpdateOne({"userid": member.id}, {"$append": {"notifications.inbox": f"{ctx.author.display_name} paid you {amount:,} coins!"}}),
                ])
                embed = voltage.SendableEmbed(
                    title="Success!",
                    description=f"You have successfully paid {amount:,} to {member.display_name}.",
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
    async def withdraw(ctx, amount):
        if userdb.find_one({"userid": ctx.author.id}):
            userdata = userdb.find_one({"userid": ctx.author.id})["economy"]["bank"]
            if userdata > 0:
                if not amount.isdigit():
                    if any(x in amount.lower() for x in ["all", 'max', 'everything', 'maximum', 'a']):
                        userdb.bulk_write([
                            pymongo.UpdateOne(
                                {"userid": ctx.author.id},
                                {"$inc": {"economy.wallet": userdata, "economy.bank": -userdata}}
                            )
                        ])
                        embed = voltage.SendableEmbed(
                            title=ctx.author.display_name,
                            icon_url=ctx.author.display_avatar.url,
                            description=f"You withdrew **all** the money from your bank account! {sep}You have `${userdb.find_one({'userid': ctx.author.id})['economy']['bank']:,}` in your bank account!",
                            color="#198754",
                        )
                        await ctx.reply(embed=embed)
                elif int(amount) < userdata:
                    userdb.bulk_write([
                        pymongo.UpdateOne(
                            {"userid": ctx.author.id},
                            {"$inc": {"economy.wallet": int(amount), "economy.bank": -int(amount)}}
                        )
                    ])
                    amt = int(amount)
                    embed = voltage.SendableEmbed(
                        title=ctx.author.display_name,
                        icon_url=ctx.author.display_avatar.url,
                        description=f"You withdrew `${amt:,}` from your bank account! {sep}You have `${userdb.find_one({'userid': ctx.author.id})['economy']['bank']:,}` in your bank account!",
                        color="#00FF00",
                    )
                    await ctx.reply(embed=embed)
                else:
                    await ctx.reply("You're trying to deposit more than you have in your bank!")
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

    @eco.command(name="daily", aliases=["dailies"], description="Claim your daily reward! (5,000 - 15,000 coins!)")
    @limiter(86400, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please try again in `{strfdelta(datetime.timedelta(seconds=delay), '{hours}h {minutes}m {seconds}s')}`!"))
    async def daily(ctx):
        if userdb.find_one({"userid": ctx.author.id}):
            amount = random.randint(5000, 15000)
            userdb.bulk_write(
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
    async def shop(ctx, item:str=None):
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
            if userdb.find_one({"userid": ctx.author.id}):
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
                    await buy_item(ctx, "Resume", 250)
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
                    await buy_item(ctx, "Golden Egg", 5000)
                elif any(x in item.lower() for x in [
                    "pb",
                    "playboi",
                    "playboy",
                    "magazine",
                    "magasine",
                    "playb",
                    "pboy",
                ]):
                    await buy_item(ctx, "Playboy", 1000)
            else:
                await create_account(ctx)

    return eco