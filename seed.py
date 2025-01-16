from pymongo import MongoClient
from uuid import uuid4
import os
from dotenv import load_dotenv
from datetime import datetime
import bcrypt

# Load environment variables
load_dotenv()

# MongoDB setup
mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb+srv://dharani96556:Dharani2002@thegreenvy.a7dsi.mongodb.net/"))
db = mongo_client['eco_friendly_ecommerce']
products_collection = db['products']
users_collection = db['users']
orders_collection = db['orders']
sellers_collection = db['sellers']

# Dummy data
products_data = [
    {
        "name": "Eco-friendly Bamboo Toothbrush",
        "description": "A toothbrush made from sustainable bamboo with soft bristles.",
        "category": "featured",
        "short_note": "Best Seller",
        "brand": "EcoBrush",
        "price": 3.99,
        "overall_rating": 4.7,
        "images": ["https://via.placeholder.com/150"],
        "stock": 100,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Reusable Grocery Bags",
        "description": "Set of 5 reusable grocery bags made from recycled materials.",
        "category": "groceries",
        "short_note": "New Arrival",
        "brand": "GreenBag",
        "price": 12.99,
        "overall_rating": 4.5,
        "images": ["https://via.placeholder.com/150"],
        "stock": 200,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    },
    {
        "name": "Organic Cotton T-Shirt",
        "description": "Comfortable t-shirt made from 100% organic cotton.",
        "category": "eco-friendly",
        "brand": "EcoWear",
        "price": 19.99,
        "overall_rating": 4.8,
        "images": ["https://via.placeholder.com/150"],
        "stock": 150,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Stainless Steel Water Bottle",
        "description": "Durable and reusable water bottle made from stainless steel.",
        "category": "eco-friendly",
        "short_note": "Best Seller",
        "brand": "HydroLife",
        "price": 24.99,
        "overall_rating": 4.9,
        "images": ["https://via.placeholder.com/150"],
        "stock": 250,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    },
    {
        "name": "Biodegradable Trash Bags",
        "description": "Eco-friendly trash bags that are fully biodegradable.",
        "category": "eco-friendly",
        "brand": "GreenTrash",
        "price": 8.99,
        "overall_rating": 4.6,
        "images": ["https://via.placeholder.com/150"],
        "stock": 300,
        "seller_id": "seller3",
        "product_id": str(uuid4())
    },
    {
        "name": "Solar Powered Charger",
        "description": "Portable solar charger for your electronic devices.",
        "category": "eco-friendly",
        "brand": "SolarTech",
        "price": 49.99,
        "overall_rating": 4.7,
        "images": ["https://via.placeholder.com/150"],
        "stock": 100,
        "seller_id": "seller4",
        "product_id": str(uuid4())
    },
    {
        "name": "Wooden Toy Set",
        "description": "A set of eco-friendly wooden toys for children.",
        "category": "toys",
        "short_note": "New Arrival",
        "brand": "EcoToys",
        "price": 29.99,
        "overall_rating": 4.8,
        "images": ["https://via.placeholder.com/150"],
        "stock": 150,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Organic Cotton Stuffed Animal",
        "description": "Stuffed animal made from 100% organic cotton.",
        "category": "toys",
        "brand": "EcoToys",
        "price": 14.99,
        "overall_rating": 4.9,
        "images": ["https://via.placeholder.com/150"],
        "stock": 200,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    },
    {
        "name": "Eco-friendly Shampoo Bar",
        "description": "A shampoo bar made from natural ingredients.",
        "category": "featured",
        "short_note": "Best Seller",
        "brand": "EcoHair",
        "price": 9.99,
        "overall_rating": 4.7,
        "images": ["https://via.placeholder.com/150"],
        "stock": 100,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Reusable Produce Bags",
        "description": "Set of 10 reusable produce bags made from organic cotton.",
        "category": "groceries",
        "short_note": "New Arrival",
        "brand": "EcoBag",
        "price": 15.99,
        "overall_rating": 4.5,
        "images": ["https://via.placeholder.com/150"],
        "stock": 200,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    },
    {
        "name": "Eco-friendly Laundry Detergent",
        "description": "Laundry detergent made from natural ingredients.",
        "category": "eco-friendly",
        "brand": "EcoClean",
        "price": 12.99,
        "overall_rating": 4.8,
        "images": ["https://via.placeholder.com/150"],
        "stock": 150,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Reusable Coffee Cup",
        "description": "A reusable coffee cup made from bamboo fiber.",
        "category": "eco-friendly",
        "short_note": "Best Seller",
        "brand": "EcoCup",
        "price": 14.99,
        "overall_rating": 4.9,
        "images": ["https://via.placeholder.com/150"],
        "stock": 250,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    },
    {
        "name": "Compostable Cutlery Set",
        "description": "A set of compostable cutlery made from cornstarch.",
        "category": "eco-friendly",
        "brand": "EcoCutlery",
        "price": 7.99,
        "overall_rating": 4.6,
        "images": ["https://via.placeholder.com/150"],
        "stock": 300,
        "seller_id": "seller3",
        "product_id": str(uuid4())
    },
    {
        "name": "Solar Powered Lantern",
        "description": "A solar powered lantern for outdoor use.",
        "category": "eco-friendly",
        "brand": "SolarLight",
        "price": 29.99,
        "overall_rating": 4.7,
        "images": ["https://via.placeholder.com/150"],
        "stock": 100,
        "seller_id": "seller4",
        "product_id": str(uuid4())
    },
    {
        "name": "Wooden Puzzle Set",
        "description": "A set of eco-friendly wooden puzzles for children.",
        "category": "toys",
        "short_note": "New Arrival",
        "brand": "EcoPuzzle",
        "price": 19.99,
        "overall_rating": 4.8,
        "images": ["https://via.placeholder.com/150"],
        "stock": 150,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Organic Cotton Doll",
        "description": "A doll made from 100% organic cotton.",
        "category": "toys",
        "brand": "EcoDoll",
        "price": 24.99,
        "overall_rating": 4.9,
        "images": ["https://via.placeholder.com/150"],
        "stock": 200,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    },
    {
        "name": "Eco-friendly Dish Soap",
        "description": "Dish soap made from natural ingredients.",
        "category": "featured",
        "short_note": "Best Seller",
        "brand": "EcoSoap",
        "price": 5.99,
        "overall_rating": 4.7,
        "images": ["https://via.placeholder.com/150"],
        "stock": 100,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Reusable Snack Bags",
        "description": "Set of 5 reusable snack bags made from silicone.",
        "category": "groceries",
        "short_note": "New Arrival",
        "brand": "EcoSnack",
        "price": 10.99,
        "overall_rating": 4.5,
        "images": ["https://via.placeholder.com/150"],
        "stock": 200,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    },
    {
        "name": "Eco-friendly Floor Cleaner",
        "description": "Floor cleaner made from natural ingredients.",
        "category": "eco-friendly",
        "brand": "EcoFloor",
        "price": 11.99,
        "overall_rating": 4.8,
        "images": ["https://via.placeholder.com/150"],
        "stock": 150,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Reusable Water Bottle",
        "description": "A reusable water bottle made from stainless steel.",
        "category": "eco-friendly",
        "short_note": "Best Seller",
        "brand": "EcoBottle",
        "price": 19.99,
        "overall_rating": 4.9,
        "images": ["https://via.placeholder.com/150"],
        "stock": 250,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    }
]

