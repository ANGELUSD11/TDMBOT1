import discord
from discord.ext import commands
import pytesseract
from PIL import Image
import io
import aiohttp
from utils.constants import Emojis

class OCRCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ocr", description="Extracts text from an attached image")
    async def ocr(self, ctx: commands.Context, image: discord.Attachment = None):
        if not image:
            if ctx.message.attachments:
                image = ctx.message.attachments[0]
            else:
                return await ctx.send(f"{Emojis.WARNING} Please attach an image to extract text from.")

        if not image.content_type or not image.content_type.startswith('image/'):
            return await ctx.send(f"{Emojis.NO} The attached file is not an image.")

        await ctx.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image.url) as response:
                    if response.status != 200:
                        return await ctx.send(f"{Emojis.NO} Failed to download the image.")
                    image_bytes = await response.read()

            img = Image.open(io.BytesIO(image_bytes))
            
            extracted_text = pytesseract.image_to_string(img, lang='spa+eng+por+fra+deu+ita+rus+jpn+chi_sim+ara')
            
            if not extracted_text.strip():
                return await ctx.send(f"{Emojis.WARNING} No readable text could be found in the image.")
                
            if len(extracted_text) <= 1950:
                await ctx.send(f"{Emojis.YES} **Extracted Text:**\n`	ext\n{extracted_text}\n`")
            else:
                await ctx.send(f"{Emojis.YES} **Extracted Text:**")
                for i in range(0, len(extracted_text), 1950):
                    await ctx.send(f"`	ext\n{extracted_text[i:i+1950]}\n`")

        except pytesseract.TesseractNotFoundError:
            await ctx.send(f"{Emojis.NO} OCR engine (Tesseract) is not installed on the host system.")
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An error occurred during OCR processing.")

async def setup(bot):
    await bot.add_cog(OCRCog(bot))
