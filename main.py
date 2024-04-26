import asyncio
import logging
import os
import random
import sys
import time
import traceback
import logging

import aiohttp
import revolt
from revolt.ext import commands

import json
from helper.database import Database
from helper.revolt_bots import RBList
from host import alive


logging.basicConfig(
  filename='app.log',
  level=logging.DEBUG,
  format='%(asctime)s - %(levelname)s - %(message)s'
  )

sep = "\n"

with open("json/config.json", "r") as f:
    config = json.load(f)

with open("json/data.json", "r") as f:
    data = json.load(f)
    data['uptime'] = int(time.time())

with open("json/data.json", "w") as r:
    json.dump(data, r, indent=2)


class HelpCommand(commands.HelpCommand):
    async def send_help(self, ctx: commands.Context):
        embed = revolt.SendableEmbed(
            title="Help",
            description=f"Use `{ctx.prefix}help <command>` to get more information on a command.",
            colour="#516BF2",
            icon_url=ctx.author.display_avatar.url
        )
        text = ""
        for i in self.client.cogs.values():
            if i.name.lower() == "owner" or i.name.lower() == "giveaway":
                pass
            else:
                text += f"{sep}### **{i.name}**{sep}{i.description}{sep}"
                for j in i.commands:
                    text += f"`{j.name}` "
        if embed.description:
            embed.description += text
        return await ctx.reply(embed=embed)


