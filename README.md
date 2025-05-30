# BigQuery to Blind Insight Data Import Tool

A React application that extracts BigQuery table schemas, converts them to JSON Schema format, and imports data into Blind Insight using the Blind Proxy.

**Note: This is a working prototype (not production code) that demonstrates integration between Blind Insight and BigQuery.**

## Features

- 🔍 Extract schema from any BigQuery table
- 🔄 Convert BigQuery schema to JSON Schema format
- 📋 Copy schemas to clipboard
- 💾 Download schemas as JSON files
- 🎨 Modern, responsive UI with glassmorphism design
- 📱 Mobile-friendly interface
- 🔐 **Real Blind Insight Integration** - Creates actual datasets and schemas
- 📊 **Data Import** - Imports actual data from BigQuery into Blind Insight
- 🛡️ **Blind Proxy Integration** - Uses the official Blind Proxy for encryption

## Architecture

- **Frontend**: React application served via Python HTTP server
- **Backend**: Express.js server with BigQuery and Blind Proxy integration
- **Database**: Google BigQuery
- **Schema Conversion**: Custom BigQuery to JSON Schema converter
- **Blind Integration**: Blind Proxy CLI for dataset/schema creation and data import

## Prerequisites

- Node.js (v14 or higher)
- Python 3 (for serving the frontend)
- Google Cloud Project with BigQuery enabled
- Google Cloud Service Account with BigQuery permissions
- **Blind Proxy CLI** installed and authenticated

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/blind-insight/importer.git
cd importer
```

Install backend dependencies:

```bash
cd cube-server
npm install
cd ..
```

### 2. Blind Proxy Setup

**Important**: The Blind Proxy must be installed and authenticated before running this application.

1. **Download the Blind Proxy** from the [Blind Insight documentation](https://docs.blindinsight.io/)
2. **Install the Blind Proxy** in the parent directory of this project:

   ```bash
   # The Blind Proxy should be located at: ../blind/blind
   ls -la ../blind/blind
   ```

3. **Authenticate with Blind Insight**:

   ```bash
   ../blind/blind login
   ```

4. **Verify authentication**:

   ```bash
   ../blind/blind organization list
   ```

   You should see your Blind Insight organizations listed.

### 3. Google Cloud Setup

1. Create a Google Cloud Project
2. Enable the BigQuery API
3. Create a Service Account with BigQuery permissions:
   - BigQuery Data Viewer
   - BigQuery Job User
4. Download the service account key file (JSON)

### 4. Environment Configuration

Create a `.env` file in the `cube-server` directory:

```bash
cd cube-server
cp env.example .env
```

Edit the `.env` file with your Google Cloud credentials:

```env
# BigQuery Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_KEY_FILE=path/to/your/service-account-key.json

# Server Configuration
PORT=3001
NODE_ENV=development
```

### 5. Running the Application

**Start the backend server:**

```bash
cd cube-server
node index.js
```

You should see:

```no-highlight
🚀 Test Schema converter API is running on port 3001
🔧 Configure BigQuery credentials in .env file for real data
```

**Start the frontend (in a new terminal):**

```bash
# From the project root directory
python3 -m http.server 3000
```

You should see:

```no-highlight
Serving HTTP on :: port 3000 (http://[::]:3000/) ...
```

### 6. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:3001

## Usage

1. Open http://localhost:3000 in your browser
2. Enter your BigQuery credentials:
   - **Project ID**: Your Google Cloud project ID
   - **Service Account Key**: Upload your JSON service account key file
   - **Dataset ID**: The BigQuery dataset containing your table
   - **Table ID**: The BigQuery table to import
3. Enter Blind Insight details:
   - **Organization**: Your Blind Insight organization slug (e.g., `blind-insight-demo`)
   - **Dataset Name**: Name for the new Blind Insight dataset
   - **Schema Name**: Name for the new Blind Insight schema
4. Click "Convert Schema" to:
   - Extract the BigQuery schema
   - Convert it to JSON Schema format
   - Create a new dataset in Blind Insight
   - Create a new schema in Blind Insight
   - Import the actual data from BigQuery into Blind Insight

## API Endpoints

- `GET /api/health` - Health check endpoint
- `GET /api/blind/status` - Check Blind Proxy authentication status
- `POST /api/blind/create-schema` - Create dataset, schema, and import data

## Troubleshooting

### Common Issues and Solutions

#### 1. "Cannot find module '@cubejs-backend/server'"

**Solution**: The app no longer uses Cube.js. Make sure you're using the updated `index.js` file.

#### 2. "Failed to execute command: spawn /path/to/blind/blind ENOENT"

**Solution**:

- Ensure the Blind Proxy is installed at `../blind/blind`
- Check that the Blind Proxy executable has proper permissions: `chmod +x ../blind/blind`

#### 3. "Please run: ./blind login"

**Solution**:

- Authenticate with Blind Insight: `../blind/blind login`
- Verify authentication: `../blind/blind organization list`

#### 4. "npm start" fails with "Could not read package.json"

**Solution**:

- This is a standalone HTML/JS app, not a React app with npm scripts
- Use `python3 -m http.server 3000` to serve the frontend

#### 5. BigQuery authentication errors

**Solution**:

- Verify your service account key file is valid
- Ensure the service account has proper BigQuery permissions
- Check that the project ID is correct

#### 6. "Dataset not found" errors

**Solution**:

- Verify the dataset ID and table ID exist in your BigQuery project
- Ensure your service account has access to the dataset

### Debug Mode

Set `NODE_ENV=development` in your `.env` file to enable detailed error logging.

### Testing the Integration

Test the Blind Proxy integration:

```bash
curl http://localhost:3001/api/blind/status
```

You should see:

```json
{
  "authenticated": true,
  "organizations": "[...]",
  "suggestion": "Use one of the organization slugs shown above"
}
```

## Project Structure

```no-highlight
importer/
├── index.html              # Main React application (CDN-based)
├── src/                    # React components
├── cube-server/
│   ├── index.js           # Express.js backend with Blind Proxy integration
│   ├── package.json       # Backend dependencies
│   └── .env              # Environment configuration
├── blind/                 # Blind Proxy CLI (should be in parent directory)
└── README.md
```

## Schema Conversion

The application converts BigQuery data types to JSON Schema types as follows:

| BigQuery Type  | JSON Schema Type     |
| -------------- | -------------------- |
| STRING         | string               |
| INTEGER/INT64  | integer              |
| FLOAT/NUMERIC  | number               |
| BOOLEAN/BOOL   | boolean              |
| TIMESTAMP/DATE | string (with format) |
| RECORD         | object               |
| REPEATED       | array                |

## Development

### Adding New Features

1. Backend changes: Edit `cube-server/index.js`
2. Frontend changes: Edit `index.html` (React components in script tags)
3. Styling: Update CSS in `index.html`

### Testing

```bash
# Test API endpoints
curl http://localhost:3001/api/health

# Test Blind Proxy integration
curl http://localhost:3001/api/blind/status

# Test schema extraction (requires valid BigQuery credentials)
curl -X POST http://localhost:3001/api/bigquery/schema \
  -H "Content-Type: application/json" \
  -d '{"projectId":"your-project","datasetId":"your-dataset","tableId":"your-table"}'
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with real BigQuery data and Blind Insight
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
