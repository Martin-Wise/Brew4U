from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int


cart = {}

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """

    day = "blank"
    hour = 10
    with db.engine.begin() as connection:
        
        result = connection.execute(sqlalchemy.text("SELECT day, hour FROM days WHERE id = (SELECT MAX(id) FROM days)"))
        day, hour = result.fetchone() 
        
        for c in customers:
            connection.execute(sqlalchemy.text(f"INSERT INTO customers_info (visit_id, day, hour, cart_id, name, class, level) VALUES ({visit_id}, '{day}', {hour}, 0, '{c.customer_name}', '{c.character_class}', {c.level})"))
    

    print(customers)

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    #cart_id = len(cart) + 1
    #cart[cart_id] = []
    name = new_cart.customer_name

    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_name) VALUES (:cust_name) RETURNING cart_id"), {"cust_name": name}) 
        cart_id = result.scalar()
        connection.execute(sqlalchemy.text("UPDATE customers_info SET cart_id = :cart_id WHERE customers_info.name = :cust_name"), {"cart_id": cart_id, "cust_name": name})
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int



@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """

    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text("INSERT INTO cart_items (cart_id, sku, quantity) VALUES (:cart_id, :sku, :quantity)"), 
                           {"cart_id": cart_id, "sku": item_sku, "quantity": cart_item.quantity})
   
    return "OK"


class CartCheckout(BaseModel):
    payment: str

class CartItem(BaseModel):
        sku: str
        quantity: int

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """


    total_gold_paid = 0
    total_potions_bought = 0
    
    #get all items in cart
    with db.engine.begin() as connection:
        result1 = connection.execute(sqlalchemy.text("SELECT sku, quantity FROM cart_items WHERE cart_id = :cart_id"), {"cart_id": cart_id})
        for sku, quantity in result1:
            #lookup sku in catalog
            result2 = connection.execute(sqlalchemy.text("SELECT price, potion_id FROM catalog WHERE sku = :sku"), {"sku": sku})
            price, potion_id = result2.fetchone()
            #calculate total potions bought and total_gold_paid
            total_gold_paid += price * quantity
            total_potions_bought += quantity
            #decrement potion amount in potion_inventory by quantity
            r, g, b, d = map(int, potion_id.split("."))
            connection.execute(sqlalchemy.text("UPDATE potion_inventory SET num = num - :quantity WHERE r = :r AND g = :g AND b = :b AND d = :d"),
                                {"quantity": quantity, "r": r, "g": g, "b": b, "d": d})
        #add gold to inv
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = gold + :total_gold_paid"), {"total_gold_paid": total_gold_paid})
    
    print(f"PURCHASE MADE: cart_id = {cart_id}, gold_earned: {total_gold_paid}, total_potions_bought: {total_potions_bought}")

    return {
        "total_potions_bought": total_potions_bought, 
        "total_gold_paid": total_gold_paid
    }
            

            

    
        
    

    
    
    
    
    
    for curItem in cart[cart_id]:
        cartSum += (curItem.price * curItem.quantity)
        r = curItem.potion_type[0]
        g = curItem.potion_type[1]
        b = curItem.potion_type[2]
        d = 0
        new_num_potions = get_num_potions(r, g, b, d) - curItem.quantity
        with db.engine.begin() as connection:
                    connection.execute(sqlalchemy.text(f"UPDATE potion_inventory SET num = {new_num_potions} WHERE r = {r} AND g = {g} AND b = {b} AND d = {d}"))

        total_potions_bought += curItem.quantity
    
    new_gold_ammount += cartSum
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET gold = {new_gold_ammount}"))
    
    return {
        "total_potions_bought": total_potions_bought, 
        "total_gold_paid": cartSum
    }
        
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

