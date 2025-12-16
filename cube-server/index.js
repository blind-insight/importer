const express = require('express');
const cors = require('cors');
const { BigQuery } = require('@google-cloud/bigquery');
const path = require('path');
const { exec } = require('child_process');
const fs = require('fs');
const os = require('os');

const app = express();
app.use(cors());
app.use(express.json({ limit: '10mb' })); // Increase limit for service account keys

// Mock schema data for testing
const mockBigQuerySchema = {
  fields: [
    {
      name: 'id',
      type: 'INTEGER',
      mode: 'REQUIRED',
      description: 'Unique identifier'
    },
    {
      name: 'name',
      type: 'STRING',
      mode: 'NULLABLE',
      description: 'User name'
    },
    {
      name: 'email',
      type: 'STRING',
      mode: 'REQUIRED',
      description: 'User email address'
    },
    {
      name: 'created_at',
      type: 'TIMESTAMP',
      mode: 'REQUIRED',
      description: 'Record creation timestamp'
    },
    {
      name: 'tags',
      type: 'STRING',
      mode: 'REPEATED',
      description: 'User tags'
    }
  ]
};

// Helper function to parse BigQuery identifiers
function parseDatasetTableId(projectId, datasetId, tableId) {
  // Clean and parse dataset ID
  let cleanDatasetId = datasetId;
  if (datasetId.includes('.')) {
    // If dataset contains dots, take the last part
    const parts = datasetId.split('.');
    cleanDatasetId = parts[parts.length - 1];
  }
  
  // Clean and parse table ID
  let cleanTableId = tableId;
  if (tableId.includes('.')) {
    // If table contains dots, take the last part
    const parts = tableId.split('.');
    cleanTableId = parts[parts.length - 1];
  }
  
  return {
    projectId: projectId.trim(),
    datasetId: cleanDatasetId.trim(),
    tableId: cleanTableId.trim()
  };
}

// Real BigQuery Schema Converter
class BigQuerySchemaConverter {
  constructor(bigQueryInstance) {
    this.bigquery = bigQueryInstance;
  }

  async getTableSchema(datasetId, tableId) {
    try {
      const dataset = this.bigquery.dataset(datasetId);
      const table = dataset.table(tableId);
      const [metadata] = await table.getMetadata();
      return metadata.schema;
    } catch (error) {
      throw new Error(`Failed to fetch table schema: ${error.message}`);
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

// Mock Schema Converter (for testing)
class MockSchemaConverter {
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
      default:
        property.type = 'string';
    }

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

const mockConverter = new MockSchemaConverter();

// API Routes
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    message: 'BigQuery Schema Converter API is running (Test Mode)',
    timestamp: new Date().toISOString()
  });
});

app.get('/api/datasets/:datasetId/tables', async (req, res) => {
  const { datasetId } = req.params;
  
  // Mock response
  res.json({ 
    tables: ['users', 'orders', 'products', 'analytics'],
    dataset: datasetId,
    note: 'This is mock data for testing'
  });
});

