import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import random
import time
import aiohttp

class CommunityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ### COMANDOS RELACIONADOS A USUÁRIOS ###
    
    @app_commands.command(name="avatar", description="Exibe o avatar de um usuário.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(
            title=f"🖼️ Avatar de {member.display_name}",
            description=f"[🔗 Clique aqui para abrir a imagem original]({member.avatar.url})",
            color=discord.Color.random()
        )
        embed.set_image(url=member.avatar.url)
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="banner", description="Exibe o banner de um usuário.")
    async def banner(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        user = await self.bot.fetch_user(member.id)
        if user.banner:
            embed = discord.Embed(
                title=f"🏞️ Banner de {member.display_name}",
                description=f"[🔗 Clique aqui para abrir a imagem original]({user.banner.url})",
                color=discord.Color.random()
            )
            embed.set_image(url=user.banner.url)
            embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ **{member.display_name}** não possui um banner configurado!")

    @app_commands.command(name="userinfo", description="Mostra informações detalhadas sobre o usuário.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user

        roles = sorted(member.roles[1:], key=lambda r: r.position, reverse=True)
        roles_display = ", ".join([role.mention for role in roles[:10]]) + (", etc." if len(roles) > 10 else "")
        roles_display = roles_display if roles else "Sem cargos"

        status_mapping = {
            'online': 'Online',
            'offline': 'Offline',
            'idle': 'Ausente',
            'dnd': 'Não Perturbe'
        }
        status = status_mapping.get(str(member.status), 'Indefinido')

        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        joined_at = f"<t:{int(member.joined_at.timestamp())}:F>" if member.joined_at else "Desconhecido"
        created_at = f"<t:{int(member.created_at.timestamp())}:F>" if member.created_at else "Desconhecido"

        days_in_server = (discord.utils.utcnow() - member.joined_at).days if member.joined_at else "Desconhecido"
        highest_role = roles[0].mention if roles else "Nenhum"
        is_boosting = "Sim" if member.premium_since else "Não"
        is_bot = "Sim" if member.bot else "Não"

        devices = []
        if member.web_status != discord.Status.offline:
            devices.append("🌐 Navegador")
        if member.desktop_status != discord.Status.offline:
            devices.append("🖥️ Computador")
        if member.mobile_status != discord.Status.offline:
            devices.append("📱 Celular")
        devices_display = ", ".join(devices) if devices else "Desconhecido"

        user_embed = discord.Embed(
            title=f"ℹ️ Informações de Usuário - {member}",
            color=discord.Color.gold()
        )
        user_embed.set_thumbnail(url=avatar_url)
        user_embed.add_field(name="🔹 Nome:", value=f"{member.name}#{member.discriminator}", inline=True)
        user_embed.add_field(name="🔹 Nome de exibição:", value=member.display_name, inline=True)
        user_embed.add_field(name="🆔 ID:", value=f"{member.id}", inline=True)
        user_embed.add_field(name="📅 Conta criada em:", value=created_at, inline=True)
        user_embed.add_field(name="📌 Status:", value=status, inline=True)
        user_embed.add_field(name="📲 Dispositivo(s):", value=devices_display, inline=True)
        user_embed.add_field(name="🤖 É um bot?", value=is_bot, inline=True)

        member_embed = discord.Embed(
            title=f"👥 Informações de Membro - {member}",
            color=discord.Color.gold()
        )
        member_embed.add_field(name="📥 Entrou no servidor em:", value=joined_at, inline=True)
        member_embed.add_field(name="📆 Dias no servidor:", value=f"{days_in_server} dias", inline=True)
        member_embed.add_field(name="📋 Cargos:", value=roles_display, inline=False)
        member_embed.add_field(name="🔒 Maior cargo:", value=highest_role, inline=True)
        member_embed.add_field(name="✨ É impulsionador?", value=is_boosting, inline=True)

        permissions_button = Button(
            label="Ver permissões",
            style=discord.ButtonStyle.primary,
            custom_id="show_permissions"
        )

        async def permissions_callback(interaction):
            if interaction.user != member:
                await interaction.response.send_message("Apenas quem usou o comando pode ver as permissões!", ephemeral=True)
                return

            permissions = [perm[0].replace('_', ' ').capitalize() for perm in member.guild_permissions if perm[1]]
            permissions_text = "\n".join(permissions) if permissions else "Sem permissões."
            await interaction.response.send_message(
                f"🛡️ Permissões de **{member}**:\n```{permissions_text}```",
                ephemeral=True
            )

        permissions_button.callback = permissions_callback
        view = View()
        view.add_item(permissions_button)

        await interaction.response.send_message(embeds=[user_embed, member_embed], view=view)

    ### COMANDOS RELACIONADOS AO SERVIDOR ###
    
    @app_commands.command(name="serverinfo", description="Mostra informações detalhadas sobre o servidor.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        bots = sum(1 for member in guild.members if member.bot)  # Contagem de bots
        members = guild.member_count - bots  # Contagem de membros humanos

        embed = discord.Embed(
            title=f"🌐 Informações do Servidor: {guild.name}",
            description="Aqui estão os detalhes completos do servidor!",
            color=discord.Color.blurple()
        )

        # Informações principais
        embed.add_field(name="🆔 ID", value=guild.id, inline=True)
        embed.add_field(name="📆 Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="👥 Membros Humanos", value=members, inline=True)
        embed.add_field(name="🤖 Bots", value=bots, inline=True)
        embed.add_field(name="💬 Canais de Texto", value=len(guild.text_channels), inline=True)
        embed.add_field(name="🔊 Canais de Voz", value=len(guild.voice_channels), inline=True)

        # Informações adicionais
        embed.add_field(name="🎭 Cargos", value=len(guild.roles), inline=True)
        embed.add_field(name="😀 Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="🏆 Boosts do Servidor", value=guild.premium_subscription_count, inline=True)
        embed.add_field(name="🎶 Canais de Música", value=len([channel for channel in guild.voice_channels if 'music' in channel.name.lower()]), inline=True)

        # Icone do servidor
        embed.set_thumbnail(url=guild.icon.url if guild.icon else "")
        embed.set_footer(text=f"Solicitado por {interaction.user.display_name}", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed)

    ### COMANDOS INTERATIVOS E DIVERTIDOS ###

    @app_commands.command(name="roll", description="Rola um dado de 1 a 100.")
    async def roll(self, interaction: discord.Interaction):
        result = random.randint(1, 100)
        await interaction.response.send_message(f"🎲 **{interaction.user.display_name} rolou um dado e tirou {result}!**")

    @app_commands.command(name="choose", description="Escolhe aleatoriamente entre as opções fornecidas.")
    async def choose(self, interaction: discord.Interaction, choices: str):
        if not choices:
            await interaction.response.send_message("❌ Por favor, forneça algumas opções!")
            return
        # Dividindo as opções passadas pelo usuário com base em vírgulas
        choices_list = choices.split(',')
        choice = random.choice(choices_list)
        await interaction.response.send_message(f"🎉 Eu escolho: **{choice.strip()}**")
  
    @app_commands.command(name="8ball", description="Faça uma pergunta e receba uma resposta.")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Sim!", "Não.", "Talvez.", "Definitivamente.", "Não conte com isso.",
            "Pergunte novamente mais tarde.", "Com certeza!", "Eu não sei."
        ]
        response = random.choice(responses)
        embed = discord.Embed(
            title="🎱 Resposta da Bola 8",
            description=f"**Pergunta:** {question}\n**Resposta:** {response}",
            color=discord.Color.random()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="meme", description="Envia um meme aleatório.")
    async def meme(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.memegen.link/images/random") as response:  # API para memes BR
                if response.status == 200:
                    data = await response.json()
                    meme_url = data.get("url")
                    meme_title = data.get("text")
                    meme_author = "Fonte: Meme API BR"

                    embed = discord.Embed(
                        title=f"😂 {meme_title}",
                        description=f"👤 **Autor:** {meme_author}",
                        color=discord.Color.random()
                    )
                    embed.set_image(url=meme_url)
                    embed.set_footer(text="Memes fornecidos por uma API incrível!")
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message("❌ Não foi possível buscar um meme no momento. Tente novamente mais tarde!")

    ### COMANDOS DE UTILIDADE ###

    @app_commands.command(name="ping", description="Verifica a latência do bot.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)  # ms
        await interaction.response.send_message(f"🏓 **Pong! Latência:** {latency}ms")
      
    @app_commands.command(name="quote", description="Exibe uma citação motivacional.")
    async def quote(self, interaction: discord.Interaction):
        quotes = [
            "A vida é curta. Quebre as regras.",
            "Não existe um caminho para a felicidade. A felicidade é o caminho.",
            "O sucesso é a soma de pequenos esforços repetidos dia após dia.",
            "Acredite em si mesmo e todo o resto virá naturalmente.",
            "O melhor ainda está por vir.",
            "O único limite para o seu sucesso é a sua própria mente.",
            "Não espere por uma oportunidade. Crie uma.",
            "Cada dia é uma nova chance para recomeçar.",
            "O verdadeiro fracasso é não tentar.",
            "Não conte os dias, faça os dias contarem.",
            "A única maneira de fazer um ótimo trabalho é amar o que você faz.",
            "A persistência é o caminho do êxito.",
            "Você nunca é velho demais para definir outro objetivo ou sonhar um novo sonho.",
            "Acredite em si mesmo e será imparável.",
            "O fracasso é apenas a oportunidade de começar de novo, com mais inteligência.",
            "Tudo que você pode imaginar é real.",
            "Seja a mudança que você deseja ver no mundo.",
            "O sucesso é ir de fracasso em fracasso sem perder o entusiasmo.",
            "Não desista. O começo é sempre a parte mais difícil.",
            "A jornada é o que importa, não o destino.",
            "Os obstáculos são aqueles perigos que você vê quando tira os olhos do objetivo.",
            "O futuro pertence àqueles que acreditam na beleza de seus sonhos.",
            "Quando você parar de lutar, você começa a vencer.",
            "Sonhe grande e ouse falhar.",
            "É nos momentos mais difíceis que encontramos as maiores forças.",
            "Nunca é tarde demais para ser o que você poderia ter sido.",
            "A única limitação que você tem é a sua mente.",
            "Acredite em seu potencial, você é mais capaz do que imagina.",
            "Não pare até se orgulhar.",
            "Coragem não é a ausência de medo, mas a decisão de que algo é mais importante do que o medo.",
            "As grandes coisas nunca vêm de zonas de conforto.",
            "A única maneira de alcançar o impossível é acreditar que é possível.",
            "O sucesso é a soma de pequenas conquistas diárias.",
            "Você não precisa ser ótimo para começar, mas precisa começar para ser ótimo.",
            "Se você quer ir rápido, vá sozinho. Se você quer ir longe, vá acompanhado.",
            "O único lugar onde o sucesso vem antes do trabalho é no dicionário.",
            "As dificuldades preparam pessoas comuns para destinos extraordinários.",
            "A vitória pertence ao mais perseverante.",
            "É melhor tentar e falhar do que nunca tentar.",
            "Acredite em você mesmo e tudo será possível.",
            "O sucesso não é o final, o fracasso não é fatal: o que conta é a coragem de continuar.",
            "Nada é impossível, a palavra em si diz ‘sou possível’.",
            "Você nunca sabe o quão forte você é, até que ser forte seja a sua única opção.",
            "O maior erro que você pode cometer na vida é o de ficar o tempo todo com medo de cometer um erro.",
            "Se você não lutar por aquilo que quer, não se queixe depois sobre o que você perdeu.",
            "Tudo o que você sempre quis está do outro lado do medo.",
            "Siga seus sonhos, não importa o que aconteça.",
            "Nunca permita que seus medos decidam seu futuro.",
            "Viva sua vida da melhor forma possível. O resto é só consequência.",
            "Os melhores são feitos de falhas e fracassos.",
            "O fracasso é o condimento que dá sabor ao sucesso.",
            "A maior glória em viver não está em nunca cair, mas em levantar cada vez que caímos.",
            "Pessoas que são loucas o suficiente para pensar que podem mudar o mundo, são aquelas que o fazem.",
            "Você não precisa ser melhor do que os outros, você precisa ser melhor do que era ontem.",
            "Todo progresso ocorre fora da zona de conforto.",
            "O maior risco é não correr nenhum risco.",
            "Viver é a coisa mais rara do mundo. A maioria das pessoas apenas existe.",
            "Cada novo começo vem de algum outro começo.",
            "Às vezes, as coisas boas precisam de tempo para acontecer.",
            "O tempo não para, o que ele espera é que você aproveite.",
            "A diferença entre o impossível e o possível está na determinação.",
            "Tudo o que você pode fazer, ou sonhar que pode, comece. A ousadia tem genialidade, poder e magia.",
            "A felicidade não é algo pronto. Ela vem de suas próprias ações.",
            "Acredite que você pode e você já está no meio do caminho.",
            "A vida é 10% o que nos acontece e 90% como reagimos.",
            "Se você quer ser bem-sucedido, precisa ser capaz de fracassar.",
            "O que você faz hoje pode melhorar todos os seus amanhãs.",
            "Quando você se concentra no lado positivo das coisas, sua vida tende a mudar.",
            "Nunca deixe o medo de errar te impedir de tentar.",
            "Acredite no seu próprio valor e as oportunidades aparecerão.",
            "Se você não correr atrás do que quer, nunca o terá.",
            "O sucesso não acontece da noite para o dia.",
            "Em algum lugar, alguém acredita em você.",
            "Não importa o quão devagar você vá, contanto que você não pare.",
            "Nunca subestime o poder de uma atitude positiva.",
            "Você é mais corajoso do que pensa, mais forte do que parece e mais inteligente do que imagina.",
            "O fracasso é uma oportunidade para começar novamente com mais experiência.",
            "Aprenda com o ontem, viva o hoje, tenha esperança para o amanhã.",
            "Não se preocupe com os erros, eles fazem parte do seu sucesso.",
            "Não espere por oportunidades, crie-as.",
            "Não há atalhos para qualquer lugar que valha a pena ir.",
            "Cada passo que você dá, mesmo os menores, te aproxima do seu objetivo.",
            "Não tenha medo de desistir do bom para buscar o ótimo.",
            "Fazendo o melhor que você pode, você já é um vencedor.",
            "Às vezes, você precisa se perder para se encontrar.",
            "Desafios são o que tornam a vida interessante, superá-los é o que dá sentido à vida.",
            "Não tenha medo de ser um iniciante.",
            "O sucesso é um péssimo professor, ele faz as pessoas inteligentes acharem que não podem perder.",
            "Seja corajoso o suficiente para viver a vida que você sempre quis.",
            "Quando você se sente com medo, é quando deve fazer as coisas mais ousadas.",
            "Cada desafio é uma oportunidade disfarçada.",
            "Grandes coisas nunca vêm de zonas de conforto.",
            "Aqueles que dizem que não podem, na verdade, podem. Aqueles que dizem que podem, fazem.",
            "O segredo do sucesso é a persistência.",
            "Seu tempo é limitado, então não o desperdice vivendo a vida de outra pessoa.",
            "Nada acontece sem coragem.",
            "Nunca duvide do seu potencial."
        ]
        
        quote = random.choice(quotes)
        await interaction.response.send_message(f"💬 **Citação:** {quote}")

# Setup da Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(CommunityCommands(bot))