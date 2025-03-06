import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

# Obter as URLs do .env
miniatura_url = os.getenv("miniatura")
banner_url = os.getenv("banner")

class Evento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Verifica se o bot foi mencionado diretamente e se a mensagem não é uma resposta
        if any(mention.id == self.bot.user.id for mention in message.mentions) and message.reference is None:
            embed = discord.Embed(
                title="⚡ **Você me chamou?** ⚡",
                description=(
                    "Olá! Parece que você precisou de mim, e estou pronto para atuar. 💛\n\n"
                    "Sou o **Zenix**, o assistente projetado para transformar sua experiência no Discord. "
                    "Com uma gama de funcionalidades inovadoras e comandos poderosos, estou aqui para **facilitar sua vida**, seja em servidores ou para interações rápidas.\n\n"
                    "Aqui estão algumas opções para você explorar o que posso fazer:\n\n"
                    "**Precisa de ajuda?**\n"
                    "   Use o comando `/ajuda` para ver todos os comandos que posso executar.\n\n"
                    "**Fique por dentro das novidades!**\n"
                    "   Para acompanhar atualizações, novas funcionalidades e melhorias, siga-nos em nosso servidor oficial e não perca nada!\n\n"
                    "**Explore mais sobre mim!**\n"
                    "   Acesse nosso site oficial para informações detalhadas, tutoriais e mais recursos exclusivos.\n\n"
                    "💡 *Não hesite em interagir! Estou aqui para tornar sua experiência no Discord mais produtiva e divertida.*"
                ),
                color=discord.Color.yellow()
            )
            embed.set_thumbnail(url=miniatura_url)  # Substitua pelo ícone do Zenix
            embed.set_image(url=banner_url)  # Substitua pelo link de uma imagem personalizada
            embed.set_footer(
                text="Zenix • A energia que você precisa para impulsionar sua experiência!",
                icon_url=miniatura_url  # Substitua pelo ícone do rodapé
            )

            # Adicionando botões interativos
            view = discord.ui.View()

            view.add_item(discord.ui.Button(
                label="🌐 Entre no meu servidor",
                url="https://discord.gg/Nm7FmNnSyA"
            ))

            view.add_item(discord.ui.Button(
                label="➕ Me adicione ao seu servidor",
                url="https://discord.com/oauth2/authorize?client_id=1308929035295784991&permissions=8&scope=bot+applications.commands"
            ))

            view.add_item(discord.ui.Button(
                label="🔗 Visite meu site",
                url="https://ofc-zenix.squareweb.app/"
            ))
          
            # Enviando a mensagem com o embed e os botões interativos
            await message.channel.send(embed=embed, view=view)

# Modificação no setup para chamar o add_cog de forma assíncrona
async def setup(bot):
    await bot.add_cog(Evento(bot))