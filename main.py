# IMPORTANT SHIT
'''
onReady : "ready"
onMessage : "message"
onMessageEdit : "message_update"
onmessageDelete : "message_delete"
onChannelCreate : "channel_create"
oncChannelEdit : "channel_update"
onChannelDelete : "channel_delete"
onGroupChannelJoin : "group_channel_join"
onGroupChannelLeave : "group_channel_leave"
onUserStartsTyping : "channel_start_typing"
onUserStopsTyping : "channel_stop_typing"
onServerEdit : "server_update"
onServerDelete : "server_delete"
onServerMemberEdit : "server_member_update"
onMemberJoin : "member_join"
onMemberLeave : "member_leave"
onRoleEdit : "server_role_update"
onRoleDelete : "server_role_delete"
onUserEdit : "user_update"
'''

"""
token="sessionToken"
name="test"
colour="linear-gradient(30deg, #fe0000 0%, #ff8400 13%, #fffc00 24%, #2fe600 37%, #00c2c0 47%, #0030a5 62%, #73005b 78%)" # the gradient should only contain hex colors
roleid="01GBN6G274YFR7KKF7KH90608R"
serverid="01G6XTX40P5B9V0MF25Z1Q9VC6"
hoist="false"
rank="1"
#curl -X PATCH -H "X-Session-Token: $token" -d "{ \"name\": \"$name\", \"rank\": $rank, \"hoist\": $hoist, \"id:\": \"$roleid\", \"colour\": \"$colour\" }" https://api.revolt.chat/servers/$serverid/roles/$roleid
curl -X PATCH -H "X-Session-Token: $token" -d "{ \"id:\": \"$roleid\", \"colour\": \"$colour\" }" https://api.revolt.chat/servers/$serverid/roles/$roleid

"""

import random, motor, pymongo,  json, time, asyncio, datetime, requests, pilcord
import voltage, os
from voltage.ext import commands
from voltage.errors import CommandNotFound, NotBotOwner, NotEnoughArgs, NotEnoughPerms, NotFoundException, BotNotEnoughPerms, RoleNotFound, UserNotFound, MemberNotFound, ChannelNotFound, HTTPError 
from host import alive
from time import time
from functools import wraps
import motor.motor_asyncio
from bardapi import BardAsync
from revoltbots import RBL

with open("json/config.json", "r") as f:
  config = json.load(f)

bard = BardAsync(token=config['BARDTOKEN'], token_from_browser=True)

sep = "\n"
DBclient = motor.motor_asyncio.AsyncIOMotorClient(config['MONGOURI'])

with open("json/data.json", "r") as f:
  data = json.load(f)
  data['uptime'] =  int(time())
with open("json/data.json", "w") as r:
  json.dump(data, r, indent=2)

async def get_prefix(message, client):
  if (await userdb.find_one({"userid": message.author.id})) is not None:
    return (await userdb.find_one({"userid": message.author.id}))['prefixes']
  else:
    return ['m!']
                                                          
class HelpCommand(commands.HelpCommand):
  async def send_help(self, ctx: commands.CommandContext):
    embed = voltage.SendableEmbed(
      title="Help",
      description=f"Use `{ctx.prefix}help <command>` to get more informtion on a command.",
      colour="#516BF2",
      icon_url=ctx.author.display_avatar.url
    )
    text = ""
    for i in self.client.cogs.values():
      text += f"{sep}### **{i.name}**{sep}{i.description}{sep}"
      for j in i.commands:
        text += f"{sep}> {j.name}"
    if embed.description:
      embed.description += text
    return await ctx.reply(embed=embed)
 
