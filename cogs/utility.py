import voltage, pymongo, os, asyncio, json, datetime, time, pendulum, re
from voltage.ext import commands

def setup(client) -> commands.Cog:
    utility = commands.Cog(
    "Utility",
    "More command testing, use these if you want *basic* utility commands."
    )

    @utility.command()
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
            except Exception as e:
                print(e)

    @utility.command(
        description="Get a users avatar!", 
        name="avatar", 
        aliases=["av", "getav", "ua"],
        #usage="m!avatar <user>",
        #example="m!avatar @css"
    )
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
    async def reminder(ctx, time, **message):
        if not message:
            message = "No message provided."
        if time:
            rtime = parse_time(str(time))
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

    return utility