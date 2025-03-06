import discord
from discord import app_commands
from discord.ext import tasks, commands
import os
import aiohttp
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
from discord.utils import get
import asyncio

# Configurações
BOT_ID = '1308929035295784991'  # Substitua pelo ID do seu bot
API_TOKEN = '👍🏻'  # Substitua pelo token da API
TOP_GG_VOTE_LINK = f'https://top.gg/bot/{BOT_ID}/vote'  # Link para votar
MONGO_URI = "link"

# Inicialização do MongoDB
client = MongoClient(MONGO_URI)
db = client['Zenix']  # Nome do banco de dados
users_collection = db['users']  # Coleção para dados dos usuários

# Criar o índice no campo 'balance' de forma decrescente
users_collection.create_index([("balance", -1)])

# ====================================================
#                       pagar
# ====================================================

class Transfer:
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id):
        """Obtém ou cria um registro para o usuário."""
        user = self.db['users'].find_one({"user_id": user_id})
        if not user:
            user = {
                "user_id": user_id,
                "balance": 0,
                "last_daily": None,
                "last_vote": None
            }

            self.db['users'].insert_one(user)
        return user

    def update_user_balance(self, user_id, amount):
        """Atualiza o saldo de um usuário."""
        self.db['users'].update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}},
            upsert=True
        )


    def pay_user(self, sender_id, recipient_id, amount):
        """Paga uma quantidade para outro usuário, se o saldo for suficiente."""
        sender = self.get_user(sender_id)
        recipient = self.get_user(recipient_id)

        if sender["balance"] < amount:
            return False  # Saldo insuficiente

        # Atualiza os saldos de ambos
        self.update_user_balance(sender_id, -amount)
        self.update_user_balance(recipient_id, amount)

        return True

# ====================================================
#                      economia
# ====================================================

class Economy(commands.Cog):
    def __init__(self, bot, transfer: Transfer):
        self.bot = bot
        self.transfer = transfer  # Adiciona a instância de Transfer
        self.penalty_loop.start()
      
    def get_user(self, user_id):
        """Obtém ou cria um registro para o usuário."""
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            user = {
                "user_id": user_id,
                "balance": 0,
                "last_daily": None,
                "last_vote": None
            }

            users_collection.insert_one(user)
        return user

    def update_user_balance(self, user_id, amount):
        """Atualiza o saldo de um usuário."""
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": amount}},
            upsert=True
        )

    def can_claim_daily(self, user):
        """Verifica se o usuário pode receber o prêmio diário."""
        now = datetime.utcnow()
        last_daily = user.get("last_daily")
        if not last_daily:
            return True
        last_daily = datetime.fromisoformat(last_daily)
        return now >= last_daily + timedelta(hours=24)

    def update_daily_time(self, user_id):
        """Atualiza o horário do prêmio diário."""
        now = datetime.utcnow().isoformat()
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_daily": now}}
        )

# ====================================================
#                      loops
# ====================================================

    @tasks.loop(hours=24)
    async def penalty_loop(self):
        """
        Loop executado a cada 24 horas para aplicar penalidades aos usuários
        que não coletaram o /daily nas últimas 24 horas.
        """
        now = datetime.utcnow()
        # Itera sobre todos os usuários cadastrados
        for user in users_collection.find({}):
            user_id = user["user_id"]
            last_daily_str = user.get("last_daily")
            if not last_daily_str:
                continue  # Usuário nunca coletou o /daily

            try:
                last_daily = datetime.fromisoformat(last_daily_str)
            except Exception:
                continue  # Se houver erro na formatação, ignora

            # Se o usuário coletou o /daily nas últimas 24 horas, pula
            if now - last_daily < timedelta(days=1):
                continue

            balance = user.get("balance", 0)
            # Só aplica penalidade se o saldo for de 100K ou mais
            if balance < 100_000:
                continue

            # Definição das taxas de penalidade:
            # - ≥ 1 Bilhão: perde 10% por dia
            # - ≥ 100 Milhões: perde 50% por semana (~7.14% por dia)
            # - ≥ 1 Milhão ou ≥ 100K: perde 10% por semana (~1.43% por dia)
            if balance >= 1_000_000_000:
                penalty_rate = 0.10  # 10% diário
            elif balance >= 100_000_000:
                penalty_rate = 0.50 / 7  # Aproximadamente 7.14% por dia
            elif balance >= 1_000_000:
                penalty_rate = 0.10 / 7  # Aproximadamente 1.43% por dia
            else:  # Para saldos entre 100K e 1M
                penalty_rate = 0.10 / 7  # Aproximadamente 1.43% por dia

            loss_amount = int(balance * penalty_rate)
            new_balance = max(0, balance - loss_amount)

            # Atualiza o saldo do usuário no banco
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"balance": new_balance}}
            )
            print(f"Usuário {user_id} penalizado em {loss_amount} Fragment(s) of Life.")

        print(f"Penalty loop executado em: {now.isoformat()}")

    @penalty_loop.before_loop
    async def before_penalty_loop(self):
        """Garante que o bot esteja pronto antes de iniciar o loop."""
        await self.bot.wait_until_ready()

