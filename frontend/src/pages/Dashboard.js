import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { warService, authService } from '../services/api';
import Users from './Users';
import '../App.css';

function Dashboard({ setIsAuthenticated }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('wars');
  const [wars, setWars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchWars();
  }, []);

  const fetchWars = async () => {
    try {
      setLoading(true);
      const data = await warService.listWars();
      setWars(data.wars || []);
      setError('');
    } catch (err) {
      setError('Failed to load wars');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWar = async () => {
    const warName = prompt('Enter war name:');
    if (!warName) return;

    try {
      const data = await warService.createSession(warName);
      navigate(`/war/${data.session_id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create war session');
    }
  };

  const handleWarClick = (sessionId) => {
    navigate(`/war/${sessionId}`);
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      setIsAuthenticated(false);
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
      setIsAuthenticated(false);
      navigate('/login');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const style = {
      display: 'inline-block',
      padding: '0.25rem 0.75rem',
      borderRadius: '4px',
      fontSize: '0.75rem',
      fontWeight: '600',
      textTransform: 'uppercase'
    };

    if (status === 'active') {
      return <span style={{ ...style, backgroundColor: '#c6f6d5', color: '#22543d' }}>Active</span>;
    } else {
      return <span style={{ ...style, backgroundColor: '#fed7d7', color: '#742a2a' }}>Completed</span>;
    }
  };

  if (loading && activeTab === 'wars') {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div>
      <div className="header">
        <h1>Torn War Calculator</h1>
        <div>
          <button className="btn btn-secondary" onClick={() => navigate('/history')} style={{ marginRight: '1rem' }}>
            History
          </button>
          <button className="btn btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      <div className="tabs-container">
        <button 
          className={`tab-btn ${activeTab === 'wars' ? 'active' : ''}`}
          onClick={() => setActiveTab('wars')}
        >
          War Dashboard
        </button>
        <button 
          className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          Login Profiles
        </button>
      </div>

      <div className="container">
        {activeTab === 'wars' && (
          <>
            {error && <div className="error">{error}</div>}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h2 style={{ color: '#2d3748', margin: 0 }}>War Dashboard</h2>
          <button className="btn btn-primary" onClick={handleCreateWar}>
            Create New War
          </button>
        </div>

        {wars.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
            <p style={{ color: '#718096', marginBottom: '1rem' }}>No wars created yet.</p>
            <button className="btn btn-primary" onClick={handleCreateWar}>
              Create Your First War
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {wars.map((war) => (
              <div
                key={war.session_id}
                className="card"
                style={{
                  cursor: 'pointer',
                  transition: 'box-shadow 0.2s',
                  padding: '1.5rem'
                }}
                onClick={() => handleWarClick(war.session_id)}
                onMouseEnter={(e) => (e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.15)')}
                onMouseLeave={(e) => (e.currentTarget.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)')}
              >
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr 100px', gap: '1rem', alignItems: 'center' }}>
                  {/* War Name */}
                  <div>
                    <p style={{ margin: '0 0 0.5rem 0', color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>
                      War Name
                    </p>
                    <p style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: '#2d3748' }}>
                      {war.war_name}
                    </p>
                  </div>

                  {/* Opponent */}
                  <div>
                    <p style={{ margin: '0 0 0.5rem 0', color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>
                      Opponent
                    </p>
                    <p style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: '#2d3748' }}>
                      {war.opposing_faction_name || 'N/A'}
                    </p>
                  </div>

                  {/* Members */}
                  <div>
                    <p style={{ margin: '0 0 0.5rem 0', color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>
                      Members
                    </p>
                    <p style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: '#2d3748' }}>
                      {war.member_count || 0}
                    </p>
                  </div>

                  {/* Created Date */}
                  <div>
                    <p style={{ margin: '0 0 0.5rem 0', color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>
                      Created
                    </p>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: '#4a5568' }}>
                      {formatDate(war.created_timestamp)}
                    </p>
                  </div>

                  {/* Status */}
                  <div style={{ textAlign: 'center' }}>
                    {getStatusBadge(war.status)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
          </>
        )}
      </div>

      {activeTab === 'users' && <Users />}
    </div>
  );
}

export default Dashboard;
