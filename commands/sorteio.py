import discord
from discord.ext import commands, tasks
from discord import app_commands
from pymongo import MongoClient
import asyncio, random, os
from datetime import datetime, timedelta
import aiohttp

# URL do MongoDB
MONGO_URI = "mongodb+srv://ryanalvessantos93:oCDkuk1Y4jWgtz74@zenix.dqtak.mongodb.net/?retryWrites=true&w=majority&appName=Zenix"

# Conectar ao MongoDB
client = MongoClient(MONGO_URI)
db = client['Zenix']
giveaways_collection = db['sorteios']

#########################################
# Modal para solicitar o ID do canal (quando método for "ID")
#########################################
class ChannelIDModal(discord.ui.Modal, title="Configurar ID do Canal"):
    channel_id = discord.ui.TextInput(
        label="ID do Canal",
        placeholder="Digite o ID do canal para postar o sorteio",
        required=True
    )

    def __init__(self, config: dict):
        super().__init__()
        self.config = config

    async def on_submit(self, interaction: discord.Interaction):
        self.config["channel_envio"] = self.channel_id.value.strip()
        await interaction.response.send_message(
            f"✅ ID do canal definido como `{self.channel_id.value}`. Agora, clique novamente em **Postar Sorteio**.",
            ephemeral=True
        )

