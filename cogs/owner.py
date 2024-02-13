import voltage, asyncio, random
from voltage.ext import commands

def setup(client) -> commands.Cog:
  owner = commands.Cog(
    "Owner",
    "Some commands for testing."
  )
  
  @owner.command()
  async def ping(ctx):
    """Sends Pong!"""
    embed=voltage.SendableEmbed(
      title="Pinging..", 
      description=f"Ping!", 
      color=0x44ff44
    )
    await ctx.reply(embed=embed)
    

  return owner