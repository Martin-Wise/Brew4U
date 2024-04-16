from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    for potion in potions_delivered:
        transfer_to_global_inventory(potion)

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        num_green_ml = result.fetchone()[0]
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        num_red_ml = result.fetchone()[0]
        result = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory"))
        num_blue_ml = result.fetchone()[0]

    output = []

    if num_green_ml > 100:
        quant_green = int(num_green_ml / 100)
        output.append(
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": quant_green
            }
        )

    if num_red_ml > 100:
        quant_red = int(num_red_ml / 100)
        output.append(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quant_red
            }
        )

    if num_blue_ml > 100:
        quant_blue = int(num_blue_ml / 100)
        output.append(
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": quant_blue
            })
    
    return output

if __name__ == "__main__":
    print(get_bottle_plan())

def get_num_potions(r, g, b, d):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num FROM potion_inventory WHERE R = {r} AND G = {g} AND B = {b} AND D = {d}"))
        num_potion = result.fetchone()
        if num_potion:
            return num_potion[0]
        else:   
            return 0

def get_ml(color):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num_{color}_ml FROM global_inventory"))
        num_color_ml = result.fetchone()[0]
        print(f"num_{color}_ml: ", num_color_ml)
        if num_color_ml > 0:
            return num_color_ml
        else:
            return 0  


def transfer_to_global_inventory(potion: PotionInventory):
    with db.engine.begin() as connection:
        
        current_num_green_ml = get_ml("green")
        current_num_red_ml = get_ml("red")
        current_num_blue_ml = get_ml("blue")
        
        pt = potion.potion_type
        current_num_potions = get_num_potions(pt[0], pt[1], pt[2], pt[3])

        quant = potion.quantity
        new_num_potions = current_num_potions + quant
        new_num_green_ml = current_num_green_ml - (pt[1] * quant)
        new_num_red_ml =  current_num_red_ml - (pt[0] * quant)
        new_num_blue_ml = current_num_blue_ml - (pt[2] * quant)
        #print("new_num_green_ml: ", new_num_green_ml)
        #print(100*potion.quantity)

        connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET num = {new_num_potions} WHERE r = {pt[0]} AND g = {pt[1]} AND b = {pt[2]} AND d = {pt[3]}"))
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_ml = {new_num_green_ml}, num_red_ml = {new_num_red_ml}, num_blue_ml = {new_num_blue_ml}"))