# ====================================================
#                      Comandos
# ====================================================


    @app_commands.command(name="pagar", description="Envie Fragment(s) of Life para outro usuário")
    async def pagar(self, interaction: discord.Interaction, amount: int, recipient: discord.User):
        sender_id = (interaction.user.id)
        recipient_id = (recipient.id)

        # Verifica se o valor é válido
        if amount <= 0:
            await interaction.response.send_message("Por favor, insira um valor válido para enviar.", ephemeral=True)
            return
        
        # Verifica se o destinatário é o próprio usuário
        if sender_id == recipient_id:
            await interaction.response.send_message("Você não pode enviar Fragment(s) of Life para si mesmo.", ephemeral=True)
            return
        
        # Utiliza a lógica de pagamento da classe Transfer
        success = self.transfer.pay_user(sender_id, recipient_id, amount)
        embed_pagaments = discord.Embed(
            title="✅ Pagamento Bem-Sucedido!",
            description=f"🎉 {interaction.user.mention}, você enviou <:123456789012:1324932626611572756> **{amount:,}** Fragment(s) of Life para {recipient.mention}! 🎁",
            color=discord.Color.green()
        )
        embed_pagaments.set_thumbnail(url=interaction.user.avatar.url)
        embed_pagaments.add_field(
            name="🛡️ Status",
            value="Transação concluída com sucesso!",
            inline=False
        )
        embed_pagaments.add_field(
            name="📤 Remetente",
            value=f"{interaction.user.mention}",
            inline=True
        )
        embed_pagaments.add_field(
            name="📥 Destinatário",
            value=f"{recipient.mention}",
            inline=True
        )
        embed_pagaments.set_footer(
            text="Obrigado por usar nosso sistema de transações! ✨",
            icon_url=interaction.client.user.avatar.url  # Pode trocar pela URL de um ícone representativo.
        )

        if success:
            # Enviar a mensagem no canal do comando
            await interaction.response.send_message(
                content=f"{interaction.user.mention} pagou para {recipient.mention}",
                embed=embed_pagaments
            )

            # Enviar mensagem no PV do remetente (interaction.user)
            try:
                await interaction.user.send(
                    content=f"Você pagou <:123456789012:1324932626611572756> **{amount:,}** Fragment(s) of Life para {recipient.mention}.",
                    embed=embed_pagaments
                )
            except discord.Forbidden:
                print(f"Não foi possível enviar mensagem para {interaction.user} (DM desativado).")

            # Enviar mensagem no PV do destinatário (recipient)
            try:
                await recipient.send(
                    content=f"{interaction.user.mention} enviou <:123456789012:1324932626611572756> **{amount:,}** Fragment(s) of Life para você!",
                    embed=embed_pagaments
                )
            except discord.Forbidden:
                print(f"Não foi possível enviar mensagem para {recipient} (DM desativado).")
        else:
            await interaction.response.send_message(f"{interaction.user.mention}, você não tem saldo suficiente para realizar esse pagamento.", ephemeral=True)
          
  
    @app_commands.command(name="saldo", description="Mostra o saldo de Fragment(s) of Life e a posição no ranking global")
    async def saldo(self, interaction: discord.Interaction, user: discord.User = None):
        if user is None:
            user = interaction.user

        user_data = self.get_user(user.id)
        balance = user_data.get("balance", 0)

        # Ranking global
        rankings = list(users_collection.find({}, {"user_id": 1, "balance": 1}))
        rankings.sort(key=lambda x: x["balance"], reverse=True)

        # Encontrar a posição do usuário
        rank_position = next((i + 1 for i, u in enumerate(rankings) if u["user_id"] == user.id), len(rankings))

        embed = discord.Embed(
            title="🧩 **Informações de Fragment(s) of Life**",
            description=f"🎉 **{user.mention}**, você possui <:123456789012:1324932626611572756> **{balance:,}** Fragment(s) of Life! 🌟",
            color=discord.Color.green()
        )

        # Adicionar ranking global SEMPRE
        embed.add_field(
            name="🏆 **Ranking Global**",
            value=f"Você está na **posição #{rank_position}** do ranking global. 🔝",
            inline=False
        )

        # Adicionar rodapé
        embed.set_footer(
            text="Continue colecionando Fragment(s) of Life e suba no ranking! 🚀",
            icon_url=interaction.client.user.avatar.url
        )

        # Adicionar thumbnail do usuário
        embed.set_thumbnail(url=user.avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Receba seu prêmio diário de Fragment(s) of Life")
    async def daily(self, interaction: discord.Interaction):
        user = self.get_user(interaction.user.id)

        # Verifica se o usuário pode reivindicar o prêmio diário
        if not self.can_claim_daily(user):
            last_daily = datetime.fromisoformat(user["last_daily"])
            time_remaining = last_daily + timedelta(hours=24) - datetime.utcnow()
            timestamp = int((datetime.utcnow() + time_remaining).timestamp())

            embed_wait = discord.Embed(
                title="⏳ **Aguarde...**",
                description=f"**{interaction.user.mention}**, você já pegou seu **/daily** hoje.\nTente novamente em <t:{timestamp}:R>. ⏰",
                color=discord.Color.orange()
            )
            embed_wait.add_field(
                name="😉 Paciência!",
                value="Seja paciente, a próxima recompensa está logo ali!",
                inline=False
            )

            await interaction.response.send_message(embed=embed_wait)
            return

        # Obtém o saldo do usuário antes de definir o prêmio
        user_balance = user.get("balance", 0)

        # Depuração no console
        print(f"Usuário: {interaction.user.name} | Saldo: {user_balance:,}")

        # Define o prêmio normal do daily
        min_reward = 500
        max_reward = 1000
        base_reward = random.randint(min_reward, max_reward)
        final_reward = base_reward  # Inicialmente, o prêmio é o padrão

        bonus_applied = False  # Flag para saber se o bônus foi ativado

        # Se o saldo for 10x maior que o máximo do daily (10.000+), aplica o bônus de 10%
        if user_balance >= (max_reward * 10):
            final_reward = int(user_balance * 0.1)  # Calcula 10%
            bonus_applied = True  # Marca que o bônus foi aplicado

        # Depuração no console
        print(f"Recompensa base: {base_reward} | Recompensa final: {final_reward} | Bônus aplicado: {bonus_applied}")

        # Atualiza o saldo e o tempo do daily
        self.update_user_balance(interaction.user.id, final_reward)
        self.update_daily_time(interaction.user.id)

        # Embed da recompensa
        embed_reward = discord.Embed(
            title="🎉 **Parabéns!**",
            description=f"**{interaction.user.mention}**, você recebeu <:123456789012:1324932626611572756> **{final_reward:,}** Fragment(s) of Life pelo seu **/daily**! 🌟",
            color=discord.Color.gold()
        )

        embed_reward.add_field(
            name="🚀 Continue sua jornada!",
            value="Continue colecionando e suba no ranking global! 💪",
            inline=False
        )

        # Se o bônus foi aplicado, adiciona uma mensagem extra no embed
        if bonus_applied:
            embed_reward.add_field(
                name="🎁 **Bônus Diário!**",
                value=f"Seu saldo era alto o suficiente, então você recebeu **10% do seu saldo atual** como recompensa! 🤑",
                inline=False
            )

        await interaction.response.send_message(embed=embed_reward)

    @app_commands.command(name="rank", description="Veja o ranking de Fragment(s) of Life")
    @app_commands.describe(scope="Escolha o tipo de ranking (local ou global)")
    @app_commands.choices(scope=[
        discord.app_commands.Choice(name="local", value="local"),
        discord.app_commands.Choice(name="global", value="global")
    ])
    async def rank(self, interaction: discord.Interaction, scope: str):
        embed = discord.Embed(
            title=f"Ranking {scope.title()} de Fragment(s) of Life",
            color=discord.Color.blue()
        )

        if scope == "global":
            # Obtém os top 10 usuários globalmente, já ordenados pelo saldo no MongoDB
            rankings = list(users_collection.find({}, {"user_id": 1, "balance": 1})
                            .sort("balance", -1)  # Ordenação direta no MongoDB
                            .limit(10))  # Limita para os 10 primeiros

            if rankings:
                for position, user_data in enumerate(rankings, start=1):
                    user = await self.bot.fetch_user(int(user_data["user_id"]))
                    username = user.name if user else "Usuário desconhecido"
                    embed.add_field(
                        name=f"**#{position}** {username}",
                        value=f"Fragment(s): **{user_data['balance']:,}** <:123456789012:1324932626611572756>",
                        inline=False
                    )
            else:
                embed.description = "Nenhum dado encontrado para este ranking."

        elif scope == "local":
            # Obtém os membros da guilda (ignorando bots)
            guild_members = {(member.id): member for member in interaction.guild.members if not member.bot}

            # Obtém os dados dos membros no MongoDB, ordenados pelo saldo
            local_rankings = list(users_collection.find(
                {"user_id": {"$in": list(guild_members.keys())}},
                {"user_id": 1, "balance": 1})
                .sort("balance", -1)
                .limit(10))  # Ordenação e limitação no MongoDB

            if local_rankings:
                for position, user_data in enumerate(local_rankings, start=1):
                    member = guild_members.get(user_data["user_id"])
                    if member:
                        embed.add_field(
                            name=f"**#{position}** {member.mention}",
                            value=f"Fragment(s): **{user_data['balance']:,}** <:123456789012:1324932626611572756>",
                            inline=False
                        )
            else:
                embed.description = "Nenhum dado encontrado para este ranking."

        else:
            await interaction.response.send_message("Por favor, escolha `local` ou `global` como escopo do ranking.", ephemeral=True)
            return

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="votar", description="Votação no Top.gg para ganhar Fragment(s) of Life")
    async def votar(self, interaction: discord.Interaction):
        user_id = (interaction.user.id)
        now = datetime.utcnow()

        # Verifica o último voto no MongoDB
        user_data = users_collection.find_one({"user_id": user_id})
        last_vote = user_data.get("last_vote", None) if user_data else None

        if last_vote:
            last_vote_time = datetime.fromisoformat(last_vote)
            if now < last_vote_time + timedelta(hours=12):
                time_remaining = last_vote_time + timedelta(hours=12) - now

                # Converte o tempo restante para timestamp Unix
                timestamp = int((now + time_remaining).timestamp())

                await interaction.response.send_message(
                    f"{interaction.user.mention}, você já votou recentemente. Tente novamente em <t:{timestamp}:R>.",
                    ephemeral=True
                )
                return


        # Verifica o voto no Top.gg de forma assíncrona
        async with aiohttp.ClientSession() as session:
            url = f'https://top.gg/api/bots/{BOT_ID}/check'
            headers = {"Authorization": API_TOKEN}
            params = {"userId": user_id}

            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    await interaction.response.send_message(
                        "Erro ao verificar o voto no Top.gg. Tente novamente mais tarde.",
                        ephemeral=True
                    )
                    return
    
                data = await response.json()
    
                if data.get("voted") == 1:
                    reward = random.randint(1000, 2000)
    
                    # Atualiza o banco de dados com a nova data de voto e saldo do usuário
                    users_collection.update_one(
                        {"user_id": user_id},
                        {"$set": {"last_vote": now.isoformat()}, "$inc": {"balance": reward}},
                        upsert=True
                    )
    
                    embed = discord.Embed(
                        title="🎉 Obrigado por votar!",
                        description=f"Você recebeu <:123456789012:1324932626611572756> **{reward:,} Fragment(s) of Life!**",
                        color=discord.Color.yellow()
                    )
                    await interaction.response.send_message(embed=embed)
                else:
                    vote_button = discord.ui.Button(label="Vote no bot", url=TOP_GG_VOTE_LINK)
                    view = discord.ui.View()
                    view.add_item(vote_button)
    
                    embed = discord.Embed(
                        title="🗳️ Votação no Top.gg",
                        description="Você ainda não votou no bot! Clique no botão abaixo para votar e apoiar nosso trabalho.",
                        color=discord.Color.yellow()
                    )
                    await interaction.response.send_message(embed=embed, view=view)

