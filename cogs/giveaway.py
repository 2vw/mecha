from revolt.ext import commands


class Giveaway(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(hidden=True)
    async def giveawaystuffs(self, ctx):
        """Adds you to the giveaway"""
        await ctx.reply("nuh uh :)")


async def setup(client):
    await client.add_cog(Giveaway(client))
