import discord
from discord.ext import commands
from discord import app_commands
import random
from sympy import sympify, SympifyError


class ComandosComunidade2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ### Comandos Slash Relacionados a Usuários ###
    @app_commands.command(name="nickname", description="📝 Altera o apelido de um usuário.")
    @app_commands.describe(membro="O membro para alterar o apelido", novo_apelido="O novo apelido do membro")
    async def apelido(self, interaction: discord.Interaction, membro: discord.Member, novo_apelido: str):
        await membro.edit(nick=novo_apelido)
        await interaction.response.send_message(
            f"✅ O apelido de {membro.display_name} foi alterado para **{novo_apelido}**!"
        )

    @app_commands.command(name="roles", description="🎭 Lista os cargos de um usuário.")
    @app_commands.describe(membro="O membro para listar os cargos (opcional)")
    async def cargos(self, interaction: discord.Interaction, membro: discord.Member = None):
        membro = membro or interaction.user
        roles = [role.mention for role in membro.roles if role.name != "@everyone"]
        lista_cargos = ', '.join(roles) if roles else 'Nenhum'

        embed = discord.Embed(
            title=f"🎭 Cargos de {membro.display_name}",
            description=lista_cargos,
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=membro.display_avatar.url)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    ### Comandos Slash Relacionados ao Servidor ###
    @app_commands.command(name="serverbanner", description="🏞️ Exibe o banner do servidor (se disponível).")
    async def server_banner(self, interaction: discord.Interaction):
        if interaction.guild.banner:
            embed = discord.Embed(
                title=f"🏞️ Banner do Servidor: {interaction.guild.name}",
                color=discord.Color.random()
            )
            embed.set_image(url=interaction.guild.banner.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Este servidor não possui um banner configurado!")

    @app_commands.command(name="emojilist", description="😀 Lista todos os emojis disponíveis no servidor.")
    async def listaemojis(self, interaction: discord.Interaction):
        emojis_normais = [str(emoji) for emoji in interaction.guild.emojis if not emoji.animated]
        emojis_animados = [str(emoji) for emoji in interaction.guild.emojis if emoji.animated]

        if not emojis_normais and not emojis_animados:
            await interaction.response.send_message("❌ Nenhum emoji disponível no servidor.")
            return

        embed_normais = discord.Embed(
            title=f"😀 Emojis Normais ({len(emojis_normais)} emojis)",
            description=", ".join(emojis_normais),
            color=discord.Color.random()
        )
        embed_animados = discord.Embed(
            title=f"🔄 Emojis Animados ({len(emojis_animados)} emojis)",
            description=", ".join(emojis_animados),
            color=discord.Color.random()
        )

        await interaction.response.send_message(embeds=[embed_normais, embed_animados])

    @app_commands.command(name="servericon", description="🌟 Exibe o ícone do servidor atual.")
    async def icone(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🌟 Ícone do Servidor: {interaction.guild.name}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=interaction.guild.icon.url if interaction.guild.icon else "")
        await interaction.response.send_message(embed=embed)

    ### Comandos Slash de Utilidade ###

    @app_commands.command(name="roleinfo", description="ℹ️ Mostra informações sobre um cargo específico.")
    @app_commands.describe(cargo="O cargo para exibir informações")
    async def roleinfo(self, interaction: discord.Interaction, cargo: discord.Role):
        embed = discord.Embed(
            title=f"ℹ️ Informações do Cargo: {cargo.name}",
            color=cargo.color
        )
        embed.add_field(name="🆔 ID", value=cargo.id, inline=False)
        embed.add_field(name="👥 Membros", value=len(cargo.members), inline=False)
        embed.add_field(name="📅 Criado em", value=cargo.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
        embed.add_field(name="🔒 Permissões", value=", ".join([perm[0].replace("_", " ").title() for perm in cargo.permissions if perm[1]]) or "Nenhuma", inline=False)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="channelinfo", description="ℹ️ Mostra informações sobre um canal específico.")
    @app_commands.describe(canal="O canal para exibir informações")
    async def channelinfo(self, interaction: discord.Interaction, canal: discord.TextChannel):
        embed = discord.Embed(
            title=f"ℹ️ Informações do Canal: {canal.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="🆔 ID", value=canal.id, inline=False)
        embed.add_field(name="📅 Criado em", value=canal.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
        embed.add_field(name="💬 Tópico", value=canal.topic or "Sem tópico", inline=False)
        embed.add_field(name="🔒 Permissões", value=f"Visível para {len(canal.members)} membros", inline=False)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="invite_server", description="🔗 Gera um link de convite para o servidor.")
    async def invite(self, interaction: discord.Interaction):
        if not interaction.channel.permissions_for(interaction.guild.me).create_instant_invite:
            await interaction.response.send_message("❌ Não tenho permissão para criar convites neste canal.", ephemeral=True)
            return

        invite = await interaction.channel.create_invite(max_age=0, max_uses=0, unique=False)
        await interaction.response.send_message(f"🔗 **Convite para o servidor:** {invite}")
  
    @app_commands.command(name="calculator", description="🧮 Realiza cálculos simples.")
    @app_commands.describe(expressao="A expressão matemática a ser calculada")
    async def calculadora(self, interaction: discord.Interaction, expressao: str):
        try:
            resultado = sympify(expressao.replace(" ", ""))
            await interaction.response.send_message(f"🧮 Resultado: **{resultado}**")
        except SympifyError:
            await interaction.response.send_message("❌ Não consegui entender a expressão matemática. Tente novamente.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Ocorreu um erro: {str(e)}")


# Setup da Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(ComandosComunidade2(bot))