import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands

import discord
import random

# ====================================================
#                      dice
# ====================================================

class DiceDuelView(discord.ui.View):
    def __init__(self, economy, aposta: int, challenger_id: int, opponent_id: int):
        super().__init__(timeout=30)
        self.economy = economy
        self.aposta = aposta
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.rolls = {}  # Armazena os dados dos jogadores {user_id: (dado1, dado2)}

    @discord.ui.button(label="Rolar Dados 🎲", style=discord.ButtonStyle.blurple)
    async def roll_dice(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.challenger_id, self.opponent_id]:
            return await interaction.response.send_message("❌ Você não está nesse duelo!", ephemeral=True)
        if interaction.user.id in self.rolls:
            return await interaction.response.send_message("🎲 Você já rolou os dados!", ephemeral=True)

        # Gera dois números aleatórios de 1 a 6
        dado1, dado2 = random.randint(1, 6), random.randint(1, 6)
        self.rolls[interaction.user.id] = (dado1, dado2)

        await interaction.response.send_message(f"🎲 Você rolou **{dado1}** e **{dado2}**!", ephemeral=True)

        # Se os dois jogadores já jogaram, processa o resultado
        if len(self.rolls) == 2:
            await self.process_result(interaction)

    async def process_result(self, interaction: discord.Interaction):
        # Obtém os valores de cada jogador
        challenger_roll = sum(self.rolls[self.challenger_id])
        opponent_roll = sum(self.rolls[self.opponent_id])

        # Determina o vencedor
        if challenger_roll > opponent_roll:
            winner_id = self.challenger_id
            loser_id = self.opponent_id
        elif opponent_roll > challenger_roll:
            winner_id = self.opponent_id
            loser_id = self.challenger_id
        else:
            winner_id = loser_id = None  # Empate

        # Embed de resultado
        embed = discord.Embed(
            title="🎲 Duelo de Dados",
            description="Os dados foram lançados! Aqui está o resultado:",
            color=discord.Color.green() if winner_id else discord.Color.orange()
        )
        embed.add_field(name=f"🎲 {interaction.guild.get_member(self.challenger_id).display_name}",
                        value=f"**{self.rolls[self.challenger_id][0]}** + **{self.rolls[self.challenger_id][1]}** = {challenger_roll}",
                        inline=True)
        embed.add_field(name=f"🎲 {interaction.guild.get_member(self.opponent_id).display_name}",
                        value=f"**{self.rolls[self.opponent_id][0]}** + **{self.rolls[self.opponent_id][1]}** = {opponent_roll}",
                        inline=True)

        if winner_id:
            ganho = self.aposta * 2
            embed.add_field(name="🏆 Vencedor", value=f"<@{winner_id}> ganhou **{ganho:,}** Fragment(s) of Life!", inline=False)
            self.economy.update_user_balance(winner_id, ganho)
            self.economy.update_user_balance(loser_id, -self.aposta)
        else:
            embed.add_field(name="⚖️ Empate", value="Os valores foram iguais, ninguém ganha nada!", inline=False)

        embed.set_footer(text="Obrigado por jogar!", icon_url=interaction.client.user.avatar.url)

        # Desativa o botão após o duelo
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=embed, view=self)

