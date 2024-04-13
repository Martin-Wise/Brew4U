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

    num_green_potions = get_num_green_potions()
    num_gold = get_gold()
    if num_green_potions < 10:
        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL" and barrel.quantity > 0 and num_gold > barrel.price:
                return [
                    {
                        "sku": barrel.sku,
                        "quantity": 1,
                    }
                ]
            else:
                return []

def get_num_green_potions():
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        num_green_potions = result.fetchone()[0]
        if num_green_potions > 0:
            return num_green_potions
        else:
            return 0

def get_gold():
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
        num_gold = result.fetchone()[0]
        if num_gold > 0:
            return num_gold
        else:
            return 0

def transfer_to_global_inventory(barrel: Barrel):
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT gold, num_green_ml"))
        current_data = result.fetchone()
        
        current_gold = current_data['gold']
        current_num_green_ml = current_data['num_green_ml']

        new_gold_ammount = current_gold - barrel.price
        new_num_green_ml = current_num_green_ml + barrel.ml_per_barrel

        update_query = sqlalchemy.text(
            """
            UPDATE global_inventory
            SET gold = :new_gold_amount,
                num_green_ml = :new_num_green_ml
            """
        )

        update_params = {
            'new_gold_amount': new_gold_ammount,
            'new_num_green_ml': new_num_green_ml
        }
        connection.execute(update_query, **update_params)


