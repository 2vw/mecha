import voltage, asyncio, random, time, psutil, pymongo, json
from voltage.ext import commands

def setup(client) -> commands.Cog:
  owner = commands.Cog(
    "Owner",
    "Some commands for testing."
  )
  
  @owner.command()
  async def statz(ctx):
    """Different from normal stats, the normal one shows the stats of the bot, this one shows complex stats. Like CPU usage and whatnot."""
    embed = voltage.SendableEmbed(
      title="Computer Stats",
      description=f"CPU Usage: `{psutil.cpu_percent()}%`\nRAM Usage: `{psutil.virtual_memory().percent}%`\nDisk Usage: `{psutil.disk_usage('/').percent}%`",
    )
    with open("json/data.json", "r") as f:
      uptime = json.load(f)['uptime']
    embed1 = voltage.SendableEmbed(
      title="Bot Stats",
      description=f"Servers: `{client.servers}`\nUsers: `{client.users}`\nUptime: `{time.strftime('%H:%M:%S', time.gmtime(time.time() - uptime))}`",
    )
    await ctx.reply(embed=embed, embeds=embed1)
  
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
        description=f"Ping! `{i}/10`",
        colour="#44ff44"
      )
      await msg.edit(embed=embed1)
    end = time.time()
    total = end - start
    await msg.edit(
      embed=voltage.SendableEmbed(
        title="Pong!",
        description=f"Pong! in {round(total, 2)}s", # usually this should be 3s - 4s, if its above, you're fucked.
        colour="#44ff44"
      )
    )
    

  return owner