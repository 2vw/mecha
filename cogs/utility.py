import voltage, pymongo, os, asyncio, json, datetime, time, pendulum, re
from mcstatus import JavaServer
from functools import wraps
from voltage.ext import commands
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

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
    "More command testing, use these if you want *basic* utility commands."
    )

    @utility.command()
    @limiter(10, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def stats(ctx):
        """Different from normal stats, the normal one shows the stats of the bot, this one shows complex stats. Like CPU usage and whatnot."""
        with open("json/data.json", "r") as f:
            uptime = json.load(f)['uptime']
        embed = voltage.SendableEmbed(
        title=f"{client.user.name}'s Stats",
        description=f"""
## Bot Stats
> Servers: `{len(client.servers)}`
> Users: `{len(client.users)}`
> Uptime: `{str(datetime.timedelta(seconds=int(round(time.time() - uptime))))}s`
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
                print(e)

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
        for doc in userdb.find().sort([("levels.xp", pymongo.DESCENDING)]).limit(10):
            count += 1
            if count <= 3:
                emoji = ["0", "🥇", "🥈", "🥉"]
                lb.append(f"{"#" * count} **{emoji[count]}** {doc['username']}\n**LVL{doc['levels']['level']}** | **{doc['levels']['totalxp'] + doc['levels']['xp']}XP**")
            elif count == 4:
                lb.append(f"\n**#4** -> {doc['username']}: **LVL {doc['levels']['level']}** | **{doc['levels']['totalxp'] + doc['levels']['xp']} XP**")
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
    
    @utility.command(name="xp", description="Gets your XP and level!")
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
        embed = voltage.SendableEmbed(
            title = f"{user.display_name}'s XP",
            description = f"""
**{user.name}** has **{txp + xp}** XP and is currently level **{level}**!
**{user.name}** is **{5 * (level ^ 2) + (50 * level) + 100 - xp}** XP away from level **{level + 1}**!
        """,
        colour="#516BF2"
        )
        await ctx.reply(embed=embed)
    
    @utility.command(description="Get information on a minecraft server!")
    @limiter(5, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def mcserver(ctx, servername):
        try:
            server = JavaServer.lookup(str(servername), timeout=5)
            status = server.status()
            embed = voltage.SendableEmbed(
                title=f"{servername}'s Information",
                description=f"**Players online:**\n`{status.players.online}` Currently Online\n**Server Latency:**\n`{round(status.latency, 2)}ms`",
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
**Suggestion From:** {ctx.guild.name}
**Suggestion:** 
{message}
            """,
            color="#516BF2"
        )
        channel = client.get_channel(config['SUGGESTION_CHANNEL'])
        await channel.send(embed=embed)
        await ctx.reply("You're suggestion has been sent! Thanks for suggesting something!")
    
    return utility