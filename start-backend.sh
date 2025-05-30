#!/bin/bash

echo "🚀 Starting BigQuery Schema Converter Backend Server..."

cd cube-server

echo "📂 Current directory: $(pwd)"
echo "📦 Starting test server (with mock data)..."

PORT=3001 node test-server.js 