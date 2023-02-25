import asyncio
import random
from pprint import pprint
import discord
import json
import cards



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
                        value='Игроки получают свои роли (см. личные сообщения).\n'
                              'Игра разделенная на 2 части: "день" и "ночь"\n'
                              'В первую ночь ничего не происходит. Мафия может наметить себе "жертву".\n'
                              'Днем все игроки обсуждают кто может быть Мафиози и голосуют за них. Мафия в свою очередь пытается доказать свою невиновность.\n'
                              'Если голоса распределились поровну, никто не выбывает.\n'
                              'Игра продолжается до полной победы одной из команд, когда соперники полностью или посажены или убиты.')

        await ctx.respond(embed=embed)


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

        rooms = data[f'{interaction.guild.id}']['rooms']
        for room in rooms:
            if room['message_id'] == interaction.message.id:
                your_room = room

        roles = cards.get_cards(len(your_room['players']))
        mafia_thread = interaction.guild.get_thread(your_room['mafia_id'])

        for player in your_room['players_roles']:
            choice = random.choice(roles)
            if choice == 'Mafia':
                your_room['mafia_count'] += 1
            if choice in self.game_roles:
                your_room['citizen_count'] += 1

            player['role'] = f'{choice}'
            roles.remove(choice)

        for player in your_room['players_roles']:
            player1 = interaction.guild.get_member(player["id"])

            embed = discord.Embed(title='Инфо', description=f'Ваша роль - {player["role"]}')
            embed.color = discord.Colour.green()

            if player['role'] == 'Mafia':
                embed.add_field(name='Мафиози этой игры: ', value='\n'.join(
                                  [mafia.mention for mafia in await self.get_mafia(your_room, interaction)]))
                embed.color = discord.Colour.red()

                await mafia_thread.add_user(player1) # add mafia player in other thread

            # await player1.send(embed=embed) # send private message with player's role

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)

        await self.night(interaction)

    async def day(self, interaction):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms = data[f'{interaction.guild.id}']['rooms']
        for room in rooms:
            if room['message_id'] == interaction.message.id:
                your_room = room


    async def night(self, interaction):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms = data[f'{interaction.guild.id}']['rooms']
        for room in rooms:
            if room['message_id'] == interaction.message.id:
                your_room = room

        channel = interaction.guild.get_thread(your_room['room_id'])
        mafia_channel = interaction.guild.get_thread(your_room['mafia_id'])
        await channel.send('Город засыпает - просыпается мафия!')
        await mafia_channel.send('И снова ночь на дворе! Кто станет следующей жертвой? Выбор за вами!')

        players = [player.mention for player in await self.get_players(your_room, interaction)]
        emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️', '🔟']
        embed = discord.Embed(title='Голосование за жертву',
                              description='Просто нажмите на реакцию с нужным номером',
                              color=discord.Colour.red())
        embed.add_field(name='Жертвы', value='\n'.join(map(lambda x: f"{x[0]} {x[1]}", list(zip(emoji, players)))))

        # await asyncio.sleep(20) # 20 seconds to think
        vote_message = await mafia_channel.send(embed=embed)

        for i in range(len(players)):
            await vote_message.add_reaction(emoji[i])

        await asyncio.sleep(10) # 10 seconds to vote

        await self.vote(interaction, vote_message)


    async def vote(self, interaction, vote_message):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms = data[f'{interaction.guild.id}']['rooms']
        for room in rooms:
            if room['message_id'] == interaction.message.id:
                your_room = room

        vote_message = self.bot.get_message(vote_message.id)
        channel = interaction.guild.get_thread(your_room['room_id'])

        players = [player.id for player in await self.get_players(your_room, interaction)]
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
                for player in your_room['players_roles']:
                    if player['id'] == result[1]:
                        role = player['role']
                        id = player['id']
                        your_room['players_roles'].remove(player)

        if role == 'Mafia':
            your_room['mafia_count'] -= 1
        elif role in self.game_roles:
            your_room['citizen_count'] -= 1

        embed = discord.Embed(title='Итог',
                              description=f'Был убит: {interaction.guild.get_member(id).mention}',
                              color=discord.Colour.red() if role != 'Mafia' else discord.Colour.green())
        embed.add_field(name='Его роль', value=role)
        embed.add_field(name='Мафиози осталось', value=f'{your_room["mafia_count"]}',
                        inline=False)

        await channel.send(embed=embed)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)

        await self.check_win(interaction)


    async def check_win(self, interaction):
        with open('db.json', 'r', encoding='UTF-8') as file:
            data = json.load(file)

        rooms = data[f'{interaction.guild.id}']['rooms']
        for room in rooms:
            if room['message_id'] == interaction.message.id:
                your_room = room

        channel = interaction.guild.get_thread(your_room['room_id'])

        if your_room['mafia_count'] == 0:
            embed = discord.Embed(title='Мирные жители победили!', color=discord.Colour.green())
        elif your_room['citizen_count'] == 0:
            embed = discord.Embed(title='Мафия победила!', color=discord.Colour.red())
        else:
            return

        await channel.send(embed=embed)
        await asyncio.sleep(15)

        mafia_thread = interaction.guild.get_thread(your_room['mafia_id'])
        citizen_thread = interaction.guild.get_thread(your_room['room_id'])

        await mafia_thread.delete()
        await citizen_thread.delete()

        rooms.remove(your_room)

        with open('db.json', 'w', encoding='UTF-8') as file:
            json.dump(data, file, indent=4)


    @discord.slash_command()
    async def test_react(self, ctx):
        msg = await ctx.send('Test message')
        msg = self.bot.get_message(msg.id)
        await msg.add_reaction('😀')
        await asyncio.sleep(1)
        print(msg.reactions)


def setup(bot):
    bot.add_cog(Game(bot))
