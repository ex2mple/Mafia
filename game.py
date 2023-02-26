import asyncio
import random
from pprint import pprint
import discord
import json
from cards import *



class Game(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game_roles = ['Citizen', 'Sherif'] # UPGRADE IF ADD NEW ROLES!!!

    @discord.slash_command()
    async def rules(self, ctx):
        embed = discord.Embed(title='Правила игры',
                              description='В игре есть всего 3 роли: мирный житель (Citizen), мафия (Mafia) и шериф (Sherif)',
                              colour=discord.Colour.blurple())
        embed.add_field(name='Мирные жители',
                        value='Игроки, вычисляющие мафию на дневных голосованиях. Никаких способностей не имеют; '
                              'просто ждут пока их убьют лол.')
        embed.add_field(name='Мафия',
                        value='Проявляет себя по большей части в ночных убийствах, '
                              'днём же представляются как мирные горожане.')
        embed.add_field(name='Шериф',
                        value='Играет на стороне мирных жителей. Ночью просыпается отдельно и может проверить '
                              'любого игрока. Полученные данные может обнародовать.', inline=False)
        embed.add_field(name='Ход игры',
                        value='Игроки получают свои роли.\n'
                              'Игра разделенная на 2 части: "день" и "ночь"\n'
                              'В первую ночь ничего не происходит. Мафия может наметить себе "жертву".\n'
                              'Днем все игроки обсуждают кто может быть Мафиози и голосуют за них. Мафия в свою очередь пытается доказать свою невиновность.\n'
                              'Если голоса распределились поровну, никто не выбывает.\n'
                              'Игра продолжается до полной победы одной из команд, когда соперники полностью или посажены или убиты.')

        await ctx.respond(embed=embed)


    async def start_game(self, interaction):
        await self.give_role(interaction)
        while True:
            vote_message = await self.night(interaction)
            await asyncio.sleep(10)  # 10 seconds to vote
            await self.vote(interaction, vote_message)
            if await self.check_win(interaction) == 1:
                break
            vote_message = await self.day(interaction)
            await asyncio.sleep(15)  # 15 seconds to vote
            await self.vote(interaction, vote_message)
            if await self.check_win(interaction) == 1:
                break


    async def get_mafia(self, your_room, interaction):
        ids = []
        for player in your_room['players_roles']:
            if player['role'] == 'Mafia':
                ids.append(interaction.guild.get_member(player['id']))
        return ids


    async def get_players(self, your_room, interaction):
        players = []
        for player in your_room['players_roles']:
            players.append(interaction.guild.get_member(player['id']))
        return players


    async def give_role(self, interaction):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(interaction, data)

        roles = get_cards(len(room['players']))
        mafia_thread = interaction.guild.get_thread(room['mafia_id'])

        for player in room['players_roles']:
            choice = random.choice(roles)
            if choice == 'Mafia':
                room['mafia_count'] += 1
            if choice in self.game_roles:
                room['citizen_count'] += 1

            player['role'] = f'{choice}'
            roles.remove(choice)

        for player in room['players_roles']:
            player1 = interaction.guild.get_member(player["id"])

            embed = discord.Embed(title='Инфо', description=f'Ваша роль - {player["role"]}')
            embed.color = discord.Colour.green()

            if player['role'] == 'Mafia':
                embed.add_field(name='Мафиози этой игры: ', value='\n'.join(
                                  [mafia.mention for mafia in await self.get_mafia(room, interaction)]))
                embed.color = discord.Colour.red()

                await mafia_thread.add_user(player1) # add mafia player in other thread

            # await player1.send(embed=embed) # send private message with player's role

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)


    async def day(self, interaction):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(interaction, data)

        # for player in room['players']:
        #     player = interaction.guild.get_member(player)
        #     await interaction.guild.get_channel(room['voice_channel']).set_permissions(player, speak=True)

        channel = interaction.guild.get_thread(room['room_id'])
        await channel.send('Город просыпается!')
        await channel.send('Наступил день! Кто кажется самым подозрительным?')

        players = [player.mention for player in await self.get_players(room, interaction)]
        emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️', '🔟']
        embed = discord.Embed(title='Кто по вашему явлеяется мафией?',
                              description='Просто нажмите на реакцию с нужным номером',
                              color=discord.Colour.red())
        embed.add_field(name='Игроки', value='\n'.join(map(lambda x: f"{x[0]} {x[1]}", list(zip(emoji, players)))))

        vote_message = await channel.send(embed=embed)
        info_message = await channel.send('У вас есть 45 секунд на раздумие и 15 секунд на голосование!')

        await asyncio.sleep(45) # 45 seconds to think

        await info_message.edit('Начинайте голосовать!')

        for i in range(len(players)):
            await vote_message.add_reaction(emoji[i])

        return vote_message


    async def night(self, interaction):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(interaction, data)

        # for player in room['players']:
        #     player = interaction.guild.get_member(player)
        #     await interaction.guild.get_channel(room['voice_channel']).set_permissions(player, speak=False)

        channel = interaction.guild.get_thread(room['room_id'])
        mafia_channel = interaction.guild.get_thread(room['mafia_id'])
        await channel.send('Город засыпает, просыпается мафия!')
        await mafia_channel.send('И снова ночь на дворе! Кто станет следующей жертвой? Выбор за вами!')

        players = [player.mention for player in await self.get_players(room, interaction)]
        emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️', '🔟']
        embed = discord.Embed(title='Голосование за жертву',
                              description='Просто нажмите на реакцию с нужным номером',
                              color=discord.Colour.red())
        embed.add_field(name='Жертвы', value='\n'.join(map(lambda x: f"{x[0]} {x[1]}", list(zip(emoji, players)))))

        vote_message = await mafia_channel.send(embed=embed)
        info_message = await mafia_channel.send('У вас есть 20 секунд на раздумие и 10 секунд на голосование!')

        await asyncio.sleep(20) # 20 seconds to think

        await info_message.edit('Начинайте голосовать!')

        for i in range(len(players)):
            await vote_message.add_reaction(emoji[i])

        return vote_message


    async def vote(self, interaction, vote_message):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(interaction, data)

        vote_message = self.bot.get_message(vote_message.id)
        channel = interaction.guild.get_thread(room['room_id'])

        players = [player.id for player in await self.get_players(room, interaction)]
        reactions_count = [reaction.count for reaction in vote_message.reactions]
        sorted_rc: list = sorted(reactions_count)

        if sorted_rc.index(max(sorted_rc)) != len(sorted_rc) - 1:
            embed = discord.Embed(title='Итог',
                                  description=f'Мнения разделились. Никого не убили!',
                                  color=discord.Colour.green())
            await channel.send(embed=embed)
            return
        else:
            max_count = max(reactions_count)

        for result in list(zip(reactions_count, players)):
            if result[0] == max_count:
                for player in room['players_roles']:
                    if player['id'] == result[1]:
                        role = player['role']
                        id = player['id']
                        room['players_roles'].remove(player)

        if role == 'Mafia':
            room['mafia_count'] -= 1
        elif role in self.game_roles:
            room['citizen_count'] -= 1

        embed = discord.Embed(title='Итог',
                              description=f'Был убит: {interaction.guild.get_member(id).mention}',
                              color=discord.Colour.red() if role != 'Mafia' else discord.Colour.green())
        embed.add_field(name='Его роль', value=role)
        embed.add_field(name='Мафиози осталось', value=f'{room["mafia_count"]}',
                        inline=False)

        await channel.send(embed=embed)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)



    async def check_win(self, interaction):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms, room = get_room(interaction, data)

        channel = interaction.guild.get_thread(room['room_id'])

        if room['mafia_count'] == 0:
            embed = discord.Embed(title='Мирные жители победили!', color=discord.Colour.green())
        elif room['citizen_count'] == 1:
            embed = discord.Embed(title='Мафия победила!', description='\n'.join(
                                  [mafia.mention for mafia in await self.get_mafia(room, interaction)]),
                                  color=discord.Colour.red())
        else:
            return 0

        await channel.send(embed=embed)
        await asyncio.sleep(15)

        mafia_thread = interaction.guild.get_thread(room['mafia_id'])
        citizen_thread = interaction.guild.get_thread(room['room_id'])

        await mafia_thread.delete()
        await citizen_thread.delete()

        rooms.remove(room)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)

        return 1


def setup(bot):
    bot.add_cog(Game(bot))
