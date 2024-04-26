import time
from revolt.ext import commands
from functools import wraps

cooldowns = {}


async def add_cooldown(ctx: commands.Context, command_name: str, seconds: int):
    cooldowns[ctx.author.id][str(command_name)] = time.time() + seconds
    return True


async def check_cooldown(ctx: commands.Context, command_name: str, seconds: int):
    try:
        if time.time() < cooldowns[ctx.author.id][command_name]:
            return True
        else:
            del cooldowns[ctx.author.id][command_name]
    except KeyError:
        await add_cooldown(ctx, command_name=command_name, seconds=seconds)
    return False


# THANK YOU VLF I LOVE YOU :kisses:
def limiter(cooldown: int, *, on_ratelimited=None, key=None):
    getter = key or (lambda ctx, *_1, **_2: ctx.author.id)

    def wrapper(callback):
        @wraps(callback)
        async def wrapped(ctx, *args, **kwargs):
            if isinstance(ctx, commands.Context):
                k = getter(ctx, *args, **kwargs)
            else:
                ctx = args[0]
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
