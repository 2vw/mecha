import voltage, pymongo, os
from voltage.ext import commands

def setup(client) -> commands.Cog:
  fun = commands.Cog(
    "Fun",
    "More command testing, use these if you want *basic* fun commands."
  )

  @fun.command()
  async def no(ctx):
    """Adds you to the fun."""
    await ctx.reply("nuh uh")

  return fun