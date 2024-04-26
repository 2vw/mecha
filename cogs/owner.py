import asyncio
import datetime
import json
import os
import traceback

import psutil
import pymongo
import sys
import time
import revolt

from revolt.ext import commands
from main import MyClient

with open("json/config.json", "r") as f:
    config = json.load(f)


def restart_bot():
    os.execv(sys.executable, ['python'] + sys.argv)


def get_badge(badge):
    if badge == 1:
        return "dev"
    elif badge == 2:
        return "admin"
    elif badge == 3:
        return "mod"
    elif badge == 4:
        return "bug"
    elif badge == 5:
        return "beta"
    else:
        return None


class Owner(commands.Cog):
    """Some commands for testing."""

    def __init__(self, client: MyClient):
        self.client: MyClient = client

    @commands.command(name="add", hidden=True)
    @commands.is_bot_owner()
    async def add(self, ctx, user: revolt.User = None):
        """Adds you to the database!"""

        user = user or ctx.author
        result = await self.client.db_client.add_user(user)
        await ctx.reply(f"Results are in! {result}")

    @commands.command(hidden=True)
    async def statz(self, ctx):
        """Different from normal stats, the normal one shows the stats of the bot, this one shows complex stats. Like CPU usage and whatnot."""
        with open("json/data.json", "r") as f:
            uptime = json.load(f)['uptime']

        embed = revolt.SendableEmbed(
            title=f"{self.client.user.name}'s Stats",
            description=f"""
## Computer Based Stats
> CPU Usage: `{psutil.cpu_percent()}%`
> RAM Usage: `{psutil.virtual_memory().percent}%`
> Disk Usage: `{psutil.disk_usage('/').percent}%`

## Bot Stats
> Servers: `{len(self.client.servers)}`
> Users: `{len(self.client.users)}`
> Uptime: `{str(datetime.timedelta(seconds=int(round(time.time() - uptime))))}s`
        """,
            colour="#44ff44"
        )  # fix the uptime formatting at some point I swear to god
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_bot_owner()
    async def oping(self, ctx):
        """Different from normal ping command, this one checks response time and rate limits."""
        start = time.time()
        embed = revolt.SendableEmbed(
            title="Pinging..",
            description=f"Ping!",
            color="#44ff44"
        )
        msg = await ctx.reply(content="[]()", embed=embed)
        for i in range(1, 10):
            embed1 = revolt.SendableEmbed(
                title="Running PING sequence!",
                description=f"Ping! `{i}/10`",
                colour="#44ff44"
            )
            await msg.edit(embed=embed1)
        end = time.time()
        total = end - start
        await msg.edit(
            embed=revolt.SendableEmbed(
                title="Pong!",
                description=f"Pong! in {round(total, 2)}s",
                # usually this should be 3s - 4s, if its above, you're fucked.
                colour="#44ff44"
            )
        )

    @commands.command(name="eval", hidden=True)
    # @commands.is_bot_owner()
    async def eval_fn(self, ctx, *, code):
        """Run commands in multiple languages!"""
        languagespecifiers = [
            "python",
            "py",
            "javascript",
            "js",
            "html",
            "css",
            "php",
            "md",
            "markdown",
            "go",
            "golang",
            "c",
            "c++",
            "cpp",
            "c#",
            "cs",
            "csharp",
            "java",
            "ruby",
            "rb",
            "coffee-script",
            "coffeescript",
            "coffee",
            "bash",
            "shell",
            "sh",
            "json",
            "http",
            "pascal",
            "perl",
            "rust",
            "sql",
            "swift",
            "vim",
            "xml",
            "yaml",
        ]
        loops = 0
        while code.startswith("`"):
            code = "".join(list(code)[1:])
            loops += 1
            if loops == 3:
                loops = 0
                break
        for languagespecifier in languagespecifiers:
            if code.startswith(languagespecifier):
                code = code.lstrip(languagespecifier)
        while code.endswith("`"):
            code = "".join(list(code)[0:-1])
            loops += 1
            if loops == 3:
                break
        code = "\n".join(f"    {i}" for i in code.splitlines())
        code = f"async def eval_expr():\n{code}"

        async def send(text):
            await ctx.send(text)

        env = {
            "bot": self.client,
            "client": self.client,
            "ctx": ctx,
            "print": send,
            "_author": ctx.author,
            "_message": ctx.message,
            "_channel": ctx.channel,
            "_guild": ctx.server,
            # "_me": ctx.me,
        }
        env.update(globals())
        try:
            exec(code, env)
            eval_expr = env["eval_expr"]
            result = await eval_expr()
            if result:
                embed = revolt.SendableEmbed(
                    title="Code Ran with no errors!",
                    description=result,
                    colour="#00FF00",
                )
                await ctx.send(content=ctx.author.mention, embed=embed)
        except Exception as e:
            embed = revolt.SendableEmbed(
                title="Error occured!",
                description=f"```{languagespecifier}\n{''.join(traceback.format_exception(type(e), e, e.__traceback__))}\n```",
                colour="#0000FF",
            )
            await ctx.send(content=ctx.author.mention, embed=embed)

    # @commands.command(name="kwargstest", aliases=['kt', 'okt', 't'], hidden=True)
    # async def kwargstest(ctx, *time, **message):
    #     """working with kwargs sucks, kids."""
    #     if ctx.author.id == "01FZB2QAPRVT8PVMF11480GRCD":
    #         await ctx.send(f"{str(time)}\n{str(message)}")
    #     else:
    #         await ctx.reply("Not owner, cant use this.")

    # @commands.command(hidden=True)
    # async def reac(self, ctx):
    #     def check(reaction, user):
    #         return user == ctx.author and str(reaction.emoji) == '👍'
    #
    #     try:
    #         reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
    #     except asyncio.TimeoutError:
    #         await ctx.send('👎')
    #     else:
    #         await ctx.send('👍')

    # @commands.command(hidden=True)
    # async def aggregate(self, ctx):
    #     await ctx.send("done")

    @commands.command(name='restart', hidden=True)
    @commands.is_bot_owner()
    async def restart(self, ctx):
        await ctx.send("Restarting bot...")
        restart_bot()

    @commands.command(hidden=True)
    @commands.is_bot_owner()
    async def servers(self, ctx):
        for server in self.client.servers:
            print(f"[{server.id}] {server.name} - {len(server.members)}")

    @commands.command(hidden=True)
    @commands.is_bot_owner()
    async def apu(self, ctx, user: revolt.User, *, prefix: str):
        await self.client.db_client.userdb.update_one(
            {
                "userid": user.id
            }, {
                "$push": {
                    "prefixes": prefix
                }
            }
        )
        await ctx.send(f"Added {prefix}, to {user.display_name}'s prefix list!")

    @commands.command(hidden=True)
    @commands.is_bot_owner()
    async def dpu(self, ctx, user: revolt.User, *, prefix: str):
        await self.client.db_client.userdb.update_one(
            {
                "userid": user.id
            }, {
                "$pull": {
                    "prefixes": prefix
                }
            }
        )
        await ctx.send(f"Removed {prefix}, from {user.display_name}'s prefix list!")

    @commands.command(hidden=True)
    @commands.is_bot_owner()
    async def addbadge(self, ctx, user: revolt.User, badge: int = None):
        if not badge:
            embed = revolt.SendableEmbed(
                title="Add Badge",
                description="Please specify a badge number!\nFor example: `m!addbadge @user 1`\nBadge List:\n```\n1 - Developer\n2 - Admin\n3 - Moderator\n4 - Bug Hunter\n5 - Beta Tester",
                colour="#FF0000"
            )
            return await ctx.send(embed=embed)
        elif get_badge(badge):
            await self.client.db_client.userdb.update_one(
                {
                    "userid": user.id
                },
                {
                    "$set": {
                        f"status.{get_badge(badge)}": True
                    }
                }
            )
            await ctx.send(f"Added badge {badge} to {user.display_name}!")

    @commands.command(hidden=True)
    @commands.is_bot_owner()
    async def removebadge(self, ctx, user: revolt.User, badge: int = None):
        if not badge:
            embed = revolt.SendableEmbed(
                title="Remove Badge",
                description="Please specify a badge number!\nFor example: `m!removebadge @user 1`\nBadge List:\n```\n1 - Developer\n2 - Admin\n3 - Moderator\n4 - Bug Hunter\n5 - Beta Tester",
            )
            await ctx.send(embed=embed)
        elif get_badge(badge):
            await self.client.db_client.userdb.update_one(
                {
                    "userid": user.id
                },
                {
                    "$set": {
                        f"status.{get_badge(badge)}": False
                    }
                }
            )
            await ctx.send(f"Removed badge {badge} from {user.display_name}!")

    @commands.command(hidden=True)
    @commands.is_bot_owner()
    async def give(self, ctx, user: revolt.User, amount: int):
        user_data = await self.client.db_client.get_user(user)
        i = len(user_data["notifications"]["inbox"])
        await self.client.db_client.userdb.bulk_write(
            [
                pymongo.UpdateOne(
                    {
                        "userid": user.id
                    },
                    {
                        "$inc": {
                            "economy.bank": amount
                        }
                    }
                ),
                pymongo.UpdateOne(
                    {
                        "userid": user.id
                    },
                    {
                        "$set": {
                            f"notifications.inbox.{str(i)}": {
                                "message": f"You've received {amount:,}!",
                                "date": time.time(),
                                "title": "You've been given some coins!",
                                "type": "admin",
                                "read": False
                            }
                        }
                    }
                )
            ]
        )
        await ctx.send(f"Gave `{user.display_name}#{user.discriminator}` `${amount:,}` coins!")

    # @commands.command(hidden=True)
    # async def betamsg(self, ctx):
    #     embed = revolt.SendableEmbed(
    #         title="Beta Message",
    #         description="React with **👍** to enable beta testing!",
    #         colour="#FF0000"
    #     )
    #     msg = await ctx.send(embed=embed, interactions={"reactions": ['👍'], "restrict_reactions": True})
    #     with open("json/data.json", "r") as f:
    #         data = json.load(f)
    #     data["BETA_ID"] = str(msg.id)
    #     with open("json/data.json", "w") as f:
    #         json.dump(data, f, indent=2)


async def setup(client):
    await client.add_cog(Owner(client))
