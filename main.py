import random, pymongo, json
import voltage, os
from voltage.ext import commands

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
      return 1
    else:
      return 0
  else:
    return add_user(user)


def check_xp(user: voltage.User):
  user_id = str(user.id)
  user_data = userdb.find_one({'userid': user_id})
  if user_data:
    return user_data['levels']['xp']
  else:
    return 0


def add_user(user: voltage.User, isbot:bool=False):
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
    print(f"Added {user.name} to the database!")
    return "Added"
  except Exception as e:
    return f"Sorry, An Error Occured!\n\n```py\n{e}\n```"

def pingDB():
  try:
    DBclient.admin.command('ping')
    return "[+] Pinged your deployment. Successfully connected to MongoDB!"
  except Exception as e:
    return f"[-] ERROR! \n\n\n{e}"

def get_user(user: voltage.User):
  if userdb.find_one({"userid": user.id}):
    return userdb.find_one({"userid": user.id})
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
  print("Up and running (finally)")

  await client.set_status(
  text="@ | Another day, another dollar!", 
  presence=voltage.PresenceType.online
)

@client.listen("message")
async def on_message(message):
  if message.author.bot:
    return
  if update_level(message.author) == 1:
    await client.get_channel(config['LEVEL_CHANNEL']).send(f"{message.author.mention} has leveled up to **{get_user(message.author)['levels']['level']}**!")
  if userdb.find_one(
    {"userid":message.author.id}
  ):
    update_level(message.author)
    if random.randint(25,100) <= 25: # 25% chance to get xp off a message
      give_xp(message.author)
    elif message.content.startswith("m!"):
      give_xp(message.author)
  else: 
    add_user(message)
  await client.handle_commands(message)

@client.command(name="add", description="Adds you to the database!")
async def add(ctx):
  result = add_user(ctx.author)
  await ctx.reply(result)


@client.command(name="xp", description="Gets your XP and level!")
async def xp(ctx):

  await ctx.reply(f"**{ctx.author.name}** has **{check_xp(ctx.author)}** XP and is currently level **{get_user(ctx.author)['levels']['level']}**!")


client.add_extension("cogs.owner")
client.add_extension("cogs.fun")

client.run(config['TOKEN'])