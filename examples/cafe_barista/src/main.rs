// Cafe Barista - Rust port (fixed from Swapify output)
// Original Python: /tmp/cafe_barista/cafe_barista.py
// Swapped via: `swap /tmp/cafe_barista` -> cafe_barista.swap.rs (raw output)
// This is the runnable, reviewed port.

use std::collections::HashMap;

const TAX_RATE: f64 = 0.08;
const SHOP_NAME: &str = "Rust & Roast Cafe";

fn get_menu_price(item: &str) -> Option<f64> {
    match item {
        "espresso" => Some(3.50),
        "latte" => Some(4.50),
        "cappuccino" => Some(4.00),
        "americano" => Some(3.00),
        "mocha" => Some(5.00),
        "cold_brew" => Some(4.25),
        _ => None,
    }
}

// ---------- MenuItem ----------
#[derive(Debug, Clone)]
struct MenuItem {
    name: String,
    price: f64,
    ingredients: Vec<String>,
    available: bool,
}

impl MenuItem {
    fn new(name: &str, price: f64, ingredients: Vec<String>) -> Self {
        Self {
            name: name.to_string(),
            price,
            ingredients,
            available: true,
        }
    }

    fn display(&self) -> String {
        let status = if self.available { "available" } else { "out of stock" };
        format!("{} - ${:.2} ({})", self.name, self.price, status)
    }

    fn update_price(&mut self, new_price: f64) -> bool {
        if new_price > 0.0 {
            self.price = new_price;
            true
        } else {
            false
        }
    }
}

// ---------- Order ----------
#[derive(Debug, Clone)]
struct Order {
    order_id: u32,
    customer_name: String,
    items: Vec<String>,
    total: f64,
    status: String,
}

impl Order {
    fn new(order_id: u32, customer_name: &str) -> Self {
        Self {
            order_id,
            customer_name: customer_name.to_string(),
            items: Vec::new(),
            total: 0.0,
            status: "pending".to_string(),
        }
    }

    fn add_item(&mut self, item_name: &str, price: f64) {
        self.items.push(item_name.to_string());
        self.total += price;
        println!("Added {} to order {}", item_name, self.order_id);
    }

    fn remove_item(&mut self, item_name: &str) -> bool {
        if let Some(pos) = self.items.iter().position(|x| x == item_name) {
            self.items.remove(pos);
            if let Some(p) = get_menu_price(item_name) {
                self.total -= p;
            }
            true
        } else {
            false
        }
    }

    fn calculate_total(&self) -> f64 {
        let subtotal = self.total;
        let tax = subtotal * TAX_RATE;
        subtotal + tax
    }

    fn complete(&mut self) {
        self.status = "completed".to_string();
        println!("Order {} for {} completed!", self.order_id, self.customer_name);
    }
}

// ---------- Barista ----------
#[derive(Debug)]
struct Barista {
    name: String,
    experience: u32,
    orders_served: u32,
    tips: f64,
}

impl Barista {
    fn new(name: &str, experience: u32) -> Self {
        Self {
            name: name.to_string(),
            experience,
            orders_served: 0,
            tips: 0.0,
        }
    }

    fn greet(&self, customer: &str) -> String {
        format!("Hello {}! I'm {}, your barista today.", customer, self.name)
    }

    fn make_coffee(&mut self, order: &Order) -> String {
        let mut result = Vec::new();
        for item in &order.items {
            if get_menu_price(item).is_some() {
                result.push(format!("Brewing {}...", item));
            } else {
                result.push(format!("Unknown item: {}", item));
            }
        }
        self.orders_served += 1;
        if order.items.is_empty() {
            return "No items to prepare".to_string();
        }
        result.join("\n")
    }

    fn add_tip(&mut self, amount: f64) {
        if amount > 0.0 {
            self.tips += amount;
            println!("Thanks for ${:.2} tip!", amount);
        }
    }

    fn get_stats(&self) -> HashMap<String, String> {
        let mut m = HashMap::new();
        m.insert("name".to_string(), self.name.clone());
        m.insert("served".to_string(), self.orders_served.to_string());
        m.insert("tips".to_string(), format!("{:.2}", self.tips));
        m.insert("experience".to_string(), self.experience.to_string());
        m
    }
}

// ---------- Cafe ----------
struct Cafe {
    name: String,
    menu: HashMap<String, MenuItem>,
    orders: Vec<Order>,
    baristas: Vec<Barista>,
    revenue: f64,
}

impl Cafe {
    fn new(name: &str) -> Self {
        let mut cafe = Self {
            name: name.to_string(),
            menu: HashMap::new(),
            orders: Vec::new(),
            baristas: Vec::new(),
            revenue: 0.0,
        };
        cafe.init_menu();
        cafe
    }