# will continue this later
class Help(commands.HelpCommand):
  async def send_help(self, ctx: commands.CommandContext):
      embed = voltage.SendableEmbed(
          title="Help",
          description=f"Use `{ctx.prefix}help <command>` to get help for a command.",
          colour="#fff0f0",
          icon_url=client.user.display_avatar.url,
      )
      text = "\n### **No Category**\n"
      covered = []
      for command in self.client.commands.values():
          if command in covered:
              continue
          if command.cog is None:
              text += f"> {command.name}\n"
              covered.append(command)
      for i in self.client.cogs.values():
          text += f"\n### **{i.name}**\n{i.description}\n"
          for j in i.commands:
              text += f"\n> {j.name}"
              covered.append(j)
      if embed.description:
          embed.description += text
      return await ctx.reply(embed=embed)

  async def send_command_help(self, ctx: commands.CommandContext, command: commands.Command):
      embed = voltage.SendableEmbed(
          title=f"Help for {command.name}",
          colour="#0000ff",
          icon_url=client.user.display_avatar.url,
      )
      text = str()
      text += f"\n### **Usage**\n> `{ctx.prefix}{command.usage}`"
      if command.aliases:
          text += f"\n\n### **Aliases**\n> {ctx.prefix}{', '.join(command.aliases)}"
      embed.description = command.description + text if command.description else text
      return await ctx.reply(embed=embed)

  async def send_cog_help(self, ctx: commands.CommandContext, cog: commands.Cog):
      embed = voltage.SendableEmbed(
          title=f"Help for {cog.name}",
          colour="#0000ff",
          icon_url=client.user.display_avatar.url,
      )
      text = str()
      text += f"\n### **Description**\n{cog.description}"
      text += f"\n\n### **Commands**\n"
      for command in cog.commands:
          text += f"> {ctx.prefix}{command.name}\n"
      embed.description = text
      return await ctx.reply(embed=embed)

  async def send_not_found(self, ctx: commands.CommandContext, target: str):
    embed = voltage.SendableEmbed(
        title="Help",
        description=f"`{ctx.prefix}{target} doesnt exist!`",
        colour="#fff0f0",
        icon_url=client.user.display_avatar.url
    )
    return await ctx.send(embed=embed)
 
async def serverupdate():
  for server in client.servers:
    i = 0
    for _ in serverdb.find({}):
      i += 1
    if not serverdb.find_one({"serverid": server.id}):
      if server.icon:
        icon = server.icon.url
      else:
        icon = None
      if server.banner:
        banner = server.banner.url
      else:
        banner = None
      if server.description:
        description = server.description
      else:
        description = None
      serverdb.insert_one(
        {
          "_id": i,
          "serverid": server.id,
          "name": server.name,
          "owner": {
            "id": server.owner.id,
            "name": server.owner.name,
            "discriminator": server.owner.discriminator
          },
          "created_at": f"{server.created_at}",
          "meta": {
            "description": description,
            "banner": banner,
            "icon": icon,
          },
          "member_count": len(server.members),
          "role_count": len(server.roles),
          "channel_count": len(server.channel_ids),
          "category_count": len(server.categories)
        }
      )
  print("Updated {} servers!".format(serverdb.count_documents({})))
      
db = DBclient['beta']
userdb = db['users']
serverdb = db['servers']
settingsdb = db['settings']
cooldowns = db['cooldowns']

import time

async def upd():
    doc = await userdb.find({}).to_list(length=None)
    for i in doc:
        await userdb.bulk_write(
        [
            pymongo.UpdateOne(
            {'userid':i['userid']}, 
            {'$set':
                {
                "economy.monthly": time.time()
                }
            }
            ),
        ]
        )
        print(f"Updated {i['username']}!")


async def update_level(user:voltage.User):
  if (await userdb.find_one({'userid':user.id})):
    user_data = await userdb.find_one({'userid':user.id})
    lvl = user_data['levels']['level']
    xp = user_data['levels']['xp']
    if 0 >= (5 * (lvl ^ 2) + (50 * lvl) + 100 - xp):
      amt = random.randint(0, 10000)
      o = 1
      for i in user_data['notifications']['inbox']:
        o += 1
      await userdb.bulk_write([
        pymongo.UpdateOne({'userid':user.id}, {'$inc':{'levels.level':1}}),
        pymongo.UpdateOne({'userid':user.id}, {'$set':{'levels.xp':0}}),
        pymongo.UpdateOne({'userid':user.id}, {'$inc':{'levels.totalxp':xp}}),
        pymongo.UpdateOne({'userid':user.id}, {'$inc':{'economy.bank':100 * lvl + amt}}),
        pymongo.UpdateOne({'userid':user.id}, {
          '$set':{
            f'notifications.inbox.{i}':{
              "message":f"Congratulations on leveling up to level {lvl+1}!{sep}You've recieved {100 * lvl + amt} coins as a reward!",
              "date":time.time(),
              "title":"Level Up!",
              "type":"level",
              "read":False
              }
            }
          }),
      ])
      return True
    else:
      return False
  else:
    return False

