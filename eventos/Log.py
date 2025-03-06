import discord
from discord.ext import commands
from discord import ui, ButtonStyle
import os
from dotenv import load_dotenv

# Carregar o arquivo .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))  # ID do canal de logs
FEEDBACK_CHANNEL_ID = int(os.getenv("FEEDBACK_CHANNEL_ID"))  # ID do canal de feedback

class FeedbackModal(ui.Modal, title="Deixe seu feedback"):
    def __init__(self, feedback_view):
        super().__init__()
        self.feedback_view = feedback_view  # Armazena a referência da view

    feedback = ui.TextInput(label="Seu feedback", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        self.feedback_view.feedback_text = self.feedback.value
        await interaction.response.send_message("✅ Feedback salvo!", ephemeral=True)

class FeedbackView(ui.View):
    def __init__(self, guild_name: str, owner: discord.User):
        super().__init__(timeout=300)
        self.rating = None
        self.feedback_text = None
        self.guild_name = guild_name
        self.owner = owner

    async def disable_all_buttons(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

    async def send_feedback(self, interaction: discord.Interaction):
        feedback_channel = interaction.client.get_channel(FEEDBACK_CHANNEL_ID)
        if not feedback_channel:
            await interaction.response.send_message("Canal de feedback não encontrado.", ephemeral=True)
            return
        
        embed = discord.Embed(title="📢 Novo Feedback Recebido", color=discord.Color.blue())
        embed.add_field(name="🏷️ Servidor", value=self.guild_name, inline=False)
        embed.add_field(name="👑 Dono", value=f"{self.owner} ({self.owner.id})", inline=False)
        embed.add_field(name="⭐ Avaliação", value=f"{self.rating if self.rating is not None else 'Nenhuma'} estrelas", inline=False)
        embed.add_field(name="📝 Feedback", value=self.feedback_text if self.feedback_text else "Nenhum comentário", inline=False)

        await feedback_channel.send(embed=embed)
        await interaction.response.send_message("✅ Feedback enviado com sucesso!", ephemeral=True)
        await self.disable_all_buttons(interaction)

    @ui.button(label="0⭐", style=ButtonStyle.green)
    async def star_0(self, interaction: discord.Interaction, button: ui.Button):
        self.rating = 0
        await interaction.response.send_message("Você escolheu 0 estrelas.", ephemeral=True)

    @ui.button(label="1⭐", style=ButtonStyle.green)
    async def star_1(self, interaction: discord.Interaction, button: ui.Button):
        self.rating = 1
        await interaction.response.send_message("Você escolheu 1 estrela.", ephemeral=True)

    @ui.button(label="2⭐", style=ButtonStyle.green)
    async def star_2(self, interaction: discord.Interaction, button: ui.Button):
        self.rating = 2
        await interaction.response.send_message("Você escolheu 2 estrelas.", ephemeral=True)

    @ui.button(label="3⭐", style=ButtonStyle.green)
    async def star_3(self, interaction: discord.Interaction, button: ui.Button):
        self.rating = 3
        await interaction.response.send_message("Você escolheu 3 estrelas.", ephemeral=True)

    @ui.button(label="4⭐", style=ButtonStyle.green)
    async def star_4(self, interaction: discord.Interaction, button: ui.Button):
        self.rating = 4
        await interaction.response.send_message("Você escolheu 4 estrelas.", ephemeral=True)

    @ui.button(label="5⭐", style=ButtonStyle.green)
    async def star_5(self, interaction: discord.Interaction, button: ui.Button):
        self.rating = 5
        await interaction.response.send_message("Você escolheu 5 estrelas.", ephemeral=True)

    @ui.button(label="📝 Escrever Feedback", style=ButtonStyle.primary)
    async def write_feedback(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(FeedbackModal(self))  # Passa a view para o modal

    @ui.button(label="🚀 Enviar", style=ButtonStyle.danger)
    async def send_button(self, interaction: discord.Interaction, button: ui.Button):
        if self.rating is None and not self.feedback_text:
            await interaction.response.send_message("❌ Você precisa avaliar ou escrever um feedback antes de enviar!", ephemeral=True)
            return
        
        await self.send_feedback(interaction)

async def send_feedback_request(owner: discord.User, guild_name: str):
    try:
        embed = discord.Embed(
            title="📢 Feedback sobre o bot",
            description="O que achou do bot em seu servidor?\nEscolha uma nota de 0 a 5 estrelas ou escreva um feedback.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Seu feedback nos ajuda a melhorar!")

        view = FeedbackView(guild_name, owner)
        await owner.send(embed=embed, view=view)
    except discord.Forbidden:
        print(f"Não foi possível enviar DM para {owner}.")

class LogEntrei(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)

        # Tentar pegar um canal disponível para criar o convite
        invite_channel = None
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).create_instant_invite:
                invite_channel = channel
                break

        invite_link = None
        if invite_channel:
            invite = await invite_channel.create_invite(max_age=0, max_uses=0, reason="Convite gerado ao bot entrar no servidor")
            invite_link = invite.url

        embed = discord.Embed(
            title="🚀 Fui adicionado a um novo servidor!",
            color=discord.Color.blue(),  # Cor azul para dar destaque
        )
        embed.add_field(name="🏷️ Nome do Servidor", value=guild.name, inline=False)
        embed.add_field(name="🆔 ID do Servidor", value=guild.id, inline=True)
        embed.add_field(name="👑 Dono do Servidor", value=f"{guild.owner} ({guild.owner_id})", inline=True)
        embed.add_field(name="📝 Descrição", value=guild.description or "Sem descrição disponível", inline=False)
        embed.add_field(name="👥 Membros", value=f"{guild.member_count} membros", inline=True)
        embed.add_field(name="🔗 Link do Convite", value=invite_link or "Não foi possível gerar o link", inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(
            text=f"Adicionado em {discord.utils.format_dt(discord.utils.utcnow(), style='F')}",
            icon_url=self.bot.user.avatar.url  # Adiciona o avatar do bot no rodapé
        )

        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print("Canal de logs não encontrado.")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
 
        await send_feedback_request(guild.owner, guild.name)

        embed = discord.Embed(
            title="Saí de um servidor!",
            color=discord.Color.red(),
        )
        embed.add_field(name="Nome do Servidor", value=guild.name, inline=False)
        embed.add_field(name="ID do Servidor", value=guild.id, inline=False)
        embed.add_field(name="Dono do Servidor", value=f"{guild.owner} ({guild.owner_id})", inline=False)
        embed.add_field(name="Quantidade de Membros na Saída", value=guild.member_count, inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(text=f"Removido em {discord.utils.format_dt(discord.utils.utcnow(), style='F')}")

        if log_channel:
            await log_channel.send(embed=embed)
        else:
            print("Canal de logs não encontrado.")

async def setup(bot):
    await bot.add_cog(LogEntrei(bot))