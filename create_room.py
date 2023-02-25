import discord
import json
import game


class Room(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    class RoomButtons(discord.ui.View):
        def __init__(self, bot):
            super().__init__()
            self.bot = bot

        @discord.ui.button(label="Присоединиться", style=discord.ButtonStyle.blurple)
        async def join_button_callback(self, button, interaction):
            with open('db.json', 'r', encoding='UTF-8') as file:
                data = json.load(file)

            def check(m):
                return m.channel == interaction.channel and m.author == interaction.user

            async def edit_msg():
                embed = discord.Embed(
                    title=f'Комната {your_room["name"]}',
                    color=discord.Colour.blurple()
                )

                embed.add_field(name='Игроки:', value='\n'.join(
                    [f'{interaction.guild.get_member(player).mention}' for player in your_room['players']]
                ))

                msg = self.bot.get_message(your_room['message_id'])
                await msg.edit(embed=embed)

            async def join():
                your_room['players'].append(interaction.user.id)
                your_room['players_roles'].append({'id': interaction.user.id, 'role': None, 'is_alive': True})
                await interaction.edit_original_response(content='Ты присоединился ✅', delete_after=3)

                await edit_msg()
                with open('db.json', 'w', encoding='UTF-8') as file:
                    json.dump(data, file, indent=4)

            rooms = data[f'{interaction.guild.id}']['rooms']
            for room in rooms:
                if room['message_id'] == interaction.message.id:
                    your_room = room

            if interaction.user.id in your_room['players']:
                await interaction.response.send_message('Ты уже присоединился!', ephemeral=True, delete_after=5)
                return

            if your_room['password'] is not None:
                await interaction.response.send_message('Введи пароль от комнаты', ephemeral=True)
                user_password = await self.bot.wait_for('message', check=check)
                await user_password.delete() # delete message with password
                if user_password.content == your_room['password']:
                    await join()
                    return
                else:
                    await interaction.followup.send('Неверный пароль!', ephemeral=True, delete_after=5)
                    return
            else:
                await interaction.response.send_message(content='Подождите...', ephemeral=True)
                await join()

        @discord.ui.button(label='Начать', style=discord.ButtonStyle.success)
        async def start_button_callback(self, button, interaction):
            with open('db.json', 'r', encoding='UTF-8') as file:
                data = json.load(file)

            await interaction.message.delete()

            rooms = data[f'{interaction.guild.id}']['rooms']
            for room in rooms:
                if room['message_id'] == interaction.message.id:
                    your_room = room

            voice_channel = your_room['voice_channel']

            if interaction.user.id != your_room['players'][0]: # if not the host pressed the button
                return

            thread = await interaction.channel.create_thread(name=f"{your_room['name']}")
            mafia_thread = await interaction.channel.create_thread(name=f"Mafia {your_room['name']}")

            for player in your_room['players']:
                player = interaction.guild.get_member(player)
                await thread.add_user(player)
                await interaction.guild.get_channel(voice_channel).set_permissions(player, speak=False) # mute players

            your_room['is_started'] = True
            your_room['room_id'] = thread.id
            your_room['mafia_id'] = mafia_thread.id # Create mafia's thread

            with open('db.json', 'w', encoding='UTF-8') as file:
                json.dump(data, file, indent=4)

            our_game = game.Game(self.bot)
            await our_game.give_role(interaction) # Start game


    @discord.slash_command()
    async def create_room(self, ctx, name: str, voice_channel: discord.VoiceChannel, password: str = None):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)
        guild = ctx.guild
        author = ctx.author

        embed = discord.Embed(
            title=f'Комната: {name}',
            color=discord.Colour.blurple()
        )
        embed.add_field(name='Игроки:', value=f'{author.mention}')
        message = await ctx.send(embed=embed, view=self.RoomButtons(self.bot))

        room = {
            'name': name,
            'password': password,
            'voice_channel': voice_channel.id,
            'players': [author.id],
            'channel_id': ctx.channel_id,
            'message_id': message.id,
            'room_id': None,
            'mafia_id': None,
            'is_started': False,
            'players_roles': [{'id': author.id, 'role': None, 'is_alive': True}],
            'mafia_count': 0,
            'citizen_count': 0
        }
        data[f'{guild.id}']['rooms'].append(room)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)




def setup(bot):
    bot.add_cog(Room(bot))
