import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import logging
import aiofiles
from datetime import datetime, timedelta

# 🎯 Carregar variáveis de ambiente do arquivo .env
load_dotenv()
TOKEN = os.getenv('TOKEN')
OWNER_IDS = list(map(int, os.getenv('OWNER_IDS', '').split(','))) if os.getenv('OWNER_IDS') else []  # IDs dos donos do bot
SUGGESTION_CHANNEL_ID = int(os.getenv('SUGGESTION_CHANNEL_ID', 0))  # Evita erro se não existir
YOUTUBE_API_KEYS = os.getenv('YOUTUBE_API_KEYS', '').split(',')
GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS', '')
SPREADSHEET_URL = os.getenv('SPREADSHEET_URL', '')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', 0))
DATA_DIR = 'data'
FILENAME_CHANNELS = os.path.join(DATA_DIR, 'channels.json')
FILENAME_SENT_VIDEOS = os.path.join(DATA_DIR, 'sent_videos.json')
CACHE_EXPIRY = timedelta(hours=1)  # Tempo de validade do cache

# 🖊️ Configurar o log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração de intents do bot (habilitar todas)
intents = discord.Intents.all()

# Inicializando o bot com intents
bot = commands.Bot(command_prefix="!", intents=intents)

# 🛡️ Donos do bot
bot.owner_ids = set(OWNER_IDS)

# Caminhos das pastas de comandos e eventos
BASE_DIR = os.path.dirname(__file__)
COMMANDS_DIR = os.path.join(BASE_DIR, 'commands')
EVENTOS_DIR = os.path.join(BASE_DIR, 'eventos')

# Criar diretórios se não existirem
os.makedirs(COMMANDS_DIR, exist_ok=True)
os.makedirs(EVENTOS_DIR, exist_ok=True)

# Função para carregar extensões automaticamente
async def load_extensions():
    """Carrega todas as extensões (Cogs) automaticamente."""
    for dir_path in [COMMANDS_DIR, EVENTOS_DIR]:
        if not os.path.exists(dir_path):
            logger.warning(f"⚠️ A pasta '{dir_path}' não foi encontrada.")
            continue

        for filename in os.listdir(dir_path):
            if filename.endswith('.py'):
                extension = f"{dir_path.split(os.path.sep)[-1]}.{filename[:-3]}"
                try:
                    await bot.load_extension(extension)
                    logger.info(f"✅ Extensão carregada: {filename}")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar extensão '{filename}': {e}")

# 🌟 Atualizar status do bot periodicamente
@tasks.loop(minutes=10)
async def update_status():
    """Atualiza o status do bot a cada 10 minutos."""
    total_servidores = len(bot.guilds)
    total_membros = sum(guild.member_count for guild in bot.guilds)
    status = f"📊 {total_servidores} servidores | 👥 {total_membros} membros"
    await bot.change_presence(activity=discord.Game(name=status))
    logger.info(f"🔄 Status atualizado: {status}")

# 🌟 Evento ao iniciar o bot
@bot.event
async def on_ready():
    """Executado quando o bot está pronto."""
    logger.info(f"🤖 Bot conectado como {bot.user}!")
    if not update_status.is_running():
        update_status.start()

# 🌟 Setup inicial do bot
@bot.event
async def setup_hook():
    """Carrega todas as extensões antes do bot ficar pronto."""
    await load_extensions()

# 🛠️ Iniciar o bot
bot.run(TOKEN)