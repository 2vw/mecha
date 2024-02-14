import voltage, asyncio, random, time, psutil, pymongo, json, datetime
from voltage.ext import commands

def setup(client) -> commands.Cog:
  owner = commands.Cog(
    "Owner",
    "Some commands for testing."
  )
  
  @owner.command()
  async def statz(ctx):
    """Different from normal stats, the normal one shows the stats of the bot, this one shows complex stats. Like CPU usage and whatnot."""
    with open("json/data.json", "r") as f:
      uptime = json.load(f)['uptime']
    embed = voltage.SendableEmbed(
      title=f"{client.user.name}'s Stats",
      description=f"""
## Computer Based Stats
> CPU Usage: `{psutil.cpu_percent()}%`
> RAM Usage: `{psutil.virtual_memory().percent}%`
> Disk Usage: `{psutil.disk_usage('/').percent}%`
      
## Bot Stats
> Servers: `{len(client.servers)}`
> Users: `{len(client.users)}`
> Uptime: `{str(datetime.timedelta(seconds=int(round(time.time() - uptime))))}s`
      """,
      colour="#44ff44"
    ) # fix the uptime formatting at some point i swear to god
    await ctx.send(embed=embed)
  
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