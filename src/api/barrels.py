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
    print(f"BARRELS - barrels_delievered: \n{barrels_delivered} \norder_id: {order_id}")

    num_red_ml = num_green_ml = num_blue_ml = num_dark_ml = gold = 0
    
    for barrel in barrels_delivered:
        if barrel.potion_type == [1, 0, 0, 0]:
            num_green_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 1, 0, 0]:
            num_red_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 1, 0]:
            num_blue_ml += barrel.ml_per_barrel * barrel.quantity
        elif barrel.potion_type == [0, 0, 0, 1]:
            num_dark_ml += barrel.ml_per_barrel * barrel.quantity

        gold -= barrel.price * barrel.quantity
        


    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("""
                                            INSERT INTO global_inventory (num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold)
                                            VALUES (:r_ml, :g_ml, :b_ml, :d_ml, :gold)
                                           """),
                            {"r_ml": num_red_ml, "b_ml": num_blue_ml, "g_ml": num_green_ml, "d_ml": num_dark_ml, "gold": gold})

    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print("BARRELS - wholesale_catalog = \n", wholesale_catalog)

    # Barrel output request list sent to Roxanne 
    output = []

    # retrieve all info from db
    with db.engine.begin() as connection:
        ml_result = connection.execute(sqlalchemy.text("""
                                                    SELECT num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, gold 
                                                    FROM global_inventory 
                                                    WHERE id = (SELECT MAX(id) FROM global_inventory)
                                                    """))
        num_red_ml, num_green_ml, num_blue_ml, num_dark_ml, num_gold = ml_result.fetchone()


        cap_result = connection.execute(sqlalchemy.text("""
                                                    SELECT ml_cap
                                                    FROM upgrades_inventory 
                                                    WHERE id = (SELECT MAX(id) FROM upgrades_inventory)
                                                    """))
        
        ml_cap = cap_result.fetchone()[0]

        panel_result = connection.execute(sqlalchemy.text("""
                                                          SELECT red_limit, green_limit, blue_limit, red_buy, green_buy, blue_buy, dark_buy
                                                          FROM panel_control
                                                          """))
        red_limit, green_limit, blue_limit, red_buy, green_buy, blue_buy, dark_buy = panel_result.fetchone()

    print(num_gold)
    #sum of all ml
    sum_ml = num_red_ml + num_green_ml + num_blue_ml + num_dark_ml
    

    # MAIN LOGIC: 
    

    # calculates the priority_list that each color ml needs to be bought based off of current color ml / color limit 
    # breaks ties with main priority list being [dark, green, red, blue]
            # dark is always first as its rare and most expensive so I should snatch that up first if I can afford/have space for it
    priority_list = {
        "green" : num_green_ml/green_limit,
        "red" : num_red_ml/red_limit,
        "blue" : num_blue_ml/blue_limit
    }

    sorted_colors = [key for key, value in sorted(priority_list.items(), key=lambda item: item[1])]
    sorted_colors.insert(0, "dark")

    # now I take the priority_list and look through the wanted_barrels lists to make purchases
    for color in sorted_colors:
            if color == "green":
                # filter from all barrels, the green ones I can afford
                green_barrels = [barrel for barrel in wholesale_catalog if barrel.potion_type == [0, 1, 0, 0] and barrel.price <= num_gold]
                if(green_barrels):
                    # select the most expensive one out of the filtered list 
                    max_green_barrel = max(green_barrels, key=lambda x: x.price)
                    # see if this barrel goes over the ml_cap
                    
                    if (max_green_barrel.ml_per_barrel + sum_ml) < ml_cap:
                        #TODO: change quantity from 1 to something more dynamic based on;
                            # what stage of the game im in (how much money I have)
                            # how much I'll make on them?
                        # set in db
                        quant_IwantBuy = green_buy
                        # total quantity I can buy (not regarding quantity sold)
                        quant_IcanBuy = num_gold / max_green_barrel.price
                        ml_space_avail = ml_cap - sum_ml
                        # total quantity I can fit into inventory
                        quant_IcanFit = ml_space_avail / max_green_barrel.ml_per_barrel
                        # minumum value between total being sold, total I can buy, and total I can fit in my inventory and the total I want to buy
                        quantity = min(quant_IcanBuy, quant_IcanFit, max_green_barrel.quantity, quant_IwantBuy)

                        sum_ml = sum_ml + (max_green_barrel.ml_per_barrel * quantity)
                        num_gold = num_gold - (max_green_barrel.price * quantity)
                        output.append(
                            {
                            "sku": max_green_barrel.sku,
                            "quantity": quantity,
                            }
                        )
                    #TODO: instead of just not buying the most expensive barrel I could see if the next smaller one would still go over the ml_cap?
                        # pros is that I would always be right up to the ml limit
                        # cons is that I would be losing money 
            
            if color == "red":
                red_barrels = [barrel for barrel in wholesale_catalog if barrel.potion_type == [1, 0, 0, 0] and barrel.price <= num_gold]
                if(red_barrels):
                    max_red_barrel = max(red_barrels, key=lambda x: x.price)
                    if (max_red_barrel.ml_per_barrel + sum_ml) < ml_cap:
            
                        quant_IwantBuy = red_buy
                        quant_IcanBuy = num_gold / max_red_barrel.price
                        ml_space_avail = ml_cap - sum_ml
                        quant_IcanFit = ml_space_avail / max_red_barrel.ml_per_barrel
                        quantity = min(quant_IcanBuy, quant_IcanFit, max_red_barrel.quantity, quant_IwantBuy)

                        sum_ml = sum_ml + (max_red_barrel.ml_per_barrel * quantity)
                        num_gold = num_gold - (max_red_barrel.price * quantity)
                        output.append(
                            {
                            "sku": max_red_barrel.sku,
                            "quantity": quantity,
                            }
                        )
            
            if color == "blue":
                blue_barrels = [barrel for barrel in wholesale_catalog if barrel.potion_type == [0, 0, 1, 0] and barrel.price <= num_gold]
                if(blue_barrels):
                    max_blue_barrel = max(blue_barrels, key=lambda x: x.price)
                    if (max_blue_barrel.ml_per_barrel + sum_ml) < ml_cap:
                        
                        quant_IwantBuy = blue_buy
                        quant_IcanBuy = num_gold / max_blue_barrel.price
                        ml_space_avail = ml_cap - sum_ml
                        quant_IcanFit = ml_space_avail / max_blue_barrel.ml_per_barrel
                        quantity = min(quant_IcanBuy, quant_IcanFit, max_blue_barrel.quantity, quant_IwantBuy)

                        sum_ml = sum_ml + (max_blue_barrel.ml_per_barrel * quantity)
                        num_gold = num_gold - (max_blue_barrel.price * quantity)
                        output.append(
                            {
                            "sku": max_blue_barrel.sku,
                            "quantity": quantity,
                            }
                        )

            if color == "dark":
                dark_barrels = [barrel for barrel in wholesale_catalog if barrel.potion_type == [0, 0, 0, 1] and barrel.price <= num_gold]
                if(dark_barrels):
                    max_dark_barrel = max(dark_barrels, key=lambda x: x.price)
                    if (max_dark_barrel.ml_per_barrel + sum_ml) < ml_cap:
                        
                        # there is an quant_IwantBuy for dark but its set insanley high
                        # the only reason I have it is so I can turn off money spending in the end game
                        quant_IwantBuy = dark_buy
                        quant_IcanBuy = num_gold / max_dark_barrel.price
                        ml_space_avail = ml_cap - sum_ml
                        quant_IcanFit = ml_space_avail / max_dark_barrel.ml_per_barrel
                        quantity = min(quant_IcanBuy, quant_IcanFit, max_dark_barrel.quantity, quant_IwantBuy)

                        sum_ml = sum_ml + (max_dark_barrel.ml_per_barrel * quantity)
                        num_gold = num_gold - (max_dark_barrel.price * quantity)
                        output.append(
                            {
                            "sku": max_dark_barrel.sku,
                            "quantity": quantity,
                            }
                        )

    print("BARRELS - requested barrels from Roxxane (output): \n", output)
    return output