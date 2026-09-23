import discord
from discord.ext import commands
import urllib.parse
import aiohttp
import io
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from utils.constants import EmbedColors, Emojis

class ImagineCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="imagine", description="Generate an AI image based on a prompt")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def imagine(self, ctx: commands.Context, *, prompt: str = None):
        if not prompt:
            return await ctx.send(f"{Emojis.WARNING} **Incorrect usage.** Format: `>imagine [description]`\nExample: `>imagine a cybernetic cat on mars`")
            
        await ctx.defer()
        
        # --- SAFETY BARRIER (Gemini AI Scanner) ---
        try:
            import os
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
                safety_prompt = f"Analyze this image generation prompt. Respond with strictly 'SAFE' or 'UNSAFE'. Consider it UNSAFE if it contains porn, nudity, sexual situations, gore, extreme violence, self-harm, or highly offensive/hateful words. Prompt: {prompt}"
                safety_response = await client.aio.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=safety_prompt
                )
                if 'UNSAFE' in safety_response.text.upper():
                    return await ctx.send(f"{Emojis.NO} **Safety Block:** Your prompt violates the safety guidelines (NSFW, gore, or offensive content). Request denied.")
        except Exception as e:
            print(f"Safety Scanner Error: {e}")
            # If the scanner fails, we still continue but rely on Pollinations safe mode
        # ------------------------------------------

        # Pollinations is a free, no-API-key image generation service
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&safe=true"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        file = discord.File(io.BytesIO(image_data), filename="imagine.png")
                        
                        embed = discord.Embed(title=f"🎨 Imagine: {prompt}", color=EmbedColors.SUCCESS)
                        embed.set_image(url="attachment://imagine.png")
                        embed.set_footer(text="Generated via Pollinations AI")
                        
                        await ctx.send(embed=embed, file=file)
                    else:
                        await ctx.send(f"{Emojis.NO} Failed to generate the image. API might be overloaded.")
        except Exception as e:
            await ctx.send(f"{Emojis.NO} An error occurred while generating the image.")
            print(f"Imagine Error: {e}")

    @commands.hybrid_command(name="edit", description="Apply NotSoBot-style filters/AI modifications to an image")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def edit(self, ctx: commands.Context, style: str = "deepfry", image: discord.Attachment = None):
        """Styles: deepfry, invert, blur, grayscale, edge"""
        image_url = None
        if image:
            image_url = image.url
        elif ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
        elif ctx.message.reference and ctx.message.reference.resolved:
            resolved = ctx.message.reference.resolved
            if hasattr(resolved, 'attachments') and resolved.attachments:
                image_url = resolved.attachments[0].url
            elif hasattr(resolved, 'embeds') and resolved.embeds and resolved.embeds[0].image:
                image_url = resolved.embeds[0].image.url
        
        if not image_url:
            # Fallback to fetch message if resolved is None
            if ctx.message.reference and ctx.message.reference.message_id:
                try:
                    resolved = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                    if resolved.attachments:
                        image_url = resolved.attachments[0].url
                    elif resolved.embeds and resolved.embeds[0].image:
                        image_url = resolved.embeds[0].image.url
                except Exception:
                    pass

        if not image_url:
            return await ctx.send(f"{Emojis.WARNING} Please attach an image or reply to a message containing an image to edit.")

        await ctx.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        return await ctx.send(f"{Emojis.NO} Failed to download the image.")
                    image_bytes = await response.read()

            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            style = style.lower()
            
            if style == "invert":
                img = ImageOps.invert(img)
            elif style == "grayscale":
                img = ImageOps.grayscale(img)
            elif style == "blur":
                img = img.filter(ImageFilter.GaussianBlur(radius=5))
            elif style == "edge":
                img = img.filter(ImageFilter.FIND_EDGES)
            elif style == "deepfry":
                # Deepfry effect simulation
                img = img.filter(ImageFilter.SHARPEN)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(3.0)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2.5)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(5.0)
            else:
                return await ctx.send(f"{Emojis.WARNING} Unknown style. Available styles: deepfry, invert, blur, grayscale, edge")

            output_buffer = io.BytesIO()
            img.save(output_buffer, format="PNG")
            output_buffer.seek(0)
            
            file = discord.File(output_buffer, filename=f"{style}_edit.png")
            embed = discord.Embed(title=f"🖼️ Edit: {style}", color=EmbedColors.SUCCESS)
            embed.set_image(url=f"attachment://{style}_edit.png")
            
            await ctx.send(embed=embed, file=file)

        except Exception as e:
            await ctx.send(f"{Emojis.NO} An error occurred while editing the image.")
            print(f"Edit Error: {e}")

async def setup(bot):
    await bot.add_cog(ImagineCog(bot))
