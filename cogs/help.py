import revolt
from revolt.ext import commands

from utilities.revolt_utilities import Paginator

from revolt import SendableEmbed
MAIN = "#dd2e44"


class HelpCommand(commands.HelpCommand):
    def get_usage(self, command: commands.Command) -> str:
        if command.usage:
            return command.usage

        parents: list[str] = []

        if command.parent:
            parent = command.parent

            while parent:
                parents.append(parent.name)
                parent = parent.parent

        parameters: list[str] = []
        names = [command.name]
        names.extend(command.aliases)

        for parameter in command.parameters[2:]:
            if parameter.kind == parameter.POSITIONAL_OR_KEYWORD:
                if parameter.default is not parameter.empty:
                    parameters.append(f"[{parameter.name}={parameter.default}]")
                else:
                    parameters.append(f"<{parameter.name}>")
            elif parameter.kind == parameter.KEYWORD_ONLY:
                if parameter.default is not parameter.empty:
                    parameters.append(f"[{parameter.name}={parameter.default}]")
                else:
                    parameters.append(f"<{parameter.name}...>")
            elif parameter.kind == parameter.VAR_POSITIONAL:
                parameters.append(f"[{parameter.name}...]")

        names = f"[{'|'.join(names)}]" if len(names) > 1 else names[0]
        return f"{' '.join(parents[::-1])} {names} {' '.join(parameters)}"

    async def create_global_help(self, context: commands.Context, commands_: dict[commands.Cog | None, list[commands.Command]]) -> Paginator:
        embed = SendableEmbed(title="Help!", description=f"""- Hello, welcome to the help page! This is the global help page.
- If you want more information use `{context.prefix}help <category|group|command>`

Here's how you can read a command's signature:

#### <argument>
if the argument is surrounded by `<>` it means that it's a required argument.
#### [argument]
if the argument is surrounded by `[]` it means that it's a optional argument.
#### argument...
if the argument is followed by `...` it means that it's a greedy argument.""", colour=MAIN)
        embeds = [embed]

        for cog, cmds in commands_.items():
            if not cmds:
                continue

            embed = SendableEmbed(title=f"Help for {cog.qualified_name if cog else 'Global'}", description=f"### {cog.qualified_name if cog else 'Global'}\n\n", colour=MAIN)

            for command in cmds:
                embed.description += f"- `{context.prefix}{self.get_usage(command)}` - {command.short_description}\n"

                if isinstance(command, commands.Group):
                    for subcommand in command.commands:
                        embed.description += f"    - `{context.prefix}{self.get_usage(subcommand)}` - {subcommand.short_description}\n"

                    embed.description += "***\n"

            embed.description = embed.description.strip()
            embeds.append(embed)

        paginator = Paginator(timeout=60, client=context.client, pages=embeds)
        paginator.add_button("first", emoji="⏪")
        paginator.add_button("previous", emoji="◀️")
        paginator.add_button("delete", emoji="🗑️")
        paginator.add_button("next", emoji="▶️")
        paginator.add_button("last", emoji="⏩")
        return paginator

    async def create_cog_help(self, context: commands.Context, cog: commands.Cog) -> SendableEmbed | Paginator:
        cmds = await self.filter_commands(context, cog.commands)
        if not cmds:
            return "No commands found in the category"

        embed = SendableEmbed(title=f"Help for {cog.qualified_name}", description=f"### {cog.qualified_name}\n\n", colour=MAIN)

        for command in cmds:
            embed.description += f"- `{context.prefix}{self.get_usage(command)}` - {command.short_description}\n"

            if isinstance(command, commands.Group):
                for subcommand in command.commands:
                    embed.description += f"    - `{context.prefix}{self.get_usage(subcommand)}` - {subcommand.short_description}\n"

                embed.description += "***\n"

        embed.description = embed.description.strip()
        return embed

    async def create_command_help(self, context: commands.Context, command: commands.Command | commands.Group) -> SendableEmbed:
        embed = SendableEmbed(title=f"Help for {command.name}", description=f"### {command.name}\n\n`{context.prefix}{self.get_usage(command)}`\n{chr(10).join('> '+l for l in command.description.split(chr(10)))}\n", colour=MAIN)

        if command.aliases:
            embed.description += f"**Aliases:** {', '.join(command.aliases)}\n"

        if command.parent:
            embed.description += f"**Parent command:** {command.parent.name}\n"

        if command.cog:
            embed.description += f"**Category:** {command.cog.qualified_name}\n"

        if isinstance(command, commands.Group):
            embed.description += f"**Children commands:** {', '.join('`'+c.name+'`' for c in command.commands)}\n"

        embed.description = embed.description.strip()
        return embed

    create_group_help = create_command_help

    async def send_help_command(self, context: commands.Context, message_payload: Paginator | dict[str, SendableEmbed | str]):
        if isinstance(message_payload, Paginator):
            await message_payload.start_paginator(context, check=lambda _, u, __: u.id == context.author.id)
        else:
            return await context.send(**message_payload)

    async def handle_no_command_found(self, context: commands.Context, name: str) -> str:
        return f"No help found for `{name}`."


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._default_help = None

    async def cog_load(self):
        self._default_help = self.client.help_command
        self.client.help_command = HelpCommand()
        cmd: commands.Command = self.client.get_command('help')
        cmd.description = "Shows help for a command, category or the entire bot"

    async def cog_unload(self):
        self.client.help_command = self._default_help


async def setup(client):  # Your help command in help.py doesn't work through the migration, so I just pasted mine
    await client.add_cog(Help(client))
