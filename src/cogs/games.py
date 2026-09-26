import discord
from discord.ext import commands
import random
import asyncio
from utils.constants import EmbedColors, Emojis

class RPSView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.choices = ['Rock', 'Paper', 'Scissors']
        self.bot_choice = random.choice(self.choices)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return False
        return True

    async def resolve_game(self, interaction: discord.Interaction, player_choice: str):
        for item in self.children:
            item.disabled = True

        result_text = ""
        if player_choice == self.bot_choice:
            result_text = "It's a tie! 🤝"
            color = EmbedColors.WARNING
        elif (player_choice == 'Rock' and self.bot_choice == 'Scissors') or \
             (player_choice == 'Paper' and self.bot_choice == 'Rock') or \
             (player_choice == 'Scissors' and self.bot_choice == 'Paper'):
            result_text = "You win! 🎉"
            color = EmbedColors.SUCCESS
        else:
            result_text = "I win! 🤖"
            color = EmbedColors.ERROR

        embed = discord.Embed(
            title="Rock, Paper, Scissors",
            description=f"You chose **{player_choice}**\nI chose **{self.bot_choice}**\n\n**{result_text}**",
            color=color
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.secondary, emoji="🪨")
    async def rock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve_game(interaction, 'Rock')

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.secondary, emoji="📄")
    async def paper_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve_game(interaction, 'Paper')

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.secondary, emoji="✂️")
    async def scissors_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.resolve_game(interaction, 'Scissors')

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            embed = discord.Embed(
                title="Rock, Paper, Scissors",
                description="Game timed out! You didn't make a choice.",
                color=EmbedColors.ERROR
            )
            await self.message.edit(embed=embed, view=self)
        except:
            pass


class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="8ball", description="Ask the magic 8-ball a question")
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes - definitely.",
            "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.",
            "Yes.", "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
            "Don't count on it.", "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful."
        ]
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=EmbedColors.INFO
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(responses), inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="coinflip", description="Flip a coin")
    async def coinflip(self, ctx: commands.Context):
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙"
        embed = discord.Embed(
            title="Coin Flip",
            description=f"{emoji} The coin landed on: **{result}**",
            color=EmbedColors.DEFAULT
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="dice", description="Roll a dice (default 6-sided)")
    async def dice(self, ctx: commands.Context, sides: int = 6):
        if sides < 2:
            await ctx.send(f"{Emojis.NO} The dice must have at least 2 sides!")
            return
        if sides > 1000:
            await ctx.send(f"{Emojis.NO} The maximum number of sides is 1000!")
            return
            
        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"You rolled a d{sides} and got: **{result}**",
            color=EmbedColors.DEFAULT
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rps", description="Play Rock, Paper, Scissors against the bot")
    async def rps(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Rock, Paper, Scissors",
            description="Choose your weapon below! 👇",
            color=EmbedColors.INFO
        )
        view = RPSView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

async def setup(bot):
    await bot.add_cog(GamesCog(bot))