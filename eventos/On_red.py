from discord.ext import commands
import discord
import logging

# Configuração do logger
logger = logging.getLogger(__name__)

class SyncCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Esse evento é chamado quando o bot está pronto. 
        Ele garante que os comandos do bot sejam sincronizados com o Discord.
        """
        # Remover a mensagem de log "Bot conectado como"
        # logger.info(f"🤖 Bot conectado como {self.bot.user}!")
        # Atualizar todos os documentos para balance ser int64
    
        # Sincronizar os comandos com o Discord
        try:
            await self.bot.tree.sync()
            logger.info("✅ Comandos sincronizados com o Discord.")
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar comandos: {e}")

# Função de configuração da extensão
async def setup(bot):
    await bot.add_cog(SyncCommands(bot))  # Modificado para usar awai
    logger.info("SyncCommands carregado com sucesso.")