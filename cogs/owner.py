import voltage, asyncio, random, time, psutil, pymongo, json, datetime, io, contextlib, requests, string
from bson.son import SON
from voltage.ext import commands
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

with open("json/config.json", "r") as f:
    config = json.load(f)

DBclient = MongoClient(config["MONGOURI"])

db = DBclient["beta"]
userdb = db["users"]
serverdb = db["servers"]

def setup(client) -> commands.Cog:
  owner = commands.Cog(
    "Owner",
    "Some commands for testing."
  )
  
  @owner.command()
  async def statz(ctx):
    """Different from normal stats, the normal one shows the stats of the bot, this one shows complex stats. Like CPU usage and whatnot."""
    if commands.is_owner:
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
    else:
        await ctx.reply("Not owner, cant use this.")
  
  @owner.command()
  async def oping(ctx):
    """Different from normal ping command, this one checks response time and rate limits."""
    if commands.is_owner:
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
    else:
      await ctx.reply("Not owner, cant use this.")
    
  @owner.command(
    name="eval",
    description="For owner use only! Runs code.",
    aliases=['ev', 'exec']
  )
  async def eval(ctx, *, code):
    if commands.is_owner:
      str_obj = io.StringIO() #Retrieves a stream of data
      try:
        with contextlib.redirect_stdout(str_obj):
          exec(code)
      except Exception as e:
        return await ctx.send(f"```{e.__class__.__name__}: {e}```")
      await ctx.send(f'```{str_obj.getvalue()}```')
    else:
      await ctx.reply("Not owner, cant use this.")
    
  @owner.command(
    name="kwargstest", 
    description="working with kwargs sucks, kids.",
    aliases=['kt', 'okt', 't']
  )
  async def kwargstest(ctx, *time, **message):
    if commands.is_owner:
      await ctx.send(f"{str(time)}\n{str(message)}")
    else:
      await ctx.reply("Not owner, cant use this.")

  @owner.command()
  async def aggregate(ctx):
    await ctx.send("done")
    
    
  return owner