"""
Cafe Barista - Python coffee shop simulator
"""
import json
import datetime
import re
import collections
from typing import List, Dict

MENU = {
    "espresso": 3.50,
    "latte": 4.50,
    "cappuccino": 4.00,
    "americano": 3.00,
    "mocha": 5.00,
    "cold_brew": 4.25
}

TAX_RATE = 0.08
SHOP_NAME = "Rust & Roast Cafe"

class MenuItem:
    def __init__(self, name: str, price: float, ingredients: List[str]):
        self.name = name
        self.price = price
        self.ingredients = ingredients
        self.available = True

    def display(self) -> str:
        status = "available" if self.available else "out of stock"
        return f"{self.name} - ${self.price:.2f} ({status})"

    def update_price(self, new_price: float) -> bool:
        if new_price > 0:
            self.price = new_price
            return True
        return False

class Order:
    def __init__(self, order_id: int, customer_name: str):
        self.order_id = order_id
        self.customer_name = customer_name
        self.items: List[str] = []
        self.total: float = 0.0
        self.status = "pending"

    def add_item(self, item_name: str, price: float):
        self.items.append(item_name)
        self.total += price
        print(f"Added {item_name} to order {self.order_id}")

    def remove_item(self, item_name: str) -> bool:
        if item_name in self.items:
            self.items.remove(item_name)
            self.total -= MENU.get(item_name, 0)
            return True
        return False

    def calculate_total(self) -> float:
        subtotal = self.total
        tax = subtotal * TAX_RATE
        return subtotal + tax

    def complete(self):
        self.status = "completed"
        print(f"Order {self.order_id} for {self.customer_name} completed!")

class Barista:
    def __init__(self, name: str, experience: int):
        self.name = name
        self.experience = experience
        self.orders_served = 0
        self.tips: float = 0.0

    def greet(self, customer: str) -> str:
        return f"Hello {customer}! I'm {self.name}, your barista today."

    def make_coffee(self, order: Order) -> str:
        result = []
        for item in order.items:
            if item in MENU:
                result.append(f"Brewing {item}...")
            else:
                result.append(f"Unknown item: {item}")
        self.orders_served += 1
        if len(order.items) == 0:
            return "No items to prepare"
        return "\n".join(result)

    def add_tip(self, amount: float):
        if amount > 0:
            self.tips += amount
            print(f"Thanks for ${amount:.2f} tip!")

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "served": self.orders_served,
            "tips": self.tips,
            "experience": self.experience
        }

class Cafe:
    def __init__(self, name: str):
        self.name = name
        self.menu: Dict[str, MenuItem] = {}
        self.orders: List[Order] = []
        self.baristas: List[Barista] = []
        self.revenue: float = 0.0
        self._init_menu()

    def _init_menu(self):
        for item_name, price in MENU.items():
            ingredients = ["coffee", "water"]
            if item_name == "latte":
                ingredients.append("milk")
            elif item_name == "mocha":
                ingredients.extend(["milk", "chocolate"])
            self.menu[item_name] = MenuItem(item_name, price, ingredients)

    def add_barista(self, barista: Barista):
        self.baristas.append(barista)
        print(f"Barista {barista.name} joined {self.name}")

    def place_order(self, customer_name: str, items: List[str]) -> Order:
        order_id = len(self.orders) + 1
        order = Order(order_id, customer_name)
        for item in items:
            if item in self.menu and self.menu[item].available:
                order.add_item(item, self.menu[item].price)
            else:
                print(f"Sorry, {item} not available")
        self.orders.append(order)
        return order

    def complete_order(self, order_id: int) -> bool:
        for order in self.orders:
            if order.order_id == order_id:
                if order.status == "pending":
                    order.complete()
                    total = order.calculate_total()
                    self.revenue += total
                    print(f"Revenue now ${self.revenue:.2f}")
                    return True
                else:
                    print(f"Order {order_id} already {order.status}")
                    return False
        print(f"Order {order_id} not found")
        return False

    def show_menu(self):
        print(f"--- {self.name} Menu ---")
        for name, item in self.menu.items():
            print(item.display())

    def daily_report(self) -> str:
        count = len(self.orders)
        pending = 0
        for o in self.orders:
            if o.status == "pending":
                pending += 1
        completed = count - pending
        report = f"Cafe {self.name}: {completed}/{count} completed, Revenue ${self.revenue:.2f}"
        # validate shop name with regex
        if re.match(r"^[A-Za-z &]+$", self.name):
            report += " [valid name]"
        return report

    def to_json(self) -> str:
        data = collections.OrderedDict()
        data["shop"] = self.name
        data["revenue"] = self.revenue
        data["orders"] = len(self.orders)
        data["date"] = str(datetime.datetime.now())
        return json.dumps(data, indent=2)


def format_price(price: float) -> str:
    return f"${price:.2f}"

def apply_discount(total: float, discount_pct: float) -> float:
    if discount_pct <= 0 or discount_pct > 50:
        return total
    discount = total * (discount_pct / 100)
    return total - discount

def is_valid_customer(name: str) -> bool:
    if len(name) < 2:
        return False
    if not re.match(r"^[A-Za-z ]+$", name):
        return False
    return True

def main():
    cafe = Cafe(SHOP_NAME)
    barista = Barista("Alex", 3)
    cafe.add_barista(barista)

    cafe.show_menu()

    print(barista.greet("Sam"))
    order = cafe.place_order("Sam", ["latte", "espresso", "mocha"])
    print(barista.make_coffee(order))

    total = order.calculate_total()
    print(f"Total with tax: {format_price(total)}")

    discounted = apply_discount(total, 10)
    print(f"With 10% discount: {format_price(discounted)}")

    cafe.complete_order(order.order_id)
    print(cafe.daily_report())
    print(cafe.to_json())

    barista.add_tip(2.50)
    print(f"Barista stats: {barista.get_stats()}")

if __name__ == "__main__":
    main()
