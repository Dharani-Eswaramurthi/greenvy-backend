from pymongo import MongoClient
from uuid import uuid4
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import bcrypt
import boto3

# Load environment variables
load_dotenv()

# MongoDB setup
mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb+srv://dharani96556:Dharani2002@thegreenvy.a7dsi.mongodb.net/"))
db = mongo_client['eco_friendly_ecommerce']
products_collection = db['products']
users_collection = db['users']
orders_collection = db['orders']
sellers_collection = db['sellers']

# AWS S3 setup
s3 = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY'), aws_secret_access_key=os.getenv('AWS_SECRET_KEY'))
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def delete_all_images_in_folder(folder):
    try:
        objects_to_delete = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=folder)
        delete_keys = {'Objects': [{'Key': obj['Key']} for obj in objects_to_delete.get('Contents', [])]}
        if delete_keys['Objects']:
            s3.delete_objects(Bucket=BUCKET_NAME, Delete=delete_keys)
            print(f"Deleted all images in folder: {folder}")
    except Exception as e:
        print(f"Error deleting images in folder {folder}: {str(e)}")

def upload_image_to_s3(file_path, s3_folder):
    try:
        file_id = str(uuid4())
        key = f"{s3_folder}/{file_id}_{os.path.basename(file_path)}"
        s3.upload_file(file_path, BUCKET_NAME, key)
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
    except Exception as e:
        print(f"S3 upload error: {str(e)}")
        return None
    

# Delete all images in the product-images folder
delete_all_images_in_folder('product-images')

# Upload seller profile and product images
seller_folder = "zero-waste-biodegradable"

# Read seller details from JSON file
with open(os.path.join(seller_folder, 'seller.json'), 'r', encoding='utf-8') as f:
    seller_details = json.load(f)

seller_profile_image = upload_image_to_s3(f"{seller_folder}/profile.png", f"product-images/{seller_folder}")

# Read product details from JSON file
with open(os.path.join(seller_folder, 'products.json'), 'r', encoding='utf-8') as f:
    products_details = json.load(f)

products_data = []
for product_details in products_details:
    product_images = []
    product_path = os.path.join(seller_folder, product_details["folder_name"])
    
    for image_file in os.listdir(product_path):
        image_path = os.path.join(product_path, image_file)
        if os.path.isfile(image_path):
            image_url = upload_image_to_s3(image_path, f"product-images/{seller_folder}/{product_details['folder_name']}")
            if image_url:
                product_images.append(image_url)
    
    products_data.append({
        "name": product_details["title"],
        "description": product_details["description"],
        "category": product_details["category"],
        "brand": product_details['brand'],
        "price": product_details["price"],
        "min_quantity": product_details["min_quantity"],
        "overall_rating": 0,
        "images": product_images,
        "stock": product_details["stock"],
        "seller_id": product_details['seller_id'],
        "product_id": str(uuid4())
    })

# Dummy data
sellers_data = [
    {
        "seller_id": seller_details["seller_id"],
        "seller_name": seller_details["seller_name"],
        "seller_description": seller_details["seller_description"],
        "seller_rating": 0,
        "seller_image": seller_profile_image,
        "products": [
            {k: v for k, v in product.items() if k != "_id"}
            for product in products_data if product["seller_id"] == seller_details["seller_id"]
        ]
    }
]

orders_data = []

# Empty the collections
products_collection.delete_many({})
# users_collection.delete_many({})
orders_collection.delete_many({})
sellers_collection.delete_many({})

# Insert dummy data into the collections
products_collection.insert_many(products_data)
sellers_collection.insert_many(sellers_data)

print("Dummy data added to the database successfully.")
