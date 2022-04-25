from discord.ext import commands
import discord
import emoji


class ReactionRolesNotSetup(commands.CommandError):
    """Reaction roles are not set up"""
    pass


def is_setup():
    async def wrap_func(ctx):
        data = await ctx.bot.config.find(ctx.guild.id)
        if data is None:
            raise ReactionRolesNotSetup

        if data.get("message_id") is None:
            raise ReactionRolesNotSetup

        return True
    return commands.check(wrap_func)


class Reactions(commands.Cog, name="ReactionsRoles"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        aliases=['rr'], invoke_without_command=True  # not working
    )
    @commands.guild_only()
    async def reactionroles(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="reactionroles")

    @reactionroles.command(name="channel")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_channels=True)
    async def rr_channel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            await ctx.send("Ooooga boooga roles go here now bozo")
        channel = channel or ctx.channel
        try:
            await channel.send("Test", delete_after=0.05)
        except discord.HTTPException:
            await ctx.send("Gib perms pls.")
            return

        nums = ["{}\N{COMBINING ENCLOSING KEYCAP}".format(
            num) for num in range(2, 5)]

        emoteroles = [["💾", "Computer Software"], ["🖥️", "Computer Hardware"], [nums[0], "Second Year"],
                      [nums[1], "Third Year"], [nums[2], "Fourth Year"], ["🎓", "Graduate Student"], ["👷", "On Co-op"]]

        embed = discord.Embed(
            title="Reaction Roles", color=discord.Color.red())
        # reaction_roles = await self.bot.reaction_roles.get_all()
        # for item in reaction_roles:
        #     role = ctx.guild.get_role(item["role"])
        #     desc += f"{item['_id']}: {role.mention}\n"
        desc = "Select your role(s) by reacting \N{BANANA}\n"

        for item in emoteroles:
            desc += f"{item[0]} - {item[1]} \n"

        embed.description = desc

        m = await channel.send(embed=embed)
        for item in emoteroles:
            await m.add_reaction(item[0])

        # await ctx.send("@everyone get yo roles ^")

# add role assignment functionality


def setup(bot):
    bot.add_cog(Reactions(bot))