class AcceptDuelView(discord.ui.View):
    def __init__(self, economy, aposta, challenger_id, opponent_id):
        super().__init__(timeout=30)
        self.economy = economy
        self.aposta = aposta
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id

    @discord.ui.button(label="🎲 Aceitar Duelo", style=discord.ButtonStyle.green)
    async def accept_duel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent_id:
            return await interaction.response.send_message("❌ Apenas o desafiado pode aceitar!", ephemeral=True)

        # Verifica saldo dos jogadores
        challenger_data = self.economy.get_user(self.challenger_id)
        opponent_data = self.economy.get_user(self.opponent_id)
        if self.aposta > challenger_data.get("balance", 0) or self.aposta > opponent_data.get("balance", 0):
            return await interaction.response.send_message("Saldo insuficiente para um dos jogadores!", ephemeral=True)

        # Criar visual do duelo
        duel_view = DiceDuelView(self.economy, self.aposta, self.challenger_id, self.opponent_id)
        duel_embed = discord.Embed(
            title="🎲 Duelo de Dados",
            description="Ambos os jogadores devem rolar os dados clicando no botão abaixo!",
            color=discord.Color.blurple()
        )
        duel_embed.add_field(
            name="💰 Aposta",
            value=f"💰 {self.aposta:,} <:123456789012:1324932626611572756> Fragment(s) of Life cada",
            inline=False
        )
        duel_embed.set_footer(text="Boa sorte!", icon_url=interaction.client.user.avatar.url)

        await interaction.message.edit(embed=duel_embed, view=duel_view)