app.get('/api/datasets/:datasetId/tables/:tableId/schema', async (req, res) => {
  const { datasetId, tableId } = req.params;
  
  try {
    const jsonSchema = mockConverter.convertToJsonSchema(mockBigQuerySchema, tableId);
    
    res.json({
      tableName: tableId,
      dataset: datasetId,
      bigQuerySchema: mockBigQuerySchema,
      jsonSchema,
      note: 'This is mock data for testing. Configure real BigQuery credentials in .env file.'
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// New endpoint for authenticated BigQuery access
app.post('/api/bigquery/schema', async (req, res) => {
  try {
    const { projectId, serviceAccountKey, datasetId, tableId } = req.body;

    // Validate required fields
    if (!projectId || !serviceAccountKey || !datasetId || !tableId) {
      return res.status(400).json({
        error: 'Missing required fields: projectId, serviceAccountKey, datasetId, tableId'
      });
    }

    // Validate service account key format - comprehensive check
    if (typeof serviceAccountKey !== 'object') {
      return res.status(400).json({
        error: 'Service account key must be a JSON object'
      });
    }
    
    const requiredFields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id'];
    const missingFields = requiredFields.filter(field => !serviceAccountKey[field]);
    
    if (missingFields.length > 0) {
      return res.status(400).json({
        error: `Service account key is missing required fields: ${missingFields.join(', ')}`,
        provided: Object.keys(serviceAccountKey),
        required: requiredFields,
        suggestion: 'Please download a complete service account key JSON file from Google Cloud Console'
      });
    }

    // Parse and clean identifiers
    const { projectId: cleanProjectId, datasetId: cleanDatasetId, tableId: cleanTableId } = parseDatasetTableId(projectId, datasetId, tableId);

    console.log('🔍 Input received:');
    console.log(`   Project ID: "${projectId}"`);
    console.log(`   Dataset ID: "${datasetId}"`);
    console.log(`   Table ID: "${tableId}"`);
    console.log('🔧 Parsed identifiers:');
    console.log(`   Clean Project ID: "${cleanProjectId}"`);
    console.log(`   Clean Dataset ID: "${cleanDatasetId}"`);
    console.log(`   Clean Table ID: "${cleanTableId}"`);

    // Initialize BigQuery with service account credentials
    const bigquery = new BigQuery({
      projectId: cleanProjectId,
      credentials: serviceAccountKey
    });

    const converter = new BigQuerySchemaConverter(bigquery);
    
    console.log(`📍 Fetching schema for: ${cleanProjectId}.${cleanDatasetId}.${cleanTableId}`);
    const schema = await converter.getTableSchema(cleanDatasetId, cleanTableId);
    const jsonSchema = converter.convertToJsonSchema(schema, cleanTableId);
    
    console.log(`✅ Successfully fetched schema for ${cleanProjectId}.${cleanDatasetId}.${cleanTableId}`);

    res.json({
      tableName: cleanTableId,
      dataset: cleanDatasetId,
      project: cleanProjectId,
      bigQuerySchema: schema,
      jsonSchema
    });
  } catch (error) {
    console.error('❌ BigQuery API Error:', error);
    res.status(500).json({ error: error.message });
  }
});

// New endpoint for Blind Insight integration
app.post('/api/blind/create-schema', async (req, res) => {
  const { spawn } = require('child_process');
  
  try {
    const { 
      organization, 
      createNewDataset, 
      datasetName, 
      datasetSlug, 
      schemaName, 
      schemaSlug, 
      fields 
    } = req.body;

    // Validate required fields
    if (!organization || !datasetSlug || !schemaName || !schemaSlug || !fields || fields.length === 0) {
      return res.status(400).json({
        error: 'Missing required fields: organization, datasetSlug, schemaName, schemaSlug, fields'
      });
    }

    console.log('🔐 Blind Integration Request:');
    console.log(`   Organization: ${organization}`);
    console.log(`   Create Dataset: ${createNewDataset}`);
    console.log(`   Dataset: ${datasetSlug} (${datasetName || 'existing'})`);
    console.log(`   Schema: ${schemaSlug} (${schemaName})`);
    console.log(`   Fields: ${fields.join(', ')}`);

    // Path to the blind executable
    const blindPath = path.join(process.cwd(), '../../blind/blind');
    
    // Function to execute blind command
    const executeBlindCommand = (args) => {
      return new Promise((resolve, reject) => {
        console.log(`🚀 Executing: ${blindPath} ${args.join(' ')}`);
        
        const blindProcess = spawn(blindPath, args, {
          stdio: ['pipe', 'pipe', 'pipe']
        });

        let stdout = '';
        let stderr = '';

        blindProcess.stdout.on('data', (data) => {
          stdout += data.toString();
        });

        blindProcess.stderr.on('data', (data) => {
          stderr += data.toString();
        });

        blindProcess.on('close', (code) => {
          console.log(`📋 Command output (code ${code}):`);
          console.log(`   stdout: ${stdout}`);
          console.log(`   stderr: ${stderr}`);
          
          if (code === 0) {
            resolve({ stdout, stderr });
          } else {
            reject(new Error(`Blind command failed with code ${code}: ${stderr || stdout}`));
          }
        });

        blindProcess.on('error', (error) => {
          reject(new Error(`Failed to execute blind command: ${error.message}`));
        });
      });
    };

    // Step 0: Check authentication and organization access
    console.log('🔍 Checking Blind authentication and organization access...');
    try {
      const orgListResult = await executeBlindCommand(['organization', 'list']);
      console.log('✅ Authentication successful. Available organizations:');
      console.log(orgListResult.stdout);
      
      // Check if the requested organization exists in the list
      if (!orgListResult.stdout.toLowerCase().includes(`"slug": "${organization}"`)) {
        return res.status(400).json({
          error: `Organization '${organization}' not found or no access. Available organizations: ${orgListResult.stdout}`,
          suggestion: 'Please check your organization slug or ensure you have access to it.'
        });
      }
    } catch (authError) {
      console.log('❌ Authentication check failed:', authError.message);
      return res.status(401).json({
        error: 'Blind authentication failed. Please ensure you are logged in.',
        details: authError.message,
        suggestion: 'Run: ./blind login'
      });
    }

    // Step 1: Create dataset if requested
    if (createNewDataset && datasetName) {
      try {
        console.log(`📦 Creating dataset: ${datasetName} (${datasetSlug})`);
        const datasetArgs = [
          'dataset', 'create',
          '--organization', organization,
          '--name', datasetName,
          '--slug', datasetSlug
        ];
        
        await executeBlindCommand(datasetArgs);
        console.log(`✅ Dataset created successfully: ${datasetSlug}`);
      } catch (error) {
        // If dataset already exists, that's OK
        if (error.message.includes('already exists') || error.message.includes('duplicate')) {
          console.log(`ℹ️  Dataset ${datasetSlug} already exists, continuing...`);
        } else if (error.message.includes('400 Bad Request')) {
          console.log(`⚠️  Blind API returned 400 Bad Request - this might be a temporary API issue. Continuing without dataset creation...`);
          console.log(`   You may need to create the dataset '${datasetSlug}' manually in Blind Insight`);
        } else {
          throw error;
        }
      }
    }

    // Step 2: Create schema
    console.log(`📋 Creating schema: ${schemaName} (${schemaSlug})`);
    
    // Create temporary schema file
    const tempSchemaFile = path.join(os.tmpdir(), `blind-schema-${Date.now()}.json`);
    
    // Convert fields to Blind JSON Schema format (must be valid JSON Schema)
    const schemaDefinition = {
      type: "object",
      properties: {}
    };
    
    // Parse field definitions (format: "fieldname:type")
    fields.forEach(field => {
      const [fieldName, fieldType] = field.split(':');
      if (fieldName && fieldType) {
        let propertyDef = {};
        
        // Convert to JSON Schema format
        switch (fieldType.toLowerCase()) {
          case 'string':
            propertyDef = {
              type: "string"
            };
            break;
          case 'integer':
            propertyDef = {
              type: "integer",
              minimum: 0,
              maximum: 999999999
            };
            break;
          case 'number':
            propertyDef = {
              type: "number",
              minimum: 0,
              maximum: 999999999,
              precision: 2
            };
            break;
          case 'boolean':
            propertyDef = {
              type: "boolean"
            };
            break;
          default:
            propertyDef = {
              type: "string"
            };
        }
        
        schemaDefinition.properties[fieldName] = propertyDef;
        // schemaDefinition.required.push(fieldName);  // Don't make all fields required by default
      }
    });
    
    // Write JSON Schema definition to temporary file
    fs.writeFileSync(tempSchemaFile, JSON.stringify(schemaDefinition, null, 2));
    console.log(`📄 Created temporary JSON Schema file: ${tempSchemaFile}`);
    console.log(`📄 JSON Schema content: ${JSON.stringify(schemaDefinition, null, 2)}`);
    
    try {
      const schemaArgs = [
        'schema', 'create',
        '--organization', organization,
        '--dataset', datasetSlug,
        '--name', schemaName,
        '--slug', schemaSlug,
        '--file', tempSchemaFile
      ];

      const schemaResult = await executeBlindCommand(schemaArgs);
      console.log(`✅ Schema created successfully: ${schemaSlug}`);
      
      // Clean up temporary file
      fs.unlinkSync(tempSchemaFile);
      console.log(`🗑️ Cleaned up temporary file: ${tempSchemaFile}`);

      // Step 3: Fetch BigQuery data and insert into Blind schema
      console.log(`📊 Fetching data from BigQuery table and inserting into Blind schema...`);
      
      let insertedRecords = 0;
      let dataInsertionError = null;
      
      try {
        // Get the original BigQuery request data from the request body
        const { projectId, serviceAccountKey, datasetId, tableId } = req.body;
        
        console.log(`🔍 BigQuery connection info:
   Project ID: ${projectId}
   Dataset ID: ${datasetId}
   Table ID: ${tableId}
   Service Account: ${serviceAccountKey ? 'provided' : 'null'}`);
        
        if (!projectId || !datasetId || !tableId) {
          console.log(`⚠️ Skipping data insertion - missing BigQuery connection info`);
          dataInsertionError = 'Missing BigQuery connection info (projectId, datasetId, or tableId)';
        } else {
          // Fetch data from BigQuery
          console.log(`📥 Fetching data from ${projectId}.${datasetId}.${tableId}...`);
          
          let bigQueryData;
          if (serviceAccountKey) {
            // Use real BigQuery connection - run query from user's project
            const userProjectId = serviceAccountKey.project_id; // Get user's project from service account
            const bigquery = new BigQuery({
              projectId: userProjectId, // Use user's project for running jobs
              keyFilename: null,
              credentials: serviceAccountKey
            });
            
            const query = `SELECT * FROM \`${projectId}.${datasetId}.${tableId}\` LIMIT 100`;
            console.log(`🔍 Executing query from project ${userProjectId}: ${query}`);
            
            const [rows] = await bigquery.query({ 
              query,
              location: 'US' // Specify location for public datasets
            });
            bigQueryData = rows;
            console.log(`✅ Fetched ${rows.length} rows from BigQuery`);
          } else {
            // For public data queries without service account, we can't run queries
            // This should not happen since we're checking for projectId/datasetId/tableId
            throw new Error('Service account required for data queries');
          }
          
          if (bigQueryData && bigQueryData.length > 0) {
            // Create temporary file with the data for Blind insertion
            const tempDataFile = path.join(os.tmpdir(), `blind-data-${Date.now()}.json`);
            
            // Convert BigQuery data to format expected by Blind - each record must be wrapped in "data" object
            const blindData = bigQueryData.map(row => {
              const convertedRow = {};
              Object.keys(row).forEach(key => {
                const value = row[key];
                if (value !== null && value !== undefined) {
                  // Find the field definition to determine the correct type
                  const fieldDef = fields.find(field => field.split(':')[0] === key);
                  if (fieldDef) {
                    const fieldType = fieldDef.split(':')[1].toLowerCase();
                    
                    // Convert to the correct type based on the field definition
                    switch (fieldType) {
                      case 'integer':
                        // Handle BigQuery integers - they come as strings or numbers
                        const intValue = typeof value === 'object' && value.value ? value.value : value;
                        const parsedInt = parseInt(String(intValue), 10);
                        convertedRow[key] = isNaN(parsedInt) ? 0 : parsedInt;
                        break;
                      case 'number':
                        // Handle BigQuery numbers - they come as strings or numbers
                        const numValue = typeof value === 'object' && value.value ? value.value : value;
                        const parsedFloat = parseFloat(String(numValue));
                        convertedRow[key] = isNaN(parsedFloat) ? 0.0 : parsedFloat;
                        break;
                      case 'boolean':
                        const boolValue = typeof value === 'object' && value.value ? value.value : value;
                        convertedRow[key] = Boolean(boolValue);
                        break;
                      default:
                        // Handle strings and dates
                        if (typeof value === 'object') {
                          if (value instanceof Date) {
                            convertedRow[key] = value.toISOString();
                          } else if (value.value !== undefined) {
                            convertedRow[key] = String(value.value);
                          } else {
                            convertedRow[key] = JSON.stringify(value);
                          }
                        } else {
                          convertedRow[key] = String(value);
                        }
                    }
                  } else {
                    // If no field definition found, keep as string with proper object handling
                    if (typeof value === 'object') {
                      if (value instanceof Date) {
                        convertedRow[key] = value.toISOString();
                      } else if (value.value !== undefined) {
                        convertedRow[key] = String(value.value);
                      } else {
                        convertedRow[key] = JSON.stringify(value);
                      }
                    } else {
                      convertedRow[key] = String(value);
                    }
                  }
                } else {
                  // Handle null/undefined values - convert to appropriate defaults for each type
                  const fieldDef = fields.find(field => field.split(':')[0] === key);
                  if (fieldDef) {
                    const fieldType = fieldDef.split(':')[1].toLowerCase();
                    switch (fieldType) {
                      case 'integer':
                        convertedRow[key] = 0;
                        break;
                      case 'number':
                        convertedRow[key] = 0.0;
                        break;
                      case 'boolean':
                        convertedRow[key] = false;
                        break;
                      default:
                        convertedRow[key] = '';
                    }
                  } else {
                    convertedRow[key] = '';
                  }
                }
              });
              // Blind Insight expects each record wrapped in a "data" object
              return { data: convertedRow };
            });
            
            fs.writeFileSync(tempDataFile, JSON.stringify(blindData, null, 2));
            console.log(`📄 Created temporary data file: ${tempDataFile}`);
            console.log(`📄 Sample data (first record): ${JSON.stringify(blindData[0], null, 2)}`);
            
            // Insert data using Blind CLI
            const insertArgs = [
              'record', 'create',
              '--organization', organization,
              '--dataset', datasetSlug,
              '--schema', schemaSlug,
              '--file', tempDataFile
            ];
            
            const insertResult = await executeBlindCommand(insertArgs);
            
            // Parse the result to get record count
            try {
              const resultJson = JSON.parse(insertResult.stdout);
              insertedRecords = resultJson.count || bigQueryData.length;
            } catch (parseError) {
              // If parsing fails, assume all records were inserted
              insertedRecords = bigQueryData.length;
            }
            
            console.log(`✅ Successfully inserted ${insertedRecords} records into Blind schema`);
            
            // Clean up temporary file
            try {
              fs.unlinkSync(tempDataFile);
              console.log(`🗑️ Cleaned up temporary data file: ${tempDataFile}`);
            } catch (cleanupError) {
              console.log(`⚠️ Could not clean up temporary data file: ${cleanupError.message}`);
            }
          } else {
            dataInsertionError = 'No data found in BigQuery table';
            console.log(`⚠️ No data found in BigQuery table`);
          }
        }
      } catch (error) {
        dataInsertionError = error.message;
        console.log(`❌ Data insertion error: ${error}`);
      }

      // Return success response with data insertion status
      const successMessage = insertedRecords > 0 
        ? `Blind schema created successfully and ${insertedRecords} records imported` 
        : dataInsertionError 
          ? `Blind schema created successfully but data import failed: ${dataInsertionError}`
          : 'Blind schema created successfully (no data import attempted)';

      return res.json({
        success: true,
        message: successMessage,
        organization,
        dataset: datasetSlug,
        schema: schemaSlug,
        fields,
        jsonSchema: schemaDefinition,
        recordsImported: insertedRecords,
        dataImportError: dataInsertionError
      });
      
    } catch (error) {
      // Clean up temporary file even on error
      try {
        fs.unlinkSync(tempSchemaFile);
        console.log(`🗑️ Cleaned up temporary file after error: ${tempSchemaFile}`);
      } catch (cleanupError) {
        console.log(`⚠️ Could not clean up temporary file: ${cleanupError.message}`);
      }
      
      // Handle 400 Bad Request errors gracefully
      if (error.message.includes('400 Bad Request')) {
        console.log(`⚠️ Blind API returned 400 Bad Request for schema creation. This might be due to:`);
        console.log(`   - Dataset '${datasetSlug}' doesn't exist`);
        console.log(`   - Schema '${schemaSlug}' already exists`);
        console.log(`   - API permissions issue`);
        console.log(`   - Temporary API service issue`);
        
        return res.status(400).json({
          success: false,
          message: `Schema creation failed due to Blind API 400 error. Please check if dataset '${datasetSlug}' exists and schema '${schemaSlug}' is unique.`,
          organization,
          dataset: datasetSlug,
          schema: schemaSlug,
          fields,
          jsonSchema: schemaDefinition,
          error: 'Blind API returned 400 Bad Request',
          suggestion: 'Try creating the dataset manually in Blind Insight first, or use a different schema name.',
          troubleshooting: {
            step1: `Check if dataset '${datasetSlug}' exists in Blind Insight`,
            step2: `Try a different schema name (current: '${schemaSlug}')`,
            step3: 'Verify your Blind Insight permissions',
            step4: 'Check Blind API status'
          }
        });
      }
      
      throw error;
    }

  } catch (error) {
    console.error('❌ Blind Integration Error:', error);
    return res.status(500).json({ 
      error: error.message,
      details: 'Make sure the Blind Proxy is installed and you are logged in'
    });
  }
});

// New endpoint to check Blind authentication status
app.get('/api/blind/status', async (req, res) => {
  const { spawn } = require('child_process');
  
  try {
    const blindPath = path.join(process.cwd(), '../../blind/blind');
    
    const executeBlindCommand = (args) => {
      return new Promise((resolve, reject) => {
        const blindProcess = spawn(blindPath, args, {
          stdio: ['pipe', 'pipe', 'pipe']
        });

        let stdout = '';
        let stderr = '';

        blindProcess.stdout.on('data', (data) => {
          stdout += data.toString();
        });

        blindProcess.stderr.on('data', (data) => {
          stderr += data.toString();
        });

        blindProcess.on('close', (code) => {
          if (code === 0) {
            resolve({ stdout, stderr });
          } else {
            reject(new Error(`Command failed with code ${code}: ${stderr || stdout}`));
          }
        });

        blindProcess.on('error', (error) => {
          reject(new Error(`Failed to execute command: ${error.message}`));
        });
      });
    };

    // Check organizations
    const orgResult = await executeBlindCommand(['organization', 'list']);
    
    res.json({
      authenticated: true,
      organizations: orgResult.stdout,
      suggestion: 'Use one of the organization slugs shown above'
    });

  } catch (error) {
    res.status(401).json({
      authenticated: false,
      error: error.message,
      suggestion: 'Please run: ./blind login'
    });
  }
});

// New endpoint to query data from Blind Insight for Jupyter/ML use cases
// Supports encrypted search, filtering, and aggregations
app.post('/api/blind/query', async (req, res) => {
  const { spawn } = require('child_process');
  
  try {
    const { 
      organization, 
      datasetSlug, 
      schemaSlug,
      limit = 1000,
      offset = 0,
      filters = [],  // Array of filter strings like ["age:>40", "name:John"]
      decrypt = false  // Only decrypt when explicitly requested (for ML use)
    } = req.body;

    // Sanitize numeric inputs (null/undefined/NaN fallback to defaults)
    const parsedLimit = Number.isFinite(Number(limit)) ? Number(limit) : 1000;
    const parsedOffset = Number.isFinite(Number(offset)) ? Number(offset) : 0;

    // Validate required fields
    if (!organization || !datasetSlug || !schemaSlug) {
      return res.status(400).json({
        error: 'Missing required fields: organization, datasetSlug, schemaSlug'
      });
    }

    console.log('📊 Blind Query Request:');
    console.log(`   Organization: ${organization}`);
    console.log(`   Dataset: ${datasetSlug}`);
    console.log(`   Schema: ${schemaSlug}`);
    console.log(`   Limit: ${parsedLimit}, Offset: ${parsedOffset}`);
    console.log(`   Filters: ${filters.length > 0 ? filters.join(', ') : 'none'}`);
    console.log(`   Decrypt: ${decrypt ? 'yes (for ML use)' : 'no (encrypted search)'}`);

    // Path to the blind executable
    const blindPath = path.join(process.cwd(), '../../blind/blind');
    
    // Function to execute blind command
    const executeBlindCommand = (args) => {
      return new Promise((resolve, reject) => {
        console.log(`🚀 Executing: ${blindPath} ${args.join(' ')}`);
        
        const blindProcess = spawn(blindPath, args, {
          stdio: ['pipe', 'pipe', 'pipe']
        });

        let stdout = '';
        let stderr = '';

        blindProcess.stdout.on('data', (data) => {
          stdout += data.toString();
        });

        blindProcess.stderr.on('data', (data) => {
          stderr += data.toString();
        });

        blindProcess.on('close', (code) => {
          console.log(`📋 Command output (code ${code}):`);
          console.log(`   stdout: ${stdout.substring(0, 500)}`);
          console.log(`   stderr: ${stderr}`);
          
          if (code === 0) {
            resolve({ stdout, stderr });
          } else {
            // Parse error message from stderr or stdout
            const errorMsg = stderr || stdout;
            // Check for common error patterns
            if (errorMsg.includes('404') || errorMsg.includes('Not Found')) {
              reject(new Error(`Dataset, schema, or organization not found: ${errorMsg}`));
            } else if (errorMsg.includes('400') || errorMsg.includes('Bad Request')) {
              reject(new Error(`Invalid request: ${errorMsg}`));
            } else {
              reject(new Error(`Blind command failed with code ${code}: ${errorMsg}`));
            }
          }
        });

        blindProcess.on('error', (error) => {
          reject(new Error(`Failed to execute blind command: ${error.message}`));
        });
      });
    };

    // Query records from Blind Insight using encrypted search
    // Blind Insight supports encrypted queries: =, <, >, min, max, count, avg, sum
    // Only decrypt when explicitly requested (for ML operations that need plaintext)
    const queryArgs = [
      'record', 'list',
      '--organization=' + organization,
      '--dataset=' + datasetSlug,
      '--schema=' + schemaSlug,
      '--limit=' + String(parsedLimit),
      '--offset=' + String(parsedOffset)
    ];
    
    // Add encrypted filters if provided
    if (filters && filters.length > 0) {
      filters.forEach(filter => {
        queryArgs.push('--filter', filter);
      });
    }
    
    // Only decrypt if explicitly requested (for ML use cases)
    if (decrypt) {
      queryArgs.push('--decrypt');
      console.log('   ⚠️  Decryption enabled - data will be decrypted for ML use');
    } else {
      console.log('   🔒 Using encrypted search - data remains encrypted');
    }

    const queryResult = await executeBlindCommand(queryArgs);
    
    // Parse the JSON response
    let records = [];
    try {
      const resultData = JSON.parse(queryResult.stdout);
      // Handle different possible response formats
      if (Array.isArray(resultData)) {
        records = resultData;
      } else if (resultData.records) {
        records = resultData.records;
      } else if (resultData.data) {
        records = resultData.data;
      } else {
        records = [resultData];
      }
      
      // Extract data from Blind format (records may be wrapped in "data" objects)
      records = records.map(record => {
        if (record.data) {
          return record.data;
        }
        return record;
      });
      
      console.log(`✅ Successfully queried ${records.length} records from Blind Insight`);
      
      res.json({
        success: true,
        count: records.length,
        records: records,
        organization,
        dataset: datasetSlug,
        schema: schemaSlug,
        encrypted: !decrypt,  // Indicate if data is still encrypted
        filters: filters || [],
        note: decrypt 
          ? 'Data has been decrypted for ML use' 
          : 'Data is encrypted - use encrypted search/filter capabilities'
      });
    } catch (parseError) {
      // If JSON parsing fails, this is a failure condition
      console.error(`❌ JSON parsing failed: ${parseError.message}`);
      console.error(`   Raw output: ${queryResult.stdout.substring(0, 500)}`);
      
      // Return failure status to accurately reflect the error
      return res.status(500).json({
        success: false,
        error: 'Failed to parse response from Blind Proxy',
        details: parseError.message,
        rawOutput: queryResult.stdout.substring(0, 1000),  // Limit size for response
        organization,
        dataset: datasetSlug,
        schema: schemaSlug,
        suggestion: 'The Blind Proxy may have returned an unexpected format. Check the raw output for details.'
      });
    }

  } catch (error) {
    console.error('❌ Blind Query Error:', error);
    
    // Determine appropriate HTTP status code based on error message
    let statusCode = 500;
    if (error.message.includes('not found') || error.message.includes('Not Found') || error.message.includes('404')) {
      statusCode = 404;
    } else if (error.message.includes('Bad Request') || error.message.includes('400') || error.message.includes('Invalid')) {
      statusCode = 400;
    } else if (error.message.includes('authentication') || error.message.includes('login')) {
      statusCode = 401;
    }
    
    return res.status(statusCode).json({ 
      success: false,
      error: error.message,
      details: 'Failed to query data from Blind Insight',
      suggestion: 'Check that the dataset, schema, and organization are correct. Ensure you are authenticated with Blind Insight.'
    });
  }
});

// Serve the HTML interface from parent directory
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'index.html'));
});

// Serve the logo file
app.get('/horizontal-light.svg', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'horizontal-light.svg'));
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`🚀 Test Schema converter API is running on port ${PORT}`);
  console.log(`�� This is running in test mode with mock data`);
  console.log(`🔧 Configure BigQuery credentials in .env file for real data`);
});

module.exports = app; 