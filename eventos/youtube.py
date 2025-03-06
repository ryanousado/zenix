import discord
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import aiofiles
from datetime import datetime, timedelta
import logging

# 🔧 Carregar variáveis de ambiente
load_dotenv()
YOUTUBE_API_KEYS = os.getenv('YOUTUBE_API_KEYS').split(',')
DATA_DIR = 'data'
FILENAME_CHANNELS = os.path.join(DATA_DIR, 'channels.json')
FILENAME_SENT_VIDEOS = os.path.join(DATA_DIR, 'sent_videos.json')
CACHE_EXPIRY = timedelta(hours=1)  # Tempo de validade do cache

# 🖊️ Configuração do log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache para armazenar os resultados da API temporariamente
video_cache = {}

# 📌 Inicializar clientes do YouTube com várias chaves de API
youtube_clients = [build('youtube', 'v3', developerKey=key) for key in YOUTUBE_API_KEYS]
current_client_index = 0


def get_next_youtube_client():
    """Alterna entre os clientes da API do YouTube."""
    global current_client_index
    client = youtube_clients[current_client_index]
    current_client_index = (current_client_index + 1) % len(youtube_clients)
    return client


class Post(commands.Cog):
    """Cog responsável por postar vídeos novos do YouTube."""

    def __init__(self, bot):
        self.bot = bot
        self.channels = {}
        self.sent_videos = []
        self.bot.loop.create_task(self.load_data())
        self.check_new_videos.start()  # Inicia a verificação automática

    async def load_data(self):
        """Carrega os dados de canais e vídeos já enviados."""
        self.channels = await self.load_channels()
        self.sent_videos = await self.load_sent_videos()

    @staticmethod
    async def load_channels():
        """Carrega a lista de canais do YouTube monitorados."""
        try:
            async with aiofiles.open(FILENAME_CHANNELS, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    async def save_channels(channels):
        """Salva a lista de canais do YouTube monitorados."""
        async with aiofiles.open(FILENAME_CHANNELS, 'w') as f:
            await f.write(json.dumps(channels))

    @staticmethod
    async def load_sent_videos():
        """Carrega a lista de vídeos já enviados."""
        try:
            async with aiofiles.open(FILENAME_SENT_VIDEOS, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    async def save_sent_videos(sent_videos):
        """Salva a lista de vídeos já enviados."""
        async with aiofiles.open(FILENAME_SENT_VIDEOS, 'w') as f:
            await f.write(json.dumps(sent_videos))

    @tasks.loop(minutes=60)
    async def check_new_videos(self):
        """Verifica e envia novos vídeos para os canais do Discord."""
        logger.info("🔍 Iniciando verificação de novos vídeos...")

        for guild_id, guild_channels in self.channels.items():
            for youtube_channel_id, discord_channel_id in guild_channels.items():
                if not discord_channel_id:
                    continue

                logger.info(f"📺 Verificando canal: {youtube_channel_id}")

                try:
                    now = datetime.now()

                    # Verificar se o vídeo já está no cache
                    if (youtube_channel_id in video_cache and 
                        now - video_cache[youtube_channel_id]['timestamp'] < CACHE_EXPIRY):
                        response = video_cache[youtube_channel_id]['data']
                    else:
                        youtube = get_next_youtube_client()
                        request = youtube.search().list(
                            part='snippet',
                            channelId=youtube_channel_id,
                            maxResults=1,
                            order='date'
                        )
                        response = request.execute()
                        video_cache[youtube_channel_id] = {
                            'timestamp': now,
                            'data': response
                        }

                    # Se houver vídeo novo, enviar para o Discord
                    if 'items' in response and response['items']:
                        video = response['items'][0]
                        video_id = video['id'].get('videoId')

                        if video_id and video_id not in self.sent_videos:
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            discord_channel = self.bot.get_channel(int(discord_channel_id))

                            if discord_channel:
                                logger.info(f"📤 Enviando novo vídeo: {video_url}")
                                message = f"🎥 **Novo vídeo no ar!** Assista agora: {video_url}"
                                await discord_channel.send(message)
                                self.sent_videos.append(video_id)
                                await self.save_sent_videos(self.sent_videos)
                        else:
                            logger.info(f"✅ Vídeo já enviado: {video_id}")
                    else:
                        logger.info(f"🚫 Nenhum vídeo encontrado para {youtube_channel_id}")

                except Exception as e:
                    logger.error(f"❌ Erro ao verificar vídeos: {e}")

    @check_new_videos.before_loop
    async def before_check_new_videos(self):
        """Garante que o bot está pronto antes de iniciar a verificação."""
        await self.bot.wait_until_ready()


# 🔧 Configuração do Cog
async def setup(bot):
    await bot.add_cog(Post(bot))