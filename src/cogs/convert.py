import discord
from discord.ext import commands
from utils.constants import Emojis

class ConvertCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="binary", description="Convert text to binary or vice versa")
    async def binary(self, ctx: commands.Context, mode: str, *, text: str):
        """Mode: 'to_bin' or 'to_text'"""
        mode = mode.lower()
        
        if mode == "to_bin":
            resultado = ' '.join(format(byte, '08b') for byte in text.encode('utf-8'))
            await ctx.send(f"{Emojis.YES} **Text to Binary:**\n`	ext\n{resultado}\n`")
            
        elif mode == "to_text":
            try:
                bin_str = text.replace(' ', '')
                if len(bin_str) % 8 != 0:
                    return await ctx.send(f"{Emojis.WARNING} Invalid binary format. Must be groups of 8 bits.")
                
                blocks = [bin_str[i:i+8] for i in range(0, len(bin_str), 8)]
                bytes_list = [int(b, 2) for b in blocks]
                resultado = bytes(bytes_list).decode('utf-8')
                await ctx.send(f"{Emojis.YES} **Binary to Text:**\n`	ext\n{resultado}\n`")
            except Exception as e:
                await ctx.send(f"{Emojis.NO} Error decoding binary.")
        else:
            await ctx.send(f"{Emojis.WARNING} Invalid mode. Use 	o_bin or 	o_text.")

async def setup(bot):
    await bot.add_cog(ConvertCog(bot))
