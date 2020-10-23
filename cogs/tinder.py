import discord
from discord.ext import commands
from discord.ext import tasks
import asyncio
import random


class Tinder(commands.Cog):
    def __init__(self, bot):
        self.bot=bot
        self.profiles = {}
        self.people = []
        self.main_server=self.bot.get_guild(int(open("mainserverid", "r").read()))
        self.main_verified=self.main_server.get_role(int(open("verifiedroleid").read()))
        self.match_dict = {}
        coro = self.startup()
        asyncio.ensure_future(coro)
        
    
    async def dump(self):
        async with self.bot.db.cursor() as c:
            await c.execute("SELECT id FROM  profiles")
            all_users = [i[0] for i in await c.fetchall()]
            await self.bot.db.commit()
            for profile in self.profiles:
                name = self.profiles[profile].title
                bio = self.profiles[profile].description
                image = str(self.profiles[profile].image.url)
                if profile in all_users:
                    await c.execute(f"UPDATE profiles SET Name='{name}' WHERE id='{profile}'")
                    await c.execute(f"UPDATE profiles SET Bio='{bio}' WHERE id='{profile}'")
                    await c.execute(f"UPDATE profiles SET Image='{image}' WHERE id='{profile}'")
                else:
                    await c.execute(f"INSERT INTO profiles VALUES (?,?,?,?)", (profile, name, bio, image))
                await self.bot.db.commit()

        async with self.bot.db.cursor() as c:
            await c.execute("SELECT id FROM matches")
            all_users = [i[0] for i in await c.fetchall()]
            await self.bot.db.commit()
            for person in self.match_dict:
                match_list = "".join(f"{i} " for i in self.match_dict[person])[:-1]
                if person in all_users:
                    await c.execute(f"UPDATE matches SET Matches='{match_list}' WHERE id='{person}'")
                else:
                    await c.execute(f"INSERT INTO matches VALUES (?,?)", (person, match_list))
                await self.bot.db.commit()


    @tasks.loop(minutes=10)
    async def save(self):
        await self.dump()



    async def startup(self):
        async with self.bot.db.cursor() as c:
            await c.execute("SELECT * FROM profiles")
            for profile in await c.fetchall():
                self.profiles[profile[0]] = discord.Embed(title=profile[1], description=profile[2])
                self.profiles[profile[0]].set_image(url=profile[3])
                self.people.append(profile[0])
                self.match_dict[profile[0]] = []
            await c.execute("SELECT * FROM matches")
            for person in await c.fetchall():
                self.match_dict[person[0]] = person[1].split(" ")
                if "" in self.match_dict[person[0]]:
                    self.match_dict[person[0]].remove("")
        self.save.start()

            
    def cog_unload(self):
        coro = self.dump()
        asyncio.ensure_future(coro)
        self.save.stop()

    @commands.command(description="Makes a profile or views yours if you already have one")
    async def profile(self, ctx, *, AboutYou=""):
        if str(ctx.author.id) in self.profiles:
            await ctx.send(embed=self.profiles[str(ctx.author.id)])
            return
        if not ctx.message.attachments:
            await ctx.send("You need to attatch an image")
            return
        if not ctx.author in self.main_server.members:
            await ctx.send(f"You need to join the {self.main_server.name} Server. ")
            return
        member = self.main_server.get_member(ctx.author.id)
        if not self.main_verified in member.roles:
            await ctx.send(f"You will need to verify yourself in the {self.main_server.name} server. To do this, please contact admins of the {self.main_server.name} server")
            return
        if not AboutYou:
            await ctx.send("Please write a bit about yourself...")
            return
        self.profiles[str(ctx.author.id)] = discord.Embed(title=f"{member.display_name}", description=AboutYou)
        image = str(ctx.message.attachments[0].url)
        self.profiles[str(ctx.author.id)].set_image(url=image)
        self.people.append(str(ctx.author.id))
        self.match_dict[str(ctx.author.id)] = []
    
    @commands.command(description="Updates your profile bio. Cannot update the ")
    async def update(self, ctx, *, bio):
        if not str(ctx.author.id) in self.profiles:
            await ctx.send("You need to create your profile with the \"profile\" command")
            return
        self.profiles[str(ctx.author.id)].description=bio
        if ctx.message.attachments:
            image = str(ctx.message.attachments[0].url)
            self.profiles[str(ctx.author.id)].set_image(url=image)
    
    @commands.command(description="Shows you your next profile")
    async def next(self, ctx):
        if not str(ctx.author.id) in self.profiles:
            await ctx.send("You need to create a profile with the \"profile\" command first")
            return
        if len(self.match_dict[str(ctx.author.id)]) > len(self.people)-2:
            await ctx.send(self.match_dict[str(ctx.author.id)])
            await ctx.send(f"{len(self.match_dict[str(ctx.author.id)])} - {len(self.people)-2}")
            await ctx.send("You have already gone through everyone here...")
            return
        possible_matches = self.people[:]
        possible_matches.remove(str(ctx.author.id))
        for match in self.match_dict[str(ctx.author.id)]:
            possible_matches.remove(match[:-1])
        match = random.choice(possible_matches)
        profile = self.profiles[match]
        msg = await ctx.send(embed=profile)
        await msg.add_reaction("\u2705")
        await msg.add_reaction("\u274e")
        def check(reaction, user):
            return(reaction.emoji in ["\u2705", "\u274e"] and user.id == ctx.author.id and reaction.message.id==msg.id)
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30)
            if reaction.emoji=="\u2705":
                if f"{user.id}+" in self.match_dict[match]:
                    match = self.bot.get_user(int(match))
                    await ctx.send(f"IT'S A MATCH!\nThey also gave you a tick!\nTheir name on discord is {match.name}#{match.discriminator}")
                    await match.send(f"This person matched with you. Good luck. Their discord is {ctx.author.name}#{ctx.author.discriminator}", embed=self.profiles[str(ctx.author.id)])
                else:
                    await ctx.send(f"Waiting for {self.profiles[match].title} to get back. Why not continue searching")
                self.match_dict[str(ctx.author.id)].append(f"{match}+")
            else:
                await ctx.send("We won't send that person's profile to you again. We also won't tell them about this so don't wory")
                self.match_dict[str(ctx.author.id)].append(f"{match}-")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to decide. You may still be offered to match with this person again.")

    @commands.command(description="Shows you your matches")
    async def matches(self, ctx):
        if not str(ctx.author.id) in self.match_dict:
            await ctx.send("You need a profile to have matches")
            return
        if len(self.match_dict[str(ctx.author.id)]) == 0:
            await ctx.send("You haven't matched with anyone yet")
            return
        positive=[]
        waiting=[]
        for match in self.match_dict[str(ctx.author.id)]:
            if match[-1] == "+":
                if f"{ctx.author.id}+" in self.match_dict[match[:-1]]:
                    positive.append(self.profiles[match[:-1]])
                else:
                    waiting.append(self.profiles[match[:-1]])
        for e in positive:
            await ctx.send("match!", embed=e)
        for e in waiting:
            if e:
                await ctx.send("waiting on...", embed=e)
    
    @commands.command(description="Safely kills bot")
    @is_me
    async def kill(self,ctx):
        await asyncio.wait_for(self.dump(), timeout=None)
        exit()

    
        

        

def setup(bot):
    bot.add_cog(Tinder(bot))