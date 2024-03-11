import voltage, asyncio, requests, aiohttp
import time, json
from functools import wraps
import datetime
from datetime import timedelta
from voltage.ext import commands

with open("json/config.json", "r") as f:
    config = json.load(f)

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

def setup(client) -> commands.Cog:

    mod = commands.Cog(
        "Moderation", 
        "Some commands for moderation, in, out, and all around."
    )

    @mod.command(description="Sets the nickname of a user!", name="nickname", aliases=['sn', 'username', 'setname'])
    @limiter(20, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def nickname(ctx, member: voltage.User, *, nick:str):
        if ctx.author.permissions.manage_nicknames or ctx.author.id == ctx.server.owner.id:
            try:
                async with aiohttp.ClientSession() as s:
                    await s.patch(
                        url=f"https://api.revolt.chat/servers/{ctx.server.id}/members/{member.id}",
                        headers={"x-bot-token": config['TOKEN']},
                        json={"nickname": nick},
                        timeout=10
                    )
                    await s.close()
            except aiohttp.ClientTimeout:
                return
            embed = voltage.SendableEmbed(
                title="Nickname",
                description=f"Changed {member.display_name}'s nickname to `{nick}`!",
                colour="#00FF00",
                icon_url=member.display_avatar.url
            )
            await ctx.send(embed=embed)
        else:
            await ctx.reply("You don't have permission to do that!")
            
        
    
    @mod.command(description="BEGONE MESSAGES!", name="purge", aliases=["clear", "c", "prune"])
    @limiter(20, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def purge(ctx, amount:int=10):
        if ctx.author.permissions.manage_messages or ctx.author.id == ctx.server.owner.id and ctx.me.permissions.manage_messages:
            if amount > 0 and amount < 101:
                if amount == 1:
                    amount += 1
                starttime = time.time()
                messages = await ctx.channel.history(limit=amount)
                ids = [m.id for m in messages]
                await ctx.send("Purging...", delete_after=2)
                async with aiohttp.ClientSession() as session:
                    await session.delete(
                        url=f"https://api.revolt.chat/channels/{ctx.channel.id}/messages/bulk",
                        headers={"x-bot-token": config['TOKEN']},
                        json={"ids": ids}
                    )
                    await session.close()
                embed = voltage.SendableEmbed(
                    description=f"# Purged!\nPurged {amount} messages in {round(time.time() - starttime, 2)}s!",
                    color="#00FF00",
                )
                await ctx.send(content=ctx.author.mention, embed=embed, delete_after=3)
            else:
                embed = voltage.SendableEmbed(
                    description="Please provide a purge amount between 1 and 100!",
                )
                await ctx.reply(embed=embed, delete_after=3)
        elif not ctx.author.permissions.manage_messages:
            embed = voltage.SendableEmbed(
                description="You `or me` doesn't have the required permission(s) to use this command!",
                color="#FF0000",
            )
            await ctx.reply(embed=embed)

    @mod.command(description="Ban a user from your server!")
    @limiter(20, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def ban(ctx, member: voltage.Member):
        if ctx.author.permissions.ban_members:
            return await ctx.send(f"Attempting to ban {member.name}!")
        elif member.id == ctx.author.id:
            return await ctx.send("You can't ban yourself!")
        else:
            return await ctx.send("You dont have the required permission!")

    @mod.command(description="Kick a user from your server!")
    @limiter(20, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
    async def kick(ctx, member: voltage.Member):
        if commands.has_perms(kick_members=True) and commands.bot_has_perms(kick_members=True):
            return await ctx.send(
                "You don't have the required permission `kick_members` that is required for this command!"
            )
        elif ctx.author.roles[0] > member.roles[0]:
            return await ctx.send(
                "That user is above your top role! I cannot kick them!"
            )
        elif member.roles[0] < client.roles[0]:
            return await ctx.send(
                "I couldnt kick the member because I do not have a high enough role to do this!"
            )
        elif ctx.author.permissions.ban_members:
            return await ctx.send(f"Attempting to kick {member.name}!")
        elif member.id == ctx.author.id:
            return await ctx.send("You can't kick yourself!")
        elif member.id == "01FZB4GBHDVYY6KT8JH4RBX4KR":
            return await ctx.send("You want to kick me?! How dare you :boohoo:")
        elif member.permissions.ban_members:
            return await ctx.send(
                "This user is an administrator! I cannot kick them! Please remove their administrative permissions before continuing."
            )
        try:
            await member.kick()
            embed = voltage.SendableEmbed(
                title="Done!", description=f"Just Kicked {member.name}!", colour="#516BF2"
            )
            await ctx.send(content=ctx.author.mention, embed=embed)
        except Exception as e:
            await ctx.send(f"I was unable to kick {member.display_name}!\n```\n{e}\n```")

    @mod.command(description="Go to the corner! >_<", name="timeout", aliases=["time", "to", "corner", "gotocorner"])
    async def timeout(ctx, member: voltage.Member, duration: int):
        if ctx.author.permissions.timeout_members and ctx.me.permissions.timeout_members:
            try:
                await member.timeout(duration)
                embed = voltage.SendableEmbed(
                    title="Done!",
                    description=f"Timed out {member.display_name} for {duration:.0f} seconds!",
                    colour="#516BF2"
                )
                return await ctx.reply(embed=embed)
            except:
                return await ctx.reply("I was unable to timeout that user!")
        else:
            return await ctx.reply("You don't have the required permission `Timeout Members` that is required for this command!")
    
    return mod