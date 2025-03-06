import discord
from discord.ext import commands
from discord import Interaction
from discord import app_commands
import datetime
import asyncio
import json
import os

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.configs = {}  # Armazena as configurações do servidor, como autorole.
        self.load_configs()  # Carrega as configurações persistidas no início.

    def load_configs(self):
        """Carrega as configurações salvas no arquivo JSON."""
        if os.path.exists("configs.json"):
            with open("configs.json", "r") as file:
                self.configs = json.load(file)

    def save_configs(self):
        """Salva as configurações no arquivo JSON."""
        with open("configs.json", "w") as file:
            json.dump(self.configs, file, indent=4)

    # Evento que atribui automaticamente o autorole ao novo membro
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Atribui automaticamente o autorole ao novo membro."""
        autorole_id = self.configs.get(str(member.guild.id), {}).get('autorole', None)
        if autorole_id:
            autorole = discord.utils.get(member.guild.roles, id=autorole_id)
            
            # Verifica se o cargo existe e se o bot pode gerenciá-lo
            if autorole:
                if autorole.position < member.guild.me.top_role.position:  # Verifica se o bot pode atribuir o cargo
                    await member.add_roles(autorole)
                    print(f"Cargo '{autorole.name}' atribuído automaticamente para {member.mention}.")
                else:
                    print(f"Não foi possível atribuir o cargo '{autorole.name}' a {member.mention} porque está acima do cargo do bot.")
            else:
                print(f"Autorole com ID {autorole_id} não encontrado no servidor.")

    # Método para definir configurações
    def set_config(self, guild_id, autorole_id=None):
        if str(guild_id) not in self.configs:
            self.configs[str(guild_id)] = {}
        if autorole_id:
            self.configs[str(guild_id)]['autorole'] = autorole_id
        self.save_configs()  # Salva as configurações sempre que uma nova for definida.

    # Método para obter configurações
    def get_config(self, guild_id):
        return self.configs.get(str(guild_id), {}).get('autorole', None)

    # Comando /config
    @app_commands.command(name="config", description="Configura o autorole do servidor.")
    async def config(self, interaction: discord.Interaction, autorole: discord.Role = None):
        """Configura ou exibe o autorole do servidor."""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa ser administrador para usar este comando.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if autorole:
            self.set_config(interaction.guild.id, autorole_id=autorole.id)
            embed = discord.Embed(
                title="Autorole Configurado ✅",
                description=f"Autorole configurado com sucesso para o cargo {autorole.mention}.",
                color=discord.Color.green(),
            )
        else:
            autorole_id = self.get_config(interaction.guild.id)
            autorole_name = (
                discord.utils.get(interaction.guild.roles, id=autorole_id).name
                if autorole_id
                else "Não configurado"
            )
            embed = discord.Embed(
                title="Configuração Atual 🔧",
                description=f"**Autorole:** {autorole_name}",
                color=discord.Color.blue(),
            )

        embed.set_footer(text="Use este comando novamente para alterar a configuração.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Comando /nuke
    @app_commands.command(name="nuke", description="Apaga o canal atual e cria um novo igual.")
    async def nuke(self, interaction: discord.Interaction):
        """Remove e recria o canal atual."""
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa ser administrador para usar este comando.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        canal = interaction.channel
        novo_canal = await canal.clone(reason="Canal foi nukado")
        await canal.delete(reason="Canal foi nukado")
        embed = discord.Embed(
            title="Canal Recriado 🔄",
            description="Este canal foi recriado com sucesso!",
            color=discord.Color.orange(),
        )
        embed.set_footer(text="Nuke executado com sucesso.")
        await novo_canal.send(embed=embed)

    # Comando /lock
    @app_commands.command(name="lock", description="Tranca o canal atual para @everyone.")
    async def lock(self, interaction: discord.Interaction):
        """Tranca o canal atual apenas para o cargo @everyone."""
        if not interaction.user.guild_permissions.manage_channels:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa ter permissão para gerenciar canais.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(
            title="Canal Trancado 🔒",
            description="O canal foi trancado. Nenhum membro poderá enviar mensagens.",
            color=discord.Color.dark_gray(),
        )
        embed.set_footer(text="Use /unlock para destrancar.")
        await interaction.response.send_message(embed=embed)

    # Comando /unlock
    @app_commands.command(name="unlock", description="Destranca o canal atual para @everyone.")
    async def unlock(self, interaction: discord.Interaction):
        """Destranca o canal atual apenas para o cargo @everyone."""
        if not interaction.user.guild_permissions.manage_channels:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa ter permissão para gerenciar canais.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(
            title="Canal Destrancado 🔓",
            description="O canal foi destrancado para o cargo @everyone. Agora os membros podem enviar mensagens.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="Use /lock para trancar novamente.")
        await interaction.response.send_message(embed=embed)

    # Comando /limpar
    @app_commands.command(name="limpar", description="Limpa um número específico de mensagens no canal.")
    @app_commands.describe(amount="Número de mensagens a serem apagadas.")
    async def limpar(self, interaction: discord.Interaction, amount: int):
        """Limpa um número específico de mensagens no canal, evitando rate limits."""
        if not interaction.user.guild_permissions.manage_messages:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa ter permissão para gerenciar mensagens.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Limite de mensagens para evitar rate limit
        max_messages_per_batch = 50  # Máximo por lote
        if amount > 500:  # Define um limite superior para evitar uso indevido
            amount = 500

        await interaction.response.defer(ephemeral=True)
    
        total_deleted = 0
        while amount > 0:
            batch_size = min(amount, max_messages_per_batch)
            deleted = await interaction.channel.purge(limit=batch_size)
            total_deleted += len(deleted)
            amount -= batch_size
        
            # Delay entre os lotes para evitar rate limit
            await asyncio.sleep(2)

        embed = discord.Embed(
            title="Mensagens Apagadas 🧹",
            description=f"{total_deleted} mensagens foram apagadas com sucesso!",
            color=discord.Color.blue(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="expulsar", description="Expulsa um membro do servidor.")
    @app_commands.describe(member="Membro a ser expulso.", reason="Razão para a expulsão.")
    async def expulsar(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        # Verifica se o usuário tem permissão para expulsar membros
        if not interaction.user.guild_permissions.kick_members:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa da permissão de **Expulsar Membros** para usar este comando.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
    
        try:
            # Expulsa o membro
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Membro Expulso ✅",
                description=f"{member.mention} foi expulso do servidor com sucesso.",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Razão:", value=reason or "Nenhuma razão fornecida.")
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Erro ❌",
                description="Não consegui expulsar o membro. Verifique minhas permissões.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="Erro Interno ❌",
                description=f"Não consegui expulsar o membro devido a um erro: `{str(e)}`.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    
    @app_commands.command(name="banir", description="Bane um membro do servidor.")
    @app_commands.describe(member="Membro a ser banido.", reason="Razão para o banimento.")
    async def banir(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        # Verifica se o usuário tem permissão para banir membros
        if not interaction.user.guild_permissions.ban_members:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa da permissão de **Banir Membros** para usar este comando.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
    
        try:
            # Bane o membro
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="Membro Banido ✅",
                description=f"{member.mention} foi banido do servidor com sucesso.",
                color=discord.Color.red(),
            )
            embed.add_field(name="Razão:", value=reason or "Nenhuma razão fornecida.")
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Erro ❌",
                description="Não consegui banir o membro. Verifique minhas permissões.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="Erro Interno ❌",
                description=f"Não consegui banir o membro devido a um erro: `{str(e)}`.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # Comando /mute
    @app_commands.command(name="silenciar", description="Silencia um membro no servidor.")
    @app_commands.describe(
        member="Membro a ser silenciado.",
        tempo="Tempo de duração (número inteiro).",
        unidade="Unidade de tempo: dias, horas, minutos ou segundos."
    )
    async def silenciar(
        self, interaction: discord.Interaction, member: discord.Member, tempo: int, unidade: str
    ):
        # Verifica se o usuário tem permissão para moderar membros
        if not interaction.user.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa da permissão de **Moderar Membros** para usar este comando.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Converte o tempo com base na unidade escolhida
        unidades_validas = {
            "dias": 86400,
            "horas": 3600,
            "minutos": 60,
            "segundos": 1
        }

        unidade = unidade.lower()
        if unidade not in unidades_validas:
            embed = discord.Embed(
                title="Unidade Inválida ❌",
                description="Escolha uma unidade válida: `dias`, `horas`, `minutos` ou `segundos`.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Calcula o tempo total em segundos
        duration_seconds = tempo * unidades_validas[unidade]
        timeout_until = discord.utils.utcnow() + datetime.timedelta(seconds=duration_seconds)

        try:
            # Aplica o timeout no membro
            await member.edit(timed_out_until=timeout_until)
            embed = discord.Embed(
                title="Membro Silenciado ✅",
                description=f"{member.mention} foi silenciado no servidor.",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Duração:", value=f"{tempo} {unidade}")
            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Erro ❌",
                description="Não consegui silenciar o membro. Verifique se o bot tem permissões suficientes.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="Erro Interno ❌",
                description=f"Não foi possível silenciar o membro devido a um erro: `{str(e)}`.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    

    # Comando /modo_lento
    @app_commands.command(name="modo_lento", description="Define o intervalo mínimo entre mensagens no canal.")
    @app_commands.describe(dias="Intervalo em dias", horas="Intervalo em horas", minutos="Intervalo em minutos", segundos="Intervalo em segundos")
    async def modo_lento(self, interaction: discord.Interaction, dias: int = 0, horas: int = 0, minutos: int = 0, segundos: int = 0):
        # Verifica se o usuário tem permissão para gerenciar canais
        if not interaction.user.guild_permissions.manage_channels:
            embed = discord.Embed(
                title="Permissão Negada ❌",
                description="Você precisa da permissão de **Gerenciar Canais** para usar este comando.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Converte o tempo total em segundos
        total_segundos = (dias * 86400) + (horas * 3600) + (minutos * 60) + segundos

        if total_segundos <= 0:
            embed = discord.Embed(
                title="Erro ❌",
                description="Por favor, forneça um valor válido para o intervalo entre mensagens.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Aplica o modo lento no canal
        try:
            await interaction.channel.edit(slowmode_delay=total_segundos)
            embed = discord.Embed(
                title="Modo Lento Ativado ✅",
                description=(
                    f"O intervalo mínimo entre mensagens neste canal foi definido para "
                    f"`{dias} dias, {horas} horas, {minutos} minutos e {segundos} segundos`."
                ),
                color=discord.Color.green(),
            )
            embed.set_footer(text=f"Comando executado por {interaction.user}", icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(
                title="Erro ❌",
                description="Não foi possível ativar o modo lento. Verifique as permissões do bot.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(
                title="Erro Interno ❌",
                description=f"Um erro ocorreu ao tentar ativar o modo lento: `{str(e)}`.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Comando /mover
    @app_commands.command(name="mover", description="Move um membro para um canal de voz.")
    @app_commands.describe(member="Membro a ser movido.", channel="Canal de voz para mover.")
    async def mover(self, interaction: discord.Interaction, member: discord.Member, channel: discord.VoiceChannel):
        if not interaction.user.guild_permissions.move_members:
            await interaction.response.send_message("**Você não tem permissão para usar este comando!**", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎧 **Mover Membro**",
            description=f"**{member.mention}** foi movido para o canal de voz **{channel.name}** com sucesso! 🚀",
            color=discord.Color.green()
        )
        embed.add_field(name="📜 Detalhes", value=f"**Membro**: {member.mention}\n**Canal de voz**: {channel.name}", inline=False)
        embed.set_footer(text="Comando executado com sucesso! 💙", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Comando /kickall
    @app_commands.command(name="kickall", description="Expulsa todos os membros de um canal de voz.")
    @app_commands.describe(channel="Canal de voz de onde os membros serão expulsos.")
    async def kickall(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("**Você não tem permissão para usar este comando!**", ephemeral=True)
            return

        # Expulsando os membros do canal de voz
        for member in channel.members:
            await member.kick()

        embed = discord.Embed(
            title="⚡ **Kick All Membros**",
            description=f"**Todos os membros** de **{channel.name}** foram expulsos com sucesso! 🚫",
            color=discord.Color.red()
        )
        embed.add_field(name="📜 Detalhes", value=f"**Canal de voz**: {channel.name}\n**Número de membros expulsos**: {len(channel.members)}", inline=False)
        embed.set_footer(text="Comando executado com sucesso! 💥", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Comando /lockdown
    @app_commands.command(name="lockdown", description="Tranca todos os canais de texto no servidor temporariamente.")
    async def lockdown(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("**Você não tem permissão para usar este comando!**", ephemeral=True)
            return

        # Trancando todos os canais de texto
        for channel in interaction.guild.text_channels:
            await channel.set_permissions(interaction.guild.default_role, send_messages=False)

        embed = discord.Embed(
            title="🔒 **Lockdown Ativado**",
            description="**Todos os canais de texto foram trancados!** 🚫 Nenhum membro poderá enviar mensagens até a liberação.",
            color=discord.Color.red()
        )
        embed.add_field(name="📜 Detalhes", value="**Ação executada com sucesso!** Todos os canais de texto estão agora bloqueados.", inline=False)
        embed.set_footer(text="Comando executado por: " + interaction.user.name, icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))