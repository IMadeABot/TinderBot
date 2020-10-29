import discord
from discord.ext import commands
import aiosqlite3
import os
import asyncio


class TinderBot(commands.Bot):
    def __init__(self):
        self.db = None
        super().__init__(command_prefix="", intents=discord.Intents.all(), case_insensitive=True)
        self.first_on_ready = True
    
    

bot = TinderBot()

OWNER_ID = #Your id here

@commands.check
async def is_me(ctx):
    return(ctx.author.id == OWNER_ID)


@bot.command(description="Reloads a cog")
@is_me
async def reload(ctx, cog_name):
    bot.unload_extension(f"cogs.{cog_name}")
    await asyncio.sleep(1)
    bot.load_extension(f"cogs.{cog_name}")
    await ctx.send(f"{cog_name} has been reloaded")


@bot.command(description="Unloads a Cog")
@is_me
async def unload(ctx, cog_name):
    bot.remove_cog(cog_name)
    bot.unload_extension(f"cogs.{cog_name}")
    await ctx.send(f"{cog_name} has been unloaded")


@bot.command(description="Loads a Cog")
@is_me
async def load(ctx, cog_name):
    bot.load_extension(f"cogs.{cog_name}")
    await ctx.send(f"{cog_name} has been loaded")



@bot.check
async def bot_check(ctx):
    return(ctx.guild==None)

@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user.name}')
    print(f'With ID: {bot.user.id}')
    if bot.first_on_ready:
        bot.first_on_ready=False
        bot.db = await aiosqlite3.connect("db/bot.db")
        cogs = os.listdir("cogs")
        for cog in cogs:
            if cog.endswith(".py"):
                try:
                    bot.load_extension(f"cogs.{cog[:-3]}")
                except Exception as e:
                    print(e)


@bot.command()
async def test(ctx):
    await bot.dump_profiles("")
    await ctx.send('pong')



TOKEN = open("token", "r").read()
bot.run(TOKEN)
