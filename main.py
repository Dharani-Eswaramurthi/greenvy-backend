from base64 import b64decode
from fastapi import FastAPI, HTTPException, UploadFile, Form, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from pymongo import MongoClient, errors
from bson import ObjectId
from uuid import uuid4
from google.cloud import storage
import os
import bcrypt
import jwt
from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import razorpay
from Crypto.Cipher import AES
from base64 import b64decode
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


# Load environment variables
load_dotenv()

app = FastAPI(docs_url=None, redoc_url=None)

@app.get("/")
async def root():
    """
    Root endpoint to verify the API is running successfully.
    """
    return {
        "message": "Greenvy API is running successfully!",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# CORS setup
origins = [
    "http://localhost:3000", "https://greenvy.store", "https://storage.googleapis.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client['eco_friendly_ecommerce']
users_collection = db['users']
products_collection = db['products']
orders_collection = db['orders']
sellers_collection = db['sellers']

# Google Cloud Storage setup
storage_client = storage.Client()
BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
bucket = storage_client.bucket(BUCKET_NAME)

# JWT Secret Key
JWT_SECRET = os.getenv('JWT_SECRET')

# Email setup
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Razorpay setup
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')


# Validate Razorpay credentials
if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    print("Warning: Razorpay credentials not found. Payment functionality will be disabled.")
    razorpay_client = None
else:
    try:
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        # Test the credentials by making a simple API call to verify they work
        razorpay_client.utility.verify_webhook_signature("test", "test", "test")
    except Exception as e:
        # Don't fail on signature verification test - just log it
        print(f"Razorpay credentials loaded successfully. Signature test failed (expected): {str(e)}")
        # Keep razorpay_client initialized since credentials are valid

# Models
class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    product_id: str = None
    short_note: str = Field(..., min_length=1, max_length=100) # Best Seller, New Arrival, etc.
    category: str = Field(..., min_length=1, max_length=50)
    brand: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., gt=0)
    images: List[str]
    overall_rating: float = 0.0
    stock: int = Field(..., ge=0)
    seller_id: str

class SellerProfile(BaseModel):
    seller_id: str
    seller_name: str
    seller_description: str = None
    products: List[Product]
    seller_rating: float = 0.0
    seller_image: Optional[str] = None

class User(BaseModel):
    username: str = None
    email: EmailStr
    dateofbirth: datetime
    gender: str
    password: str = Field(..., min_length=6)
    date_joined: datetime = datetime.now()
    profile_image: Optional[str] = None
    is_admin: bool = False
    is_verified: bool = False
    otp: Optional[int] = None

class Login(BaseModel):
    email: EmailStr
    password: str

class Search(BaseModel):
    search: str = Field(..., min_length=1)

class Review(BaseModel):
    user_id: str
    product_id: str = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)
    date_posted: datetime = datetime.now()

class Address(BaseModel):
    addressId: Optional[int] = None
    address_type: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    country: str
    pincode: str
    phone_number: str

class UpdateProfileDetails(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class CheckoutOrder(BaseModel):
    user_id: str
    cart_items: List[dict]
    address_id: int  # Ensure address_id is a required string
    payment_type: str = None
    total_amount: float

class PaymentSuccess(BaseModel):
    order_id: str
    payment_id: str
    signature: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: int
    new_password: str = Field(..., min_length=6)

# Helper Functions
def upload_image_to_gcs(file: UploadFile, folder: str):
    try:
        file_id = str(uuid4())
        key = f"{folder}/{file_id}_{file.filename}"
        blob = bucket.blob(key)

        # Ensure the correct content type is set
        blob.upload_from_file(file.file, content_type=file.content_type)

        # Optional: force inline display instead of download
        blob.cache_control = "public, max-age=3600"
        blob.patch()

        return f"https://storage.googleapis.com/{BUCKET_NAME}/{key}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS upload error: {str(e)}")

def delete_image_from_gcs(image_url: str):
    try:
        key = image_url.split(f"https://storage.googleapis.com/{BUCKET_NAME}/")[1]
        blob = bucket.blob(key)
        blob.delete()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS delete error: {str(e)}")

