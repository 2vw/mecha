import asyncio
import datetime
import json
import time

import revolt
from revolt.ext import commands

from main import MyClient

with open("json/config.json", "r") as f:
    config = json.load(f)


class Moderation(commands.Cog):
    description = "Some commands for moderation, in, out, and all around."

    def __init__(self, client: MyClient):
        self.client: MyClient = client

    @commands.command(name="nickname", aliases=['sn', 'username', 'setname'])
    @commands.has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 20, bucket=commands.BucketType.member)
    async def nickname(self, ctx, member: revolt.Member, *, nick: str):
        """Sets the nickname of a user!"""
        await member.edit(nick=nick)
        embed = revolt.SendableEmbed(
            title="Nickname",
            description=f"Changed {member.display_name}'s nickname to `{nick}`!",
            colour="#00FF00",
            icon_url=member.display_avatar.url if member.display_avatar else None
        )
        await ctx.send(embed=embed)

    @commands.command(name="purge", aliases=["clear", "c", "prune"])
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 20, bucket=commands.BucketType.member)
    async def purge(self, ctx: commands.Context, amount: int = 10):
        """BEGONE MESSAGES!"""
        if 0 < amount < 101:
            if amount == 1:
                amount += 1

            starttime = time.time()
            messages = await ctx.channel.history(limit=amount)
            await ctx.channel.delete_messages(messages)
            embed = revolt.SendableEmbed(
                description=f"# Purged!\nPurged {amount} messages in {round(time.time() - starttime, 2)}s!",
                color="#00FF00",
            )
            msg = await ctx.send(content=ctx.author.mention, embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
        else:
            embed = revolt.SendableEmbed(
                description="Please provide a purge amount between 1 and 100!",
            )
            await ctx.reply(embed=embed, delete_after=3)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 20, bucket=commands.BucketType.member)
    async def ban(self, ctx, member: revolt.Member):  # command seems incomplete
        """Ban a user from your server!"""
        if ctx.author.roles[0] > member.roles[0]:
            return await ctx.send(
                "That user is above your top role! I cannot ban them!"
            )
        elif member.id == ctx.author.id:
            return await ctx.send("You can't ban yourself!")
        elif member.id == "01FZB4GBHDVYY6KT8JH4RBX4KR":
            return await ctx.send("You want to ban me?! How dare you :boohoo:")
        try:
            await member.ban()
            embed = revolt.SendableEmbed(
                title="Done!", description=f"Just Banned {member.name}!", colour="#516BF2"
            )
            await ctx.send(content=ctx.author.mention, embed=embed)
        except Exception as e:
            await ctx.send(f"I was unable to kick {member.display_name}!\n```\n{e}\n```")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.cooldown(1, 20, bucket=commands.BucketType.member)
    async def kick(self, ctx, member: revolt.Member):
        """Kick a user from your server!"""
        if ctx.author.roles[0] > member.roles[0]:
            return await ctx.send(
                "That user is above your top role! I cannot kick them!"
            )
        elif member.id == ctx.author.id:
            return await ctx.send("You can't kick yourself!")
        elif member.id == "01FZB4GBHDVYY6KT8JH4RBX4KR":
            return await ctx.send("You want to kick me?! How dare you :boohoo:")
        try:
            await member.kick()
            embed = revolt.SendableEmbed(
                title="Done!", description=f"Just Kicked {member.name}!", colour="#516BF2"
            )
            await ctx.send(content=ctx.author.mention, embed=embed)
        except Exception as e:
            await ctx.send(f"I was unable to kick {member.display_name}!\n```\n{e}\n```")

    @commands.command(name="timeout", aliases=["time", "to", "corner", "gotocorner"])
    @commands.has_permissions(timeout_members=True)
    async def timeout(self, ctx, member: revolt.Member, duration: int):
        """Go to the corner! >_<"""
        try:
            await member.timeout(datetime.timedelta(seconds=duration))
            embed = revolt.SendableEmbed(
                title="Done!",
                description=f"Timed out {member.display_name} for {duration:.0f} seconds!",
                colour="#516BF2"
            )
            return await ctx.reply(embed=embed)
        except:
            return await ctx.reply("I was unable to timeout that user!")


async def setup(client):
    await client.add_cog(Moderation(client))
