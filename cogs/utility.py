import voltage, pymongo, os, asyncio, json, datetime, time, pendulum
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

    @utility.command(
        description="🕒 | Set a reminder up to a month! (1d, 1h, 1m, 1s) 'm!reminder 10 'm' do the dishes'",
        name="reminder",
        aliases=["remind", "alert", "timer", "schedule", "setreminder", "setalert", "settimer", "setschedule"]
    )
    async def reminder(ctx, time:int, timetype, *, reminder):
        mainembed = voltage.SendableEmbed(
            description=f"""
Set a reminder: `{reminder}`
See you in `{time}{timetype}`!
""",
            colour="#516BF2",
        )
        mtime = 0
        if timetype.lower() in ["s", "sec", "seconds"]:
            mtime = time
        elif timetype.lower() in ["m", "min", "minutes"]:
            mtime = time * 60
        elif timetype.lower() in ["h", "hrs", "hs", "hours", "hour", "hr"]:
            mtime = time * 3600
        elif timetype.lower() in ["d", "day", "da", "days"]:
            mtime = time * 86400
        else:
            mtime = time
        if mtime == 0:
            embed = voltage.SendableEmbed(
                title='Warning',
                description='Please specify a proper duration.',
                colour="#B59F3B"
            )
            await ctx.reply(embed=embed, content="[]()")
        elif mtime > 7776000:
            embed = voltage.SendableEmbed(
                title='Warning', 
                description='Your reminder is **too far** in the future!\nMaximum duration is 90 days.',
                colour="#FF0000"
                )
            await ctx.reply(embed=embed, content="[]()")
        else:
            msg = await ctx.send(content=ctx.author.mention, embed=mainembed)
            await asyncio.sleep(mtime)
            finished = voltage.SendableEmbed(
                title=f"Reminded on {pendulum.now().to_day_datetime_string()}!",
                url=f"https://app.revolt.chat/server/{ctx.server.id}/channels/{ctx.channel.id}/{ctx.message.id}",
                description=f"`{time}{timetype}` ago you asked me to remind you of `{reminder}`!",
                colour="#00FF00",
            )
            editwith = voltage.SendableEmbed(
                title=f"Reminded on {pendulum.now().to_day_datetime_string()}!",
                url=f"https://app.revolt.chat/server/{ctx.server.id}/channels/{ctx.channel.id}/{ctx.message.id}",
                description=f"On *{pendulum.now().to_day_datetime_string()}*, {ctx.author.mention} asked me to remind them of:\n`{reminder}`.",
                colour="#FF0000",
            )
            await ctx.send(content=ctx.author.mention, embed=finished)
            try:
                await msg.edit(content=ctx.author.mention, embed=editwith)
            except:
                pass

    return utility