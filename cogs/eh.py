import discord
from discord.ext import commands
import aiosqlite3


class Eh(commands.Cog):
    def __init__(self, bot):
        self.bot=bot


    @commands.Cog.listener()
    async def on_command_error(self, ctx, e: Exception):
        if not ctx.guild:
            await ctx.send(e)


def setup(bot):
    bot.add_cog(Eh(bot))