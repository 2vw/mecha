import voltage, pymongo, os, random, aiohttp, requests, json
from voltage.ext import commands
from bardapi import BardAsync
import google.generativeai as genai


with open("json/config.json", "r") as f:
  config = json.load(f)

genai.configure(api_key=config["GOOGLEAPIKEY"])

model = genai.GenerativeModel('gemini-pro')
bard = BardAsync(token=config['BARDTOKEN'])

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

  def split_text(text, max_chars):
    """
    Splits a large text into groups by newlines if they're over a character limit,
    without cutting out words while keeping its format.

    Args:
        text (str): The input text.
        max_chars (int): The maximum number of characters per group.

    Returns:
        list: A list of strings, each representing a group of text.
    """
    lines = text.split("\n")
    result = []
    current_group = ""

    for line in lines:
        if len(current_group) + len(line) <= max_chars:
            current_group += line + "\n"
        else:
            result.append(current_group.strip())
            current_group = line + "\n"

    if current_group:
        result.append(current_group.strip())

    return result

  @fun.command(
    name="ai",
    aliases=['talkai'],
    description="Talk to an AI"
  )
  async def ai(ctx, *, question):
    embed = voltage.SendableEmbed(
      title=f"{ctx.author.name}",
      icon_url=ctx.author.avatar.url,
      description=f"Your question: `{question}`\n\nGenerating Response..",
      colour="#516BF2"
    )
    await ctx.reply(embed=embed)
    chat = model.start_chat()
    response = chat.send_message(question)

    groups = split_text(response.text, 800)

    for i, group in enumerate(groups):
      embed = voltage.SendableEmbed(
        description=group,
        colour="#516BF2"
      )
      await ctx.send(embed=embed)

    
  return fun