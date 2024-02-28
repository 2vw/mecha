import voltage, pymongo, os, random, aiohttp, requests
from voltage.ext import commands

def setup(client) -> commands.Cog:
  fun = commands.Cog(
    "Fun",
    "More command testing, use these if you want *basic* fun commands."
  )

  @fun.command(
    description="Are you gay or no?",
    aliases=["howgay", "gay", "amigay", "gaypercent", "gayamount", "GayRate"],
    name="gayrate"
  )
  async def gayrate(ctx, member: voltage.Member = None):
    if member is None:
      member = ctx.author
    rate = random.randint(1, 100)
    embed = voltage.SendableEmbed(
      title=f"{ctx.author.name}",
      icon_url=ctx.author.avatar.url,
      description=f"🏳️‍🌈 | {member.display_name} is `{str(rate)}%` gay!",
      color="#516BF2",
    )
    await ctx.reply(embed=embed)

  @fun.command(name="8ball", description="Seek your fortune!")
  async def _8ball(ctx, *, question):
    responses = [
      "I belive not",
      "I dont think so",
      "No",
      "Maybe",
      "Ask again later",
      "Yes",
      "Affirmative",
      "I Belive So",
      "Its possible",
    ]
    embed = voltage.SendableEmbed(
      title=f"{ctx.author.name}",
      icon_url=ctx.author.avatar.url,
      description=f"""My response to `{str(question)}`...\n `{random.choice(responses)}`!""",
      color="#516BF2",
    )
    await ctx.reply(embed=embed)

  @fun.command(
    description="Get some cute doggo pics",
    aliases=[
      "dogpic",
      "doggos",
      "dogs",
      "dogpics",
      "dogpictures",
      "getdog",
      "getdogpics"
  ],
    name="dog"
  )
  async def dog(ctx):
    async with aiohttp.ClientSession() as session:
      q = requests.get("https://some-random-api.ml/img/dog/")
      json = q.json()['link']
    embed = voltage.SendableEmbed(
      title="Doggo!",
      icon_url=ctx.author.display_avatar.url,
      media=json,
      colour="#516BF2"
    )
    await ctx.send(content="[]()", embed=embed)

  @fun.command(
    description="Get some cute kitty pics",
    aliases=[
      "kitpic",
      "kitten",
      "cats",
      "catpics",
      "catpictures",
      "getcat",
      "getcatpicss"
  ],
    name="cat"
  )
  async def cat(ctx):
    async with aiohttp.ClientSession() as session:
      q = requests.get("https://some-random-api.ml/img/cat/")
      json = q.json()['link']
    embed = voltage.SendableEmbed(
      title="Doggo!",
      icon_url=ctx.author.display_avatar.url,
      media=json,
      colour="#516BF2"
    )
    await ctx.send(content="[]()", embed=embed)

    
  return fun