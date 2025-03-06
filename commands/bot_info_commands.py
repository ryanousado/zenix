import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Obter as URLs do .env
miniatura_url = os.getenv("miniatura")
banner_url = os.getenv("banner")


# Configurações de arquivos e IDs de canais
FILENAME_SUGGESTIONS = os.path.join('data', 'suggestions.json')
FILENAME_ERRORS = os.path.join('data', 'erros_reportados.json')
SUGGESTION_CHANNEL_ID = int(os.getenv('SUGGESTION_CHANNEL_ID', 0))
ERROR_REPORT_CHANNEL_ID = int(os.getenv('ERROR_REPORT_CHANNEL_ID', 0))

class BotInfoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Função para carregar sugestões
    def load_suggestions(self) -> list:
        try:
            with open(FILENAME_SUGGESTIONS, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    # Função para salvar sugestões
    def save_suggestions(self, suggestions: list):
        os.makedirs(os.path.dirname(FILENAME_SUGGESTIONS), exist_ok=True)
        with open(FILENAME_SUGGESTIONS, 'w') as f:
            json.dump(suggestions, f, indent=4)

    # Comando /invite
    @app_commands.command(name="invite", description="Obtenha um link para adicionar o bot ao seu servidor.")
    async def invite(self, interaction: discord.Interaction):
        invite_url = (
            "https://discord.com/oauth2/authorize"
            "?client_id=1308929035295784991&permissions=8"
            "&scope=bot+applications.commands"
        )

        embed = discord.Embed(
            title="🌟 **Convite do Zenix** 🌟",
            description=(
                "Adicione o **Zenix** ao seu servidor e transforme sua experiência no Discord!"
            ),
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=miniatura_url)
        embed.set_footer(
            text="Zenix • A energia que você precisa para impulsionar sua experiência!",
            icon_url=miniatura_url
        )

        # Botão de convite
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="➕ Me adicione ao seu servidor",
            url=invite_url,
            style=discord.ButtonStyle.link
        ))

        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    # Comando /info
    @app_commands.command(name="info", description="Obtenha informações detalhadas sobre o bot.")
    async def info(self, interaction: discord.Interaction):
        total_guilds = len(self.bot.guilds)
        total_members = sum(guild.member_count for guild in self.bot.guilds)

        embed = discord.Embed(
            title="🤖 **Informações do Zenix**",
            description="Tudo o que você precisa saber sobre este incrível bot!",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="👑 **Criadores**",
            value=(
                "🛠️ **Ryan**: Criador principal do bot.\n"
                "🛠️ **Juliana**: Co-programadora dedicada.\n"
                "🛠️ **Haruzx**: Co-programadora dedicada."
            ),
            inline=False
        )
        embed.add_field(
            name="🌐 **Servidor Oficial**",
            value="[🔗 Clique aqui para entrar no servidor oficial](https://discord.gg/T4c3eNamVR)\n📢 Participe da nossa comunidade!",
            inline=False
        )
        embed.add_field(
            name="📊 **Estatísticas**",
            value=(
                f"🏢 **Servidores:** Estamos em `{total_guilds}` servidores.\n"
                f"👥 **Membros:** Já temos mais de `{total_members}` membros!"
            ),
            inline=False
        )
        embed.add_field(
            name="✨ **Funcionalidades do Bot**",
            value=(
                "💡 **Gestão:** Gerencie seu servidor de forma mais eficiente com comandos automáticos.\n"
                "🎉 **Interação:** Torne a comunidade mais engajada com comandos interativos.\n"
                "🔒 **Segurança:** Recursos seguros e atualizados para proteger seu servidor.\n"
                "📢 **Anúncios:** Personalize anúncios e notificações com praticidade."
            ),
            inline=False
        )
        embed.add_field(
            name="📌 **Notas Adicionais**",
            value=(
                "💻 Este bot está em constante evolução, recebendo atualizações frequentes.\n"
                "📩 Caso encontre um problema, utilize o comando `/reportar_erro`.\n"
                "📩 Caso tenha alguma sugestão, utilize o comando `/suggest`."
            ),
            inline=False
        )
        embed.set_thumbnail(url=miniatura_url)
        embed.set_footer(
            text="Obrigado por usar o Zenix! 🚀",
            icon_url=miniatura_url
        )
        embed.set_image(url=banner_url)

        # Botões interativos
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="🌐 Entre no meu servidor",
            url="https://discord.gg/Nm7FmNnSyA",
            style=discord.ButtonStyle.link
        ))
        view.add_item(discord.ui.Button(
            label="➕ Me adicione ao seu servidor",
            url="https://discord.com/oauth2/authorize?client_id=1308929035295784991&permissions=8&scope=bot+applications.commands",
            style=discord.ButtonStyle.link
        ))
        view.add_item(discord.ui.Button(
            label="🔗 Visite meu site",
            url="https://ofc-zenix.squareweb.app/",
            style=discord.ButtonStyle.link
        ))

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # Comando /suggest
    @app_commands.command(name="suggest", description="Envie uma sugestão ou feedback.")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        suggestions = self.load_suggestions()
        suggestions.append({"user": interaction.user.name, "suggestion": suggestion})
        self.save_suggestions(suggestions)

        suggestion_channel = self.bot.get_channel(SUGGESTION_CHANNEL_ID)
        if suggestion_channel:
            embed = discord.Embed(
                title="📢 **Nova Sugestão**",
                description=suggestion,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Enviado por: {interaction.user.name}")
            await suggestion_channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Obrigado pela sua sugestão! Ela foi enviada com sucesso.",
            ephemeral=True
        )

    # Comando /reportar_erro
    @app_commands.command(name="reportar_erro", description="Reporte um erro ou problema encontrado no bot.")
    async def reportar_erro(self, interaction: discord.Interaction, erro: str):
        try:
            with open(FILENAME_ERRORS, 'r') as f:
                erros_reportados = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            erros_reportados = []

        erros_reportados.append({"user": interaction.user.name, "erro": erro})
        os.makedirs(os.path.dirname(FILENAME_ERRORS), exist_ok=True)
        with open(FILENAME_ERRORS, 'w') as f:
            json.dump(erros_reportados, f, indent=4)

        erro_channel = self.bot.get_channel(ERROR_REPORT_CHANNEL_ID)
        if erro_channel:
            embed = discord.Embed(
                title="⚠️ **Novo Relatório de Erro**",
                description=erro,
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Enviado por: {interaction.user.name}")
            await erro_channel.send(embed=embed)

        await interaction.response.send_message(
            "✅ Obrigado por reportar o erro! Nossa equipe analisará o problema o mais rápido possível.",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(BotInfoCommands(bot))