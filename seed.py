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
        "name": "Product 1",
        "description": "Description for product 1",
        "category": "featured",
        "brand": "Brand A",
        "price": 100.0,
        "overall_rating": 3.63,
        "images": ["https://via.placeholder.com/150"],
        "stock": 10,
        "seller_id": "seller1",
        "product_id": str(uuid4())
    },
    {
        "name": "Product 2",
        "description": "Description for product 2",
        "category": "groceries",
        "brand": "Brand B",
        "price": 50.0,
        "overall_rating": 4.5,
        "images": ["https://via.placeholder.com/150"],
        "stock": 20,
        "seller_id": "seller2",
        "product_id": str(uuid4())
    }
]

users_data = [
    {
        "username": "user1",
        "email": "user1@example.com",
        "dateofbirth": datetime(1990, 1, 1).isoformat(),
        "gender": "male",
        "password": bcrypt.hashpw("password1".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "date_joined": datetime.now().isoformat(),
        "is_admin": False,
        "is_verified": True,
        "user_id": str(uuid4())
    },
    {
        "username": "admin1",
        "email": "admin1@example.com",
        "dateofbirth": datetime(1985, 5, 15).isoformat(),
        "gender": "female",
        "password": bcrypt.hashpw("adminpassword".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "date_joined": datetime.now().isoformat(),
        "is_admin": True,
        "is_verified": True,
        "user_id": "seller1"
    }
]

sellers_data = [
    {
        "seller_id": "seller1",
        "seller_name": "Admin Seller",
        "seller_rating": 4.5,
        "seller_image": "https://via.placeholder.com/150"
    },
    {
        "seller_id": "seller2",
        "seller_name": "Another Seller",
        "seller_rating": 4.0,
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
        "total_amount": 250.0,
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
