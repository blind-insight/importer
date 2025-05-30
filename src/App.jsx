import { useState } from 'react'
import './App.css'

// Mock BigQuery schema for testing
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

function App() {
  const [datasetId, setDatasetId] = useState('')
  const [tableId, setTableId] = useState('')
  const [jsonSchema, setJsonSchema] = useState(null)
  const [bigQuerySchema, setBigQuerySchema] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('json')

  const convertFieldToJsonSchema = (field) => {
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
            property.properties[subField.name] = convertFieldToJsonSchema(subField);
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
  };

  const convertToJsonSchema = (bgSchema, tableName) => {
    const schema = {
      type: 'object',
      title: tableName,
      properties: {},
      required: []
    };

    bgSchema.fields.forEach(field => {
      const property = convertFieldToJsonSchema(field);
      schema.properties[field.name] = property;
      
      if (field.mode === 'REQUIRED') {
        schema.required.push(field.name);
      }
    });

    return schema;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!datasetId.trim() || !tableId.trim()) {
      alert('Please enter both dataset ID and table ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // For now, use mock data. In production, this would call your API
      const response = await fetch(`http://localhost:3001/api/datasets/${datasetId}/tables/${tableId}/schema`);
      
      let data;
      if (response.ok) {
        data = await response.json();
        setBigQuerySchema(data.bigQuerySchema);
        setJsonSchema(data.jsonSchema);
      } else {
        // Fallback to mock data if API isn't available
        setBigQuerySchema(mockBigQuerySchema);
        setJsonSchema(convertToJsonSchema(mockBigQuerySchema, tableId));
      }
    } catch (err) {
      // Use mock data as fallback
      setBigQuerySchema(mockBigQuerySchema);
      setJsonSchema(convertToJsonSchema(mockBigQuerySchema, tableId));
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Schema copied to clipboard!');
    });
  };

  const downloadSchema = (schema, filename) => {
    const dataStr = JSON.stringify(schema, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', filename);
    linkElement.click();
  };

  return (
    <div className="app">
      <header className="header">
        <h1>BigQuery Schema to JSON Schema Converter</h1>
        <p>Convert BigQuery table schemas to JSON Schema format</p>
      </header>

      <main className="main">
        <div className="converter-form">
          <h2>Extract BigQuery Schema</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="datasetId">Dataset ID:</label>
              <input
                type="text"
                id="datasetId"
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
                placeholder="Enter BigQuery dataset ID"
                disabled={loading}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="tableId">Table ID:</label>
              <input
                type="text"
                id="tableId"
                value={tableId}
                onChange={(e) => setTableId(e.target.value)}
                placeholder="Enter BigQuery table ID"
                disabled={loading}
                required
              />
            </div>
            
            <button type="submit" disabled={loading}>
              {loading ? 'Converting...' : 'Convert Schema'}
            </button>
          </form>

          {error && (
            <div className="error">
              <h3>Error:</h3>
              <p>{error}</p>
            </div>
          )}
        </div>

        {jsonSchema && (
          <div className="results">
            <h2>Schema Results for: {tableId}</h2>
            
            <div className="tabs">
              <button 
                className={activeTab === 'json' ? 'active' : ''}
                onClick={() => setActiveTab('json')}
              >
                JSON Schema
              </button>
              <button 
                className={activeTab === 'bigquery' ? 'active' : ''}
                onClick={() => setActiveTab('bigquery')}
              >
                BigQuery Schema
              </button>
            </div>

            <div className="tab-content">
              {activeTab === 'json' && (
                <div className="schema-section">
                  <div className="schema-header">
                    <h3>JSON Schema</h3>
                    <div className="actions">
                      <button onClick={() => copyToClipboard(JSON.stringify(jsonSchema, null, 2))}>
                        Copy
                      </button>
                      <button onClick={() => downloadSchema(jsonSchema, `${tableId}_json_schema.json`)}>
                        Download
                      </button>
                    </div>
                  </div>
                  <pre className="schema-content">
                    {JSON.stringify(jsonSchema, null, 2)}
                  </pre>
                </div>
              )}
              
              {activeTab === 'bigquery' && (
                <div className="schema-section">
                  <div className="schema-header">
                    <h3>Original BigQuery Schema</h3>
                    <div className="actions">
                      <button onClick={() => copyToClipboard(JSON.stringify(bigQuerySchema, null, 2))}>
                        Copy
                      </button>
                      <button onClick={() => downloadSchema(bigQuerySchema, `${tableId}_bigquery_schema.json`)}>
                        Download
                      </button>
                    </div>
                  </div>
                  <pre className="schema-content">
                    {JSON.stringify(bigQuerySchema, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App 