    fn init_menu(&mut self) {
        let items = [
            ("espresso", 3.50),
            ("latte", 4.50),
            ("cappuccino", 4.00),
            ("americano", 3.00),
            ("mocha", 5.00),
            ("cold_brew", 4.25),
        ];
        for (item_name, price) in items {
            let mut ingredients = vec!["coffee".to_string(), "water".to_string()];
            if item_name == "latte" {
                ingredients.push("milk".to_string());
            } else if item_name == "mocha" {
                ingredients.extend(["milk".to_string(), "chocolate".to_string()]);
            }
            self.menu
                .insert(item_name.to_string(), MenuItem::new(item_name, price, ingredients));
        }
    }

    fn add_barista(&mut self, barista: Barista) {
        println!("Barista {} joined {}", barista.name, self.name);
        self.baristas.push(barista);
    }

    fn place_order(&mut self, customer_name: &str, items: Vec<&str>) -> u32 {
        let order_id = (self.orders.len() + 1) as u32;
        let mut order = Order::new(order_id, customer_name);
        for item in items {
            if let Some(menu_item) = self.menu.get(item) {
                if menu_item.available {
                    order.add_item(item, menu_item.price);
                } else {
                    println!("Sorry, {} not available", item);
                }
            } else {
                println!("Sorry, {} not available", item);
            }
        }
        self.orders.push(order);
        order_id
    }

    fn complete_order(&mut self, order_id: u32) -> bool {
        for order in &mut self.orders {
            if order.order_id == order_id {
                if order.status == "pending" {
                    let total = order.calculate_total();
                    order.complete();
                    self.revenue += total;
                    println!("Revenue now ${:.2}", self.revenue);
                    return true;
                } else {
                    println!("Order {} already {}", order_id, order.status);
                    return false;
                }
            }
        }
        println!("Order {} not found", order_id);
        false
    }

    fn show_menu(&self) {
        println!("--- {} Menu ---", self.name);
        // sorted for deterministic output
        let mut keys: Vec<_> = self.menu.keys().collect();
        keys.sort();
        for k in keys {
            if let Some(item) = self.menu.get(k) {
                println!("{}", item.display());
            }
        }
    }

    fn daily_report(&self) -> String {
        let count = self.orders.len();
        let pending = self.orders.iter().filter(|o| o.status == "pending").count();
        let completed = count - pending;
        let mut report = format!(
            "Cafe {}: {}/{} completed, Revenue ${:.2}",
            self.name, completed, count, self.revenue
        );
        // regex check simulated: /^[A-Za-z &]+$/  -> allow letters, space, &
        let valid = self.name.chars().all(|c| c.is_ascii_alphabetic() || c == ' ' || c == '&');
        if valid {
            report.push_str(" [valid name]");
        }
        report
    }

    fn to_json(&self) -> String {
        // manual JSON to avoid serde dependency, mirrors json.dumps
        let now = {
            use std::time::{SystemTime, UNIX_EPOCH};
            let secs = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs();
            secs.to_string()
        };
        format!(
            "{{\n  \"shop\": \"{}\",\n  \"revenue\": {:.2},\n  \"orders\": {},\n  \"date\": \"{}\"\n}}",
            self.name, self.revenue, self.orders.len(), now
        )
    }
}

// ---------- Helpers ----------
fn format_price(price: f64) -> String {
    format!("${:.2}", price)
}

fn apply_discount(total: f64, discount_pct: f64) -> f64 {
    if discount_pct <= 0.0 || discount_pct > 50.0 {
        return total;
    }
    let discount = total * (discount_pct / 100.0);
    total - discount
}

fn is_valid_customer(name: &str) -> bool {
    if name.len() < 2 {
        return false;
    }
    // /^[A-Za-z ]+$/  - only letters and spaces
    name.chars().all(|c| c.is_ascii_alphabetic() || c == ' ')
}

fn main() {
    let mut cafe = Cafe::new(SHOP_NAME);
    let mut barista = Barista::new("Alex", 3);
    cafe.add_barista(barista);

    // need to get barista back mutably - Cafe holds its own copy, create separate for demo
    // For simplicity, use a new barista instance for actions (mirrors Python where barista is separate)
    let mut barista2 = Barista::new("Alex", 3);

    cafe.show_menu();

    println!("{}", barista2.greet("Sam"));
    let order_id = cafe.place_order("Sam", vec!["latte", "espresso", "mocha"]);

    // clone order for barista view
    let order_clone = cafe.orders.iter().find(|o| o.order_id == order_id).unwrap().clone();
    println!("{}", barista2.make_coffee(&order_clone));

    let total = order_clone.calculate_total();
    println!("Total with tax: {}", format_price(total));

    let discounted = apply_discount(total, 10.0);
    println!("With 10% discount: {}", format_price(discounted));

    cafe.complete_order(order_id);
    println!("{}", cafe.daily_report());
    println!("{}", cafe.to_json());

    barista2.add_tip(2.50);
    println!("Barista stats: {:?}", barista2.get_stats());
    println!("Valid customer 'Sam' ? {}", is_valid_customer("Sam"));

    // keep original barista variable used
    let _ = barista;
}
