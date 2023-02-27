import discord
import json
from discord.ext import commands

token = 'MTA3NTcyNDYzNTU5NDgzMzkyMA.Gxn5GY.2zyG1zGsYPCJEMLSbagrzqej8rgTecoLwT6lQU'
intents = discord.Intents.all()
bot = discord.Bot(debug_guilds=[921377212500967444, 771736345437274132, 1079115208032784444], intents=intents)


@bot.event
async def on_ready():
    # with open('db.json', 'r', encoding='UTF-8') as file:
    #     data = json.load(file)

    print('---Bot is ready!---')


@bot.event
async def on_guild_join(guild: discord.Guild):
    with open('db.json', 'r', encoding='UTF-8') as file:
        data = json.load(file)

    # mafia = await guild.create_role(name='Citizen')
    # citizen = await guild.create_role(name='Citizen')

    data[f'{guild.id}'] = {'info': {
            'name': guild.name, 'created_at': f"{guild.created_at}"
        },
        'rooms': []
    }


    with open('db.json', 'w', encoding='UTF-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

@bot.event
async def on_guild_remove(guild: discord.Guild):
    with open('db.json', 'r', encoding='UTF-8') as file:
        data: dict = json.load(file)

    del data[f'{guild.id}']

    with open('db.json', 'w', encoding='UTF-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


@bot.slash_command()
@commands.is_owner()
async def test_join(ctx):
    guild = ctx.guild

    with open('db.json', 'r', encoding='UTF-8') as file:
        data = json.load(file)
    #
    # mafia = await guild.create_role(name='Citizen')
    # citizen = await guild.create_role(name='Citizen')

    data[f'{guild.id}'] = {'info': {
        'name': guild.name, 'created_at': f"{guild.created_at}"
    },
        'rooms': []
    }

    with open('db.json', 'w', encoding='UTF-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


@bot.slash_command()
@commands.is_owner()
async def reload_ext(ctx):
    cogs_list = ['create_room']
    for cog in cogs_list:
        bot.reload_extension(f'{cog}')
    print('Extensions have been successfully reloaded!')



@bot.slash_command()
async def rules(ctx):
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

cogs_list = ['create_room']
for cog in cogs_list:
    bot.load_extension(f'{cog}')


if __name__ == '__main__':
    bot.run(token)