users_data = [
    {
        "username": "john_doe",
        "email": "john.doe@example.com",
        "dateofbirth": datetime(1990, 1, 1).isoformat(),
        "gender": "male",
        "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "date_joined": datetime.now().isoformat(),
        "is_admin": False,
        "is_verified": True,
        "user_id": str(uuid4())
    },
    {
        "username": "jane_smith",
        "email": "jane.smith@example.com",
        "dateofbirth": datetime(1985, 5, 15).isoformat(),
        "gender": "female",
        "password": bcrypt.hashpw("securepassword".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "date_joined": datetime.now().isoformat(),
        "is_admin": True,
        "is_verified": True,
        "user_id": "seller1"
    },
    {
        "username": "alice_jones",
        "email": "alice.jones@example.com",
        "dateofbirth": datetime(1992, 3, 22).isoformat(),
        "gender": "female",
        "password": bcrypt.hashpw("mypassword".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "date_joined": datetime.now().isoformat(),
        "is_admin": False,
        "is_verified": True,
        "user_id": str(uuid4())
    },
    {
        "username": "bob_brown",
        "email": "bob.brown@example.com",
        "dateofbirth": datetime(1988, 7, 30).isoformat(),
        "gender": "male",
        "password": bcrypt.hashpw("password456".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "date_joined": datetime.now().isoformat(),
        "is_admin": False,
        "is_verified": True,
        "user_id": str(uuid4())
    }
]

sellers_data = [
    {
        "seller_id": "seller1",
        "seller_name": "EcoMart",
        "seller_description": "Your one-stop shop for eco-friendly products.",
        "seller_rating": 4.7,
        "seller_image": "https://via.placeholder.com/150"
    },
    {
        "seller_id": "seller2",
        "seller_name": "GreenGoods",
        "seller_description": "Sustainable and eco-friendly products for everyday use.",
        "seller_rating": 4.6,
        "seller_image": "https://via.placeholder.com/150"
    },
    {
        "seller_id": "seller3",
        "seller_name": "EcoHome",
        "seller_description": "Eco-friendly home essentials and products.",
        "seller_rating": 4.5,
        "seller_image": "https://via.placeholder.com/150"
    },
    {
        "seller_id": "seller4",
        "seller_name": "SolarStore",
        "seller_description": "Solar-powered gadgets and accessories.",
        "seller_rating": 4.8,
        "seller_image": "https://via.placeholder.com/150"
    }
]

orders_data = [
    {
        "user_id": users_data[0]["user_id"],
        "cart_items": [
            {"product_id": products_data[0]["product_id"], "quantity": 2},
            {"product_id": products_data[1]["product_id"], "quantity": 1}
        ],
        "address_id": 1234,
        "payment_type": "card",
        "total_amount": 20.97,
        "order_id": str(uuid4()),
        "order_status": "Order Placed",
        "payment_status": "Success"
    },
    {
        "user_id": users_data[2]["user_id"],
        "cart_items": [
            {"product_id": products_data[2]["product_id"], "quantity": 3},
            {"product_id": products_data[3]["product_id"], "quantity": 1}
        ],
        "address_id": 5678,
        "payment_type": "paypal",
        "total_amount": 84.96,
        "order_id": str(uuid4()),
        "order_status": "Order Placed",
        "payment_status": "Success"
    }
]

# Empty the collections
products_collection.delete_many({})
users_collection.delete_many({})
orders_collection.delete_many({})
sellers_collection.delete_many({})

# Insert dummy data into the collections
products_collection.insert_many(products_data)
users_collection.insert_many(users_data)
orders_collection.insert_many(orders_data)
sellers_collection.insert_many(sellers_data)

print("Dummy data added to the database successfully.")
