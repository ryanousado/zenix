import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

# Função para calcular o timestamp
def calculate_timestamp(seconds):
    target_time = datetime.utcnow() + timedelta(seconds=seconds)
    return int(target_time.timestamp())

# Função de contagem regressiva
async def countdown(interaction: discord.Interaction, message: str, countdown_time: int):
    # Calcula o timestamp inicial
    timestamp = calculate_timestamp(countdown_time)

    # Cria o embed inicial
    embed = discord.Embed(
        title="⏳ Contagem Regressiva",
        description=f"**Mensagem:** {message}\n\n**Termina em:** <t:{timestamp}:R>",
        color=discord.Color.blue()
    )

    # Envia a mensagem inicial com embed
    await interaction.response.send_message(embed=embed)

    # Aguarda o tempo da contagem regressiva
    await asyncio.sleep(countdown_time)

    # Mensagem final
    embed = discord.Embed(
        title="🎉 Contagem Finalizada!",
        description=f"**Mensagem:** {message}\n\nA contagem foi concluída!",
        color=discord.Color.green()
    )
    # Edita a mensagem original com o novo embed
    await interaction.edit_original_response(embed=embed)

# Definindo o Cog para o comando 'timer'
class TimerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Comando de barra para iniciar o timer
    @app_commands.command(name="timer", description="Inicia um timer para eventos com contagem regressiva")
    async def timer(self, interaction: discord.Interaction, message: str, hours: int = 0, minutes: int = 0):
        # Calcula o tempo total em segundos
        countdown_time = (hours * 3600) + (minutes * 60)

        if countdown_time <= 0:
            await interaction.response.send_message("❌ O tempo deve ser maior que zero.", ephemeral=True)
            return

        # Inicia a contagem regressiva
        await countdown(interaction, message, countdown_time)

# Função setup para carregar o Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(TimerCog(bot))