# will continue this later
class Help(commands.HelpCommand):
    async def send_help(self, ctx: commands.Context):
        embed = revolt.SendableEmbed(
            title="Help",
            description=f"Use `{ctx.prefix}help <command>` to get help for a command.",
            colour="#fff0f0",
            icon_url=client.user.display_avatar.url,
        )
        text = "\n### **No Category**\n"
        covered = []
        for command in ctx.client.commands.values():
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

    async def send_command_help(self, ctx: commands.Context, command: commands.Command):
        embed = revolt.SendableEmbed(
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

    async def send_cog_help(self, ctx: commands.Context, cog: commands.Cog):
        embed = revolt.SendableEmbed(
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

    async def send_not_found(self, ctx: commands.Context, target: str):
        embed = revolt.SendableEmbed(
            title="Help",
            description=f"`{ctx.prefix}{target} doesnt exist!`",
            colour="#fff0f0",
            icon_url=client.user.display_avatar.url
        )
        return await ctx.send(embed=embed)


class MyClient(commands.CommandsClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db_client = Database(self)
        self.RBList = RBList(self)

        # log uncaught exceptions
        def log_exceptions(type, value, tb):
            for line in traceback.TracebackException(type, value, tb).format(chain=True):
                logging.exception(line)
            logging.exception(value)

            sys.__excepthook__(type, value, tb)  # calls default excepthook

        sys.excepthook = log_exceptions

        self.get_prefix = self.db_client.get_prefix

    async def status(self):
        print("Started Status Loop")
        while True:
            statuses = [
                f"Playing with {len(self.servers)} servers and {len(self.users)} users!",
                f"Watching {len(self.users)} users!",
                f"My waifu is better than yours!!! | {len(self.servers)} servers",
                f"Lea | {len(self.servers)} servers",
                f"Hey everyone! | {len(self.servers)} servers",
                f"I am a bot | {len(self.servers)} servers",
                f"Please stop asking to see my feet | {len(self.servers)} servers",
                f"guys my father just came back with the milk O_O - delta2571 | {len(self.servers)} servers",
                f"Revolt > shitcord | {len(self.servers)} servers",
                f"William Says HI! | {len(self.servers)} servers",
                f"Playing the numbers game | {len(self.servers)} servers",
                f"Spreading joy across {len(self.users)} users!",
                f"Running rampant in {len(self.servers)} servers!",
                f"Chillin' with {len(self.users)} users!",
                f"Your friendly bot | {len(self.servers)} servers | {len(self.users)} users",
                f"Beep boop! I'm a bot | {len(self.servers)} servers",
                f"Try 'm!help' to get started | {len(self.servers)} servers",
                f"ccccccuthdkhugjktlcfvrhvtrdkgrfcikeekdvtfdrn | {len(self.servers)} servers",
                f"Gaming rn, talk later? | {len(self.servers)} servers",
                f"saul goodman | {len(self.servers)} servers",
                f"Max was here | {len(self.servers)} servers",
            ]
            status = random.choice(statuses)
            await self.edit_status(text=status, presence=revolt.PresenceType.online)
            await asyncio.sleep(60)

    async def stay_on(self):
        i = 0
        while True:
            channel = self.get_channel(config['REMIND_CHANNEL'])
            embed = revolt.SendableEmbed(
                title="I'm online!",
                description=f"I'm online!\nIts been {i} hour(s)!",
            )
            await channel.send(embed=embed)
            await asyncio.sleep(60 * 60)
            i += 1

    async def ready(self):
        self.RBList.post()
        print("Up and running")  # Prints when the client is ready. You should know this
        with open("json/data.json", "r") as f:
            data = json.load(f)
        if time.time() - data['uptime'] > 3600:
            print("Back online! Starting up again!")

        print(f"Connected to {len(self.servers)} servers and {len(self.users)} users!")
        await asyncio.gather(
            self.db_client.update_stats(users=len(self.users), servers=len(self.servers)),
            self.db_client.update(),
            self.status(),
            self.db_client.do(),
            self.db_client.upd(),
            self.db_client.cheater_beater()
        )

    async def old_level_stuff(self, message: revolt.Message):  # running this in the on_message event drops the speed down to your grandmothers crawl. keep this in a function pls
        # Moving it for consistency's sake - andreaw
        if await self.db_client.update_level(message.author):
            try:
                channel = self.get_channel(config['LEVEL_CHANNEL'])
                embed = revolt.SendableEmbed(
                    title=f"{message.author.name} has leveled up!",
                    description=f"{message.author.name} has leveled up to level **{(await get_user(message.author))['levels']['level']}**!",
                    color="#44ff44",
                    icon_url=message.author.avatar.url if message.author.avatar else "https://ibb.co/mcTxwnf"
                )
                await channel.send(embed=embed)  # praise kink? it's whatever
            except KeyError:
                print(
                    "keyerror :("
                )  # this should never happen, if it does, tell William, if it doesn't, tell William anyway.

        if (await userdb.find_one(
                {"userid": message.author.id}
        )):  # super fucking stupid but it makes pylance happy
            await self.db_client.update_level(message.author)
            await self.db_client.give_xp(message.author, random.randint(1, 5))
        else:
            print(await self.db_client.add_user(message))

    async def level_stuff(self, message: revolt.Message):
        try:
            if message.content == "<@01FZB4GBHDVYY6KT8JH4RBX4KR>":
                user_data = await self.db_client.get_user(message.author)
                if user_data is not None:
                    prefix = user_data['prefixes']
                    prefix = prefix or ["m!"]
                    embed = revolt.SendableEmbed(
                        title="Prefix",
                        description=f"Your prefixes are:\n ```\n{chr(10).join(prefix)}\n```\nIf you want to change your prefix, type `m!prefix <new prefix>`!",
                        colour="#198754",
                    )
                    await message.reply(embed=embed)
                else:
                    return print(await self.db_client.add_user(message.author))
        except Exception:
            pass

        if await self.db_client.update_level(message.author):
            try:
                channel = self.get_channel(config['LEVEL_CHANNEL'])
                embed = revolt.SendableEmbed(
                    title=f"{message.author.name} has leveled up!",
                    description=f"{message.author.name} has leveled up to level **{(await self.db_client.get_user(message.author))['levels']['level']}**!",
                    color="#44ff44",
                    icon_url=message.author.avatar.url if message.author.avatar else "https://ibb.co/mcTxwnf"
                )
                await channel.send(embed=embed)  # praise kink? it's whatever
            except KeyError:
                print(
                    "LEVEL CHANNEL ISN'T DEFINED OR USER DOESNT EXIST"
                )  # this should never happen, if it does, tell William, if it doesn't, tell William anyway.
            return

        user_data = await self.db_client.get_user(message.author)
        if user_data:
            if user_data['levels']['lastmessage'] < time.time():
                await self.db_client.give_xp(message.author, random.randint(1, 2))
                await self.db_client.update_level(message.author)
                await self.db_client.userdb.update_one(
                    {"userid": message.author.id},
                    {
                        "$set": {
                            "levels.lastmessage": int(time.time()) + 5
                        }
                    }
                )
            else:
                return f"{message.author.name} is on cooldown for {user_data['levels']['lastmessage'] - int(time.time()):.0f} seconds"
        else:
            return await self.db_client.add_user(message)

    async def logging_stuff(self, message):
        try:
            if message.server is None:
                return

            return await self.db_client.add_user(message.author)
        except Exception:
            pass

    # EVENTS
    async def on_ready(self):
        # Cog loading shenanigans
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    print(f"Loaded {filename[:-3]} Cog!")
                except Exception as e:
                    print(f"Could not load {filename[:-3]}:", e)
                    # traceback.print_exception(type(e), e, e.__traceback__)

    # Thank TheBobBobs, bro is a fucking goat for this.
    async def on_message(self, message: revolt.Message):
        if message.author.bot or message.server is None:
            return

        await self.process_commands(message)  # so everything else doesn't trip over its clumsy ass selves.

        asyncio.create_task(self.level_stuff(message))  # pièce de résistance
        asyncio.create_task(self.db_client.afk_check(message))
        asyncio.create_task(self.logging_stuff(message))

    async def on_reaction_add(self, message, user, reaction):
        try:
            with open("json/data.json", "r") as f:
                data = json.load(f)

            if message.channel.id == message.author.id:
                return
            elif message.id == data['BETA_ID'] and reaction == "👍" and user.id != message.author.id:
                msg = await message.reply(f"👍 | You've just joined the beta club, <@{user.id}>!")
                await asyncio.sleep(5)
                await msg.delete()
        except KeyError:
            pass

    async def on_reaction_remove(self, message, user, reaction):
        with open("json/data.json", "r") as f:
            data = json.load(f)

        try:
            if message.channel.id == message.author.id:
                return
            elif message.id == data['BETA_ID'] and reaction == "👍" and user != message.author.id:
                msg = await message.reply(f"👍 | You've just left the beta club, <@{user}>!", delete_after=5)
                await asyncio.sleep(5)
                await msg.delete()
        except KeyError:
            pass

    async def on_server_join(self, server: revolt.Server):
        channel = self.get_channel(config['SERVER_CHANNEL'])
        embed = revolt.SendableEmbed(
            title="New Server alert!",
            description=f"## Just Joined a new server!\nNow at **{len(self.servers)}** servers!",
            color="#516BF2",
        )
        await channel.send(content="[]()", embed=embed)

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        errormsgs = [
            "Error! Error!",
            "LOOK OUT!!! ERROR!!",
            "Whoops!",
            "Oopsie!",
            "Something went wrong!",
            "Something happened..",
            "What happened? I know!",
            "404!",
            "ERROR.. ERROR..",
            "An Error Occurred!"
        ]

        embed = revolt.SendableEmbed(
            title=random.choice(errormsgs),
            colour="#516BF2"
        )

        if isinstance(error, commands.CommandNotFound):
            embed.description = "That command doesnt exist!"
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"Missing required argument `{error.missing}`"
        elif isinstance(error, revolt.HTTPError):
            traceback.print_exception(type(error), error, error.__traceback__)
        elif isinstance(error, commands.UserConverterError):
            embed.description = f"`{error.argument}` is not a valid user mention/id/name"
        # elif isinstance(error, NotFoundException):  # I don't know when this error is raised
        #     embed = voltage.SendableEmbed(
        #         title=random.choice(errormsgs),
        #         description=error,
        #         colour="#516BF2"
        #     )
        #     return await message.reply(message.author.mention, embed=embed)
        elif isinstance(error, commands.MissingPermissionsError):
            fmt = ', '.join(f"`{perm}`" for perm, allowed in error.permissions.items() if allowed)
            embed.description = f"You need {fmt} permission(s)"
        elif isinstance(error, commands.NotBotOwner):
            embed.description = "You dont own me! You cant use my owner only commands!"
        # elif isinstance(error, commands.IntConverterError):
        #     embed.description = f"`{error.argument}` is not a number"
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"You're on cooldown! Please wait `{round(error.retry_after, 2)}s`!"
        elif isinstance(error, PermissionError):  # If the bot tries to do something, and it fails, it'll raise a forbidden: 403
            try:
                return await message.reply("I don't have permission to do that!")
            except Exception:
                pass
        else:
            # traceback.print_exception(type(error), error, error.__traceback__)
            logging.error(error)
            return

        return await ctx.message.reply(embed=embed)


async def main():
    while True:
        async with aiohttp.ClientSession() as session:
            client = MyClient(session, config['TOKEN'])  # Replace with your token in config, config.json to be exact, for everyone else, you know what this does stop fucking stalling pls :).
            await client.start()
            alive()  # yeah blah blah stolen from old Mecha but hey, it works so why not copy and paste it, we're developers.


if __name__ == '__main__':
    asyncio.run(main())


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
