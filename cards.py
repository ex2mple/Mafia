import random


class Role:
    def __init__(self, quantity):
        self.quantity = quantity


class Mafia(Role):
    pass


class Citizen(Role):
    pass


class Sherif(Role):
    pass


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

