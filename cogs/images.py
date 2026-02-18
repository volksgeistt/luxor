import discord
from discord.ext import commands
from typing import Optional, Tuple
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import io
import aiohttp
import random
from io import BytesIO
import numpy as np
import asyncio
from config import config

class ImageManipulation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    async def download_image(self, url: str) -> Optional[Image.Image]:
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
                return Image.open(BytesIO(data))
        except Exception:
            return None

    async def send_image(self, ctx, image: Image.Image, format: str = 'PNG'):
        buffer = BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return await ctx.send(file=discord.File(buffer, f'result.{format.lower()}'))

    async def get_image_url(self, ctx, url: Optional[str] = None) -> Optional[str]:
        if url:
            return url
        if ctx.message.attachments:
            return ctx.message.attachments[0].url
        if ctx.message.reference:
            replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if replied_msg.attachments:
                return replied_msg.attachments[0].url
        return None

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def image(self, ctx):
        await ctx.send(embed=discord.Embed(title=f"Image Manipulation",description=f"`image`, `image blur`, `image deepfry`, `image meme`, `image swirl`, `image spread`, `image grayscale`, `image invert`\n{config.ques_emoji} Example: `image meme [url] [text]`",color=config.hex))

    @image.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    async def blur(self, ctx, url: Optional[str] = None, strength: int = 5):
        image_url = await self.get_image_url(ctx, url)
        if not image_url:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : please provide an image or image url.", color=config.hex))
        
        async with ctx.typing():
            img = await self.download_image(image_url)
            if not img:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : failed to get the image", color=config.hex))
            
            blurred = img.filter(ImageFilter.GaussianBlur(radius=strength))
            await self.send_image(ctx, blurred)

    @image.command()
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def deepfry(self, ctx, url: Optional[str] = None):
        image_url = await self.get_image_url(ctx, url)
        if not image_url:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : please provide an image or image url.", color=config.hex))
        
        async with ctx.typing():
            img = await self.download_image(image_url)
            if not img:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : failed to get the image", color=config.hex))
            
            img = ImageEnhance.Contrast(img).enhance(2)
            img = ImageEnhance.Sharpness(img).enhance(100)
            img = ImageEnhance.Color(img).enhance(2)
            
            await self.send_image(ctx, img)

    @image.command()
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def meme(self, ctx, url: Optional[str] = None, *, text: str):
        """Create a top and bottom text meme"""
        image_url = await self.get_image_url(ctx, url)
        if not image_url:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : please provide an image or image url.", color=config.hex))
        
        text_parts = text.split('|', 1)
        top_text = text_parts[0].strip().upper()
        bottom_text = text_parts[1].strip().upper() if len(text_parts) > 1 else ""
        
        async with ctx.typing():
            img = await self.download_image(image_url)
            if not img:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : failed to get the image", color=config.hex))
            
            draw = ImageDraw.Draw(img)
            
            font_size = int(img.width / 10)
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            def draw_text_with_outline(text, position):
                bbox = font.getbbox(text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (img.width - text_width) // 2
                
                for offset in [(1,1), (-1,-1), (1,-1), (-1,1)]:
                    draw.text((x + offset[0], position[1] + offset[1]), 
                            text, font=font, fill='black')
                draw.text((x, position[1]), text, font=font, fill='white')
                
                return text_height
            
            if top_text:
                text_height = draw_text_with_outline(top_text, (0, 10))
            
            if bottom_text:
                text_height = draw_text_with_outline(bottom_text, (0, img.height - text_height - 20))
            
            await self.send_image(ctx, img)

    @image.command()
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def swirl(self, ctx, url: Optional[str] = None, strength: int = 5):
        image_url = await self.get_image_url(ctx, url)
        if not image_url:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : please provide an image or image url.", color=config.hex))
        
        async with ctx.typing():
            img = await self.download_image(image_url)
            if not img:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : failed to get the image", color=config.hex))
            
            img_array = np.array(img)
            height, width = img_array.shape[:2]
            center_x, center_y = width // 2, height // 2
            
            y, x = np.ogrid[:height, :width]
            distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            angle = strength * np.exp(-distance / (width/50))
            
            x_new = (x - center_x) * np.cos(angle) - (y - center_y) * np.sin(angle) + center_x
            y_new = (x - center_x) * np.sin(angle) + (y - center_y) * np.cos(angle) + center_y
            
            x_new = np.clip(x_new, 0, width-1).astype(np.float32)
            y_new = np.clip(y_new, 0, height-1).astype(np.float32)
            
            x0 = np.floor(x_new).astype(np.int32)
            x1 = x0 + 1
            y0 = np.floor(y_new).astype(np.int32)
            y1 = y0 + 1
            
            x0 = np.clip(x0, 0, width-1)
            x1 = np.clip(x1, 0, width-1)
            y0 = np.clip(y0, 0, height-1)
            y1 = np.clip(y1, 0, height-1)
            
            wa = (x1-x_new) * (y1-y_new)
            wb = (x1-x_new) * (y_new-y0)
            wc = (x_new-x0) * (y1-y_new)
            wd = (x_new-x0) * (y_new-y0)
            
            output = np.zeros_like(img_array)
            for i in range(img_array.shape[2]):
                channel = img_array[:,:,i]
                output[:,:,i] = (wa * channel[y0, x0] + 
                                wb * channel[y1, x0] + 
                                wc * channel[y0, x1] + 
                                wd * channel[y1, x1])
            
            swirled = Image.fromarray(output.astype(np.uint8))
            await self.send_image(ctx, swirled)

    @image.command()
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def spread(self, ctx, url: Optional[str] = None, strength: int = 5):
        image_url = await self.get_image_url(ctx, url)
        if not image_url:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : please provide an image or image url.", color=config.hex))
        
        async with ctx.typing():
            img = await self.download_image(image_url)
            if not img:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : failed to get the image", color=config.hex))
            
            img_array = np.array(img)
            height, width = img_array.shape[:2]
            result = np.zeros_like(img_array)
            
            for y in range(height):
                for x in range(width):
                    rand_x = x + random.randint(-strength, strength)
                    rand_y = y + random.randint(-strength, strength)
                    
                    rand_x = max(0, min(rand_x, width-1))
                    rand_y = max(0, min(rand_y, height-1))
                    
                    result[y, x] = img_array[rand_y, rand_x]
            
            spread_img = Image.fromarray(result)
            await self.send_image(ctx, spread_img)

    @image.command()
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def grayscale(self, ctx, url: Optional[str] = None):
        image_url = await self.get_image_url(ctx, url)
        if not image_url:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : please provide an image or image url.", color=config.hex))
        
        async with ctx.typing():
            img = await self.download_image(image_url)
            if not img:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : failed to get the image", color=config.hex))
            
            grayscale = ImageOps.grayscale(img)
            await self.send_image(ctx, grayscale)

    @image.command()
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def invert(self, ctx, url: Optional[str] = None):
        image_url = await self.get_image_url(ctx, url)
        if not image_url:
            return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : please provide an image or image url.", color=config.hex))
        
        async with ctx.typing():
            img = await self.download_image(image_url)
            if not img:
                return await ctx.send(embed=discord.Embed(description=f"{config.error_emoji} {ctx.author.mention} : failed to get the image", color=config.hex))
            
            inverted = ImageOps.invert(img.convert('RGB'))
            await self.send_image(ctx, inverted)

async def setup(bot):
    await bot.add_cog(ImageManipulation(bot))