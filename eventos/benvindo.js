import discord
from discord.ext import commands
import json
import os

class BemViindo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = "data/bem_vindo.json"
        self.ensure_data_file()

    def ensure_data_file(self):
        """Cria o arquivo JSON se ele não existir."""
        if not os.path.exists(self.data_path):
            with open(self.data_path, 'w') as file:
                json.dump({}, file)  # Cria um dicionário vazio inicialmente

    def load_welcome_data(self):
        """Carrega as configurações de boas-vindas do arquivo JSON."""
        with open(self.data_path, 'r') as file:
            return json.load(file)

    def save_welcome_data(self, data):
        """Salva as configurações de boas-vindas no arquivo JSON."""
        with open(self.data_path, 'w') as file:
            json.dump(data, file, indent=4)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Carregar as configurações de boas-vindas para o servidor (guild)
        welcome_data = self.load_welcome_data()
        guild_id = member.guild.id

        if guild_id in welcome_data:
            settings = welcome_data[guild_id]

            # Recuperar as configurações do banco de dados
            channel_id = settings.get('channel_id')
            embed_title = settings.get('embed_title', None)
            embed_description = settings.get('embed_description', None)
            embed_color = discord.Color.blurple() if not settings.get('embed_color') else discord.Color(int(settings['embed_color'].strip("#"), 16))
            embed_image = settings.get('embed_image', None)
            embed_footer = settings.get('embed_footer', None)
            button_label = settings.get('redirect_button_label', None)
            button_url = settings.get('redirect_button_url', None)

            # Encontrar o canal configurado
            channel = member.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title=embed_title or "Bem-vindo!",
                    description=embed_description or f"Seja bem-vindo ao servidor, {member.mention}!",
                    color=embed_color
                )

                if embed_image:
                    embed.set_image(url=embed_image)
                if embed_footer:
                    embed.set_footer(text=embed_footer)

                # Criar um botão de redirecionamento, se configurado
                if button_label and button_url:
                    button = discord.ui.Button(label=button_label, url=button_url)
                    view = discord.ui.View()
                    view.add_item(button)

                    await channel.send(embed=embed, view=view)
                else:
                    await channel.send(embed=embed)
        else:
            # Se não houver configurações, enviar uma mensagem padrão
            channel = member.guild.system_channel
            if channel:
                await channel.send(f"Seja bem-vindo(a), {member.mention}!")

    async def cog_unload(self):
        """Não há necessidade de fechar a conexão com banco de dados em JSON."""
        pass

async def setup(bot):
    await bot.add_cog(BemViindo(bot))