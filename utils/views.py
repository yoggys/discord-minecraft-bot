from discord import ButtonStyle, Interaction, User
from discord.ui import Button, View, button


class ConfirmView(View):
    def __init__(self, author: User) -> None:
        super().__init__()
        self.author: User = author

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.author.id

    @button(label="Confirm", style=ButtonStyle.green)
    async def confirm_callback(self, _: Button, interaction: Interaction) -> None:
        await interaction.respond("✅ Confirmed", ephemeral=True)
        self.stop()

    @button(label="Cancel", style=ButtonStyle.red)
    async def cancel_callback(self, _: Button, interaction: Interaction) -> None:
        await interaction.respond("❌ Canceled", ephemeral=True)
        self._dispatch_timeout()
