import voltage, pymongo, os, random, aiohttp
from voltage.ext import commands

def setup(client) -> commands.Cog:
  fun = commands.Cog(
    "Fun",
    "More command testing, use these if you want *basic* fun commands."
  )

  @fun.command(
    description="Are you gay or no?",
    aliases=["howgay", "gay", "amigay", "gaypercent", "gayamount"],
    name="GayRate"
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
    description="Get some cute doggo pics + facts!",
    aliases=[
      "dogpic",
      "doggos",
      "dogs",
      "dogpics",
      "dogpictures",
      "getdog",
      "getdogs"
  ],
    name="dog"
  )
  async def dog(ctx):
    async with aiohttp.ClientSession() as session:
      request = await session.get("https://some-random-api.ml/img/dog")
      dogjson = await request.json()
      request2 = await session.get("https://some-random-api.ml/facts/dog")
      factjson = await request2.json()

    embed = voltage.SendableEmbed(
      title="Doggo!",
      icon_url=ctx.author.display_avatar.url,
      media=dogjson["link"],
      colour="#516BF2",
      description=factjson["fact"],
    )
    await ctx.send(content="[]()", embed=embed)
    
  return fun