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

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml FROM global_inventory"))
        num_red_ml, num_green_ml, num_blue_ml, num_dark_ml = result.fetchone()

        
        

    output = []

    if num_red_ml >= 100 and num_blue_ml >= 100:
        num_red_ml = num_red_ml - 100
        num_blue_ml = num_blue_ml - 100
        output.append(
            {
                "potion_type": [50, 0, 50, 0],
                "quantity": 2
            }
        )

    if num_red_ml >= 100:
        quant_red = int(num_red_ml / 100)
        output.append(
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": quant_red
            }
        )
    
    if num_green_ml >= 100:
        quant_green = int(num_green_ml / 100)
        output.append(
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": quant_green
            }
        )

    if num_blue_ml >= 100:
        quant_blue = int(num_blue_ml / 100)
        output.append(
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": quant_blue
            })
        
    if num_dark_ml >= 100:
        quant_dark = int(num_dark_ml / 100)
        output.append(
            {
                "potion_type": [0, 0, 0, 100],
                "quantity": quant_dark
            })
    
    print("BOTTLER PLAN: ", output)
    return output

if __name__ == "__main__":
    print(get_bottle_plan())

def get_num_potions(r, g, b, d):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num FROM potion_inventory WHERE R = {r} AND G = {g} AND B = {b} AND D = {d}"))
        num_potion = result.fetchone()
        if num_potion:
            return num_potion
        else:   
            return 0

def get_ml(color):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num_{color}_ml FROM global_inventory"))
        num_color_ml = result.fetchone()[0]
        print(f"num_{color}_ml: ", num_color_ml)
        if num_color_ml:
            return num_color_ml
        else:
            return 0  


def transfer_to_global_inventory(potion: PotionInventory):

    r, g, b, d = potion.potion_type
    quant = potion.quantity

    used_red =   r * quant
    used_green = g * quant
    used_blue =  b * quant
    used_dark =  d * quant
    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET num = num + :quant WHERE r = :r AND g = :g AND b = :b AND d = :d"),
                           {"quant": quant, "r": r, "g": g, "b": b, "d": d})
        if result.rowcount == 0:
          connection.execute(sqlalchemy.text("INSERT INTO potion_inventory (r, g, b, d, num) VALUES (:r, :g, :b, :d, :num)"), 
                             {"num": quant, "r": r, "g": g, "b": b, "d": d})

        connection.execute(sqlalchemy.text("""UPDATE global_inventory SET num_red_ml = num_red_ml - :used_red, 
                                                                         num_green_ml = num_green_ml - :used_green, 
                                                                         num_blue_ml = num_blue_ml - :used_blue,
                                                                         num_dark_ml = num_dark_ml - :used_dark"""),
                           { "used_red": used_red, "used_green": used_green, "used_blue": used_blue, "used_dark": used_dark})



