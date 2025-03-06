import discord
from discord.ext import commands
from google.cloud import dialogflow_v2 as dialogflow
import json
import os

class Inteligencia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "config.json"
        self.channels = self.load_config()
        
        # Defina o caminho da chave do JSON gerado no Google Cloud
        self.dialogflow_credentials_path = "caminho/para/sua/chave/dialogflow.json"
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.dialogflow_credentials_path

        # Configurações do Dialogflow
        self.dialogflow_project_id = "SEU_PROJETO_DIALOGFLOW"
        self.session_client = dialogflow.SessionsClient()
        self.language_code = "pt-BR"

    def load_config(self):
        """Carrega as configurações do arquivo."""
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_config(self):
        """Salva as configurações no arquivo."""
        with open(self.config_file, "w") as f:
            json.dump(self.channels, f)

    @commands.command(name="setchannel")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx, channel: discord.TextChannel):
        """Define o canal onde o bot responderá."""
        self.channels[str(ctx.guild.id)] = channel.id
        self.save_config()
        await ctx.send(f"Canal configurado para: {channel.mention}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        guild_id = str(message.guild.id)
        if guild_id in self.channels and message.channel.id == self.channels[guild_id]:
            prompt = message.content.strip()

            if prompt:
                try:
                    # Criando sessão do Dialogflow
                    session = self.session_client.session_path(self.dialogflow_project_id, message.author.id)
                    text_input = dialogflow.TextInput(text=prompt, language_code=self.language_code)
                    query_input = dialogflow.QueryInput(text=text_input)
                    
                    # Enviando requisição ao Dialogflow
                    response = self.session_client.detect_intent(session=session, query_input=query_input)
                    await message.channel.send(response.query_result.fulfillment_text)
                except Exception as e:
                    await message.channel.send("Desculpe, ocorreu um erro ao processar sua solicitação.")

# Adicionando a extensão ao bot
async def setup(bot):
    await bot.add_cog(Inteligencia(bot))