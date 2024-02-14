# """
# OK SO TODO IS THIS A GOOD IDEA?
# IF NOT, JUST DON'T USE IT
# IT'S A MESS
# ANYWAYS LOOK AT THE FLASK SITE AND SEE IF YOU CAN IMPLEMENT IT
# THEN ADD IT TO THE COG IF POSSIBLE
#
#
#
# PUSH TO GIT LATER PLEASEEEEEEE!!!!!!!!
# tis a mess lol
# """

import random, pymongo, json, time, asyncio
import voltage, os
from voltage.ext import commands
from host import alive

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

with open("config.json", "r") as f:
  config = json.load(f)

DBclient = MongoClient(config['MONGOURI'], server_api=ServerApi('1'))

db = DBclient['beta']
userdb = db['users']

def update_level(user:voltage.User):
  if userdb.find_one({'userid':user.id}):
    user_data = userdb.find_one({'userid':user.id})
    if user_data['levels']['xp'] > (100 * user_data['levels']['level']):
      userdb.update_one({'userid':user.id}, {'$inc':{'levels.level':1}})
      return True
    else:
      return False
  else:
    return add_user(user)


def check_xp(user: voltage.User):
  user_id = str(user.id)
  user_data = userdb.find_one({'userid': user_id})
  if user_data:
    return user_data['levels']['xp']
  else:
    return 0


def add_user(user: voltage.User, isbot:bool=False): # long ass fucking function to add users to the database if they dont exist yet. but it works..
  if userdb.find_one({"userid": user.id}):
    return "User already exists."
  id = 1
  for i in userdb.find({}):
    id += 1
  try:
    userdb.insert_one({
        "_id": id,
        "username": user.name,
        "userid": user.id,
        "levels": {
            "xp": 0,
            "level": 1
        },
        "economy": {
            "wallet": 0,
            "bank": 0,
            "data": {
                "inventory": {
                    "bank_loan": 1
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
        "status": {
            "beta": False,
            "familyfriendly": False,
            "premium": False,
            "admin": False,
            "isBot": isbot,
            "banned": False
        }
    })
    return "Added"
  except Exception as e:
    return f"Sorry, An Error Occured!\n\n```\n{e}\n```"

def pingDB(): # ping the database; never gonna use this, might need it, add it.
  try:
    DBclient.admin.command('ping')
    return "[+] Pinged your deployment. Successfully connected to MongoDB!"
  except Exception as e:
    return f"[-] ERROR! \n\n\n{e}"

def get_user(user: voltage.User):
  if user := userdb.find_one({"userid": user.id}):
    return user
  else:
    return "User not found."  
 
def give_xp(user: voltage.User):   
  userdb.update_one(
      {"userid":user.id},
      {
          "$inc": {
          "levels.xp": random.randint(1, 5)
          }
      }
  )

prefixes = ["m!"]
client = commands.CommandsClient(prefix=prefixes)


@client.listen("ready")
async def ready():
  print("Up and running (finally)") # Prints when the client is ready. You should know this

  await client.set_status(
  text="@ | Another day, another dollar!", # DONT DO THIS! We're only doing it because its convienient and we need to port the switcher :)
  presence=voltage.PresenceType.online # you can change this if you want but its not required, just read the fucking docs.
)

async def levelstuff(message): # running this in the on_message event drops the speed down to your grandmothers crawl. keep this in a function pls
  if update_level(message.author):
    try:
      channel = client.get_channel(config['LEVEL_CHANNEL'])
      await channel.send(f"{message.author.name} has leveled up to **{get_user(message.author)['levels']['level']}**!") # praise kink? its whatever
    except KeyError:
      print("keyerror :(") # this should never happen, if it does, tell William, if it doesnt, tell William anyways.
  if userdb.find_one(
    {"userid":message.author.id}
  ): #super fucking stupid but it makes pylance happy
    update_level(message.author)
    if random.randint(25,100) <= 50: # 50% chance to get xp off a message, im too lazy to input my own rate limit fuck that
      give_xp(message.author)
    if message.content.startswith("m!"): # good boy points if you use commands (will have to replace this later when custom prefixing is implemented)
      give_xp(message.author)
  else: 
    print(add_user(message))

# this shit is so fucking weird but hey, it works
# Thank TheBobBobs, bro is a fucking goat for this.
@client.listen("message")
async def on_message(message):
  if message.author.bot:
    return
  asyncio.create_task(levelstuff(message)) # pièce de résistance
  await client.handle_commands(message) # so everything else doesnt trip over its clumsy ass selves.

@client.command(name="add", description="Adds you to the database!") # whos really using this command? Like really, move this to owner.py when pls..
async def add(ctx):
  result = add_user(ctx.author)
  await ctx.reply(f"Results are in! {result}")


@client.command(name="xp", description="Gets your XP and level!")
async def xp(ctx):
  user = get_user(ctx.author)
  level = user['levels']['level'] # this is so stupid
  xp = user['levels']['xp'] # this is so stupid
  await ctx.reply(f"**{ctx.author.name}** has **{xp}** XP and is currently level **{level}**!") # praise kink? its whatever

# Cog loading schenanigans
client.add_extension("cogs.owner")
client.add_extension("cogs.fun")

alive() #yeah blah blah stolen from old Mecha but hey, it works so why not copy and paste it, we're developers.
client.run(config['TOKEN']) # Replace with your token in config, config.json to be exact, for everyone else, you know what this does stop fucking stalling pls :).