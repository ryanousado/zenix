import discord
from discord.ext import commands

class BanAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def ban_all(self, ctx, user_id: int, *, reason=None):
        user_banned = False
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                try:
                    await guild.ban(discord.Object(id=user_id), reason=reason)
                    user_banned = True
                    await ctx.send(f"Usuário com ID {user_id} foi banido de {guild.name}.")
                except discord.Forbidden:
                    await ctx.send(f"Não tenho permissão para banir no servidor {guild.name}.")
                except discord.HTTPException:
                    await ctx.send(f"Falha ao banir no servidor {guild.name}.")
        if not user_banned:
            await ctx.send(f"O usuário com ID {user_id} não foi encontrado em nenhum servidor acessível.")
        else:
            await ctx.send(f"Banimento de usuário com ID {user_id} concluído.")

# Função para adicionar a extensão ao bot
async def setup(bot):
    await bot.add_cog(BanAll(bot))