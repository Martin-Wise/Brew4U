from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    num_red_potions = get_num_potions(100, 0, 0, 0)
    num_green_potions = get_num_potions(0, 100, 0, 0)
    num_blue_potions = get_num_potions(0, 0, 100, 0)
    num_purple_potions = get_num_potions(50, 0, 50, 0)


    output = []

    if (num_red_potions > 0):
        output.append(
            {
                "sku": "RED_POTION",
                "name": "Red Potion",
                "quantity": num_red_potions,
                "price": 55,
                "potion_type": [100, 0, 0, 0],
            })
    if (num_green_potions > 0):
        output.append(
            {
                "sku": "GREEN_POTION",
                "name": "Green Potion",
                "quantity": num_green_potions,
                "price": 55,
                "potion_type": [0, 100, 0, 0],
            })
    if (num_blue_potions > 0):
        output.append(
            {
                "sku": "BLUE_POTION",
                "name": "Blue Potion",
                "quantity": num_green_potions,
                "price": 60,
                "potion_type": [0, 0, 100, 0],
            })
    if (num_purple_potions > 0):
        output.append(
            {
                "sku": "PURPLE_POTION",
                "name": "Full Regen Potion",
                "quantity": num_purple_potions,
                "price": 75,
                "potion_type": [50, 0, 50, 0],
            })

    return output

def get_num_potions(r, g, b, d):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num FROM potion_inventory WHERE R = {r} AND G = {g} AND B = {b} AND D = {d}"))
        num_potion = result.fetchone()
        if num_potion:
            return num_potion[0]
        else:   
            return 0

