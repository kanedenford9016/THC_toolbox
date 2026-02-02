import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';

function Archive() {
  const navigate = useNavigate();

  return (
    <div>
      <div className="header">
        <h1>Audit Log Archive</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>

      <div className="container">
        <div className="card">
          <h2>Archived Audit Logs</h2>
          <p>This page provides read-only access to archived audit logs for compliance purposes.</p>
          <p>Filter by date range, action type, and user.</p>
        </div>
      </div>
    </div>
  );
}

export default Archive;
