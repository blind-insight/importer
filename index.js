const CubejsServer = require('@cubejs-backend/server');
const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// BigQuery Schema Extractor
const { BigQuery } = require('@google-cloud/bigquery');

class BigQuerySchemaExtractor {
  constructor() {
    this.bigquery = new BigQuery({
      projectId: process.env.GOOGLE_CLOUD_PROJECT_ID,
      keyFilename: process.env.GOOGLE_CLOUD_KEY_FILE
    });
  }

  async extractTableSchema(datasetId, tableId) {
    try {
      const [metadata] = await this.bigquery
        .dataset(datasetId)
        .table(tableId)
        .getMetadata();
      
      return metadata.schema;
    } catch (error) {
      console.error('Error extracting schema:', error);
      throw error;
    }
  }

  async listTablesInDataset(datasetId) {
    try {
      const [tables] = await this.bigquery.dataset(datasetId).getTables();
      return tables.map(table => table.id);
    } catch (error) {
      console.error('Error listing tables:', error);
      throw error;
    }
  }

  convertToJsonSchema(bigQuerySchema, tableName) {
    const jsonSchema = {
      type: 'object',
      title: tableName,
      properties: {},
      required: []
    };

    bigQuerySchema.fields.forEach(field => {
      const property = this.convertFieldToJsonSchema(field);
      jsonSchema.properties[field.name] = property;
      
      if (field.mode === 'REQUIRED') {
        jsonSchema.required.push(field.name);
      }
    });

    return jsonSchema;
  }

  convertFieldToJsonSchema(field) {
    const property = {
      description: field.description || ''
    };

    // Map BigQuery types to JSON Schema types
    switch (field.type) {
      case 'STRING':
        property.type = 'string';
        break;
      case 'INTEGER':
      case 'INT64':
        property.type = 'integer';
        break;
      case 'FLOAT':
      case 'FLOAT64':
      case 'NUMERIC':
      case 'BIGNUMERIC':
        property.type = 'number';
        break;
      case 'BOOLEAN':
      case 'BOOL':
        property.type = 'boolean';
        break;
      case 'TIMESTAMP':
      case 'DATETIME':
      case 'DATE':
      case 'TIME':
        property.type = 'string';
        property.format = field.type.toLowerCase();
        break;
      case 'RECORD':
        property.type = 'object';
        property.properties = {};
        if (field.fields) {
          field.fields.forEach(subField => {
            property.properties[subField.name] = this.convertFieldToJsonSchema(subField);
          });
        }
        break;
      default:
        property.type = 'string';
    }

    // Handle arrays
    if (field.mode === 'REPEATED') {
      return {
        type: 'array',
        items: property,
        description: field.description || ''
      };
    }

    return property;
  }
}

// API Routes
const schemaExtractor = new BigQuerySchemaExtractor();

app.get('/api/datasets/:datasetId/tables', async (req, res) => {
  try {
    const { datasetId } = req.params;
    const tables = await schemaExtractor.listTablesInDataset(datasetId);
    res.json({ tables });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/datasets/:datasetId/tables/:tableId/schema', async (req, res) => {
  try {
    const { datasetId, tableId } = req.params;
    const bigQuerySchema = await schemaExtractor.extractTableSchema(datasetId, tableId);
    const jsonSchema = schemaExtractor.convertToJsonSchema(bigQuerySchema, tableId);
    
    res.json({
      tableName: tableId,
      bigQuerySchema,
      jsonSchema
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'BigQuery Schema Converter API is running' });
});

// Cube.js server
const server = new CubejsServer({
  port: process.env.CUBEJS_API_PORT || 4000,
});

server.listen().then(({ app: cubeApp, port }) => {
  console.log(`🚀 Cube.js server is running on port ${port}`);
});

// Start Express server
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`🚀 Schema converter API is running on port ${PORT}`);
});

module.exports = app; 