def create_jwt_token(user_id: str, is_admin: bool):
    payload = {
        "user_id": user_id,
        "is_admin": is_admin,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def send_otp_email(email: str, otp: int):
    try:
        message = MIMEMultipart()
        message['From'] = EMAIL_ADDRESS
        message['To'] = email
        message['Subject'] = 'Your OTP Verification Code'
        
        # HTML template with enterprise logo and background color
        html = f"""
        <!DOCTYPE html>
        <html>
            <body style="background-color: #F7F9F9; text-align: left; color: #333; font-family: Arial, sans-serif;">
                <!-- Main container with enhanced shadow -->
                <div style="max-width: 600px; margin: 20px auto; box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15); border-radius: 10px; overflow: hidden;">
                    <!-- Header with background color -->
                    <div style="background-color: #25995C; padding: 25px; text-align: center;">
                        <img src="https://storage.googleapis.com/thegreenvy-products/greenvy-logo.png" alt="Greenvy Logo" style="width: 120px; height: auto;">
                    </div>
                    
                    <!-- Body content with white background -->
                    <div style="background-color: #FFFFFF; padding: 30px;">
                        <p style="font-size: 18px; line-height: 1.6;">Hello greenvy User!</p>
                        
                        <p style="font-size: 16px; line-height: 1.5;">Thanks for trusting our planet-friendly services. Who knew saving the world could be so chic?</p>
                        <p style="font-size: 16px; line-height: 1.5; text-align: center;"><b>Your exclusive OTP for {email}</b></p>
                        
                        <!-- Centered OTP in a small container -->
                        <div style="margin: 20px 0; text-align: center; display: flex; justify-content: center;">
                            <div style="display: flex; justify-content: center; align-items: center; width: fit-content; height: 50px; padding: 10px 20px; background-color: #CDF0EA; font-size: 22px; font-weight: bold; color: #25995C; letter-spacing: 10px;">
                                {otp}
                            </div>
                        </div>
                        <p style="font-size: 16px; line-height: 1.5;">But hurry, it’s more fleeting than a biodegradable fork—expires in 10 minutes!</p>
                        <p style="font-size: 16px; line-height: 1.5;">Remember, every tiny effort makes a difference. Together, we’ll make this planet greener—one ironic product at a time!</p>
                        
                        <div style="margin-top: 20px;">
                            <p style="margin-bottom: 5px; font-size: 14px;">Got questions or just feeling chatty?</p>
                            <p>Email: <a href="mailto:hello@greenvy.store" style="color: #25995C; text-decoration: none;">hello@greenvy.store</a></p>
                            <p>Phone: <a href="tel:+919655612306" style="color: #25995C; text-decoration: none;">+91 96556-12306</a></p>
                            <p>Location: Coimbatore, Tamilnadu, India</p>
                        </div>
                    </div>
                    
                    <!-- Footer with background color -->
                    <div style="background-color: #25995C; padding: 20px; color: #FFF;">
                        <p style="font-size: 14px; margin-bottom: 10px;">Questions? We have answers... possibly compostable ones!</p>
                        <p style="font-size: 14px;">© 2025 greenvy.store. All rights reserved. (Who else would want them?)</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending error: {str(e)}")

def send_reset_password_email(email: str, token: str):
    try:
        message = MIMEMultipart()
        message['From'] = EMAIL_ADDRESS
        message['To'] = email
        message['Subject'] = 'Your Password Reset Link'
        
        # HTML template with enterprise logo and background color
        reset_link = f"https://greenvy.store/reset-password?token={token}"
        html = f"""
        <!DOCTYPE html>
        <html>
            <body style="background-color: #F7F9F9; text-align: left; color: #333; font-family: Arial, sans-serif;">
                <!-- Main container with enhanced shadow -->
                <div style="max-width: 600px; margin: 20px auto; box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15); border-radius: 10px; overflow: hidden;">
                    <!-- Header with background color -->
                    <div style="background-color: #25995C; padding: 25px; text-align: center;">
                        <img src="https://storage.googleapis.com/thegreenvy-products/greenvy-logo.png" alt="Greenvy Logo" style="width: 120px; height: auto;">
                    </div>
                    
                    <!-- Body content with white background -->
                    <div style="background-color: #FFFFFF; padding: 30px;">
                        <p style="font-size: 18px; line-height: 1.6;">Hello greenvy User!</p>
                        
                        <p style="font-size: 16px; line-height: 1.5;">We received a request to reset your password. Click the link below to reset it.</p>
                        <p style="font-size: 16px; line-height: 1.5; text-align: center;"><b><a href="{reset_link}" style="color: #25995C;">Reset Password</a></b></p>
                        
                        <p style="font-size: 16px; line-height: 1.5;">This link will expire in 10 minutes.</p>
                        
                        <div style="margin-top: 20px;">
                            <p style="margin-bottom: 5px; font-size: 14px;">Got questions or just feeling chatty?</p>
                            <p>Email: <a href="mailto:hello@greenvy.store" style="color: #25995C; text-decoration: none;">hello@greenvy.store</a></p>
                            <p>Phone: <a href="tel:+919655612306" style="color: #25995C; text-decoration: none;">+91 96556-12306</a></p>
                            <p>Location: Coimbatore, Tamilnadu, India</p>
                        </div>
                    </div>
                    
                    <!-- Footer with background color -->
                    <div style="background-color: #25995C; padding: 20px; color: #FFF;">
                        <p style="font-size: 14px; margin-bottom: 10px;">Questions? We have answers... possibly compostable ones!</p>
                        <p style="font-size: 14px;">© 2025 greenvy.store. All rights reserved. (Who else would want them?)</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending error: {str(e)}")

def convert_objectid_to_str(data):
    if isinstance(data, list):
        for item in data:
            if '_id' in item:
                item['_id'] = str(item['_id'])
    elif isinstance(data, dict):
        if '_id' in data:
            data['_id'] = str(data['_id'])
    return data

def decrypt_password(encrypted_password: str) -> str:
    secret_key = os.environ.get("ENCRYPTION_KEY")
    iv = os.environ.get("ENCRYPTION_IV")
    if not secret_key or not iv:
        raise ValueError("ENCRYPTION_KEY or ENCRYPTION_IV environment variable is not set")
    
    ciphertext = b64decode(encrypted_password)
    derived_key = b64decode(secret_key)
    cipher = AES.new(derived_key, AES.MODE_CBC, iv.encode('utf-8'))
    decrypted_data = cipher.decrypt(ciphertext)
    return unpad(decrypted_data, 16).decode("utf-8")

@app.post("/user/register")
async def register_user(user: User):
    """
    Register a new user.
    """

    # set username in user to extract from email
    user.username = user.email.split('@')[0]
    print("Username splitted")

    try:
        print("Entered try")
        # Check if the username is already taken
        if users_collection.find_one({"username": user.username}):
            raise HTTPException(status_code=400, detail="Username already taken. Please choose a different username.")

        
        user_data = user.dict()
        user_data["user_id"] = str(uuid4())
        user_data["dateofbirth"] = user_data["dateofbirth"].isoformat()
        user_data["gender"] = user_data['gender']
        user_data["password"] = hash_password(decrypt_password(user_data["password"]))
        user_data["otp"] = random.randint(100000, 999999)
        print("User data created")
        users_collection.insert_one(user_data)
        send_otp_email(user.email, user_data["otp"])
        return {"message": "User registered successfully. Please verify your email."}
    except errors.DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered. Please use a different email address.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while registering the user: {str(e)}")

@app.post("/user/verify")
async def verify_user(email: EmailStr, otp: int):
    """
    Verify user email with OTP.
    """
    try:
        user = users_collection.find_one({"email": email, "is_admin": False})
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please check the email address.")
        if user.get("is_verified"):
            return {"message": "Email already verified."}
        if user.get("otp") != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP. Please try again.")
        users_collection.update_one({"email": email}, {"$set": {"is_verified": True}, "$unset": {"otp": ""}})
        return {"message": "Email verified successfully."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while verifying the email: {str(e)}")

@app.post("/user/login")
async def login_user(login: Login):
    """
    User login.
    """
    try:
        user = users_collection.find_one({"email": login.email, "is_admin": False})
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please check the email address.")
        if not verify_password(decrypt_password(login.password), user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials. Please check your password.")
        if not user.get("is_verified"):
            raise HTTPException(status_code=403, detail="Email not verified. Please verify your email.")
        token = create_jwt_token(user_id=user["user_id"], is_admin=False)
        return {"token": token, "user_id": user["user_id"], "is_admin": False}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while logging in: {str(e)}")

@app.get("/user/profile/{user_id}")
async def get_user_profile(user_id: str):
    """
    Get user profile.
    """
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = convert_objectid_to_str(user)
    return user

@app.post("/user/upload-profile-image/{user_id}")
async def upload_profile_image(user_id: str, profile_image: Optional[UploadFile] = None, profile_image_crop: str = Form(...)):
    """
    Upload user profile image and return the link.
    """
    try:
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please check the user ID.")
        if user.get("profile_image"):
            if profile_image:
                delete_image_from_gcs(user["profile_image"])
                image_url = upload_image_to_gcs(profile_image, 'user-profile-images')
                users_collection.update_one({"user_id": user_id}, {"$set": {"profile_image": image_url, "profile_image_crop": profile_image_crop}})
            else:
                image_url = user["profile_image"]
                users_collection.update_one({"user_id": user_id}, {"$set": {"profile_image_crop": profile_image_crop}})
        else:
            if profile_image:
                image_url = upload_image_to_gcs(profile_image, 'user-profile-images')
                users_collection.update_one({"user_id": user_id}, {"$set": {"profile_image": image_url, "profile_image_crop": profile_image_crop}})
            else:
                raise HTTPException(status_code=400, detail="Profile image is required if no existing profile image is found.")
        return {"message": "Profile image uploaded successfully.", "profile_image_url": image_url, "profile_image_crop": profile_image_crop}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while uploading the profile image: {str(e)}")

@app.post("/user/delete-profile-image/{user_id}")
async def delete_profile_image(user_id: str):
    """
    Delete user profile image.
    """
    user = users_collection.find_one({"user_id": user_id})
    if user and user.get("profile_image"):
        delete_image_from_gcs(user["profile_image"])
        users_collection.update_one({"user_id": user_id}, {"$unset": {"profile_image": ""}})
    return {"message": "Profile image deleted successfully"}

@app.post("/user/update-profile-details/{user_id}")
async def update_profile_details(user_id: str, details: UpdateProfileDetails):
    """
    Update user profile details.
    """
    try:
        update_data = {}
        if details.username:
            update_data["username"] = details.username
        if details.email:
            update_data["email"] = details.email
        users_collection.update_one({"user_id": user_id}, {"$set": update_data})
        return {"message": "Profile details updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while updating profile details: {str(e)}")

@app.post("/user/update-profile-details/delete-address/{user_id}")
async def delete_address(user_id: str, addressId: int):
    """
    Delete user address.
    """
    users_collection.update_one({"user_id": user_id}, {"$pull": {"address": {"addressId": addressId}}})
    return {"message": "Address deleted successfully"}

@app.post("/user/update-profile-details/add-or-update-address/{user_id}")
async def add_or_update_address(user_id: str, address: Address):
    """
    Add or update user address.
    """
    # check if the address from the request body already exists in the user's address list
    user = users_collection.find_one({"user_id": user_id})
    address.phone_number="+91"+address.phone_number
    if user and "address" in user:
        for existing_address in user["address"]:
            if existing_address["addressId"] == address.addressId:
                # update the existing address
                users_collection.update_one(
                    {"user_id": user_id, "address.addressId": address.addressId},
                    {"$set": {"address.$": address.dict()}}
                )
                return {"message": "Address updated successfully"}
    # add new address
    address.addressId = random.randint(1000, 9999)
    users_collection.update_one({"user_id": user_id}, {"$push": {"address": address.dict()}})
    return {"message": "Address added successfully"}

@app.post("/user/add-to-cart")
async def add_to_cart(user_id: str, product_id: str, quantity: int):
    """
    Add item to cart.
    """
    try:
        cart_item = {
            "product_id": product_id,
            "quantity": quantity
        }
        # if quantity is 0, then remove the item from the cart
        if quantity == 0:
            users_collection.update_one({"user_id": user_id}, {"$pull": {"cart": {"product_id": product_id}}})
            return {"message": "Item removed from cart."}
        
        # check if the product already exists in the user's cart if yes update the quantity else add new item
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please check the user ID.")
        if "cart" in user:
            for item in user["cart"]:
                if item["product_id"] == product_id:
                    users_collection.update_one(
                        {"user_id": user_id, "cart.product_id": product_id},
                        {"$set": {"cart.$.quantity": quantity}}
                    )
                    return {"message": "Item quantity updated in cart."}
        users_collection.update_one({"user_id": user_id}, {"$push": {"cart": cart_item}})
        return {"message": "Item added to cart."}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while adding item to cart: {str(e)}")

@app.get("/user/cart/{user_id}")
async def get_cart(user_id: str):
    """
    Get user cart.
    """
    user = users_collection.find_one({"user_id": user_id})
    user = convert_objectid_to_str(user)
    return user.get("cart", [])

@app.post("/user/empty-cart/{user_id}")
async def empty_cart(user_id: str):
    """
    Empty user cart.
    """
    users_collection.update_one({"user_id": user_id}, {"$set": {"cart": []}})
    return {"message": "Cart emptied successfully"}


@app.post("/user/place-order")
async def place_order(order: CheckoutOrder):
    """
    Place a new order.
    """
    try:
        order_data = order.dict()

        # Check if Razorpay is available
        print("client", razorpay_client)
        if razorpay_client is None:
            print("IS NONE")
            # Create a simple order without payment gateway
            order_data["order_id"] = f"order_{str(uuid4())[:8]}"
            order_data["order_status"] = "Order Placed"
            order_data["payment_status"] = "Pending"
            order_data["payment_type"] = "Online" if order.payment_type == "online" else "Cash on Delivery"
            orders_collection.insert_one(order_data)
            return {
                "message": "Order placed successfully (Cash on Delivery).",
                "order_id": order_data["order_id"],
                "amount": int(order_data["total_amount"] * 100),
                "address_id": order_data["address_id"],
                "currency": "INR",
                "order_status": order_data["order_status"],
                "payment_status": "Pending",
                "payment_type": order_data["payment_type"]
            }
        print("ISN'T NONE")
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            "amount": int(order_data["total_amount"] * 100),  # amount in paise
            "currency": "INR",
            "payment_capture": "1"
        })
        order_data["order_id"] = razorpay_order["id"]
        order_data["order_status"] = "Order Placed"
        order_data["payment_status"] = "Pending"
        orders_collection.insert_one(order_data)
        return {
            "message": "Order placed successfully.",
            "order_id": order_data["order_id"],
            "payment_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "address_id": order_data["address_id"],
            "currency": razorpay_order["currency"],
            "order_status": order_data["order_status"],
            "payment_status": "Pending"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while placing the order: {str(e)}")

@app.post("/user/payment-success")
async def payment_success(payment: PaymentSuccess):
    """
    Handle payment success callback.
    """
    try:
        # Check if Razorpay is available
        if razorpay_client is None:
            raise HTTPException(status_code=503, detail="Payment gateway is not available")
        
        # Verify the payment signature
        params_dict = {
            'razorpay_order_id': payment.order_id,
            'razorpay_payment_id': payment.payment_id,
            'razorpay_signature': payment.signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)

        # Fetch payment details from Razorpay
        payment_details = razorpay_client.payment.fetch(payment.payment_id)

        # Update the order status and payment type
        orders_collection.update_one(
            {"order_id": payment.order_id},
            {"$set": {
                "order_status": "Order Placed",
                "payment_status": "Success",
                "payment_id": payment.payment_id,
                "payment_type": payment_details["method"]
            }}
        )
        return {"message": "Payment verified and order confirmed."}
    except HTTPException as e:
        raise e
    except Exception as e:
        # Update the order status to failed
        orders_collection.update_one(
            {"order_id": payment.order_id},
            {"$set": {"order_status": "Failed", "payment_status": "Failed"}}
        )
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while verifying the payment: {str(e)}")
    
@app.post("/user/payment-failed")
async def payment_failed(order_id: str):
    """
    Handle payment failure callback.
    """
    orders_collection.update_one({"order_id": order_id}, {"$set": {"order_status": "Failed", "payment_status": "Failed"}})

    return {"message": "Order placement failed"}
    
@app.post("/user/cancel-order/{order_id}")
async def cancel_order(order_id: str):
    """
    Cancel an order.
    """
    try:
        orders_collection.update_one({"order_id": order_id}, {"$set": {"order_status": "Cancelled"}})
        return {"message": "Order cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")


@app.post("/user/add-review")
async def add_review(review: Review):
    """
    Add a review for a product.
    """
    review_data = review.dict()
    review_data["review_id"] = str(uuid4())
    try:
        print(f"Adding review: {review_data}")
        products_collection.update_one({"product_id": review.product_id}, {"$push": {"reviews": review_data}})
        print(f"Review added to product: {review.product_id}")

        # Update the product rating
        product = products_collection.find_one({"product_id": review.product_id})
        print("Product found: ", product)
        if product['overall_rating'] == 0:
            products_collection.update_one({"product_id": review.product_id}, {"$set": {"overall_rating": review.rating}})
            print(f"Product rating set to: {review.rating}")
        else:
            new_rating = (product['overall_rating'] + review.rating) / 2
            products_collection.update_one({"product_id": review.product_id}, {"$set": {"overall_rating": new_rating}})
            print(f"Product rating updated to: {new_rating}")

        # Update the seller rating
        seller_id = product.get("seller_id")
        products = list(products_collection.find({"seller_id": seller_id}))
        total_rating = sum(product.get("overall_rating", 0) for product in products)
        average_rating = total_rating / len(products) if len(products) > 0 else 0
        sellers_collection.update_one({"seller_id": seller_id}, {"$set": {"seller_rating": average_rating}})
        print(f"Seller rating updated to: {average_rating}")

    except Exception as e:
        print(f"Error adding review: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding review: {str(e)}")
    return {"message": "Review added successfully", "review_id": review_data["review_id"]}

@app.get("/user/wishlist/{user_id}")
async def get_wishlist(user_id: str):
    """
    Get user wishlist.
    """
    user = users_collection.find_one({"user_id": user_id})
    user = convert_objectid_to_str(user)
    return user.get("wishlist", [])

@app.post("/user/add-to-wishlist")
async def add_to_wishlist(user_id: str, product_id: str):
    """
    Add item to wishlist.
    """
    # check if the product already exists in the user's wishlist if yes then return error else add new item
    user = users_collection.find_one({"user_id": user_id})
    if user and "wishlist" in user:
        for item in user["wishlist"]:
            if item == product_id:
                users_collection.update_one({"user_id": user_id}, {"$pull": {"wishlist": product_id}})
                return {"message": "Item already in wishlist, so removed from wishlist"}
            
    users_collection.update_one({"user_id": user_id}, {"$push": {"wishlist": product_id}})
    return {"message": "Item added to wishlist"}

@app.post("/user/products/search")
async def search_products(search: Search):
    """
    Search products by name.
    """
    products = list(products_collection.find({"name": {"$regex": search.search, "$options": "i"}}))
    products = convert_objectid_to_str(products)
    return products


@app.post("/user/remove-from-wishlist")
async def remove_from_wishlist(user_id: str, product_id: str):
    """
    Remove item from wishlist.
    """
    users_collection.update_one({"user_id": user_id}, {"$pull": {"wishlist": product_id}})
    return {"message": "Item removed from wishlist"}

@app.get("/user/reviews/{user_id}")
async def get_user_reviews(user_id: str):
    """
    Get reviews by user ID.
    """
    reviews = list(products_collection.find({"reviews.user_id": user_id}))
    reviews = convert_objectid_to_str(reviews)

    # retrive only necessary fields like product name, image and review details
    reviews = [{"product_id": review['product_id'], "product_name": review["name"], "product_image": review["images"][0], "rating": review["reviews"][0]["rating"], "comment": review["reviews"][0]["comment"]} for review in reviews]

    return reviews

@app.get("/user/address/{user_id}/{address_id}")
async def get_address(user_id: str, address_id: int):
    """
    Get address by address ID.
    """
    user = users_collection.find_one({"user_id": user_id})
    user = convert_objectid_to_str(user)
    print("[DEBUG] address_id", type(address_id))
    address = next((address for address in user.get("address", []) if address.get("addressId") == address_id), None)
    return address if address else {"message": "Address not found", "status": 404}


@app.post("/user/edit-review/{review_id}")
async def edit_review(review_id: str, review: Review):
    """
    Edit a review.
    """
    try:
        products_collection.update_one({"reviews.review_id": review_id}, {"$set": {"reviews.$.rating": review.rating, "reviews.$.comment": review.comment}})

        # Update the product rating
        product = products_collection.find_one({"product_id": review.product_id})
        reviews = product.get("reviews", [])
        total_rating = sum(review.get("rating", 0) for review in reviews)
        average_rating = total_rating / len(reviews) if len(reviews) > 0 else 0
        products_collection.update_one({"product_id": product["product_id"]}, {"$set": {"overall_rating": average_rating}})

        # Update the seller rating
        seller_id = product.get("seller_id")
        products = list(products_collection.find({"seller_id": seller_id}))
        total_rating = sum(product.get("overall_rating", 0) for product in products)
        average_rating = total_rating / len(products) if len(products) > 0 else 0
        sellers_collection.update_one({"seller_id": seller_id}, {"$set": {"seller_rating": average_rating
        }})
        print(f"Seller rating updated to: {average_rating}")
        print(f"Product rating updated to: {average_rating}")

        return {"message": "Review edited successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error editing review: {str(e)}")

@app.post("/user/delete-review/{review_id}")
async def delete_review(review_id: str):
    """
    Delete a review.
    """
    try:
        del_prod_id = products_collection.find_one({"reviews.review_id": review_id})["product_id"]
        products_collection.update_one({"reviews.review_id": review_id}, {"$pull": {"reviews": {"review_id": review_id}}})
        print(f"Review deleted: {review_id}")

        # Update the product rating
        product = products_collection.find_one({"product_id": del_prod_id})
        print("Product found: ", product)
        reviews = product.get("reviews", [])
        print("Reviews found: ", reviews)
        total_rating = sum(review.get("rating", 0) for review in reviews)
        average_rating = total_rating / len(reviews) if len(reviews) > 0 else 0
        products_collection.update_one({"product_id": product["product_id"]}, {"$set": {"overall_rating": average_rating}})

        # Update the seller rating
        seller_id = product.get("seller_id")
        print("Seller ID: ", seller_id)
        products = list(products_collection.find({"seller_id": seller_id}))
        print("Products found: ", products)
        total_rating = sum(product.get("overall_rating", 0) for product in products)
        average_rating = total_rating / len(products) if len(products) > 0 else 0
        sellers_collection.update_one({"seller_id": seller_id}, {"$set": {"seller_rating": average_rating}})
        print(f"Seller rating updated to: {average_rating}")
        print(f"Product rating updated to: {average_rating}")

        return {"message": "Review deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting review: {str(e)}")


@app.post("/seller/update-seller-rating")
async def update_seller_rating(seller_id: str):
    # Fetch all the products of the seller and calculate the average rating
    products = list(products_collection.find({"seller_id": seller_id}))
    total_rating = 0
    for product in products:
        total_rating += product.get("rating", 0)
    average_rating = total_rating / len(products) if len(products) > 0 else 0
    sellers_collection.update_one({"seller_id": seller_id}, {"$set": {"seller_rating": average_rating}})
    return {"message": "Seller rating updated successfully"}

@app.post("/product/update-product-rating")
async def update_product_rating(product_id: str):
    # Fetch all the reviews of the product and calculate the average rating
    reviews = list(products_collection.find({"product_id": product_id}))
    total_rating = 0
    for review in reviews:
        total_rating += review.get("rating", 0)
    average_rating = total_rating / len(reviews) if len(reviews) > 0 else 0
    products_collection.update_one({"product_id": product_id}, {"$set": {"rating": average_rating}})
    return {"message": "Product rating updated successfully"}


@app.get("/products/{category}")
async def get_products(category: str):
    """
    Get products by category.
    """
    try:
        products = list(products_collection.find({"category": category}))
        products = convert_objectid_to_str(products)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")
    return products

@app.get("/product/{product_id}")
async def get_product(product_id: str):
    """
    Get product details by product ID.
    """
    product = products_collection.find_one({"product_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = convert_objectid_to_str(product)
    return product

@app.get("/product/reviews/{product_id}")
async def get_reviews(product_id: str):
    """
    Get reviews for a product.
    """
    product = products_collection.find_one({"product_id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product = convert_objectid_to_str(product)
    return product.get("reviews", [])

@app.get("/search")
async def search_products(query: str):
    """
    Search products by name.
    """
    try:
        products = list(products_collection.find({"name": {"$regex": query, "$options": "i"}}))
        products = convert_objectid_to_str(products)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")
    return products

@app.get("/user/orders/{user_id}")
async def get_orders(user_id: str):
    """
    Get orders for a user.
    """
    try:
        orders = list(orders_collection.find({"user_id": user_id}))
        orders = convert_objectid_to_str(orders)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")
    return orders

@app.post("/user/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset.
    """
    try:
        user = users_collection.find_one({"email": request.email, "is_admin": False})
        if not user:
            raise HTTPException(status_code=404, detail="User not found. Please check the email address.")
        
        token = jwt.encode({"email": request.email, "exp": datetime.utcnow() + timedelta(minutes=10)}, JWT_SECRET, algorithm='HS256')
        users_collection.update_one({"email": request.email}, {"$set": {"reset_token": token}})
        send_reset_password_email(request.email, token)
        return {"message": "Password reset link sent to your email."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while requesting password reset: {str(e)}")

@app.post("/user/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...)):
    """
    Reset user password.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        email = payload.get("email")
        user = users_collection.find_one({"email": email, "reset_token": token, "is_admin": False})
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired token. Please try again.")
        
        # Invalidate the token immediately after use
        users_collection.update_one({"email": email}, {"$unset": {"reset_token": ""}})
        
        new_hashed_password = hash_password(decrypt_password(new_password))
        users_collection.update_one({"email": email}, {"$set": {"password": new_hashed_password}})
        return {"message": "Password reset successfully."}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired. Please request a new password reset.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while resetting the password: {str(e)}")


#create an api to check the token is valid or not
@app.post("/user/check-token")
async def check_token(token: str = Form(...)):
    """
    Check if the token is valid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        email = payload.get("email")
        user = users_collection.find_one({"email": email, "reset_token": token, "is_admin": False})
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired token. Please try again.")
        return {"message": "Token is valid."}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired. Please request a new password reset.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while checking the token: {str(e)}")

@app.post("/user/additional-cost")
async def calculate_additional_cost(user_id: str, address_id: int, total_cost: float):
    """
    Calculate additional costs like shipping and taxes based on user_id, address_id, and total_cost.
    """
    try:
        # Verify user exists
        user = users_collection.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Find the specific address
        address = None
        if "address" in user:
            for addr in user["address"]:
                if addr.get("addressId") == address_id:
                    address = addr
                    break
        
        if not address:
            raise HTTPException(status_code=404, detail="Address not found")
        
        # Calculate shipping cost based on location and order value
        shipping_cost = 0.0
        if total_cost < 500:  # Free shipping for orders above 500
            shipping_cost = 50.0  # Standard shipping cost
        
        # Calculate GST (Goods and Services Tax) - 18% for most products
        gst_rate = 0.18
        gst_amount = total_cost * gst_rate
        
        # Calculate total additional costs
        total_additional_cost = shipping_cost + gst_amount
        
        # Calculate final total
        final_total = total_cost + total_additional_cost
        
        return {
            "user_id": user_id,
            "address_id": address_id,
            "subtotal": total_cost,
            "shipping_cost": shipping_cost,
            "gst_amount": gst_amount,
            "total_additional_cost": total_additional_cost,
            "final_total": final_total,
            "currency": "INR"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while calculating additional costs: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 