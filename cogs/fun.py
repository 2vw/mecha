import json
import random

import google.generativeai as genai
import revolt
from revolt.ext import commands

with open("json/config.json", "r") as f:
    config = json.load(f)

genai.configure(api_key=config["GOOGLEAPIKEY"])
model = genai.GenerativeModel('gemini-pro')


class Fun(commands.Cog):
    description = "More command testing, use these if you want *basic* fun commands."

    def __init__(self, client):
        self.client = client

    @staticmethod
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

    @commands.command(
        aliases=["howgay", "gay", "amigay", "gaypercent", "gayamount", "GayRate"],
        name="gayrate"
    )
    async def gayrate(self, ctx: commands.Context, member: revolt.Member = None):
        """Are you gay or no?"""
        if member is None:
            member = ctx.author

        rate = random.randint(1, 100)
        embed = revolt.SendableEmbed(
            title=f"{ctx.author.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            description=f"🏳️‍🌈 | {member.display_name} is `{str(rate)}%` gay!",
            color="#516BF2",
        )
        await ctx.reply(embed=embed)

    @commands.command(name="8ball")
    async def _8ball(self, ctx, *, question):
        """Seek your fortune!"""
        responses = [
            "I believe not",
            "I dont think so",
            "No",
            "Maybe",
            "Ask again later",
            "Yes",
            "Affirmative",
            "I Believe So",
            "Its possible",
        ]
        embed = revolt.SendableEmbed(
            title=ctx.author.name,
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None,
            description=f"My response to `{str(question)}`...\n `{random.choice(responses)}`!",
            color="#516BF2",
        )
        await ctx.reply(embed=embed)

    @commands.command(
        name="ai",
        aliases=['talkai'],
    )
    async def ai(self, ctx, *, question):
        """"Talk to an AI"""
        embed = revolt.SendableEmbed(
            title=f"{ctx.author.name}",
            icon_url=ctx.author.avatar.url,
            description=f"Your question: `{question}`\n\nGenerating Response..",
            colour="#516BF2"
        )
        await ctx.reply(embed=embed)
        chat = model.start_chat()
        response = chat.send_message(question)

        groups = self.split_text(response.text, 800)

        for group in groups:
            embed = revolt.SendableEmbed(
                description=group,
                colour="#516BF2"
            )
            await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Fun(client))

