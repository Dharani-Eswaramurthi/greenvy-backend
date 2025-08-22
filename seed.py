from pymongo import MongoClient
from uuid import uuid4
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import bcrypt
from google.cloud import storage
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth import default

# Load environment variables
load_dotenv()

# MongoDB setup
mongo_client = MongoClient("mongodb+srv://dharani96556:sPyNc7QdRnmcExi5@thegreenvy-db.iuywaii.mongodb.net/")
db = mongo_client['eco_friendly_ecommerce']
products_collection = db['products']
users_collection = db['users']
orders_collection = db['orders']
sellers_collection = db['sellers']

# Google Cloud Storage setup
BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')

# Try to initialize GCS client with proper error handling
try:
    # Try to use default credentials first
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    print(f"Successfully connected to GCS bucket: {BUCKET_NAME}")
except Exception as e:
    print(f"Warning: Could not initialize Google Cloud Storage with default credentials: {str(e)}")
    print("Please ensure you have:")
    print("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable to your service account key file")
    print("2. Or run 'gcloud auth application-default login' if using gcloud CLI")
    print("3. Set GCS_BUCKET_NAME environment variable")
    
    # Set dummy functions for testing without GCS
    storage_client = None
    bucket = None

def delete_all_images_in_folder(folder):
    if bucket is None:
        print(f"Skipping delete operation - GCS not available")
        return
    try:
        blobs = bucket.list_blobs(prefix=folder)
        for blob in blobs:
            blob.delete()
        print(f"Deleted all images in folder: {folder}")
    except Exception as e:
        print(f"Error deleting images in folder {folder}: {str(e)}")

def upload_image_to_gcs(file_path, gcs_folder):
    if bucket is None:
        print(f"Skipping upload for {file_path} - GCS not available")
        return f"dummy_url_for_{os.path.basename(file_path)}"
    try:
        file_id = str(uuid4())
        blob_name = f"{gcs_folder}/{file_id}_{os.path.basename(file_path)}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        print(f"Uploaded {file_path} to GCS bucket: {BUCKET_NAME}")
        return f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
    except Exception as e:
        print(f"GCS upload error: {str(e)}")
        return None
    

# Delete all images in the product-images folder
delete_all_images_in_folder('product-images')

# Upload seller profile and product images
seller_folder = "zero-waste-biodegradable"

# Read seller details from JSON file
with open(os.path.join(seller_folder, 'seller.json'), 'r', encoding='utf-8') as f:
    seller_details = json.load(f)

seller_profile_image = upload_image_to_gcs(f"{seller_folder}/profile.png", f"product-images/{seller_folder}")

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
            image_url = upload_image_to_gcs(image_path, f"product-images/{seller_folder}/{product_details['folder_name']}")
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
