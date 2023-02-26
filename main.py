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

cogs_list = ['create_room', 'game']
for cog in cogs_list:
    bot.load_extension(f'{cog}')


if __name__ == '__main__':
    bot.run(token)