async def check_xp(user: voltage.User):
  user_id = str(user.id)
  user_data = await userdb.find_one({'userid': user_id})
  if user_data:
    return user_data['levels']['xp']
  else:
    return 0

async def add_user(user: voltage.User, isbot:bool=False): # long ass fucking function to add users to the database if they dont exist yet. but it works..
  if await userdb.find_one({"userid": user.id}):
    return "User already exists."
  try:
    await userdb.insert_one({
        "_id": (await userdb.count_documents({}) + 1),
        "username": user.name,
        "userid": user.id,
        "levels": {
            "xp": 0,
            "level": 0,
            "totalxp": 0,
            "lastmessage": time.time()
        },
        "prefixes": ["m!"],
        "economy": {
            "wallet": 0,
            "bank": 0,
            "total": 0,
            "daily": time.time(),
            "monthly": time.time(),
            "data": {
                "inventory": {
                    "Bank Loan": 1
                },
                "job": "unemployed"
            },
            "buffs": {
                "beginner_luck": 100
            },
            "debuffs": {},
            "achievements": {
                "early_user": True,
                "beta_tester": True
            }
        },
        "notifications": {
          "inbox": {
            "1":{
              "message": f"Welcome to Mecha, {user.name}!{sep}To get started, type `m!help` in this server to get started!",
              "date": time.time(),
              "title": "Welcome To Mecha!",
              "type": "bot",
              "read": False
            }
          }
        },
        "status": {
            "developer": False,
            "admin": False,
            "moderator": False,
            "friend": False,
            "premium": False,
            "bug": False,
            "beta": False,
            "familyfriendly": False,
            "isBot": isbot,
            "banned": False,
            "afk": {}
        }
    })
    return "Added"
  except Exception as e:
    return f"Sorry, An Error Occured!{sep}{sep}```{sep}{e}{sep}```"

async def update_stats(users, servers):
  if settingsdb.find_one(
    {
      "_id": 1
    }
  ):
    settingsdb.update_one(
      {
        "_id": 1,
        "setting": "stats"
      },
      {
        "$set": {
          "users": users,
          "servers": servers
        }
      }
    )
  else:
    settingsdb.insert_one(
      {
        "_id": 1,
        "setting": "stats",
        "users": users,
        "servers": servers
      }
    )
  print("Updated stats! Users: " + str(users) + " Servers: " + str(servers))

async def pingDB(): # ping the database; never gonna use this, might need it, add it.
  try:
    await DBclient.admin.command('ping')
    return "[+] Pinged your deployment. Successfully connected to MongoDB!"
  except Exception as e:
    return f"[-] ERROR! {sep}{sep}{sep}{e}"

async def get_user(user: voltage.User):
  if user := (await userdb.find_one({"userid": user.id})):
    return user
  else:
    return "User not found."  
 
async def give_xp(user: voltage.User, xp:int):
  await userdb.update_one(
    {"userid": user.id},
    {"$inc": {"levels.xp": xp}}
  )

prefixes = ["m!"]
client = commands.CommandsClient(prefix=get_prefix, help_command=HelpCommand)

RBList = RBL.RevoltBots(ApiKey=config['RBL_KEY'], botId="01FZB4GBHDVYY6KT8JH4RBX4KR")

# USE THIS IF YOU NEED TO ADD NEW KEYS TO THE DATABASE
async def do():
  while True:
    curs = userdb.find()
    async for user in curs:
      try:
        ud = client.get_user(user['userid'])

        await userdb.update_one(
          {'userid':user['userid']}, 
          {
            '$set':{
              "username": f"{ud.name}#{ud.discriminator}"
            }
          }
        )
      except:
        pass
    print(f"Updated {(await userdb.count_documents({}))} users!")
    await asyncio.sleep(60*60)

async def get():
  """ GET Stats """
  res = RBList.getStats()
  print(res)


def post():
  """ POST Stats """
  res = requests.post(
    url="https://revoltbots.org/api/v1/bots/stats",
    headers={
      "Authorization": config['RBL_KEY'],
      "servers": str(len(client.servers)),
    }
  )
  if res.status_code != 200:
    print(res)

