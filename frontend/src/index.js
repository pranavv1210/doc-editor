import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Make sure this path is correct relative to index.js
import App from './App'; // Make sure this path is correct relative to index.js

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);