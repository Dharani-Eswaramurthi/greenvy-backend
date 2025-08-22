# Google Cloud Storage Setup with OAuth Credentials

## Current Situation
You have an OAuth 2.0 client credentials file, but Google Cloud Storage requires service account authentication for server-to-server operations.

## Option 1: Convert to Service Account (Recommended)

### Step 1: Create a Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "IAM & Admin" > "Service Accounts"
3. Click "Create Service Account"
4. Name: `storage-service-account`
5. Description: `Service account for file uploads`
6. Click "Create and Continue"

### Step 2: Grant Permissions
Add these roles:
- `Storage Object Admin`
- `Storage Admin` (if needed)

### Step 3: Create Service Account Key
1. Click on your service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" format
5. Download the file

### Step 4: Update Environment
Create a `.env` file:
```env
MONGO_URI=mongodb+srv://dharani96556:sPyNc7QdRnmcExi5@thegreenvy-db.iuywaii.mongodb.net/
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
GCS_BUCKET_NAME=your-bucket-name
```

## Option 2: Use gcloud CLI (Easier)

### Step 1: Install gcloud CLI
Download from: https://cloud.google.com/sdk/docs/install

### Step 2: Authenticate
```bash
gcloud auth application-default login
```

### Step 3: Set Project
```bash
gcloud config set project able-folio-400909
```

### Step 4: Update Environment
```env
MONGO_URI=mongodb+srv://dharani96556:sPyNc7QdRnmcExi5@thegreenvy-db.iuywaii.mongodb.net/
GCS_BUCKET_NAME=your-bucket-name
```

## Option 3: Use OAuth for Web Application (Advanced)

If you want to use your existing OAuth credentials, you'll need to implement a web-based authentication flow. This is more complex and not recommended for server-side operations.

## Quick Test

After setting up any option above:

```bash
python seed.py
```

## Troubleshooting

### "Could not automatically determine credentials"
- Make sure you've set up authentication using one of the options above
- Check that your project has billing enabled
- Verify the bucket exists and is accessible

### "Bucket not found"
- Check your `GCS_BUCKET_NAME` environment variable
- Ensure the bucket exists in your Google Cloud project
- Verify your service account has access to the bucket

## Security Notes
- Never commit credentials to version control
- Use environment variables for sensitive information
- Consider using Google Cloud Secret Manager for production
