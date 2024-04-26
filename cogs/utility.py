import asyncio
import json
import re
import time

import pendulum
import pilcord
import pymongo
import revolt
# from mcstatus import JavaServer
from revolt.ext import commands

from main import MyClient

with open("json/config.json", "r") as f:
    config = json.load(f)

# TODO: Add settings or add customization options for this
settings = pilcord.CardSettings(
    background_color="#454FBF",
    text_color="white",
    bar_color="#5945bf",
    background="assets/background.jpg"
)


def parse_time(time: str):  # I am not touching this  - andreaw
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


# Fixed :)
async def get_badges(badges, user: revolt.User):
    """
    Outputs a sorted array of badge names
    """
    badgeslist = []
    with open("json/data.json", "r") as f:
        data = json.load(f)

    for badge in badges:
        if badge.lower() in data:
            # if (await userdb.find_one({"userid": user.id}))['status'][badge.lower()]:
            badgeslist.append(f":{data.get(badge)}:")

    # Output the sorted array of badge names
    return badgeslist


class Utility(commands.Cog):
    description = "Utility commands for Mecha, these commands consist of leaderboard commands, leveling commands, and more."

    def __init__(self, client: MyClient):
        self.client: MyClient = client

    @commands.command(
        name="profile",
        aliases=["ui", "userinfo"]
    )
    async def profile(self, ctx, user: revolt.User = None):
        """Get information on any user! Including yourself!"""
        user = user or ctx.author

        user_data = await self.client.db_client.get_user(user)
        print(user_data)
        if user_data is not None:
            data = user_data['status']
            badges = await get_badges(data, user_data)
            badgetext = f"\n## {''.join(badges)}"
            ubio = user_data['profile']['bio'],
            colour = user_data['profile']['colour']
        else:
            colour = "#454FBF"
            badgetext = ""
            ubio = "No bio set."

        embed = revolt.SendableEmbed(
            title=f"{user.display_name}'s Profile",
            description=f"""###
### **Username:** `{user.name}#{user.discriminator}`{badgetext}
> **ID:** `{user.id}`
### **Bio:** 
> {ubio}""",
            colour=colour
        )
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.cooldown(1, 10, bucket=commands.BucketType.user)
    async def stats(self, ctx):
        """Get some statistics up in here!"""
        with open("json/data.json", "r") as f:
            uptime = json.load(f)['uptime']

        elapsed_time = int(time.time() - uptime)
        days, remainder = divmod(elapsed_time, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = revolt.SendableEmbed(
            title=f"{self.client.user.name}'s Stats",
            description=f"""
## Bot Stats
> Servers: `{len(self.client.servers)}`
> Users: `{len(self.client.users)}`
> [Uptime](https://stats.uptimerobot.com/2JgmlCVB0O): `{days}d {hours}h {minutes}m {seconds}s`
            """,
            colour="#44ff44"
        )  # fix the uptime formatting at some point I swear to god
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Get the bot's ping!"""
        # `{round((time.time() - ctx.message.created_at)*1000,2)}ms`
        await ctx.reply(f"Pong!")

    @commands.command(name="avatar", aliases=["av", "getav", "ua"])
    @commands.cooldown(1, 3, bucket=commands.BucketType.user)
    async def avatar(self, ctx, member: revolt.Member = None):
        """Get a users avatar!"""

        member = member or ctx.author

        if member.display_avatar:
            b = await member.display_avatar.read()
            f = revolt.File(b)
            u = await self.client.upload_file(f, 'attachments')
            embed = revolt.SendableEmbed(
                title=f"{member.display_name}'s avatar!",
                media=u.id,
                colour="#516BF2",
            )
            await ctx.reply(embed=embed)
        else:
            return await ctx.reply(f"{member.name} does not have an avatar!")

    @commands.command(
        name="reminder", aliases=["remind", "alert", "timer", "schedule", "setreminder", "setalert", "settimer",
                                  "setschedule"]
        )
    @commands.cooldown(1, 10, bucket=commands.BucketType.user)
    async def reminder(self, ctx: commands.Context, time, *, message):
        """🕒 | Set a reminder up to a month! (1d, 1h, 1m, 1s) 'm!reminder 10 'm' do the dishes'"""
        if not message:
            message = "No message provided."

        rtime = parse_time(str(time))
        if not rtime:
            return await ctx.send("Please specify a proper duration. (i.e 10s, 5m, 1h, 1d)")
        mainembed = revolt.SendableEmbed(
            description=f"""
Set a reminder: `{message}`
See you in `{time}`!
""",
            colour="#516BF2",
        )
        mtime = time
        if mtime == 0:
            embed = revolt.SendableEmbed(
                title='Warning',
                description='Please specify a proper duration.',
                colour="#B59F3B"
            )
            await ctx.reply(embed=embed, content="[]()")
        elif rtime == 0:
            embed = revolt.SendableEmbed(
                title='Warning',
                description='Your reminder is **too far** in the future!\nMaximum duration is 90 days.',
                colour="#FF0000"
            )
            await ctx.reply(embed=embed, content="[]()")
        else:
            msg = await ctx.send(content=ctx.author.mention, embed=mainembed)
            await asyncio.sleep(rtime)
            finished = revolt.SendableEmbed(
                title=f"Reminded on {pendulum.now().to_day_datetime_string()}!",
                url=ctx.message.jump_url,
                description=f"`{time}` ago you asked me to remind you of `{message}`!",
                colour="#00FF00",
            )
            editwith = revolt.SendableEmbed(
                title=f"Reminded on {pendulum.now().to_day_datetime_string()}!",
                url=ctx.message.jump_url,
                description=f"On *{pendulum.now().to_day_datetime_string()}*, {ctx.author.mention} asked me to remind them of:\n`{message}`.",
                colour="#FF0000",
            )
            await ctx.send(content=ctx.author.mention, embed=finished)

            try:
                await msg.edit(content=ctx.author.mention, embeds=[editwith])
            except Exception:
                pass

    @commands.command()
    @commands.cooldown(1, 10, bucket=commands.BucketType.user)
    async def leaderboard(self, ctx):
        lb = []
        count = 0
        d = self.client.db_client.userdb.find().sort([("levels.totalxp", pymongo.DESCENDING)]).limit(10)
        for doc in (await d.to_list(length=10)):
            count += 1
            if count <= 3:
                emoji = ["0", "🥇", "🥈", "🥉"]
                lb.append(
                    f"{'#' * count} **{emoji[count]}** {doc['username']}\n**LVL{doc['levels']['level']}** | **{doc['levels']['totalxp'] + doc['levels']['xp']}XP**"
                    )
            elif count == 4:
                lb.append(
                    f"\n**#4** -> {doc['username']}: **LVL {doc['levels']['level']}** | **{doc['levels']['totalxp'] + doc['levels']['xp']} XP**"
                    )
            else:
                lb.append(
                    f"**#{count}** -> {doc['username']}: **LVL {doc['levels']['level']}** | **{doc['levels']['totalxp'] + doc['levels']['xp']} XP**"
                    )

        embed = revolt.SendableEmbed(
            title="View the Leaderboard",
            description='\n'.join(lb),
            color="#516BF2"
        )
        await ctx.send(
            embed=embed
        )

    @commands.command(aliases=["setbio", "sb", "changebio", "createbio", "cb", "sbio"], name="bio")
    async def bio(self, ctx, *, bio: str):
        """Set your bio"""
        if len(bio) > 300:
            return await ctx.send(
                "Your bio is too looooooooooooooooooooooooooong! Make sure its 300 characters or less!"
            )

        user_data = await self.client.db_client.get_user(ctx.author)
        if user_data:
            await self.client.db_client.userdb.update_one(
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

    @commands.command(name="xp", aliases=['level'])
    @commands.cooldown(1, 3, bucket=commands.BucketType.user)
    async def xp(self, ctx, user: revolt.User = None):  # Bot just shuts down ._.  - andreaw
        """Gets your XP and level!"""
        user = user or ctx.author

        try:
            data = await self.client.db_client.get_user(ctx.author)
        except Exception:
            return await ctx.send("User not found!")
        level = data['levels']['level']  # this is so stupid
        xp = data['levels']['xp']  # this is so stupid
        txp = data['levels']['totalxp']  # this is so stupid
        a = pilcord.RankCard(
            settings=settings,
            avatar=user.display_avatar.url or user.default_avatar.url,
            level=level,
            current_exp=xp,
            max_exp=5 * (level ^ 2) + (50 * level) + 100,
            username=user.display_name
        )
        card = await a.card3()

        await ctx.reply(attachments=[revolt.File(f=card.read(), filename="rank.png")])

    # mcstatus errors for me, idk  - andreaw
    # @commands.command()
    # @commands.cooldown(1, 5, bucket=commands.BucketType.user)
    # async def mcserver(self, ctx, servername):
    #     """Get information on a minecraft server!"""
    #
    #     try:
    #         server = JavaServer.lookup(str(servername), timeout=5)
    #         status = server.status()  # this might be blocking
    #         embed = revolt.SendableEmbed(
    #             title=f"{servername}'s Information",
    #             description=f"**Players online:**\n`{status.players.online}` Currently Online\n**Server Latency:**\n`{round(status.latency, 2)}ms`",
    #             colour="#516BF2",
    #         )
    #         await ctx.reply(embed=embed)
    #     except Exception:
    #         await ctx.reply("Server not found! Or the server is offline!\n`TIP: the server name might end in .net or .com! Try both!`")

    @commands.command(name="suggest", aliases=['suggestion', 'sug', 'request', 'feature', 'idea'])
    @commands.cooldown(1, 20, bucket=commands.BucketType.user)
    async def suggest(self, ctx, *, message):
        """Suggest something!"""
        if len(message) > 1000:
            return await ctx.send("Suggestion must be under 1000 characters!")

        embed = revolt.SendableEmbed(
            title="Suggestion!",
            description=f"""
**Suggested by:** {ctx.author.mention}
**Suggestion From:** {ctx.server.name}
**Suggestion:** 
{message}
            """,
            color="#516BF2"
        )
        channel = self.client.get_channel(config['SUGGESTION_CHANNEL'])
        await channel.send(embed=embed)
        await ctx.reply("You're suggestion has been sent! Thanks for suggesting something!")

    @commands.command(name="prefixes", aliases=['p', 'prefix'])
    async def prefixes(self, ctx):
        """Get your personal line of prefixes!"""
        user_data = await self.client.db_client.get_user(ctx.author)

        if user_data:
            prefixes = user_data['prefixes']
            embed = revolt.SendableEmbed(
                title="Your prefixes!",
                description=f"Your prefixes are:\n ```\n{chr(10).join(prefixes)}\n```",
                colour="#516BF2",
            )
            await ctx.reply(embed=embed)
        else:
            return ctx.send("You dont have an account! Create one with the `m!add` command!")

    @commands.command(name="addprefix", aliases=['ap', 'newprefix', 'add-prefix'])
    async def addprefix(self, ctx, *, prefix):
        """Add a prefix to your personal line of prefixes!"""

        user_data = await self.client.db_client.get_user(ctx.author)
        if user_data:
            if prefix[0] == " ":
                return await ctx.send("Prefix cannot start with a space!")
            elif any(x in prefix for x in user_data['prefixes']):
                return await ctx.send("This prefix is already in your list of prefixes!")
            else:
                await self.client.db_client.userdb.update_one(
                    {'userid': ctx.author.id}, {'$push': {'prefixes': prefix}}
                    )
                prefixes = user_data['prefixes']
                embed = revolt.SendableEmbed(
                    title="Added a new prefix to your list!",
                    description=f"Added `{prefix}` to your list of {len(prefixes) + 1}!\nTo see your prefixes, type `m!prefixes` or alternatively; mention me!",
                    colour="#516BF2",
                )
                await ctx.reply(embed=embed)
        else:
            return await ctx.send("You dont have an account! Create one with the `m!add` command!")

    @commands.command(name="removeprefix", aliases=['rp', 'remove-prefix'])
    async def removeprefix(self, ctx, *, prefix):
        """Remove a prefix from your personal line of prefixes!"""

        user_data = await self.client.db_client.get_user(ctx.author)
        if user_data:
            if len(user_data['prefixes']) > 1:
                if prefix in user_data['prefixes']:
                    await self.client.db_client.userdb.update_one(
                        {'userid': ctx.author.id}, {'$pull': {'prefixes': prefix}}
                        )
                    embed = revolt.SendableEmbed(
                        title="Removed a prefix from your list!",
                        description=f"Removed `{prefix}` from your list of {len(prefixes) - 1}!\nTo see your prefixes, type `m!prefixes` or alternatively; mention me!",
                    )
                    await ctx.reply(embed=embed)
                else:
                    return await ctx.send("That prefix is not in your list!", delete_after=3)
            else:
                return await ctx.send("You can't remove the only prefix!", delete_after=3)
        else:
            return await ctx.send("You dont have an account! Create one with the `m!add` command!", delete_after=3)

    # thanks to TheBobBobs for the formatting, what a G
    @commands.command(name="snitch")
    async def snitch(self, ctx):
        """Find out who reacted to any message with any reaction!"""
        if not ctx.message.reply_ids:
            return await ctx.send("no")

        i = 0
        for message_id in ctx.message.reply_ids:
            reply = await ctx.channel.fetch_message(message_id)
            text = ""
            if len(reply.reactions) > 0:
                for reaction in reply.reactions:
                    users = reply.reactions[reaction]
                    user_mentions = ' '.join(fr'<\@{u.id}>' for u in users)
                    text += f":{reaction}: - {len(reply.reactions[reaction])}\n- {user_mentions}\n"

                embed = revolt.SendableEmbed(
                    title="Snitch!",
                    description=f"{text}\n\n[{reply.content}]({reply.jump_url})",
                    colour="#00FF00",
                )
                await ctx.reply(embed=embed)
            else:
                embed = revolt.SendableEmbed(
                    title="Snitch!",
                    description="No reactions were found!",
                    colour="#FF0000",
                )
                await ctx.reply(embed=embed)
            i += 1

    # @commands.command()
    # async def confirm(self, ctx):
    #     embed = revotl.SendableEmbed(
    #         title="Confirm!",
    #         description="React with ✅ to confirm!",
    #         colour="#516BF2",
    #         icon_url=ctx.author.display_avatar.url
    #     )
    #     ms = await ctx.send(embed=embed, interactions={"reactions": ["✅"], "restrict_reactions": False})
    #     try:
    #         def check(message, user, reaction):
    #             #print(message.id == ms.id)
    #             #print(user == ctx.author.id)
    #             #print(reaction == "✅")
    #             return ms.id == message.id and user == ctx.author.id and reaction == "✅"
    #         await client.wait_for("message_react", check=check, timeout=15.0)
    #         embed = revolt.SendableEmbed(
    #             title="Confirmed!",
    #             description="You have confirmed!",
    #             colour="#00FF00",
    #             icon_url=ctx.author.display_avatar.url
    #         )
    #         return await ms.edit(embed=embed)
    #     except asyncio.TimeoutError:
    #         return await ctx.send("Confirmation timed out!")

    @commands.command(
        name="familyfriendly",
        aliases=['ff', 'family-friendly', 'f-f'],
    )
    async def familyfriendly(self, ctx, toggle: bool):
        """Removes some of the nsfw commands and makes Mecha more family friendly PG clean"""
        user_data = await self.client.db_client.get_user(ctx.author)
        if user_data:
            if toggle:
                await self.client.db_client.userdb.update_one(
                    {
                        'userid': ctx.author.id
                    },
                    {
                        '$set': {
                            'status.familyfriendly': True
                        }
                    }
                )
                embed = revolt.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Family friend mode `Activated`! | 😇",
                    color="#00FF00",
                )
                await ctx.send(content="[]()", embed=embed)
            else:
                await self.client.db_client.userdb.update_one(
                    {
                        'userid': ctx.author.id
                    },
                    {
                        '$set': {
                            'status.familyfriendly': False
                        }
                    }
                )
                embed = revolt.SendableEmbed(
                    title=ctx.author.display_name,
                    icon_url=ctx.author.display_avatar.url,
                    description="Family friend mode `Deactivated`! | 😈",
                    color="#00FF00",
                )
                await ctx.send(content="[]()", embed=embed)
        else:
            embed = revolt.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description="Please create an account with `m!add`!",
                color="#dc3545",
            )
            await ctx.reply(embed=embed)

    @commands.command(name="afk", aliases=["awayfromkeyboard", 'brb'])
    async def afk(self, ctx, *, reason: str = "AFK"):
        """Set your AFK status!"""
        user_data = await self.client.db_client.get_user(ctx.author)
        if user_data:
            await self.client.db_client.userdb.update_one(
                {
                    'userid': ctx.author.id
                },
                {
                    '$set': {
                        f'status.afk.{ctx.server.id}': {
                            f'reason': reason,
                            f'lastseen': int(time.time()),
                            f'afk': True
                        }
                    }
                }
            )
            embed = revolt.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description=f"Set your AFK status to:\n{reason}",
                color="#00FF00"
            )
            await ctx.reply(embed=embed)
        else:
            embed = revolt.SendableEmbed(
                title=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url,
                description="Please create an account with `m!add`!",
                color="#dc3545",
            )
            await ctx.reply(embed=embed)

    @commands.command(name="inbox")
    async def inbox(self, ctx, page: int = 1):
        """View your inbox!"""

        notifications_per_page = 5
        skipped_notifications = (page - 1) * notifications_per_page
        i = 0 + skipped_notifications
        user_data = await self.client.db_client.get_user(ctx.author)
        user_notifications = user_data['notifications']['inbox']

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
                description += f"\n{str(days) + 'd ' if days > 0 else ''}{str(hours) + 'h ' if hours > 0 else ''}{str(minutes) + 'm ' if minutes > 0 else ''}{seconds}s ago • {user_notifications[notification]['message']}\n"

        embed = revolt.SendableEmbed(
            title=f"Inbox for {ctx.author.display_name}",
            description=description,
            colour="#00FF00"
        )
        await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Utility(client))