def checkVotes():
  """ GET Votes """
  res = RBList.checkVotes()
  print(res)

def getVoter(user: voltage.User):
  """ Check Voter """
  res = RBList.checkVoter(userId=user.id)
  print(res)

async def update():
  print("Started Update Loop")
  while True:
    documents = userdb.find()
    async for i in documents:
      total = 0
      total += int(i["economy"]["wallet"]) 
      total += int(i["economy"]["bank"])
      userdb.update_many(
        {
          "_id": i["_id"]
        },
        {
          "$set": {
            "economy.total": total
          }
        }
      )
    await asyncio.sleep(120) # sleep for 2 minutes

async def add_cooldown(ctx, command_name:str, seconds:int):
  cooldowns[ctx.author.id][str(command_name)] = time() + seconds
  return True

async def check_cooldown(ctx, command_name:str, seconds:int):
  try:
    if (time() < cooldowns[ctx.author.id][command_name]):
      return True
    else:
      del cooldowns[ctx.author.id][command_name]
  except KeyError:
    await add_cooldown(ctx, command_name=command_name, seconds=seconds)
  return False

# THANK YOU VLF I LOVE YOU :kisses:
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

async def status():
  print("Started Status Loop")
  while True:
    statuses = [
      f"Playing with {len(client.cache.servers)} servers and {len(client.members)} users!",
      f"Watching {len(client.members)} users!",
      f"My waifu is better than yours!!! | {len(client.cache.servers)} servers",
      f"Lea | {len(client.cache.servers)} servers",
      f"Hey everyone! | {len(client.cache.servers)} servers",
      f"I am a bot | {len(client.cache.servers)} servers",
      f"Please stop asking to see my feet | {len(client.cache.servers)} servers",
      f"guys my father just came back with the milk O_O - delta2571 | {len(client.cache.servers)} servers",
      f"Revolt > shitcord | {len(client.cache.servers)} servers",
      f"William Says HI! | {len(client.cache.servers)} servers",
      f"Playing the numbers game | {len(client.cache.servers)} servers",
      f"Spreading joy across {len(client.members)} users!",
      f"Running rampant in {len(client.cache.servers)} servers!",
      f"Chillin' with {len(client.members)} users!",
      f"Your friendly bot | {len(client.cache.servers)} servers | {len(client.members)} users",
      f"Beep boop! I'm a bot | {len(client.cache.servers)} servers",
      f"Try 'm!help' to get started | {len(client.cache.servers)} servers",
      f"ccccccuthdkhugjktlcfvrhvtrdkgrfcikeekdvtfdrn | {len(client.cache.servers)} servers",
      f"Gaming rn, talk later? | {len(client.cache.servers)} servers",
      f"saul goodman | {len(client.cache.servers)} servers",
      f"Max was here | {len(client.cache.servers)} servers",
      ]
    status = random.choice(statuses)
    await client.set_status(status, voltage.PresenceType.online)
    await asyncio.sleep(60)

async def stayon():
  i = 0
  while True:
    channel = client.get_channel(config['REMIND_CHANNEL'])
    embed = voltage.SendableEmbed(
      title="I'm online!",
      description=f"I'm online!{sep}Its been {i} hour(s)!",
    )
    await channel.send(embed=embed)
    await asyncio.sleep(60*60)
    i += 1

async def afkCheck(message):
  try:
    if (await userdb.find_one({"userid": message.author.id})):
      if (await userdb.find_one({"userid": message.author.id}))['status']['afk'][message.server.id]['afk']:
        if (await userdb.find_one({"userid": message.author.id}))['status']['afk'][message.server.id]['lastseen'] + 2 < int(time.time()):
          await userdb.update_one(
            {"userid": message.author.id}, 
            {"$set": {"status.afk.{}".format(message.server.id): {"afk": False}}}
          )
          embed = voltage.SendableEmbed(
            title="AFK!",
            description=f"Welcome back, {message.author.mention}!{sep}I've removed your AFK status!",
            colour="#00ff00",
            icon_url=message.author.avatar.url
          )
          await message.reply(embed=embed, delete_after=5)
        else:
          return "TooEarly"
      else:
        return "NotAfk"
    else:
      return "DoesntExist"
  except:
    return

