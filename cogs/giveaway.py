import voltage, pymongo, os
from voltage.ext import commands

def setup(client) -> commands.Cog:
    giveaway = commands.Cog(
    "Giveaway",
    "More command testing, use these if you want *basic* fun commands."
    )

    @giveaway.command()
    async def giveawaystuffs(ctx):
        """Adds you to the giveaway"""
        await ctx.reply("nuh uh :)")

    return giveaway