import voltage, asyncio, random, time
from voltage.ext import commands

def setup(client) -> commands.Cog:
  owner = commands.Cog(
    "Owner",
    "Some commands for testing."
  )
  
  @owner.command()
  async def ping(ctx):
    """Sends Pong!"""
    start = time.time()
    embed=voltage.SendableEmbed(
      title="Pinging..", 
      description=f"Ping!", 
      color="#44ff44"
    )
    msg = await ctx.reply(content="[]()", embed=embed)
    for i in range(1,10):
      embed1 = voltage.SendableEmbed(
        title="Running PING sequence!",
        description=f"Ping! {i}/10",
        colour="#44ff44"
      )
      await msg.edit(embed=embed1)
    end = time.time()
    total = end - start
    msg = await msg.edit(embed=voltage.SendableEmbed(
      title="Pong!",
      description=f"Pong! in {round(total, 2)}s",
      colour="#44ff44"
    ))
    

  return owner