import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Select, View, Button

from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

# Obter as URLs do .env
miniatura_url = os.getenv("miniatura")
banner_url = os.getenv("banner")

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ajuda", description="Exibe a lista de comandos disponíveis.")
    async def ajuda(self, interaction: discord.Interaction):
        # Configuração das categorias com emojis e descrições
        options = [
            discord.SelectOption(label="Comandos de Usuário", description="Ações e informações sobre usuários.", emoji="👤"),
            discord.SelectOption(label="Comandos do Servidor", description="Tudo sobre o servidor.", emoji="🌐"),
            discord.SelectOption(label="Comandos Divertidos", description="Para se divertir e relaxar.", emoji="🎉"),
            discord.SelectOption(label="Comandos de Utilidade", description="Ferramentas práticas para o dia a dia.", emoji="🛠️"),
            discord.SelectOption(label="Adm", description="Comandos exclusivos para administração.", emoji="🔧"),
            discord.SelectOption(label="Comandos XP", description="Gerencie sua experiência e ranking.", emoji="📊"),
            discord.SelectOption(label="Informações do Bot", description="Descubra tudo sobre o bot.", emoji="🤖"),
            discord.SelectOption(label="Comandos do YouTube", description="Monitore canais e notificações.", emoji="📺"),
            discord.SelectOption(label="Fragments of Life", description="Economia e recompensas do sistema.", emoji="💎"),
            discord.SelectOption(label="jogos", description="Aposte e se divirta com nossos jogos.", emoji="🎮"),
            discord.SelectOption(label="Penalidades", description="Saiba quanto você perde sem o /daily.", emoji="⚠️"),
        ]

        select_menu = Select(placeholder="Selecione uma categoria...", options=options)

        async def select_callback(inter: discord.Interaction):
            if not select_menu.values:
                await inter.response.send_message("Por favor, selecione uma opção válida.", ephemeral=True)
                return

            selected = select_menu.values[0]
            embed = discord.Embed(color=discord.Color.from_rgb(30, 144, 255))
            
            if selected == "Comandos de Usuário":
                embed.title = "👤 Comandos de Usuário"
                embed.description = (
                    "**/avatar [@usuário]**\n"
                    "Veja o avatar de um usuário.\n\n"
                    "**/banner [@usuário]**\n"
                    "Exibe o banner de um usuário.\n\n"
                    "**/userinfo [@usuário]**\n"
                    "Mostra informações detalhadas sobre um usuário.\n\n"
                    "**/nickname [@usuário] [novo_apelido]**\n"
                    "Altere o apelido de alguém.\n\n"
                    "**/roles [@usuário]**\n"
                    "Lista os cargos de um usuário.\n\n"
                    "**/status [@usuário]**\n"
                    "Exibe o status atual de um usuário.\n\n"
                    "**/activity [@usuário]**\n"
                    "Mostra a atividade atual de um usuário.\n\n"
                    "**/toprole [@usuário]**\n"
                    "Exibe o cargo mais alto de um usuário."
                )
            elif selected == "Comandos do Servidor":
                embed.title = "🌐 Comandos do Servidor"
                embed.description = (
                    "**/serverinfo**\n"
                    "Exibe informações detalhadas do servidor.\n\n"
                    "**/serverstats**\n"
                    "Mostra estatísticas do servidor.\n\n"
                    "**/emojilist**\n"
                    "Lista todos os emojis do servidor.\n\n"
                    "**/roleinfo [nome_do_cargo]**\n"
                    "Exibe informações sobre um cargo.\n\n"
                    "**/channelinfo [#canal]**\n"
                    "Fornece detalhes de um canal.\n\n"
                    "**/servericon**\n"
                    "Exibe o ícone do servidor.\n\n"
                    "**/serverbanner**\n"
                    "Mostra o banner do servidor.\n\n"
                    "**/invite**\n"
                    "Gera um link permanente de convite."
                )
            elif selected == "Comandos Divertidos":
                embed.title = "🎉 Comandos Divertidos"
                embed.description = (
                    "**/roll**\n"
                    "Role um dado de 1 a 100.\n\n"
                    "**/flip**\n"
                    "Jogue cara ou coroa.\n\n"
                    "**/choose [opções]**\n"
                    "Escolha aleatoriamente entre as opções fornecidas.\n\n"
                    "**/8ball [pergunta]**\n"
                    "Receba uma resposta misteriosa da bola mágica.\n\n"
                    "**/meme**\n"
                    "Receba um meme aleatório para animar o dia."
                )
            elif selected == "Comandos de Utilidade":
                embed.title = "🛠️ Comandos de Utilidade"
                embed.description = (
                    "**/ping**\n"
                    "Verifique a latência do bot.\n\n"
                    "**/time**\n"
                    "Veja o horário atual.\n\n"
                    "**/calculator [expressão]**\n"
                    "Realize cálculos simples."
                )
            elif selected == "Adm":
                embed.title = "🔧 Comandos Adm"
                embed.description = (
                    "**/config**\n"
                    "Configure parâmetros administrativos.\n\n"
                    "**/nuke**\n"
                    "Resete um canal (uso com cautela!).\n\n"
                    "**/lock**\n"
                    "Bloqueie um canal.\n\n"
                    "**/unlock**\n"
                    "Desbloqueie um canal.\n\n"
                    "**/limpar**\n"
                    "Limpe mensagens do chat.\n\n"
                    "**/expulsar**\n"
                    "Expulse membros indesejados.\n\n"
                    "**/banir**\n"
                    "Banir usuários problemáticos.\n\n"
                    "**/silenciar**\n"
                    "Silencie membros temporariamente.\n\n"
                    "**/modo_lento**\n"
                    "Ative o modo lento para o canal."
                )
            elif selected == "Comandos XP":
                embed.title = "📊 Comandos XP"
                embed.description = (
                    "**/xp**\n"
                    "Verifique seu XP atual.\n\n"
                    "**/rank xp**\n"
                    "Exiba o ranking de XP do servidor.\n\n"
                    "**/config xp**\n"
                    "Configure o sistema de XP."
                )
            elif selected == "Informações do Bot":
                embed.title = "🤖 Informações do Bot"
                embed.description = (
                    "**/invite**\n"
                    "Obtenha o link de convite do bot.\n\n"
                    "**/info**\n"
                    "Veja informações detalhadas do bot.\n\n"
                    "**/suggest**\n"
                    "Envie suas sugestões para melhorar o bot.\n\n"
                    "**/report**\n"
                    "Reporte erros ou problemas encontrados."
                )
            elif selected == "Comandos do YouTube":
                embed.title = "📺 Comandos do YouTube"
                embed.description = (
                    "**/add_channel**\n"
                    "Monitore um canal do YouTube.\n\n"
                    "**/remove_channel**\n"
                    "Remova um canal monitorado.\n\n"
                    "**/set_post_channel**\n"
                    "Configure o canal para notificações de novos vídeos."
                )
            elif selected == "Fragments of Life":
                embed.title = "💎 Fragments of Life"
                embed.description = (
                    "**/saldo**\n"
                    "Verifique seu saldo de Fragment(s) of Life.\n\n"
                    "**/rank**\n"
                    "Exiba o ranking global ou local.\n\n"
                    "**/pagar [quantidade] [@usuário]**\n"
                    "Transfira Fragment(s) de Life para outro usuário.\n\n"
                    "**/daily**\n"
                    "Receba uma recompensa diária de Fragment(s) of Life.\n\n"
                    "**/votar**\n"
                    "Ganhe recompensas votando."
                )
                embed.color = discord.Color.gold()
            elif selected == "jogos":
                embed.title = "🎮 Comandos de Jogos"
                embed.description = (
                    "**/cara_ou_coroa [aposta] [@usuário opcional]**\n"
                    "Jogue Cara ou Coroa apostando seus Fragment(s) of Life!\n\n"
                    "**/grafico [aposta]**\n"
                    "Aposte no movimento do gráfico (subir ou descer).\n\n"
                    "**/raspadinha [aposta]**\n"
                    "Jogue Raspadinha e tente ganhar prêmios!\n\n"
                    "**/mines [aposta] [bombas]**\n"
                    "Jogue Minas e desafie sua sorte!\n\n"
                    "**/dados_duelo [aposta] [@usuário]**\n"
                    "Desafie alguém para um duelo de dados."
                )
                embed.color = discord.Color.from_rgb(255, 105, 180)
            elif selected == "Penalidades":
                embed.title = "⚠️ Penalidades"
                embed.description = (
                    "Mantenha seu **/daily** em dia para evitar penalidades automáticas!\n\n"
                    "➤ **Saldo entre 100K e 1M:** perde aproximadamente **1.43% por dia** (*cerca de 10% por semana*).\n\n"
                    "➤ **Saldo entre 1M e 100M:** perde aproximadamente **1.43% por dia** (*cerca de 10% por semana*).\n\n"
                    "➤ **Saldo entre 100M e 1B:** perde aproximadamente **7.14% por dia** (*cerca de 50% por semana*).\n\n"
                    "➤ **Saldo de 1B ou mais:** perde **10% por dia**.\n\n"
                    "Fique atento e não deixe passar o seu **/daily**!"
                )
                embed.color = discord.Color.red()

            await inter.response.edit_message(embed=embed)

        select_menu.callback = select_callback

        # Botões customizados
        server_button = Button(label="Entre no Meu Servidor", url="https://discord.gg/T4c3eNamVR", style=discord.ButtonStyle.link)
        add_button = Button(label="Me Adicione", url="https://discord.com/oauth2/authorize?client_id=1308929035295784991&permissions=8&scope=bot+applications.commands", style=discord.ButtonStyle.link)
        site_button = Button(label="Meu Site", url="https://ofc-zenix.squareweb.app/", style=discord.ButtonStyle.link)

        view = View(timeout=None)
        view.add_item(select_menu)
        view.add_item(server_button)
        view.add_item(add_button)
        view.add_item(site_button)

        # Embed inicial com imagem e layout atrativo
        embed = discord.Embed(
            title="✨ Bem-vindo à Central de Comandos do Zenix! ✨",
            description=(
                "Explore o universo de possibilidades com **Zenix**!\n\n"
                "📂 **Selecione uma categoria no menu abaixo** para descobrir os comandos disponíveis.\n\n"
                "📩 **Precisa de ajuda?** Utilize os seguintes comandos:\n"
                "   └ `/reportar_erro` para reportar problemas\n"
                "   └ `/suggest` para enviar sugestões\n\n"
                "⭐ *Sua experiência é nossa prioridade!*"
            ),
            color=discord.Color.yellow()
        )
        embed.set_thumbnail(url=miniatura_url)
        embed.set_image(url=banner_url)
        embed.set_footer(
            text="Feito com carinho por Zenix 💙 | Acompanhe as novidades!",
            icon_url=miniatura_url
        )

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