@client.listen("ready")
async def ready():
  post()
  print("Up and running") # Prints when the client is ready. You should know this
  with open("json/data.json", "r") as f:
    data = json.load(f)
  if time.time() - data['uptime'] > 3600:
    print("Back online! Starting up again!")
    
  print(f"Connected to {len(client.servers)} servers and {len(client.users)} users!")
  await asyncio.gather(update_stats(users=len(client.users), servers=len(client.servers)), update(), status(), do())

@client.command()
@limiter(5, on_ratelimited=lambda ctx, delay, *_1, **_2: ctx.send(f"You're on cooldown! Please wait `{round(delay, 2)}s`!"))
async def foo(ctx):
  await ctx.send(f"Not on cooldown, but now you are!{sep}Cooldown is `5` seconds!")

async def oldlevelstuff(message): # running this in the on_message event drops the speed down to your grandmothers crawl. keep this in a function pls
  if await update_level(message.author):
    try:
      channel = client.get_channel(config['LEVEL_CHANNEL'])
      embed = voltage.SendableEmbed(
        title = f"{message.author.name} has leveled up!",
        description = f"{message.author.name} has leveled up to level **{(await get_user(message.author))['levels']['level']}**!",
        color = "#44ff44",
        icon_url = message.author.avatar.url or "https://ibb.co/mcTxwnf"
      )
      await channel.send(embed=embed) # praise kink? its whatever
    except KeyError:
      print("keyerror :(") # this should never happen, if it does, tell William, if it doesnt, tell William anyways.
  if (await userdb.find_one(
    {"userid":message.author.id}
  )): #super fucking stupid but it makes pylance happy
    await update_level(message.author)
    await give_xp(message.author, random.randint(1, 5))
  else: 
    print(await add_user(message))

async def loggingstuff(message):
  if message.server.id == message.author.id:
    return
  else:
    return await add_user(message.author)

async def levelstuff(message):
  try:
    if message.content.startswith("<@01FZB4GBHDVYY6KT8JH4RBX4KR>"):
      if (await userdb.find_one({"userid":message.author.id})) is not None:
        prefix = (await userdb.find_one({"userid":message.author.id}))['prefixes']
        if prefix == []:
          prefix = ["m!"]
        embed = voltage.SendableEmbed(
          title="Prefix",
          description=f"Your prefixes are:{sep} ```{sep}{f'{sep}'.join(prefix)}{sep}```{sep}If you want to change your prefix, type `m!prefix <new prefix>`!",
          colour="#198754",
        )
        await message.reply(embed=embed)
      else:
        return print(await add_user(message.author))
  except:
    pass
  if await update_level(message.author):
    try:
      channel = client.get_channel(config['LEVEL_CHANNEL'])
      embed = voltage.SendableEmbed(
        title = f"{message.author.name} has leveled up!",
        description = f"{message.author.name} has leveled up to level **{(await get_user(message.author))['levels']['level']}**!",
        color = "#44ff44",
        icon_url = message.author.avatar.url or "https://ibb.co/mcTxwnf"
      )
      await channel.send(embed=embed) # praise kink? its whatever
    except KeyError:
      print("LEVEL CHANNEL ISNT DEFINED OR USER DOESNT EXIST") # this should never happen, if it does, tell William, if it doesnt, tell William anyways.
  elif await userdb.find_one(
    {"userid":message.author.id}
  ):
    if (await userdb.find_one({"userid":message.author.id}))['levels']['lastmessage'] < time.time():
      await give_xp(message.author, random.randint(1,2))
      await update_level(message.author)
      userdb.update_one(
        {"userid":message.author.id},
        {
          "$set":{
            "levels.lastmessage": int(time.time()) + 5
          }
        }
      )
    else:
      return f"{message.author.name} is on cooldown for {(await userdb.find_one({'userid':message.author.id}))['levels']['lastmessage'] - int(time.time()):.0f} seconds"
  else:
    return (await add_user(message))

# Thank TheBobBobs, bro is a fucking goat for this.
@client.listen("message")
async def on_message(message):
  if message.author.bot:
    return
  if message.channel.id == message.author.id:
    return
  asyncio.create_task(levelstuff(message)) # pièce de résistance
  asyncio.create_task(afkCheck(message))
  asyncio.create_task(loggingstuff(message))
  await client.handle_commands(message) # so everything else doesnt trip over its clumsy ass selves."

