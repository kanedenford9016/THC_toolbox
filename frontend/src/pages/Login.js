import React, { useState } from 'react';
import { authService } from '../services/api';
import '../App.css';

function Login({ setIsAuthenticated }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await authService.login(username, password, apiKey);
      setIsAuthenticated(true);
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '400px', marginTop: '10vh' }}>
      <div className="card">
        <h1 style={{ textAlign: 'center', color: '#2d3748', marginBottom: '2rem' }}>
          Torn War Calculator
        </h1>
        
        {error && <div className="error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <label htmlFor="username" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
            Torn Username
          </label>
          <input
            type="text"
            id="username"
            className="input"
            placeholder="Enter your Torn username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />

          <label htmlFor="password" style={{ display: 'block', marginTop: '1rem', marginBottom: '0.5rem', fontWeight: '600' }}>
            Password
          </label>
          <div style={{ position: 'relative' }}>
            <input
              type={showPassword ? "text" : "password"}
              id="password"
              className="input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ paddingRight: '2.5rem' }}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              style={{
                position: 'absolute',
                right: '0.5rem',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#4a5568',
                fontSize: '0.875rem',
                padding: '0.25rem'
              }}
            >
              {showPassword ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>

          <label htmlFor="apiKey" style={{ display: 'block', marginTop: '1rem', marginBottom: '0.5rem', fontWeight: '600' }}>
            Torn API Key
          </label>
          <div style={{ position: 'relative' }}>
            <input
              type={showApiKey ? "text" : "password"}
              id="apiKey"
              className="input"
              placeholder="Enter your Torn API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              required
              style={{ paddingRight: '2.5rem' }}
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              style={{
                position: 'absolute',
                right: '0.5rem',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: '#4a5568',
                fontSize: '0.875rem',
                padding: '0.25rem'
              }}
            >
              {showApiKey ? '👁️' : '👁️‍🗨️'}
            </button>
          </div>
          
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#e2e8f0', borderRadius: '6px' }}>
          <p style={{ margin: 0, fontSize: '0.875rem', color: '#4a5568' }}>
            <strong>Note:</strong> You must be a faction administrator (Leader, Co-leader, or Officer) to access this tool.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
