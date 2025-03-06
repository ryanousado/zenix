import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta, datetime
import re


class EmbedConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Configura um embed interativo para ser postado.")
    async def embed(self, interaction: discord.Interaction):
        embed_data = {
            "title": "Digite seu título",
            "title_url": None,
            "author": None,
            "author_image": None,
            "author_url": None,
            "color": discord.Color.blurple(),
            "description": "sua descrição",  # Descrição inicial
            "footer": None,
            "footer_image": None,
            "thumbnail": None,
            "image": None,
            "timestamp": None,
        }

        # Variável para salvar a forma de envio
        delivery_method = {"type": None, "value": None}

        redirect_buttons = {}

        embed_preview = discord.Embed(
            title=embed_data["title"] or "Título não definido",
            description=embed_data["description"] or "Descrição não definida",
            color=embed_data["color"],
        )

        class EmbedConfigView(discord.ui.View):
            def __init__(self, user_id):
                super().__init__(timeout=600)
                self.user_id = user_id

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id != self.user_id:
                    await interaction.response.send_message(
                        "Você não tem permissão para interagir com este menu.", ephemeral=True
                    )
                    return False
                return True
        class ButtonConfig(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label=f"Botão {i+1}", value=str(i))
                    for i in range(5)
                ]
                super().__init__(
                    placeholder="Selecione um botão para configurar (até 5)",
                    min_values=1,
                    max_values=1,
                    options=options
                )

            async def callback(self, select_interaction: discord.Interaction):
                button_index = int(self.values[0])
                modal = discord.ui.Modal(title=f"Configurar Botão {button_index+1}")

                url_input = discord.ui.TextInput(
                    label="URL do botão",
                    required=True,
                    placeholder="https://example.com",
                    style=discord.TextStyle.short
                )
                label_input = discord.ui.TextInput(
                    label="Texto do botão",
                    required=True,
                    placeholder="Clique aqui",
                    style=discord.TextStyle.short
                )
                modal.add_item(url_input)
                modal.add_item(label_input)

                async def on_submit(modal_interaction: discord.Interaction):
                    # Salva os dados do botão na variável local
                    redirect_buttons[button_index] = {
                        "label": label_input.value,
                        "url": url_input.value,
                    }
                    await modal_interaction.response.send_message(
                        f"Botão {button_index+1} configurado: '{label_input.value}' -> {url_input.value}",
                        ephemeral=True
                    )
                    # Opcional: atualizar a prévia se desejar mostrar que o botão foi configurado

                modal.on_submit = on_submit
                await select_interaction.response.send_modal(modal)

        class ConfigSelect(discord.ui.Select):
            def __init__(self, placeholder, options):
                super().__init__(placeholder=placeholder, options=options)

            async def callback(self, select_interaction: discord.Interaction):
                selection = self.values[0]
                modal = discord.ui.Modal(title=f"Configurar {selection}")
                input_field = discord.ui.TextInput(label=f"Digite o {selection}", required=True, style=discord.TextStyle.paragraph)
                modal.add_item(input_field)

                async def on_submit(modal_interaction: discord.Interaction):
                    embed_data[selection] = input_field.value
                    if selection in ["title", "description"]:
                        setattr(embed_preview, selection, input_field.value)
                    elif selection == "color":
                        try:
                            embed_data["color"] = discord.Color(int(input_field.value.strip("#"), 16))
                            embed_preview.color = embed_data["color"]
                        except ValueError:
                            await modal_interaction.response.send_message("Formato de cor inválido. Use #RRGGBB.", ephemeral=True)
                            return
                    elif selection == "image":
                        embed_preview.set_image(url=input_field.value)
                    elif selection == "thumbnail":
                        embed_preview.set_thumbnail(url=input_field.value)
                    elif selection == "footer":
                        embed_preview.set_footer(text=input_field.value)
                    elif selection == "footer_image":
                        embed_preview.set_footer(text=embed_data.get("footer"), icon_url=input_field.value)
                    elif selection == "author":
                        embed_preview.set_author(name=input_field.value)
                    elif selection == "author_image":
                        embed_preview.set_author(name=embed_data.get("author"), icon_url=input_field.value)
                    elif selection == "author_url":
                        embed_preview.set_author(name=embed_data.get("author"), url=input_field.value)
                    elif selection == "timestamp":
                        try:
                            duration_seconds = parse_duration(input_field.value)
                            embed_data["timestamp"] = datetime.utcnow() + timedelta(seconds=duration_seconds)
                            embed_preview.timestamp = embed_data["timestamp"]
                        except ValueError:
                            await modal_interaction.response.send_message("Formato de duração inválido. Exemplo: 1d 2h 30m 10s", ephemeral=True)
                            return

                    await modal_interaction.response.edit_message(embeds=[embed_tutorial, embed_preview])

                modal.on_submit = on_submit
                await select_interaction.response.send_modal(modal)

        class DeliveryMethodSelect(discord.ui.Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label="📬 ID do Canal", value="id", description="Enviar pelo ID do canal"),
                    discord.SelectOption(label="🌐 Webhook", value="webhook", description="Enviar por um Webhook"),
                ]
                super().__init__(placeholder="Escolha a forma de postagem", options=options)

            async def callback(self, select_interaction: discord.Interaction):
                new_type = self.values[0]
                if new_type != delivery_method["type"]:
                    # Resetando o valor anterior
                    delivery_method["value"] = None
        
                delivery_method["type"] = new_type
                modal = discord.ui.Modal(title="Configurar Forma de Envio")
                input_field = discord.ui.TextInput(label=f"Digite o {new_type}", required=True)
                modal.add_item(input_field)

                async def on_submit(modal_interaction: discord.Interaction):
                    delivery_method["value"] = input_field.value
                    # Atualiza o embed_tutorial com as configurações da forma de envio
                    embed_tutorial.description = (
                        "**Escolha as opções desejadas para configurar seu embed:**\n\n"
                        "⚙️ **Informações Básicas**\n"
                        "• Título, Descrição, Cor, Imagem, Thumbnail\n\n"
                        "🔧 **Informações Avançadas**\n"
                        "• Título URL, Autor, Autor Imagem, Autor URL, Rodapé, Rodapé Imagem, Timestamp\n\n"
                        f"📤 **Forma de Postagem**\n"
                        f"Forma de envio configurada: **{delivery_method['type']}**\n"
                        f"Valor: `{delivery_method['value']}`"
                    )
                    await modal_interaction.response.edit_message(
                        embeds=[embed_tutorial, embed_preview],
                        view=view,
                    )

                modal.on_submit = on_submit
                await select_interaction.response.send_modal(modal)
      
        class PostButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="Postar", style=discord.ButtonStyle.green)

            async def callback(self, button_interaction: discord.Interaction):
                if not delivery_method["type"] or not delivery_method["value"]:
                    await button_interaction.response.send_message(
                        "⚠️ Forma de envio não configurada! Configure antes de postar.", ephemeral=True
                    )
                    return
                try:
                    if delivery_method["type"] == "id":
                        channel = interaction.guild.get_channel(int(delivery_method["value"]))
                        if channel:
                            # Cria uma nova view para adicionar os botões configurados (se houver)
                            view = discord.ui.View()
                            for idx in sorted(redirect_buttons.keys()):
                                dados = redirect_buttons[idx]
                                view.add_item(discord.ui.Button(label=dados["label"], url=dados["url"]))
                    
                            await channel.send(embed=embed_preview, view=view)
                            await button_interaction.response.send_message("✅ Embed postado com sucesso!", ephemeral=True)
                        else:
                            raise ValueError("ID inválido.")
                    elif delivery_method["type"] == "webhook":
                        webhook = discord.Webhook.from_url(delivery_method["value"], adapter=discord.RequestsWebhookAdapter())
                        webhook.send(embed=embed_preview)
                        await button_interaction.response.send_message("✅ Embed enviado via Webhook com sucesso!", ephemeral=True)
                except Exception as e:
                    await button_interaction.response.send_message("❌ Ocorreu um erro ao enviar o embed.", ephemeral=True)
         
        def parse_duration(duration: str) -> int:
            pattern = re.compile(r"(?:(\d+)d)?\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?")
            match = pattern.fullmatch(duration.strip())
            if not match:
                raise ValueError("Formato inválido")
            days, hours, minutes, seconds = (int(group) if group else 0 for group in match.groups())
            return days * 86400 + hours * 3600 + minutes * 60 + seconds

        view = EmbedConfigView(interaction.user.id)
        view.add_item(ConfigSelect("⚙️ Informações Básicas", [
            discord.SelectOption(label="📌 Título", value="title"),
            discord.SelectOption(label="📝 Descrição", value="description"),
            discord.SelectOption(label="🎨 Cor", value="color"),
            discord.SelectOption(label="🖼️ Imagem", value="image"),
            discord.SelectOption(label="🔳 Thumbnail", value="thumbnail"),
        ]))
        view.add_item(ConfigSelect("🔧 Informações Avançadas", [
            discord.SelectOption(label="🔗 Título URL", value="title_url"),
            discord.SelectOption(label="👤 Autor", value="author"),
            discord.SelectOption(label="🖼️ Autor Imagem", value="author_image"),
            discord.SelectOption(label="🔗 Autor URL", value="author_url"),
            discord.SelectOption(label="📝 Rodapé", value="footer"),
            discord.SelectOption(label="🖼️ Rodapé Imagem", value="footer_image"),
            discord.SelectOption(label="⏰ Timestamp", value="timestamp"),
        ]))
        view.add_item(DeliveryMethodSelect())
        view.add_item(ButtonConfig())  # Adicionando o seletor de botões
        view.add_item(PostButton())

        embed_tutorial = discord.Embed(
            title="🎨 Configuração do Embed",
            description=(
                "**Escolha as opções desejadas para configurar seu embed:**\n\n"
                "⚙️ **Informações Básicas**\n"
                "• Título, Descrição, Cor, Imagem, Thumbnail\n\n"
                "🔧 **Informações Avançadas**\n"
                "• Título URL, Autor, Autor Imagem, Autor URL, Rodapé, Rodapé Imagem, Timestamp\n\n"
                "📤 **Forma de Postagem**\n"
                "• Escolha entre enviar por **ID do Canal** ou **Webhook**."
            ),
            color=discord.Color.gold()
        )

        await interaction.response.send_message(embeds=[embed_tutorial, embed_preview], view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(EmbedConfig(bot))