@client.listen("message_react")
async def on_message_react(message, user, reaction):
  with open("json/data.json", "r") as f:
    data = json.load(f)
  if message.channel.id == message.author.id:
    return
  elif message.id == data['BETA_ID'] and reaction == "👍" and user != message.author.id:
      return await message.reply(f"👍 | You've just joined the beta club, <@{user}>!", delete_after=5)

@client.listen("message_unreact")
async def on_message_unreact(message, user, reaction):
  if message.channel.id == message.author.id:
    return
  elif message.id == data['BETA_ID'] and reaction == "👍" and user != message.author.id:
      return await message.reply(f"👍 | You've just left the beta club, <@{user}>!", delete_after=5)

@client.listen("server_added")
async def server_added(message):
  channel = client.get_channel(config['SERVER_CHANNEL'])
  embed = voltage.SendableEmbed(
    title="New Server alert!",
    description=f"## Just Joined a new server!{sep}Now at **{len(client.servers)}** servers!",
    color="#516BF2",
  )
  await channel.send(content="[]()", embed=embed)

@client.command(name="add", description="Adds you to the database!") # whos really using this command? Like really, move this to owner.py when pls..
async def add(ctx, user:voltage.User=None):
  if user is None:
    user = ctx.author
  result = (await add_user(user))
  await ctx.reply(f"Results are in! {result}")

errormsg = [
  "Error! Error!",
  "LOOK OUT!!! ERROR!!",
  "Whoops!",
  "Oopsie!",
  "Something went wrong!",
  "Something happened..",
  "What happened? I know!",
  "404!",
  "ERROR.. ERROR..",
  "An Error Occured!"
]

# error handling shit
@client.error("message")
async def on_message_error(error: Exception, message):
  if isinstance(error, CommandNotFound):
    embed = voltage.SendableEmbed(
      title=random.choice(errormsg),
      description="That command doesnt exist!",
      colour="#516BF2"
    )
    return await message.reply(message.author.mention, embed=embed)
  elif isinstance(error, NotEnoughArgs):
    embed = voltage.SendableEmbed(
      title=random.choice(errormsg),
      description="YOU'RE MISSING ARGS!\n{}".format(error),
      colour="#516BF2"
    )
    return await message.reply(message.author.mention, embed=embed)
  elif isinstance(error, HTTPError):
    print(error)
  elif isinstance(error, UserNotFound):
    embed = voltage.SendableEmbed(
      title=random.choice(errormsg),
      description="That user doesnt exist!",
      colour="#516BF2"
    )
    return await message.reply(message.author.mention, embed=embed)
  elif isinstance(error, NotFoundException):
    embed = voltage.SendableEmbed(
      title=random.choice(errormsg),
      description=error,
      colour="#516BF2"
    )
    return await message.reply(message.author.mention, embed=embed)
  elif isinstance(error, NotEnoughPerms):
    embed = voltage.SendableEmbed(
      title=random.choice(errormsg),
      description=error,
      colour="#516BF2"
    )
    return await message.reply(message.author.mention, embed=embed)
  elif isinstance(error, NotBotOwner):
    embed = voltage.SendableEmbed(
      title=random.choice(errormsg),
      description="You dont own me! You cant use my owner only commands!",
      colour="#516BF2"
    )
    return await message.reply(message.author.mention, embed=embed)
  elif isinstance(error, ValueError):
    embed = voltage.SendableEmbed(
      title=random.choice(errormsg),
      description="You provided a value that isnt a number!",
      colour="#516BF2"
    )
    return await message.reply(message.author.mention, embed=embed)
  else:
    raise(error)


# Cog loading schenanigans
for filename in os.listdir("./cogs"):
  if filename.endswith(".py"):
    try:
      client.add_extension(f"cogs.{filename[:-3]}")
      print(f"Loaded {filename[:-3]} Cog!")
    except Exception as e:
      print(e)

while True:
  alive() #yeah blah blah stolen from old Mecha but hey, it works so why not copy and paste it, we're developers.
  client.run(config['TOKEN'], bot=True, banner=False) # Replace with your token in config, config.json to be exact, for everyone else, you know what this does stop fucking stalling pls :).