#########################################
# Cog principal do sorteio
#########################################
class Giveaway(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()  # Inicia a verificação de sorteios pendentes

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        agora = datetime.utcnow()
        # Busca sorteios cujo horário final já passou
        sorteios_terminados = giveaways_collection.find({"fim": {"$lte": agora}})
        for sorteio in sorteios_terminados:
            canal = self.bot.get_channel(sorteio["canal_id"])
            if not canal:
                continue
            try:
                mensagem = await canal.fetch_message(sorteio["mensagem_id"])
            except Exception:
                continue

            participantes = sorteio.get("participantes", [])
            if not participantes:
                embed = discord.Embed(
                    title="⚠️ Sorteio Encerrado",
                    description="Nenhum participante.",
                    color=discord.Color.red()
                )
                await mensagem.edit(embed=embed, view=None)
            else:
                num_winners = sorteio["config"]["basicas"].get("ganhadores", 1)
                winners = random.sample(participantes, min(num_winners, len(participantes)))
                winner_mentions = ", ".join(f"<@{w}>" for w in winners)
                embed = discord.Embed(
                    title="🎉 Sorteio Encerrado 🎉",
                    description=f"🏆 **Ganhadores:** {winner_mentions}",
                    color=discord.Color.green()
                )
                view = ResortearView(sorteio["mensagem_id"], participantes, num_winners)
                await mensagem.edit(embed=embed, view=view)
            giveaways_collection.delete_one({"mensagem_id": sorteio["mensagem_id"]})

    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="sorteio", description="Abre o painel de configuração para postar um sorteio")
    async def sorteio(self, interaction: discord.Interaction):
        # Estrutura de configuração para o sorteio
        config = {
            "basicas": {
                "nome": None,
                "prêmio": None,
                "ganhadores": 1,  # Número de ganhadores (padrão 1)
                "banner": None,
                "thumbnail": None,
                "descrição": None,
                "tempo": None,
                "unidade_tempo": None
            },
            "requisitos": {
                "texto": None  # Requisito em texto livre
            },
            "botoes_redirecionamento": [],  # Lista de botões com "label" e "url"
            "metodo_envio": None,           # "id" ou "webhook"
            "webhook_info": None,           # URL do webhook (se método for webhook)
            "channel_envio": None           # ID do canal (se método for "id")
        }

        view = PainelConfigView(config, self.bot, interaction)
        embed = discord.Embed(
            title="🎉 Painel de Configuração do Sorteio",
            description="Utilize os menus abaixo para configurar o sorteio. As configurações serão atualizadas à medida que você as insere.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

#########################################
# Painel de Configuração (View)
#########################################
class PainelConfigView(discord.ui.View):
    def __init__(self, config: dict, bot: commands.Bot, interaction: discord.Interaction):
        super().__init__(timeout=300)  # 5 minutos para configurar
        self.config = config
        self.bot = bot
        self.interaction = interaction
        self.message = None  # Será atribuído após o envio da mensagem

    async def update_message(self):
        embed = discord.Embed(
            title="🎉 Painel de Configuração do Sorteio",
            color=discord.Color.blue()
        )
        basicas = self.config["basicas"]
        embed.add_field(
            name="Configurações Básicas",
            value=(
                f"**Nome:** {basicas['nome'] or 'Não definido'}\n"
                f"**Prêmio:** {basicas['prêmio'] or 'Não definido'}\n"
                f"**Banner:** {basicas['banner'] or 'Não definido'}\n"
                f"**Thumbnail:** {basicas['thumbnail'] or 'Não definido'}\n"
                f"**Descrição:** {basicas['descrição'] or 'Não definido'}\n"
                f"**Tempo:** {basicas['tempo'] or 'Não definido'} {basicas['unidade_tempo'] or ''}"
            ),
            inline=False
        )
        embed.add_field(
            name="Requisitos",
            value=f"{self.config['requisitos']['texto'] or 'Nenhum requisito definido'}",
            inline=False
        )
        botoes = self.config["botoes_redirecionamento"]
        botoes_text = "\n".join([f"{i+1}. {btn['label']} -> {btn['url']}" for i, btn in enumerate(botoes)]) or "Nenhum"
        embed.add_field(
            name="Botões de Redirecionamento",
            value=botoes_text,
            inline=False
        )
        metodo = self.config["metodo_envio"] or "Não definido"
        webhook_info = self.config["webhook_info"] or ""
        channel_envio = self.config.get("channel_envio") or ""
        embed.add_field(
            name="Método de Envio",
            value=f"{metodo}\nWebhook: {webhook_info}\nCanal: {channel_envio}",
            inline=False
        )
        # Habilita o botão de postar se os campos obrigatórios estiverem preenchidos:
        # (nome, prêmio, tempo, unidade de tempo e método de envio)
        if (basicas["nome"] and basicas["prêmio"] and basicas["tempo"] and basicas["unidade_tempo"]
                and self.config["metodo_envio"]):
            self.postar_button.disabled = False
        else:
            self.postar_button.disabled = True

        if self.message:
            await self.message.edit(embed=embed, view=self)
        else:
            await self.interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.select(
        placeholder="Configurações Básicas",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="Nome", value="nome"),
            discord.SelectOption(label="Prêmio", value="prêmio"),
            discord.SelectOption(label="Quantidade de Ganhadores", value="ganhadores"),
            discord.SelectOption(label="Banner", value="banner"),
            discord.SelectOption(label="Thumbnail", value="thumbnail"),
            discord.SelectOption(label="Descrição", value="descrição"),
            discord.SelectOption(label="Tempo", value="tempo")
        ]
    )
    async def basicas_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        campo = select.values[0]
        await interaction.response.send_message(f"Digite o valor para **{campo}**:", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60)
            texto = msg.content.strip()
            if campo == "tempo":
                try:
                    valor = int(texto)
                    self.config["basicas"]["tempo"] = valor
                except ValueError:
                    await interaction.followup.send("Valor inválido! Deve ser um número.", ephemeral=True)
                    return
                await interaction.followup.send("Digite a unidade de tempo (minutos, horas ou dias):", ephemeral=True)
                msg2 = await self.bot.wait_for("message", check=check, timeout=60)
                unidade = msg2.content.strip().lower()
                if unidade not in ["minutos", "horas", "dias"]:
                    await interaction.followup.send("Unidade inválida. Use: minutos, horas ou dias.", ephemeral=True)
                    return
                self.config["basicas"]["unidade_tempo"] = unidade
            elif campo == "ganhadores":
                try:
                    valor = int(texto)
                    self.config["basicas"]["ganhadores"] = valor
                except ValueError:
                    await interaction.followup.send("Valor inválido! Deve ser um número.", ephemeral=True)
                    return
            else:
                self.config["basicas"][campo] = texto

            await msg.delete()
            await self.update_message()
        except asyncio.TimeoutError:
            await interaction.followup.send("Tempo esgotado para inserir o valor.", ephemeral=True)

    @discord.ui.select(
        placeholder="Requisitos (texto livre)",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="Digite um requisito", value="digitar")
        ]
    )
    async def requisitos_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "digitar":
            await interaction.response.send_message("Digite o requisito desejado:", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
                self.config["requisitos"]["texto"] = msg.content.strip()
                await msg.delete()
                await self.update_message()
            except asyncio.TimeoutError:
                await interaction.followup.send("Tempo esgotado para inserir o requisito.", ephemeral=True)

    @discord.ui.select(
        placeholder="Botões de Redirecionamento",
        min_values=0, max_values=1,
        options=[
            discord.SelectOption(label="Adicionar Botão", value="adicionar"),
            discord.SelectOption(label="Remover Botão", value="remover")
        ]
    )
    async def botoes_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        escolha = select.values[0]
        if escolha == "adicionar":
            if len(self.config["botoes_redirecionamento"]) >= 5:
                await interaction.response.send_message("Já há 5 botões adicionados.", ephemeral=True)
                return
            await interaction.response.send_message("Digite o **label** do botão:", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg_label = await self.bot.wait_for("message", check=check, timeout=60)
                label = msg_label.content.strip()
                await interaction.followup.send("Digite a URL de redirecionamento:", ephemeral=True)
                msg_url = await self.bot.wait_for("message", check=check, timeout=60)
                url = msg_url.content.strip()
                self.config["botoes_redirecionamento"].append({"label": label, "url": url})
                await msg_label.delete()
                await msg_url.delete()
                await self.update_message()
            except asyncio.TimeoutError:
                await interaction.followup.send("Tempo esgotado para adicionar o botão.", ephemeral=True)
        else:  # remover
            if not self.config["botoes_redirecionamento"]:
                await interaction.response.send_message("Não há botões para remover.", ephemeral=True)
                return
            opcoes = []
            for i, btn in enumerate(self.config["botoes_redirecionamento"]):
                opcoes.append(discord.SelectOption(label=f"{i+1} - {btn['label']}", value=str(i)))
            remover_view = discord.ui.View(timeout=60)
            remover_select = discord.ui.Select(
                placeholder="Selecione o botão para remover",
                options=opcoes, min_values=1, max_values=1
            )

            async def remover_callback(rem_interaction: discord.Interaction):
                indice = int(remover_select.values[0])
                self.config["botoes_redirecionamento"].pop(indice)
                await rem_interaction.response.send_message("Botão removido.", ephemeral=True)
                await self.update_message()

            remover_select.callback = remover_callback
            remover_view.add_item(remover_select)
            await interaction.response.send_message("Selecione o botão para remover:", view=remover_view, ephemeral=True)

    @discord.ui.select(
        placeholder="Método de Envio",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="ID", value="id"),
            discord.SelectOption(label="Webhook", value="webhook")
        ]
    )
    async def metodo_envio_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        metodo = select.values[0]
        self.config["metodo_envio"] = metodo
        if metodo == "webhook":
            await interaction.response.send_message("Digite a URL do webhook:", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
                self.config["webhook_info"] = msg.content.strip()
                await msg.delete()
                await interaction.followup.send("Método de envio definido como webhook.", ephemeral=True)
            except asyncio.TimeoutError:
                await interaction.followup.send("Tempo esgotado para inserir o webhook.", ephemeral=True)
        else:
            # Se o método for "id", solicite o ID do canal para envio
            await interaction.response.send_message("Digite o ID do canal para envio:", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
                self.config["channel_envio"] = msg.content.strip()
                await msg.delete()
                await interaction.followup.send("Método de envio definido como ID.", ephemeral=True)
            except asyncio.TimeoutError:
                await interaction.followup.send("Tempo esgotado para inserir o canal.", ephemeral=True)
        await self.update_message()

    @discord.ui.button(label="📤 Postar Sorteio", style=discord.ButtonStyle.green, custom_id="postar_button")
    async def postar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        basicas = self.config["basicas"]
        # Verifica se os campos mínimos estão preenchidos
        if not (basicas["nome"] and basicas["prêmio"] and basicas["tempo"] and basicas["unidade_tempo"]
                and self.config["metodo_envio"]):
            await interaction.response.send_message("Preencha as configurações mínimas!", ephemeral=True)
            return

        # Calcula o horário final do sorteio
        tempo = basicas["tempo"]
        unidade = basicas["unidade_tempo"]
        if unidade == "minutos":
            delta = timedelta(minutes=tempo)
        elif unidade == "horas":
            delta = timedelta(hours=tempo)
        elif unidade == "dias":
            delta = timedelta(days=tempo)
        else:
            delta = timedelta(minutes=tempo)

        fim = datetime.utcnow() + delta
        timestamp = int(fim.timestamp())

        embed = discord.Embed(
            title=f"🎉 {basicas['nome']} 🎉",
            description=(
                f"Prêmio: {basicas['prêmio']}\n"
                f"Número de Ganhadores: {basicas['ganhadores']}\n"
                f"Termina em: <t:{timestamp}:R>"
            ),
            color=discord.Color.gold()
        )
        if basicas["banner"]:
            embed.set_image(url=basicas["banner"])
        if basicas["thumbnail"]:
            embed.set_thumbnail(url=basicas["thumbnail"])
        if basicas["descrição"]:
            embed.add_field(name="Descrição", value=basicas["descrição"], inline=False)
        if self.config["requisitos"]["texto"]:
            embed.add_field(name="Requisitos", value=self.config["requisitos"]["texto"], inline=False)

        # Aqui iremos remover a opção webhook e usar apenas o método "id"
        if self.config["metodo_envio"] == "id":
            # Se o canal ainda não foi configurado, solicita o ID do canal
            if not self.config.get("channel_envio"):
                modal = ChannelIDModal(self.config)
                await interaction.response.send_modal(modal)
                return
            try:
                channel_id = int(self.config["channel_envio"])
            except ValueError:
                await interaction.response.send_message("ID do canal inválido.", ephemeral=True)
                return

            canal = interaction.guild.get_channel(channel_id)
            if not canal:
                await interaction.response.send_message("Canal não encontrado ou sem permissão de acesso.", ephemeral=True)
                return

            # Cria a view do sorteio com os botões de Participar, Sair e Ver Participantes.
            view = LotteryView(self.bot, self.config)
            msg = await canal.send(embed=embed, view=view)
        else:
            # Caso haja outro método configurado (por exemplo, webhook) e você optou por não usá-lo, envie uma mensagem de erro
            await interaction.response.send_message("Método de envio não suportado. Utilize o método 'ID'.", ephemeral=True)
            return

        # Armazena os dados do sorteio no MongoDB para persistência.
        data = {
            "mensagem_id": msg.id,
            "canal_id": msg.channel.id,
            "fim": fim,
            "participantes": [],
            "config": self.config,
            "owner_id": interaction.user.id
        }
        giveaways_collection.insert_one(data)
        await interaction.response.send_message("Sorteio postado com sucesso!", ephemeral=True)
        self.stop()

#########################################
# View do Sorteio (botões)
#########################################
class LotteryView(discord.ui.View):
    def __init__(self, bot: commands.Bot, config: dict):
        super().__init__(timeout=None)
        self.bot = bot
        self.config = config

    @discord.ui.button(label="✅ Participar", style=discord.ButtonStyle.primary)
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        mensagem_id = interaction.message.id
        giveaway = giveaways_collection.find_one({"mensagem_id": mensagem_id})
        if not giveaway:
            await interaction.response.send_message("Sorteio não encontrado.", ephemeral=True)
            return

        if interaction.user.id in giveaway["participantes"]:
            await interaction.response.send_message("Você já está participando.", ephemeral=True)
            return

        giveaways_collection.update_one(
            {"mensagem_id": mensagem_id},
            {"$push": {"participantes": interaction.user.id}}
        )
        await interaction.response.send_message("Você entrou no sorteio!", ephemeral=True)

    @discord.ui.button(label="❌ Sair", style=discord.ButtonStyle.danger)
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        mensagem_id = interaction.message.id
        giveaway = giveaways_collection.find_one({"mensagem_id": mensagem_id})
        if not giveaway:
            await interaction.response.send_message("Sorteio não encontrado.", ephemeral=True)
            return
        if interaction.user.id not in giveaway["participantes"]:
            await interaction.response.send_message("Você não está participando.", ephemeral=True)
            return
        giveaways_collection.update_one(
            {"mensagem_id": mensagem_id},
            {"$pull": {"participantes": interaction.user.id}}
        )
        await interaction.response.send_message("Você saiu do sorteio.", ephemeral=True)

    @discord.ui.button(label="👥 Ver Participantes", style=discord.ButtonStyle.secondary)
    async def ver_participantes(self, interaction: discord.Interaction, button: discord.ui.Button):
        mensagem_id = interaction.message.id
        giveaway = giveaways_collection.find_one({"mensagem_id": mensagem_id})
        if not giveaway:
            await interaction.response.send_message("Sorteio não encontrado.", ephemeral=True)
            return
        participantes = giveaway["participantes"]
        if not participantes:
            await interaction.response.send_message("Nenhum participante.", ephemeral=True)
        else:
            lista = "\n".join(f"<@{p}>" for p in participantes)
            await interaction.response.send_message(f"Participantes:\n{lista}", ephemeral=True)

#########################################
# View para Resortear
#########################################
class ResortearView(discord.ui.View):
    def __init__(self, mensagem_id: int, participantes: list, num_winners: int):
        super().__init__(timeout=24*3600)
        self.mensagem_id = mensagem_id
        self.participantes = participantes
        self.num_winners = num_winners

    @discord.ui.button(label="🔄 Resortear", style=discord.ButtonStyle.blurple)
    async def resortear(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.participantes:
            await interaction.response.send_message("Nenhum participante para sortear.", ephemeral=True)
            return
        winners = random.sample(self.participantes, min(self.num_winners, len(self.participantes)))
        winner_mentions = ", ".join(f"<@{w}>" for w in winners)
        embed = discord.Embed(
            title="🎉 Sorteio Resortado 🎉",
            description=f"🏆 **Ganhadores:** {winner_mentions}",
            color=discord.Color.green()
        )
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message(f"O(s) novo(s) ganhador(es): {winner_mentions}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaway(bot))
