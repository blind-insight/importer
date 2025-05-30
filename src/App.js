import React, { useState } from 'react';
import './App.css';
import SchemaConverter from './components/SchemaConverter';
import SchemaDisplay from './components/SchemaDisplay';

function App() {
  const [schemaData, setSchemaData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSchemaFetch = async (datasetId, tableId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:3001/api/datasets/${datasetId}/tables/${tableId}/schema`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setSchemaData(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching schema:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>BigQuery Schema to JSON Schema Converter</h1>
        <p>Convert BigQuery table schemas to JSON Schema format using Cube.js</p>
      </header>
      
      <main className="App-main">
        <div className="converter-container">
          <SchemaConverter 
            onSchemaFetch={handleSchemaFetch}
            loading={loading}
            error={error}
          />
          
          {schemaData && (
            <SchemaDisplay 
              schemaData={schemaData}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App; 