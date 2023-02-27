import discord
import json

import cards
import game


class Room(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    class CheckPassword(discord.ui.Modal):
        def __init__(self, bot, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.bot = bot

            self.add_item(discord.ui.InputText(label="Введи пароль от комнаты"))

        async def callback(self, interaction: discord.Interaction):
            with open('db.json', 'r', encoding='UTF-8') as file:
                data = json.load(file)

            rooms, room = cards.get_room(interaction, data)

            if self.children[0].value == room['password']:
                await Room.RoomButtons.join(self, interaction)
            else:
                await interaction.response.send_message('Неверный пароль!', ephemeral=True, delete_after=2)


    class RoomButtons(discord.ui.View):
        def __init__(self, bot):
            super().__init__()
            self.bot = bot

        async def join(self, interaction):
            with open('db.json', 'r', encoding='UTF-8') as file:
                data = json.load(file)

            rooms, room = cards.get_room(interaction, data)

            room['players'].append(interaction.user.id)
            room['players_roles'].append({'id': interaction.user.id, 'role': None})
            await interaction.response.send_message(content='Ты присоединился ✅', ephemeral=True, delete_after=3)

            await Room.send_embed(self, interaction, room)
            with open('db.json', 'w', encoding='UTF-8') as file:
                json.dump(data, file, indent=4)

        @discord.ui.button(label="Присоединиться", style=discord.ButtonStyle.blurple)
        async def join_button_callback(self, button, interaction: discord.Interaction):
            with open('db.json', 'r', encoding='UTF-8') as file:
                data = json.load(file)

            rooms, room = cards.get_room(interaction, data)

            if interaction.user.id in room['players']:
                await interaction.response.send_message('Ты уже присоединился!', ephemeral=True, delete_after=5)
                return

            if room['password'] is not None:
                modal = Room.CheckPassword(bot=self.bot, title="Введи пароль от комнаты")
                await interaction.response.send_modal(modal)
            else:
                await self.join(interaction)

        @discord.ui.button(label='Начать', style=discord.ButtonStyle.success)
        async def start_button_callback(self, button, interaction):
            with open('db.json', 'r', encoding='UTF-8') as file:
                data = json.load(file)

            rooms, room = cards.get_room(interaction, data)

            if interaction.user.id != room['players'][0]: # if not the host pressed the button
                return
            else:
                await interaction.message.delete()
                thread = await interaction.channel.create_thread(name=f"{room['name']}")
                mafia_thread = await interaction.channel.create_thread(name=f"Mafia {room['name']}")

                for player in room['players']:
                    player = interaction.guild.get_member(player)
                    await thread.add_user(player)
                    await interaction.channel.set_permissions(player, add_reactions=False)

                room['room_id'] = thread.id
                room['mafia_id'] = mafia_thread.id # Create mafia's thread

            with open('db.json', 'w', encoding='UTF-8') as file:
                json.dump(data, file, indent=4)

            our_game = game.Game(self.bot, interaction)
            await our_game.start_game()

        @discord.ui.button(label='Удалить комнату', style=discord.ButtonStyle.danger)
        async def delete_button_callback(self, button, interaction):
            with open('db.json', 'r', encoding='UTF-8') as file:
                data = json.load(file)

            rooms, room = cards.get_room(interaction, data)

            if interaction.user.id != room['players'][0]: # if not the host pressed the button
                return
            else:
                await interaction.message.delete()
                rooms.remove(room)

                with open('db.json', 'w', encoding='UTF-8') as file:
                    json.dump(data, file, indent=4)

    async def send_embed(self, interaction, room):
        embed = discord.Embed(
            title=f'Комната: {room["name"]}',
            color=discord.Colour.blurple()
        )

        embed.add_field(name='Игроки:', value='\n'.join(
            [f'{interaction.guild.get_member(player).mention}' for player in room['players']]
        ))

        if room['message_id'] is None:
            msg = await interaction.send(embed=embed, view=self.RoomButtons(self.bot))
            room['message_id'] = msg.id
        else:
            msg = self.bot.get_message(room['message_id'])
            await msg.edit(embed=embed)

    @discord.slash_command()
    async def create_room(self, ctx, name: str, voice_channel: discord.VoiceChannel = None, password: str = None):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        await ctx.delete()
        guild = ctx.guild
        author = ctx.author

        room = {
            'name': name,
            'password': password,
            'voice_channel': voice_channel.id if not AttributeError else None,
            'players': [author.id],
            'channel_id': ctx.channel_id,
            'message_id': None,
            'room_id': None,
            'mafia_id': None,
            'players_roles': [{'id': author.id, 'role': None}],
            'mafia_count': 0,
            'citizen_count': 0
        }

        await self.send_embed(ctx, room)

        data[f'{guild.id}']['rooms'].append(room)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)


def setup(bot):
    bot.add_cog(Room(bot))
