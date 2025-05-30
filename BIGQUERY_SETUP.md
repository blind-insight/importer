# BigQuery Authentication Setup Guide

## How to Connect Your BigQuery Account

To use real BigQuery data instead of mock data, you'll need to set up authentication with Google Cloud.

### Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your **Project ID** (you'll need this in the app)

### Step 2: Enable BigQuery API
1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "BigQuery API"
3. Click **Enable**

### Step 3: Create a Service Account
1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Enter a name (e.g., "bigquery-schema-converter")
4. Click **Create and Continue**
5. Add the **BigQuery Data Viewer** role
6. Click **Continue** then **Done**

### Step 4: Generate Service Account Key
1. Click on your newly created service account
2. Go to the **Keys** tab
3. Click **Add Key** > **Create new key**
4. Select **JSON** format
5. Click **Create** - this will download the JSON key file

### Step 5: Use in the App
1. Select "Real BigQuery Connection" in the app
2. Enter your **Project ID**
3. Upload the **Service Account Key JSON file**
4. Enter your **Dataset ID** and **Table ID**
5. Click **Convert Schema**

## Security Notes
- ⚠️ **Never commit service account keys to version control**
- 🔒 The service account key is processed locally and not stored
- 👀 Only BigQuery Data Viewer permissions are needed
- 🚫 The app doesn't modify your BigQuery data, only reads schemas

## Common Issues

### "Access Denied" Error
- Ensure your service account has **BigQuery Data Viewer** role
- Check that the BigQuery API is enabled in your project

### "Dataset not found" Error
- Verify the dataset exists in your specified project
- Check that the dataset name is correct (case-sensitive)

### "Table not found" Error
- Ensure the table exists in the specified dataset
- Verify the table name is correct (case-sensitive)

## Example
- Project ID: `my-analytics-project`
- Dataset ID: `user_data`
- Table ID: `customer_profiles`
- Full table reference: `my-analytics-project.user_data.customer_profiles` 