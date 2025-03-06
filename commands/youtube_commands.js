
import discord
from discord.ext import commands
from discord import app_commands
from googleapiclient.discovery import build
import json
import re
import os

# Diretório de dados
DATA_DIR = 'data'
FILENAME_CHANNELS = os.path.join(DATA_DIR, 'channels.json')

# Verificar se o diretório existe, se não, criá-lo
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class YouTubeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.youtube_clients = self.init_youtube_clients()
        self.current_client_index = 0

    def init_youtube_clients(self):
        """Inicializa os clientes do YouTube com múltiplas chaves de API."""
        api_keys = os.getenv('YOUTUBE_API_KEYS', '').split(',')
        return [build('youtube', 'v3', developerKey=key) for key in api_keys if key]

    def get_next_youtube_client(self):
        """Alterna entre os clientes do YouTube para distribuir as requisições."""
        if not self.youtube_clients:
            raise RuntimeError("Nenhuma chave de API do YouTube configurada.")
        client = self.youtube_clients[self.current_client_index]
        self.current_client_index = (self.current_client_index + 1) % len(self.youtube_clients)
        return client

    def load_channels(self):
        """Carrega os dados de canais do arquivo JSON."""
        try:
            with open(FILENAME_CHANNELS, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            # Recria o arquivo se houver erro de leitura
            with open(FILENAME_CHANNELS, 'w') as f:
                json.dump({}, f)
            return {}

    def save_channels(self, channels):
        """Salva os dados de canais no arquivo JSON de forma segura."""
        temp_filename = f"{FILENAME_CHANNELS}.tmp"
        with open(temp_filename, 'w') as temp_file:
            json.dump(channels, temp_file, indent=4)
        os.replace(temp_filename, FILENAME_CHANNELS)

    def extract_channel_id(self, youtube_url):
        """Extrai o ID de um canal do YouTube a partir da URL."""
        patterns = [
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([^\/\?&]+)',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/user\/([^\/\?&]+)',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/c\/([^\/\?&]+)',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([^\/\?&]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        return None

    def get_channel_id(self, youtube, identifier):
        """Resolve o ID do canal do YouTube, seja por ID direto, username ou URL personalizada."""
        try:
            # Se já for um ID de canal (começa com "UC"), retorna diretamente
            if identifier.startswith("UC") and len(identifier) > 20:
                return identifier  

            # Verifica padrões de URL e extrai o identificador correto
            patterns = [
                r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([^\/\?&]+)',  # /channel/UCxxxxx
                r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/user\/([^\/\?&]+)',  # /user/username
                r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/c\/([^\/\?&]+)',  # /c/customname
                r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([^\/\?&]+)',  # /@username
                r'@([a-zA-Z0-9_-]+)'  # Apenas @username
            ]

            for pattern in patterns:
                match = re.search(pattern, identifier)
                if match:
                    identifier = match.group(1)
                    break

            # Busca diretamente o canal pelo nome, se não for um ID direto
            request = youtube.search().list(
                part="snippet",
                q=identifier,  
                type="channel",
                maxResults=1
            )
            response = request.execute()

            if 'items' in response and response['items']:
                return response['items'][0]['snippet']['channelId']

        except Exception as e:
            print(f"Erro ao obter ID do canal: {e}")

        return None

    @app_commands.command(name="add_channel", description="Adiciona um canal do YouTube para monitoramento.")
    async def add_channel(self, interaction: discord.Interaction, youtube_url: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        youtube_channel_id = self.extract_channel_id(youtube_url)
        if not youtube_channel_id:
            await interaction.response.send_message("URL do YouTube inválida.", ephemeral=True)
            return

        youtube = self.get_next_youtube_client()
        resolved_channel_id = self.get_channel_id(youtube, youtube_channel_id)
        if not resolved_channel_id:
            await interaction.response.send_message("Não foi possível resolver o ID do canal do YouTube.", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        channels = self.load_channels()

        # Certifique-se de que a guilda existe no JSON
        if guild_id not in channels:
            channels[guild_id] = {}

        # Adiciona o canal do YouTube
        channels[guild_id][resolved_channel_id] = None
        self.save_channels(channels)

        await interaction.response.send_message(
            f"Canal do YouTube `{youtube_channel_id}` adicionado. Configure o canal do Discord com `/set_post_channel`.",
            ephemeral=True
        )

    @app_commands.command(name="remove_channel", description="Remove um canal do YouTube do monitoramento.")
    async def remove_channel(self, interaction: discord.Interaction, youtube_url: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        youtube_channel_id = self.extract_channel_id(youtube_url)
        if not youtube_channel_id:
            await interaction.response.send_message("URL do YouTube inválida.", ephemeral=True)
            return

        youtube = self.get_next_youtube_client()
        resolved_channel_id = self.get_channel_id(youtube, youtube_channel_id)
        if not resolved_channel_id:
            await interaction.response.send_message("Não foi possível resolver o ID do canal do YouTube.", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        channels = self.load_channels()

        if guild_id in channels and resolved_channel_id in channels[guild_id]:
            del channels[guild_id][resolved_channel_id]
            if not channels[guild_id]:
                del channels[guild_id]
            self.save_channels(channels)
            await interaction.response.send_message(f"Canal do YouTube `{youtube_channel_id}` removido.", ephemeral=True)
        else:
            await interaction.response.send_message(f"O canal `{youtube_channel_id}` não está na lista.", ephemeral=True)

    @app_commands.command(name="set_post_channel", description="Define o canal do Discord onde os vídeos serão postados.")
    async def set_post_channel(self, interaction: discord.Interaction, youtube_url: str, discord_channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Você não tem permissão para usar este comando.", ephemeral=True)
            return

        youtube_channel_id = self.extract_channel_id(youtube_url)
        if not youtube_channel_id:
            await interaction.response.send_message("URL do YouTube inválida.", ephemeral=True)
            return

        youtube = self.get_next_youtube_client()
        resolved_channel_id = self.get_channel_id(youtube, youtube_channel_id)
        if not resolved_channel_id:
            await interaction.response.send_message("Não foi possível resolver o ID do canal do YouTube.", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        channels = self.load_channels()

        if guild_id in channels and resolved_channel_id in channels[guild_id]:
            channels[guild_id][resolved_channel_id] = discord_channel.id
            self.save_channels(channels)
            await interaction.response.send_message(
                f"Canal de postagem configurado para o canal {discord_channel.mention}.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"O canal do YouTube `{youtube_channel_id}` não está na lista. Adicione-o primeiro com `/add_channel`.", ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(YouTubeCommands(bot))