# ====================================================
#                      grafico
# ====================================================

class GraficoView(discord.ui.View):
    def __init__(self, interaction, economy, aposta, user_id):
        super().__init__(timeout=15)
        self.interaction = interaction
        self.economy = economy
        self.aposta = aposta
        self.user_id = user_id
        self.resultado = random.choice(["subiu", "desceu"])
        self.multiplicador = round(min(5, 0.1 + (random.expovariate(1.5) ** 1.8)), 2)
        
    async def processar_aposta(self, escolha, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Você não pode apertar este botão!", ephemeral=True)

        ganho = int(self.aposta * self.multiplicador) if escolha == self.resultado else -self.aposta
        self.economy.update_user_balance(self.user_id, ganho)
        
        resultado_str = "📈 **O gráfico subiu!**" if self.resultado == "subiu" else "📉 **O gráfico desceu!**"
        cor_embed = discord.Color.green() if ganho > 0 else discord.Color.red()
        emoji_resultado = "🎉" if ganho > 0 else "💔"
        
        embed = discord.Embed(
            title="📊 Resultado do Jogo do Gráfico",
            description=f"{resultado_str}\n💵 **Multiplicador:** `{self.multiplicador}x`",
            color=cor_embed
        )
        
        embed.set_thumbnail(url=interaction.client.user.avatar.url)
        embed.add_field(
            name="🛡️ Status",
            value="Transação concluída com sucesso!" if ganho > 0 else "Infelizmente, você perdeu essa rodada!",
            inline=False
        )
        embed.add_field(
            name="📤 Jogador",
            value=f"{interaction.user.mention}",
            inline=True
        )
        embed.add_field(
            name="💰 Resultado",
            value=f"{emoji_resultado} **{'Ganhou' if ganho > 0 else 'Perdeu'} {abs(ganho):,} <:123456789012:1324932626611572756> Fragment(s) of Life!**",
            inline=True
        )
        
        embed.set_footer(
            text="Obrigado por jogar! Tente novamente para mais sorte! 🎲",
            icon_url=interaction.client.user.avatar.url
        )
        
        self.clear_items()  # Remove os botões após a escolha
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Subiu 📈", style=discord.ButtonStyle.green)
    async def subiu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar_aposta("subiu", interaction)
    
    @discord.ui.button(label="Desceu 📉", style=discord.ButtonStyle.red)
    async def desceu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar_aposta("desceu", interaction)


# ====================================================
#           Jogo de Cara ou Coroa (vs Bot)
# ====================================================

class CaraCoroaViewBot(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, economy, aposta: int, user_id: int):
        super().__init__(timeout=15)
        self.interaction = interaction
        self.economy = economy
        self.aposta = aposta
        self.user_id = user_id

    async def process_choice(self, choice: str, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Você não pode usar estes botões!", ephemeral=True)
        
        resultado = random.choice(["cara", "coroa"])
        if choice == resultado:
            ganho = int(self.aposta * 1.9)
        else:
            ganho = -self.aposta

        # Atualiza o saldo do usuário
        self.economy.update_user_balance(self.user_id, ganho)

        emoji_resultado = "🎉" if ganho > 0 else "💔"
        embed = discord.Embed(
            title="🎲 Cara ou Coroa (Bot)",
            description=f"Você escolheu **{choice}** e o resultado foi **{resultado}**!",
            color=discord.Color.green() if ganho > 0 else discord.Color.red()
        )
        embed.add_field(
            name="📤 Resultado",
            value=f"{emoji_resultado} **{'Ganhou' if ganho > 0 else 'Perdeu'} {abs(ganho):,} <:123456789012:1324932626611572756> Fragment(s) of Life!**"
        )
        embed.set_footer(text="Boa sorte na próxima!", icon_url=interaction.client.user.avatar.url)
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Cara", style=discord.ButtonStyle.blurple)
    async def cara(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice("cara", interaction)

    @discord.ui.button(label="Coroa", style=discord.ButtonStyle.blurple)
    async def coroa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice("coroa", interaction)


# ====================================================
#         Jogo de Cara ou Coroa (Duelo entre 2 players)
# ====================================================

class CaraCoroaDuelView(discord.ui.View):
    def __init__(self, economy, aposta: int, challenger_id: int, opponent_id: int):
        super().__init__(timeout=30)
        self.economy = economy
        self.aposta = aposta
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.choices = {}  # Armazena as escolhas dos jogadores: {user_id: escolha}

    async def process_choice(self, choice: str, interaction: discord.Interaction):
        if interaction.user.id not in [self.challenger_id, self.opponent_id]:
            return await interaction.response.send_message("❌ Você não participa deste duelo!", ephemeral=True)
        if interaction.user.id in self.choices:
            return await interaction.response.send_message("Você já fez sua escolha!", ephemeral=True)
        
        self.choices[interaction.user.id] = choice
        await interaction.response.send_message(f"Você escolheu **{choice}**.", ephemeral=True)

        if len(self.choices) == 2:
            resultado = random.choice(["cara", "coroa"])
            challenger_choice = self.choices[self.challenger_id]
            opponent_choice = self.choices[self.opponent_id]

            if challenger_choice == resultado and opponent_choice != resultado:
                vencedor = self.challenger_id
            elif opponent_choice == resultado and challenger_choice != resultado:
                vencedor = self.opponent_id
            else:
                vencedor = None  # Empate

            if vencedor:
                ganho = self.aposta
                perdedor = self.opponent_id if vencedor == self.challenger_id else self.challenger_id
                self.economy.update_user_balance(vencedor, ganho)
                self.economy.update_user_balance(perdedor, -self.aposta)

            embed = discord.Embed(
                title="🎲 Cara ou Coroa (Duelo)",
                description=f"Resultado do lançamento: **{resultado}**",
                color=discord.Color.green() if vencedor else discord.Color.orange()
            )
            if vencedor:
                embed.add_field(
                    name="🏆 Vencedor",
                    value=f"<@{vencedor}> ganhou {self.aposta:,} <:123456789012:1324932626611572756> Fragment(s) of Life!",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚖️ Empate",
                    value="Ambos acertaram ou ambos erraram. Ninguém ganha nada!",
                    inline=False
                )
            
            embed.set_footer(text="Obrigado por jogar!", icon_url=interaction.client.user.avatar.url)
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Cara", style=discord.ButtonStyle.green)
    async def btn_cara(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice("cara", interaction)

    @discord.ui.button(label="Coroa", style=discord.ButtonStyle.red)
    async def btn_coroa(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice("coroa", interaction)


# ====================================================
#                  Jogo da Raspadinha
# ====================================================

class RaspadinhaGame:
    def __init__(self, interaction: discord.Interaction, economy, aposta: int, user_id: int):
        self.interaction = interaction
        self.economy = economy
        self.aposta = aposta
        self.user_id = user_id

    async def start(self):
        # Definição dos prêmios e probabilidades (multiplicadores podem ser fracionados)
        premios = {
            "❌": {"chance": 500, "multiplicador": 0.0},    # 50% de chance
            "💰": {"chance": 100, "multiplicador": 3.0},      # 10% de chance
            "💎": {"chance": 50, "multiplicador": 5.0},      # 5% de chance
            "👑": {"chance": 20, "multiplicador": 10.0},      # 2% de chance
            "🍀": {"chance": 1, "multiplicador": 150.0}       # 0.1% de chance
        }
        roleta = []
        for simbolo, dados in premios.items():
            roleta.extend([simbolo] * dados["chance"])
        resultado = [random.choice(roleta) for _ in range(3)]
        multiplicador = sum(premios[s]["multiplicador"] for s in resultado) / 3
        ganho = int(round(self.aposta * multiplicador - self.aposta))

        # Atualiza o saldo do usuário
        self.economy.update_user_balance(self.user_id, ganho)

        embed = discord.Embed(
            title="🎟️ Raspadinha",
            description=f"🃏 Resultado: {' | '.join(resultado)}",
            color=discord.Color.green() if ganho > 0 else discord.Color.red()
        )
        embed.add_field(
            name="📤 Resultado",
            value=f"💰 **{'Ganhou' if ganho > 0 else 'Perdeu'} {abs(ganho):,} <:123456789012:1324932626611572756> Fragment(s) of Life!**",
            inline=False
        )
        embed.set_footer(text="Tente novamente!", icon_url=self.interaction.client.user.avatar.url)
        await self.interaction.response.send_message(embed=embed)


# ====================================================
#                      Botão de Aceitar
# ====================================================

class AcceptButtonView(discord.ui.View):
    def __init__(self, economy, aposta, challenger_id, opponent_id):
        super().__init__(timeout=60)
        self.economy = economy
        self.aposta = aposta
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id

        # Criando botão "Aceitar" manualmente
        self.accept_button = discord.ui.Button(label="Aceitar", style=discord.ButtonStyle.green)
        self.accept_button.callback = self.accept_duel  # Define a função de callback
        self.add_item(self.accept_button)

    async def accept_duel(self, interaction: discord.Interaction):
        if interaction.user.id != self.opponent_id:
            return await interaction.response.send_message("❌ Apenas o oponente pode aceitar o desafio!", ephemeral=True)

        # Verifica saldo dos jogadores
        challenger_data = self.economy.get_user(self.challenger_id)
        opponent_data = self.economy.get_user(self.opponent_id)
        if self.aposta > challenger_data.get("balance", 0) or self.aposta > opponent_data.get("balance", 0):
            return await interaction.response.send_message("Saldo insuficiente para ambos os jogadores.", ephemeral=True)

        # Criar a visualização do duelo
        duel_view = CaraCoroaDuelView(self.economy, self.aposta, self.challenger_id, self.opponent_id)
        duel_embed = discord.Embed(
            title="🎲 Cara ou Coroa (Duelo)",
            description="Ambos os jogadores, escolham sua opção:",
            color=discord.Color.blurple()
        )
        duel_embed.add_field(
            name="Aposta",
            value=f"💰 {self.aposta:,} <:123456789012:1324932626611572756> Fragment(s) of Life cada",
            inline=False
        )
        duel_embed.set_footer(text="Clique em uma opção!", icon_url=interaction.client.user.avatar.url)

        await interaction.message.edit(embed=duel_embed, view=duel_view)


# ====================================================
#                      Cog de Gambling
# ====================================================

class Gambling(commands.Cog):
    def __init__(self, bot, economy):
        self.bot = bot
        self.economy = economy  # Sistema de economia já implementado

    @app_commands.command(name="cara_ou_coroa", description="Jogue Cara ou Coroa apostando Fragment(s) of Life!")
    @app_commands.describe(aposta="Valor da aposta", opponent="Opcional: desafiar outra pessoa")
    async def cara_ou_coroa(self, interaction: discord.Interaction, aposta: int, opponent: discord.Member = None):
        user = self.economy.get_user(interaction.user.id)
        if aposta < 100 or aposta > user.get("balance", 0):
            return await interaction.response.send_message("Fragment(s) of Life insuficientes ou aposta inválida!", ephemeral=True)

        # Se nenhum oponente ou se o próprio usuário for mencionado, joga contra o bot.
        if opponent is None or opponent.id == interaction.user.id:
            view = CaraCoroaViewBot(interaction, self.economy, aposta, interaction.user.id)
            embed = discord.Embed(
                title="🎲 Cara ou Coroa",
                description="Escolha sua opção:",
                color=discord.Color.blurple()
            )
            embed.add_field(
                name="Aposta",
                value=f"💰 {aposta:,} <:123456789012:1324932626611572756> Fragment(s) of Life",
                inline=False
            )
            embed.set_footer(text="Clique em uma opção!", icon_url=interaction.client.user.avatar.url)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            # Jogo em duelo com outra pessoa.
            opponent_data = self.economy.get_user(opponent.id)
            if aposta < 100 or aposta > opponent_data.get("balance", 0):
                return await interaction.response.send_message("Oponente com Fragment(s) of Life insuficientes ou aposta inválida!", ephemeral=True)
    
            embed = discord.Embed(
                title="🎲 Desafio de Cara ou Coroa",
                description=f"{opponent.mention}, você foi desafiado por {interaction.user.mention} para um duelo de Cara ou Coroa com aposta de {aposta:,} <:123456789012:1324932626611572756> Fragment(s) of Life. Aceita?",
                color=discord.Color.gold()
            )
        
            view = AcceptButtonView(self.economy, aposta, interaction.user.id, opponent.id)
            await interaction.response.send_message(
                content=f"{opponent.mention}, você foi desafiado por {interaction.user.mention}",
                embed=embed,
                view=view
            )

    @app_commands.command(name="grafico", description="Aposte no movimento do gráfico (subir ou descer).")
    async def jogo_grafico(self, interaction: discord.Interaction, aposta: int):
        """Jogo do Gráfico (Subir ou Descer)"""
        user = self.economy.get_user(interaction.user.id)
        if aposta < 100 or aposta > user.get("balance", 0):
            return await interaction.response.send_message("Fragment(s) of Life insuficientes ou aposta inválida!", ephemeral=True)

        embed = discord.Embed(
            title="📊 Jogo do Gráfico",
            description="Escolha se o gráfico vai **subir 📈** ou **descer 📉**.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Aposta",
            value=f"💰 {aposta:,} <:123456789012:1324932626611572756> Fragment(s) of Life",
            inline=False
        )
        embed.set_footer(text="Clique no botão para jogar!", icon_url=interaction.client.user.avatar.url)
        view = GraficoView(interaction, self.economy, aposta, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="raspadinha", description="Jogue Raspadinha e tente ganhar prêmios!")
    @app_commands.describe(aposta="Valor da aposta")
    async def raspadinha(self, interaction: discord.Interaction, aposta: int):
        user = self.economy.get_user(interaction.user.id)
        if aposta < 100 or aposta > user.get("balance", 0):
            return await interaction.response.send_message("Fragment(s) of Life insuficientes ou aposta inválida!", ephemeral=True)
        game = RaspadinhaGame(interaction, self.economy, aposta, interaction.user.id)
        await game.start()

    @app_commands.command(name="dados_duelo", description="Desafie alguém para um duelo de dados!")
    @app_commands.describe(aposta="Valor da aposta", opponent="Oponente a desafiar")
    async def dados_duelo(self, interaction: discord.Interaction, aposta: int, opponent: discord.Member):
        user = self.economy.get_user(interaction.user.id)
        if aposta < 100 or aposta > user.get("balance", 0):
            return await interaction.response.send_message("Fragment(s) of Life insuficientes ou aposta inválida!", ephemeral=True)

        opponent_data = self.economy.get_user(opponent.id)
        if aposta > opponent_data.get("balance", 0):
            return await interaction.response.send_message("Oponente não tem saldo suficiente!", ephemeral=True)

        embed = discord.Embed(
            title="🎲 Desafio de Dados",
            description=f"{opponent.mention}, você foi desafiado por {interaction.user.mention} para um duelo de dados com aposta de {aposta:,} Fragment(s) of Life. Aceita?",
            color=discord.Color.gold()
        )
        view = AcceptDuelView(self.economy, aposta, interaction.user.id, opponent.id)

        await interaction.response.send_message(content=f"{opponent.mention}, você foi desafiado!", embed=embed, view=view)

async def setup(bot):
    transfer = Transfer(db)  
    economy = Economy(bot, transfer)  # Cria a instância do sistema de economia
    
    await bot.add_cog(economy)  # Adiciona primeiro a economia
    await bot.add_cog(Gambling(bot, economy))  # Adiciona Gambling passando Economy como dependência