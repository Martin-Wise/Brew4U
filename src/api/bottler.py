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
        result = connection.execute("SELECT num_green_ml FROM global_inventory ORDER BY created_at DESC LIMIT 1")
    
    num_green_ml = result.fetchone()

    if num_green_ml > 100:
        quant_green : int = num_green_ml / 100
        return [
            {
                "potion_type": [0, 0, 100, 0],
                "quantity": quant_green
            }
        ]

    else :
        return []

if __name__ == "__main__":
    print(get_bottle_plan())

def transfer_to_global_inventory(potions: PotionInventory):
    with db.engine.begin() as connection:
        result = connection.execute("SELECT num_green_potions, num_green_ml FROM global_inventory ORDER BY created_at DESC LIMIT 1")
        current_data = result.fetchone()
        
        current_num_green_potions = current_data['num_green_potions']
        current_num_green_ml = current_data['num_green_ml']

        new_num_green_potions = current_num_green_potions + potions.quantity
        new_num_green_ml = current_num_green_ml - (100 * potions.quantity)

        update_query = sqlalchemy.text(
            """
            UPDATE global_inventory
            SET num_green_potions = :new_num_green_potions,
                num_green_ml = :new_num_green_ml
            """
        )

        update_params = {
            'new_num_green_potions': new_num_green_potions,
            'new_num_green_ml': new_num_green_ml
        }
        connection.execute(update_query, **update_params)
