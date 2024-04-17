from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    for barrel in barrels_delivered:
        transfer_to_global_inventory(barrel)

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    output = []

    bought_green = False
    bought_blue = False
    bought_red = False

    num_green_potions = get_num_potions(0, 100, 0, 0)
    num_red_potions = get_num_potions(100, 0, 0, 0)
    num_blue_potions = get_num_potions(0, 0, 100, 0)
    num_gold = get_gold()

    print("num_green_potions", num_green_potions)
    print("num_blue_potions", num_blue_potions)
    print("num_green_poitons", num_green_potions)

    if num_green_potions < 5:
        for barrel in wholesale_catalog:
            if not bought_green and barrel.sku == "SMALL_GREEN_BARREL" and barrel.quantity > 0 and num_gold >= barrel.price:
                bought_green = True
                num_gold -= barrel.price
                output.append(
                    {
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                )

    if num_red_potions < 5:
        for barrel in wholesale_catalog:
            if not bought_red and barrel.sku == "SMALL_RED_BARREL" and barrel.quantity > 0 and num_gold >= barrel.price:
                bought_red = True
                num_gold -= barrel.price
                output.append(
                    {
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                ) 

    if num_blue_potions < 5:
        for barrel in wholesale_catalog:
            if not bought_blue and barrel.sku == "SMALL_BLUE_BARREL" and barrel.quantity > 0 and num_gold >= barrel.price:
                bought_blue = True
                num_gold -= barrel.price
                output.append(
                    {
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                )

      

    print(output)
    return output

def get_num_potions(r, g, b, d):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(f"SELECT num FROM potion_inventory WHERE R = {r} AND G = {g} AND B = {b} AND D = {d}"))
        num_potion = result.fetchone()
        if num_potion:
            return num_potion[0]
        else:   
            return 0


def get_gold():
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        num_gold = result.fetchone()[0]
        print("num_gold: ", num_gold)
        if num_gold > 0:
            return num_gold
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

def transfer_to_global_inventory(barrel: Barrel):
    with db.engine.begin() as connection:
        color = barrel_color(barrel)
        current_gold = get_gold()
        current_ml = get_ml(color)

        new_gold_ammount = current_gold - barrel.price
        new_num_ml = current_ml + barrel.ml_per_barrel

        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {new_gold_ammount}, num_{color}_ml = {new_num_ml}"))
        
def barrel_color(barrel: Barrel):
    print("barrel.potion_type: ", barrel.potion_type)
    if(barrel.potion_type[0] == 1): return "red"
    elif(barrel.potion_type[1] == 1): return "green"
    elif(barrel.potion_type[2] == 1): return "blue"
    else: return "dark" 


