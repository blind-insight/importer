import React, { useState } from 'react';
import './SchemaConverter.css';

const SchemaConverter = ({ onSchemaFetch, loading, error }) => {
  const [datasetId, setDatasetId] = useState('');
  const [tableId, setTableId] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!datasetId.trim() || !tableId.trim()) {
      alert('Please enter both dataset ID and table ID');
      return;
    }
    
    onSchemaFetch(datasetId.trim(), tableId.trim());
  };

  return (
    <div className="schema-converter">
      <h2>Extract BigQuery Schema</h2>
      
      <form onSubmit={handleSubmit} className="converter-form">
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
        
        <button 
          type="submit" 
          className="convert-button"
          disabled={loading}
        >
          {loading ? 'Converting...' : 'Convert Schema'}
        </button>
      </form>
      
      {error && (
        <div className="error-message">
          <h3>Error:</h3>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
};

export default SchemaConverter; 