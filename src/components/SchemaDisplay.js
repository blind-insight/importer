import React, { useState } from 'react';
import './SchemaDisplay.css';

const SchemaDisplay = ({ schemaData }) => {
  const [activeTab, setActiveTab] = useState('json');

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Schema copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy: ', err);
    });
  };

  const downloadSchema = (schema, filename) => {
    const dataStr = JSON.stringify(schema, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = filename;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="schema-display">
      <h2>Schema Results for: {schemaData.tableName}</h2>
      
      <div className="tab-container">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'json' ? 'active' : ''}`}
            onClick={() => setActiveTab('json')}
          >
            JSON Schema
          </button>
          <button 
            className={`tab ${activeTab === 'bigquery' ? 'active' : ''}`}
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
                <div className="schema-actions">
                  <button 
                    onClick={() => copyToClipboard(JSON.stringify(schemaData.jsonSchema, null, 2))}
                    className="action-button"
                  >
                    Copy
                  </button>
                  <button 
                    onClick={() => downloadSchema(schemaData.jsonSchema, `${schemaData.tableName}_json_schema.json`)}
                    className="action-button"
                  >
                    Download
                  </button>
                </div>
              </div>
              <pre className="schema-content">
                {JSON.stringify(schemaData.jsonSchema, null, 2)}
              </pre>
            </div>
          )}
          
          {activeTab === 'bigquery' && (
            <div className="schema-section">
              <div className="schema-header">
                <h3>Original BigQuery Schema</h3>
                <div className="schema-actions">
                  <button 
                    onClick={() => copyToClipboard(JSON.stringify(schemaData.bigQuerySchema, null, 2))}
                    className="action-button"
                  >
                    Copy
                  </button>
                  <button 
                    onClick={() => downloadSchema(schemaData.bigQuerySchema, `${schemaData.tableName}_bigquery_schema.json`)}
                    className="action-button"
                  >
                    Download
                  </button>
                </div>
              </div>
              <pre className="schema-content">
                {JSON.stringify(schemaData.bigQuerySchema, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SchemaDisplay; 