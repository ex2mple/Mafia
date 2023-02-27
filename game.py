import asyncio
import random
from pprint import pprint
import discord
import json
from cards import *



class Game:
    def __init__(self, bot, interaction):
        self.bot = bot
        self.interaction = interaction
        self._game_roles = ['Citizen', 'Sherif'] # UPGRADE IF ADD NEW ROLES!!!


    async def start_game(self) -> None:
        await self.give_role()
        while True:
            vote_message = await self.night()
            await asyncio.sleep(10)  # 10 seconds to vote
            await self.vote(vote_message)
            if await self.check_win() == 1:
                break
            vote_message = await self.day()
            await asyncio.sleep(15)  # 15 seconds to vote
            await self.vote(vote_message)
            if await self.check_win() == 1:
                break

    async def get_mafia(self, your_room: dict) -> list:
        ids = []
        for player in your_room['players_roles']:
            if player['role'] == 'Mafia':
                ids.append(self.interaction.guild.get_member(player['id']))
        return ids


    async def get_players(self, your_room: dict) -> list:
        players = []
        for player in your_room['players_roles']:
            players.append(self.interaction.guild.get_member(player['id']))
        return players


    async def give_role(self) -> None:
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(self.interaction, data)

        roles = get_cards(len(room['players']))
        mafia_thread = self.interaction.guild.get_thread(room['mafia_id'])

        for player in room['players_roles']:
            choice = random.choice(roles)
            discord_player = self.interaction.guild.get_member(player["id"])

            if choice == 'Mafia':
                await mafia_thread.add_user(discord_player)
                room['mafia_count'] += 1
            if choice in self._game_roles:
                room['citizen_count'] += 1

            player['role'] = choice
            roles.remove(choice)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)


    async def day(self) -> discord.Message:
        """

        :param interaction:
        :return:
        """
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(self.interaction, data)
        voice_channel = self.interaction.guild.get_channel(room['voice_channel'])

        if voice_channel:
            for player in room['players']:
                player = self.interaction.guild.get_member(player)
                await voice_channel.set_permissions(player, speak=True)

        channel = self.interaction.guild.get_thread(room['room_id'])
        await channel.send('Город просыпается!')

        players = [player.mention for player in await self.get_players(room)]
        emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️', '🔟']
        embed = discord.Embed(title='Кто по вашему явлеяется мафией?',
                              description='Просто нажмите на реакцию с нужным номером',
                              color=discord.Colour.red())
        embed.add_field(name='Игроки', value='\n'.join(map(lambda x: f"{x[0]} {x[1]}", list(zip(emoji, players)))))

        vote_message = await channel.send(embed=embed, content='У вас есть 45 секунд на раздумие и 15 секунд на голосование!')

        await asyncio.sleep(45) # 45 seconds to think

        await vote_message.edit(content='Начинайте голосовать!')

        for i in range(len(players)):
            await vote_message.add_reaction(emoji[i])

        return vote_message


    async def night(self) -> discord.Message:
        """

        :param interaction:
        :return: vote_message: discord.Message
        """
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(self.interaction, data)
        voice_channel = self.interaction.guild.get_channel(room['voice_channel'])

        if voice_channel:
            for player in room['players']:
                player = self.interaction.guild.get_member(player)
                await voice_channel.set_permissions(player, speak=False)

        channel = self.interaction.guild.get_thread(room['room_id'])
        mafia_channel = self.interaction.guild.get_thread(room['mafia_id'])
        await channel.send('Город засыпает, просыпается мафия!')

        players = [player.mention for player in await self.get_players(room)]
        emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️', '🔟']
        embed = discord.Embed(title='Голосование за жертву',
                              description='Просто нажмите на реакцию с нужным номером',
                              color=discord.Colour.red())
        embed.add_field(name='Жертвы', value='\n'.join(map(lambda x: f"{x[0]} {x[1]}", list(zip(emoji, players)))))

        vote_message = await mafia_channel.send(content='У вас есть 20 секунд на раздумие и 10 секунд на голосование!', embed=embed)

        await asyncio.sleep(20) # 20 seconds to think

        await vote_message.edit(content='Начинайте голосовать!')

        for i in range(len(players)):
            await vote_message.add_reaction(emoji[i])

        return vote_message


    async def vote(self, vote_message: discord.Message) -> None:
        """

        :param interaction:
        :param vote_message:
        :return:
        """
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(self.interaction, data)

        vote_message = self.bot.get_message(vote_message.id)
        channel = self.interaction.guild.get_thread(room['room_id'])

        players = [player.id for player in await self.get_players(room)]
        reactions_count = [reaction.count for reaction in vote_message.reactions]
        sorted_rc: list = sorted(reactions_count)

        if sorted_rc.index(max(sorted_rc)) != len(sorted_rc) - 1:
            embed = discord.Embed(title='Итоги голосования',
                                  description=f'Мнения разделились. Никого не убили!',
                                  color=discord.Colour.blurple())
            await channel.send(embed=embed)
            return

        winner = reactions_count.index(max(reactions_count))

        for player in room['players_roles']:
            if player['id'] == players[winner]:
                role, id = player['role'], player['id']
                room['players_roles'].remove(player)

        player_count = 'mafia_count' if role == 'Mafia' else 'citizen_count'
        room[player_count] -= 1

        embed = discord.Embed(title='Итоги голосования',
                              description=f'Был убит: {self.interaction.guild.get_member(id).mention}',
                              color=discord.Colour.red() if role != 'Mafia' else discord.Colour.green())
        embed.add_field(name='Его роль', value=role)
        embed.add_field(name='Мафиози осталось', value=f'{room["mafia_count"]}',
                        inline=False)

        await channel.send(embed=embed)
        await self.interaction.channel.set_permissions(self.interaction.guild.get_member(id), send_messages=False)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)


    async def check_win(self) -> int:
        """

        :param interaction: discord.Interaction
        :return: int
        """
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(self.interaction, data)

        channel = self.interaction.guild.get_thread(room['room_id'])

        if room['mafia_count'] == 0:
            embed = discord.Embed(title='Мирные жители победили!', color=discord.Colour.green())
        elif room['citizen_count'] == 1: # ВЕРНУТЬ НА 1
            embed = discord.Embed(title='Мафия победила!', description='\n'.join(
                                  [mafia.mention for mafia in await self.get_mafia(room)]),
                                  color=discord.Colour.red())
        else:
            return 0

        await channel.send(embed=embed)
        await asyncio.sleep(10)

        await self.interaction.guild.get_thread(room['mafia_id']).delete()
        await self.interaction.guild.get_thread(room['room_id']).delete()

        for player in room['players']:
            player = self.interaction.guild.get_member(player)
            await self.interaction.channel.set_permissions(player, add_reactions=True, send_messages=True)

        rooms.remove(room)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)

        return 1

