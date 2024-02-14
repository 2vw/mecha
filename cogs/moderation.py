import voltage, asyncio
import time, json
import datetime
from datetime import timedelta
from voltage.ext import commands


def setup(client) -> commands.Cog:

    mod = commands.Cog(
        "Moderation", 
        "Some commands for moderation, in, out, and all around."
    )

    @mod.command(description="Sets the nickname of a user!", name="nickname", aliases=['setnick', 'setusername', 'snick', 'suser', 'snick'])
    @commands.has_perms(manage_nicknames=True)
    @commands.bot_has_perms(manage_nicknames=True)
    async def nickname(ctx, member: voltage.User, *, nick):
        try:
            await member.change_nickname(nick)
            await ctx.reply(f"Changed {member.name}'s nickname to {nick}!")
        except:
            await ctx.reply("Something went wrong! Sorry about that!")
        
    
    @mod.command(description="BEGONE MESSAGES!")
    @commands.has_perms(manage_messages=True)
    async def purge(ctx, amount: int) -> None:
        starttime = time.time()
        await ctx.channel.purge(amount)
        embed = voltage.SendableEmbed(
            description=f"# Purged!\nPurged {amount} messages in {round(time.time() - starttime, 2)}s!",
            color="#00FF00",
        )
        await ctx.send(content=ctx.author.mention, embed=embed)

    @mod.command(
        description="Set a custom prefix for this server!",
        aliases=["setprefix", "prefix", "serverprefix", "p", "sp"],
    )
    @commands.has_perms(manage_server=True)
    async def sp(ctx, prefix):
      with open("prefixes.json", "r") as f:
        prefixes = json.load(f)
      with open("prefixes.json", "w") as f:
        prefixes[str(ctx.server.id)] = prefix
        json.dump(prefixes, f, indent=2)
        embed = voltage.SendableEmbed(
          title="New Prefix!",
          description=f"Set this servers prefix to `{prefix}`!",
          colour="#516BF2",
        )
      return await ctx.send(content=ctx.author.mention, embed=embed)

    @mod.command(description="Ban a user from your server!")
    @commands.has_perms(ban_members=True)
    async def ban(ctx, member: voltage.Member):
        if ctx.author.roles[0] > len(member.roles):
            return await ctx.send(
                "That user is above your top role! I cannot ban them!"
            )
        elif ctx.author.permissions.ban_members:
            return await ctx.send(f"Attempting to ban {member.display_name}!")
        elif member.id == ctx.author.id:
            return await ctx.send("You can't ban yourself!")
        elif member.id == "01FZB4GBHDVYY6KT8JH4RBX4KR":
            return await ctx.send("You want to ban me?! How dare you :boohoo:")
        elif member.permissions.ban_members:
            return await ctx.send(
                "This user is an administrator! I cannot ban them! Please remove their administrative permissions before continuing."
            )
        try:
            await member.ban()
            embed = voltage.SendableEmbed(
                title="Done!", description=f"Just Banned {member.name}!", colour="#516BF2"
            )
            await ctx.reply(content="[]()]", embed=embed)
        except Exception as e:
            await ctx.send(f"I was unable to ban {member.display_name}!\n```\n{e}\n```")

    @mod.command(description="Kick a user from your server!")
    async def kick(ctx, member: voltage.Member):
        if not ctx.author.permissions.kick_members:
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

    return mod