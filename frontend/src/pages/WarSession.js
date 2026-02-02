import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';

function WarSession() {
  const navigate = useNavigate();

  return (
    <div>
      <div className="header">
        <h1>War Session Management</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>

      <div className="container">
        <div className="card">
          <h2>War Session Page</h2>
          <p>This page is under construction. Full implementation includes:</p>
          <ul>
            <li>Member list with hit counts</li>
            <li>Total earnings and price per hit inputs</li>
            <li>Bonus management for individual members</li>
            <li>Other payments section</li>
            <li>Automatic payout calculations</li>
            <li>PDF export functionality</li>
            <li>Complete war session button</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default WarSession;
