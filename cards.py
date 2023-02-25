import random
import discord

def get_cards(players_quantity):
    match players_quantity:
        case 2:
            roles = ['Mafia', 'Citizen']
        case 3:
            roles = ['Mafia', 'Citizen', 'Mafia']
        case 4:
            roles = ['Mafia', 'Citizen', 'Citizen', 'Citizen']
        case 5:
            roles = ['Mafia', 'Citizen', 'Citizen', 'Citizen', 'Mafia']
        case 6:
            roles = ['Mafia', 'Citizen', 'Citizen', 'Citizen', 'Mafia', 'Sherif']
        case 7:
            roles = ['Mafia', 'Citizen', 'Citizen', 'Citizen', 'Mafia', 'Sherif', 'Mafia']

    random.shuffle(roles)

    return roles

def get_room(interaction, data):
    rooms = data[f'{interaction.guild.id}']['rooms']
    for room in rooms:
        if room['message_id'] == interaction.message.id:
            return rooms, room
