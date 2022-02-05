# bot.py
import os
import random
import discord
import youtube_dl
import asyncio
import pafy

from discord.ext import commands
# from music import Player
from dotenv import load_dotenv

#https://youtu.be/46ZHJcNnPJ8 <- credit

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# class CustomClient(discord.Client):
#     async def on_ready(self):
#         print(f'{self.user} has connected to Discord!')

#     async def on_message(self, message):
#         if message.author == client.user:
#             return

#         brooklyn_99_quotes = [
#         'I\'m the human form of the 💯 emoji.',
#         'Bingpot!',
#         'Cool. Cool cool cool cool cool cool cool',
#         'no doubt no doubt no doubt no doubt.'
#         ]

#         if message.content == '99!':
#             response = random.choice(brooklyn_99_quotes)
#             await message.channel.send(response)

#     async def on_member_join(self, member): #doesn't work
#         await member.create_dm()
#         await member.dm_channel.send(f'Hi {member.name}, welcome to this shit hole!')

#     async def on_member_remove(member): #doesn't work
#         await member.create_dm()
#         await member.dm_channel.send(f'later shit hole!')

class Player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}

        self.setup()

    def setup(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []

    async def check_queue(self, ctx):
        if len(self.song_queue[ctx.guild.id]) > 0:
            ctx.voice_client.stop()
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)

    async def search_song(self, amount, song, get_url = False):
        info = await self.bot.loop.run_in_execution(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet" : True}).extract_info(f"ytseach{amount}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info ["entries"]] if get_url else info

    async def play_song(self, ctx, song):
        url = pafy.new(song).getbestaudio().url
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after = lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.5 #adjust base audio level

    @commands.command()
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("You are not connected to a voice channel.")

        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()

        await ctx.author.voice.channel.connect()

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client is not None:
            return await ctx.voice_client.disconnect()
        
        await ctx.send("I am not connected to a voice channel.")

    @commands.command()
    async def play(self, ctx, *, song = None):
        if song is None:
            return await ctx.send("You must include a song to play.")

        if ctx.voice_client is None:
            return await ctx.send("I must be in a voice channel to play a song.")

        #handle song where song is not a url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send("Searching for song...")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Sorry, I cound not find that song.")
        
            song = result[0]

        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(f"Song added to queue at postion: {queue_len + 1}.")

            else:
                return await ctx.send("Sorry, can only queue up to 10 songs")

        await self.play_song(ctx, song)
        await ctx.send(f"Now playing: {song}")

    @commands.command()
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.send("You forgot to include a song to search for.")

        await ctx.send("Searching for song...")

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Results for '{song}':", description="*You can use these URL's to play an exact song if the one you want isn't the one playing")

        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"Displaying the first {amount} results.")
        await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx): #display current guild's queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There are no songs in queue.")

        embed = discord.Embed(title="Song Queue", describtion="", colour=discord.Color.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            embed.description += f"{i}) {url}\n"

            i += 1

        embed.set_footer(text="Pogchamp!")
        await ctx.send(embed=embed)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not playing anything.")
        
        if ctx.author.voice is None:
            return await ctx.send("You are not connect to voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("You are not connect to the correct voice channel.")

        poll = discord.Embed(title=f"Votre to skip current song (50% Threshold):")
        poll.add_field(name="skip", value=":white_check_mark:")
        poll.add_field(name="stay", value=":no_entry_sign:")
        poll.set_footer(text="voting ends in 15 seconds.")

        poll_msg = await ctx.send(embed=poll) #only returns temp message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") #yes
        await poll_msg.add_reaction(u"\U0001F6AB") #no

        await asyncio.sleep(15) #15 sec wait

        poll_msg = await ctx.channel.fetch_message(poll_id)

        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1
                        reacted.append(user.id)

        skip = False

        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.49: # 50% or higher
                skip = True
                embed = discord.Embed(title="Skip successful", describtion="***Now skipping currently playing song!***")

        if not skip:
            embed = discord.Embed(title="Skip failed", describtion="***Continuing the party with the current song!***")

        embed.set_footer(text="Voting has ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()
            await self.check_queue(ctx)
        
@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready!")

bot.add_cog(Player(bot))
bot.run(TOKEN)

# client = Player()
# client.run(TOKEN)