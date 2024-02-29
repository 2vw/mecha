import voltage, pymongo, os, asyncio, json, datetime, time, pendulum, re, requests, pilcord
from mcstatus import JavaServer
from functools import wraps
from voltage.ext import commands
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

sep = "\n"

# TODO: Add settings or add customization options for this
settings = pilcord.CardSettings(
    background_color="#454FBF",
    text_color="white",
    bar_color="#5945bf",
    background="assets/background.jpg"
)

# Fixed :)
async def get_badges(badges, user:voltage.User):
    """
    Outputs a sorted array of badge names
    """
    badgeslist = []
    with open("json/data.json", "r") as f:
        data = json.load(f)
        
    for badge in badges:
        if badge.lower() in data:
            if userdb.find_one({"userid": user.id})['status'][badge.lower()]:
                badgeslist.append(f":{data.get(badge)}:")
    
    # Output the sorted array of badge names
    return badgeslist

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

def setup(client) -> commands.Cog:
    utility = commands.Cog(
    "Utility",
    "Utility commands for Mecha, these commands consist of leaderboard commands, leveling commands, and more."
    )

    """@utility.command(
        name="profile",
        aliases=["ui", "userinfo"],
        description = "Get information on any user! Including yourself!"
    )
    async def profile(ctx, user: voltage.User = None):
        if not user:
            user = ctx.author
        if userdb.find_one({"userid": user.id}):
            userdata = userdb.find_one({"userid": user.id})
            data = userdata['status']
            badges = await get_badges(data, user)
            badgetext = f"{sep}## {''.join(badges)}"
            ubio = str(userdata['profile']['bio']),
            colour = userdata['profile']['colour']
        elif not userdb.find_one({"userid": user.id}):
            colour = "#454FBF"
            badgetext = ""
            ubio = "No bio set."
        userdate = user.created_at
        embed = voltage.SendableEmbed(
            title=f"{user.display_name}'s Profile",
            description=f###
### **Username:** `{user.name}#{user.discriminator}`{badgetext}
> **ID:** `{user.id}`
### **Bio:** 
> {ubio}
###,
            colour=colour
        )
        await ctx.reply(embed=embed)"""

    @utility.command()
    @limiter(10, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def stats(ctx):
        """Get some statistics up in here!"""
        with open("json/data.json", "r") as f:
            uptime = json.load(f)['uptime']
        elapsed_time = int(time.time() - uptime)
        days, remainder = divmod(elapsed_time, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        embed = voltage.SendableEmbed(
        title=f"{client.user.name}'s Stats",
        description=f"""
## Bot Stats
> Servers: `{len(client.servers)}`
> Users: `{len(client.users)}`
> [Uptime](https://stats.uptimerobot.com/2JgmlCVB0O): `{days}d {hours}h {minutes}m {seconds}s`
        """,
        colour="#44ff44"
        ) # fix the uptime formatting at some point i swear to god
        await ctx.send(embed=embed)

    def parse_time(time:str):
        if time:
            gtime = 0
            try:
                if any(x in time for x in ["d", "h", "m", "s"]):
                    # mlist = list[time] will use this soon :) just gotta get a release out tbh
                    mtime = re.sub("d|h|m|s", "", time)
                    if any(x in time for x in ["s", "sec", "seconds"]):
                        ntime = int(re.sub("d|h|m|s", "", str(time)))
                        stime = ntime * 1
                    elif any(x in time for x in ["m", "min", "minutes"]):
                        ntime = int(re.sub("d|h|m|s", "", str(time)))
                        mintime = ntime * 60
                    elif any(x in time for x in ["h", "hrs", "hs", "hours", "hour", "hr"]):
                        ntime = int(re.sub("d|h|m|s", "", str(time)))
                        htime = ntime * 3600
                    elif any(x in time for x in ["d", "day", "da", "days"]):
                        ntime = int(re.sub("d|h|m|s", "", str(time)))
                        dtime = ntime * 86400
                    try:
                        if stime:
                            gtime = gtime + int(stime)
                    except:
                        pass
                    try:
                        if mintime:
                            gtime = gtime + int(mintime)
                    except:
                        pass
                    try:
                        if htime:
                            gtime = gtime + int(htime)
                    except:
                        pass
                    try:
                        if dtime:
                            gtime = gtime + int(dtime)
                    except:
                        pass
                    if int(gtime) > 7776000:
                        return 0
                    return gtime
                else:
                    return None
            except Exception as e:
                return e

    @utility.command(
        description="Get a users avatar!", 
        name="avatar", 
        aliases=["av", "getav", "ua"],
        #usage="m!avatar <user>",
        #example="m!avatar @css"
    )
    @limiter(3, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def avatar(ctx, member: voltage.Member):
        embed = voltage.SendableEmbed(
            title=f"{member.display_name}'s avatar!",
            media=member.display_avatar.url,
            colour="#516BF2",
        )
        await ctx.reply(content="[]()", embed=embed)

    @utility.command(
        description="🕒 | Set a reminder up to a month! (1d, 1h, 1m, 1s) 'm!reminder 10 'm' do the dishes'",
        name="reminder",
        aliases=["remind", "alert", "timer", "schedule", "setreminder", "setalert", "settimer", "setschedule"],
        #usage="m!reminder <time> <message>",
        #example="m!reminder 10m do the dishes"
    )
    @limiter(10, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def reminder(ctx, time, **message):
        if not message:
            message = "No message provided."
        if time:
            rtime = parse_time(str(time))
            if not rtime:
                return await ctx.send("Please specify a proper duration. (i.e 10s, 5m, 1h, 1d)")
        mainembed = voltage.SendableEmbed(
            description=f"""
Set a reminder: `{message}`
See you in `{time}`!
""",
            colour="#516BF2",
        )
        mtime = time
        if mtime == 0:
            embed = voltage.SendableEmbed(
                title='Warning',
                description='Please specify a proper duration.',
                colour="#B59F3B"
            )
            await ctx.reply(embed=embed, content="[]()")
        elif rtime == 0:
            embed = voltage.SendableEmbed(
                title='Warning', 
                description='Your reminder is **too far** in the future!\nMaximum duration is 90 days.',
                colour="#FF0000"
                )
            await ctx.reply(embed=embed, content="[]()")
        else:
            msg = await ctx.send(content=ctx.author.mention, embed=mainembed)
            await asyncio.sleep(rtime)
            finished = voltage.SendableEmbed(
                title=f"Reminded on {pendulum.now().to_day_datetime_string()}!",
                url=f"https://app.revolt.chat/server/{ctx.server.id}/channels/{ctx.channel.id}/{ctx.message.id}",
                description=f"`{time}` ago you asked me to remind you of `{message}`!",
                colour="#00FF00",
            )
            editwith = voltage.SendableEmbed(
                title=f"Reminded on {pendulum.now().to_day_datetime_string()}!",
                url=f"https://app.revolt.chat/server/{ctx.server.id}/channels/{ctx.channel.id}/{ctx.message.id}",
                description=f"On *{pendulum.now().to_day_datetime_string()}*, {ctx.author.mention} asked me to remind them of:\n`{message}`.",
                colour="#FF0000",
            )
            await ctx.send(content=ctx.author.mention, embed=finished)
            try:
                await msg.edit(content=ctx.author.mention, embed=editwith)
            except:
                pass
    
    @utility.command()
    @limiter(10, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def leaderboard(ctx):
        lb = []
        count = 0
        for doc in userdb.find().sort([("levels.totalxp", pymongo.DESCENDING)]).limit(10):
            count += 1
            if count <= 3:
                emoji = ["0", "🥇", "🥈", "🥉"]
                lb.append(f"{'#' * count} **{emoji[count]}** {doc['username']}{sep}**LVL{doc['levels']['level']}** | **{doc['levels']['totalxp'] + doc['levels']['xp']}XP**")
            elif count == 4:
                lb.append(f"{sep}**#4** -> {doc['username']}: **LVL {doc['levels']['level']}** | **{doc['levels']['totalxp'] + doc['levels']['xp']} XP**")
            else:
                lb.append(f"**#{count}** -> {doc['username']}: **LVL {doc['levels']['level']}** | **{doc['levels']['totalxp'] + doc['levels']['xp']} XP**")
        embed = voltage.SendableEmbed(
            title = "View the Leaderboard",
            description='\n'.join(lb),
            color="#516BF2"
        )
        await ctx.send(
            embed=embed
        )
    
    @utility.command(
        aliases=["setbio", "sb", "changebio", "createbio", "cb", "sbio"],
        name="bio",
        description="Set your bio"
    )
    async def bio(ctx, *, bio: str):
        if userdb.find_one({"userid": ctx.author.id}):
            if len(bio) > 250:
                return await ctx.send(
                    "Your bio is too looooooooooooooooooooooooooong! Make sure its under 250 characters!"
                )
            userdb.update_one(
                {"userid": ctx.author.id},
                {"$set": {"bio": bio}}
            )
            await ctx.send(
                f"Set your bio to `{bio}`!"
            )
        else:
            return await ctx.send(
                "You need to create an account first!"
            )
    
    @utility.command(name="xp", description="Gets your XP and level!", aliases=["profile", 'level', 'ui', 'userinfo'])
    @limiter(3, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def xp(ctx, user:voltage.User=None):
        if not user:
            user = ctx.author
        try:
            data = userdb.find_one({'userid':user.id})
        except:
            return await ctx.send("User not found!")
        level = data['levels']['level'] # this is so stupid
        xp = data['levels']['xp'] # this is so stupid
        txp = data['levels']['totalxp'] # this is so stupid
        a = pilcord.RankCard(
            settings=settings,
            avatar=user.display_avatar.url or user.default_avatar.url,
            level=level,
            current_exp=xp,
            max_exp=5 * (level ^ 2) + (50 * level) + 100,
            username=user.display_name
        )
        card = await a.card3()
        
        await ctx.reply(attachments=[voltage.File(f=card.read(), filename="rank.png")])
    
    @utility.command(description="Get information on a minecraft server!")
    @limiter(5, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def mcserver(ctx, servername):
        try:
            server = JavaServer.lookup(str(servername), timeout=5)
            status = server.status()
            embed = voltage.SendableEmbed(
                title=f"{servername}'s Information",
                description=f"**Players online:**{sep}`{status.players.online}` Currently Online{sep}**Server Latency:**{sep}`{round(status.latency, 2)}ms`",
                colour="#516BF2",
            )
            await ctx.reply(embed=embed)
        except:
            await ctx.reply("Server not found! Or the server is offline!\n`TIP: the server name might end in .net or .com! Try both!`")
    
    @utility.command(name="suggest", aliases=['suggestion', 'sug', 'request', 'feature', 'idea'], description="Suggest something!")
    @limiter(20, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def suggest(ctx, *, message):
        if len(message) > 1000:
            return await ctx.send("Suggestion must be under 1000 characters!")
        embed = voltage.SendableEmbed(
            title = "Suggestion!",
            description = f"""
**Suggested by:** {ctx.author.mention}
**Suggestion From:** {ctx.server.name}
**Suggestion:** 
{message}
            """,
            color="#516BF2"
        )
        channel = client.get_channel(config['SUGGESTION_CHANNEL'])
        await channel.send(embed=embed)
        await ctx.reply("You're suggestion has been sent! Thanks for suggesting something!")
    
    @utility.command(
        name="prefixes",
        aliases=['p', 'prefix'],
        description="Get your personal line of prefixes!",
    )
    async def prefixes(ctx):
        if userdb.find_one({'userid':ctx.author.id}):
            prefixes = userdb.find_one({'userid':ctx.author.id})['prefixes']
            embed = voltage.SendableEmbed(
                title="Your prefixes!",
                description=f"Your prefixes are:{sep} ```{sep}{f'{sep}'.join(prefixes)}{sep}```",
                colour="#516BF2",
            )
            await ctx.reply(embed=embed)
        else:
            return ctx.send("You dont have an account! Create one with the `m!add` command!")
    
    @utility.command(
        name="addprefix",
        aliases=['ap', 'newprefix', 'add-prefix'],
        description="Add a prefix to your personal line of prefixes!",
    )
    async def addprefix(ctx, *, prefix):
        if userdb.find_one({'userid':ctx.author.id}):
            if prefix[0] == " ":
                return await ctx.send("Prefix cannot start with a space!")
            elif any(x in prefix for x in userdb.find_one({'userid':ctx.author.id})['prefixes']):
                return await ctx.send("This prefix is already in your list of prefixes!")
            else:
                userdb.update_one({'userid':ctx.author.id}, {'$push':{'prefixes':prefix}})
                prefixes = userdb.find_one({'userid':ctx.author.id})['prefixes']
                embed = voltage.SendableEmbed(
                    title="Added a new prefix to your list!",
                    description=f"Added `{prefix}` to your list of {len(prefixes)}!{sep}To see your prefixes, type `m!prefixes` or alternatively; mention me!",
                    colour="#516BF2",
                )
                await ctx.reply(embed=embed)
        else:
            return await ctx.send("You dont have an account! Create one with the `m!add` command!")
    
    @utility.command(
        name="removeprefix",
        aliases=['rp', 'remove-prefix'],
        description="Remove a prefix from your personal line of prefixes!",
    )
    async def removeprefix(ctx, *, prefix):
        if userdb.find_one({'userid':ctx.author.id}):
            if len(userdb.find_one({'userid':ctx.author.id})['prefixes']) > 1 :
                if prefix in userdb.find_one({'userid':ctx.author.id})['prefixes']:
                    userdb.update_one({'userid':ctx.author.id}, {'$pull':{'prefixes':prefix}})
                    prefixes = userdb.find_one({'userid':ctx.author.id})['prefixes']
                    embed = voltage.SendableEmbed(
                        title="Removed a prefix from your list!",
                        description=f"Removed `{prefix}` from your list of {len(prefixes)}!{sep}To see your prefixes, type `m!prefixes` or alternatively; mention me!",
                    )
                    await ctx.reply(embed=embed)
                else:
                    return await ctx.send("That prefix is not in your list!", delete_after=3)
            else:
                return await ctx.send("You can't remove the only prefix!", delete_after=3)
        else:
            return await ctx.send("You dont have an account! Create one with the `m!add` command!", delete_after=3)
    
    
    # thanks to TheBobBobs for the formatting, what a G
    @utility.command(name="snitch", description="Find out who reacted to any message with any reaction!")
    async def snitch(ctx):
        if ctx.message.reply_ids:
            i = 0
            for message in ctx.message.reply_ids:
                reply = await ctx.channel.fetch_message(ctx.message.reply_ids[i])
                text = ""
                if len(reply.reactions) > 0:
                    for reaction in reply.reactions:
                        users = reply.reactions[reaction]
                        user_mentions = ' '.join(f'<\@{u.id}>' for u in users)
                        text += f":{reaction}: - {len(reply.reactions[reaction])}{sep}- {user_mentions}{sep}"
                    embed = voltage.SendableEmbed(
                        title="Snitch!",
                        description=f"{text}{sep}{sep}[{reply.content}](/server/{reply.server.id}/channel/{reply.channel.id}/{reply.id})",
                        colour="#00FF00",
                    )
                    await ctx.reply(embed=embed)
                else:
                    embed = voltage.SendableEmbed(
                        title="Snitch!",
                        description="No reactions were found!",
                        colour="#FF0000",
                    )
                    await ctx.reply(embed=embed)
                i += 1
        else:
            return await ctx.send("no")
    
    @utility.command()
    async def confirm(ctx):
        try:
            result = requests.post(
                url=f"https://api.revolt.chat/channels/{ctx.channel.id}/messages",
                headers={
                    "x-bot-token": config['TOKEN']
                },
                json={
                    "content": "Do you confirm?",
                    "interactions": {
                        "reactions": [
                            "01HPX2NV8VVPYKFV0YYADQH33X"
                        ]
                    }
                }
            )
            
        except Exception as e:
            return e
    
    @utility.command(
        name="familyfriendly",
        description="Removes some of the nsfw commands and makes Mecha more family friendly PG clean",
        aliases=['ff', 'family-friendly', 'f-f'],
    )
    async def familyfriendly(ctx, toggle):
        if userdb.find_one({'userid': ctx.author.id}):
            if toggle.lower() in ["yes", "on", "activated", "y", "online", "true"]:
                userdb.update_one(
                    {
                        'userid': ctx.author.id
                    },
                    {
                        '$set': {
                            'status.familyfriendly': True
                        }
                    }
                )
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Family friend mode `Activated`! | 😇",
                    color="#00FF00",
                )
                await ctx.send(content="[]()", embed=embed)
            elif toggle.lower() in ["no", "false", "off", "deny", "removed", "n"]:
                userdb.update_one(
                    {
                        'userid': ctx.author.id
                    },
                    {
                        '$set': {
                            'status.familyfriendly': False
                        }
                    }
                )
                embed = voltage.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Family friend mode `Deactivated`! | 😈",
                    color="#00FF00",
                )
                await ctx.send(content="[]()", embed=embed)
        else:
            embed = voltage.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description="Please create an account with `m!add`!",
                color="#dc3545",
            )
            await ctx.reply(embed=embed)
    
    @utility.command(name="inbox", description="View your inbox!")
    async def inbox(ctx, page: int = 1):
        notifications_per_page = 5
        skipped_notifications = (page - 1) * notifications_per_page
        i = 0 + skipped_notifications
        user_notifications = userdb.find_one(
            {'userid': ctx.author.id}
        )['notifications']['inbox']

        if len(user_notifications) == 0:
            description = "No notifications found. 😭"
        else:
            description = "# Your Inbox\n"
            for notification in user_notifications:
                if i == notifications_per_page:
                    break
                i += 1
                elapsed_time = int(time.time() - user_notifications[notification]['date'])
                days, remainder = divmod(elapsed_time, 86400)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                description += f"\n{str(days)+'d ' if days > 0 else ''}{str(hours) + 'h ' if hours > 0 else ''}{str(minutes) + 'm ' if minutes > 0 else ''}{seconds}s ago • {user_notifications[notification]['message']}\n"

        embed = voltage.SendableEmbed(
            title=f"Inbox for {ctx.author.display_name}", 
            description=description,
            colour="#00FF00"
        )
        await ctx.send(embed=embed)
    
    return utility