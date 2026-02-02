import React, { useState, useEffect } from 'react';
import { authService } from '../services/api';
import '../styles/Users.css';

function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createdUser, setCreatedUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    torn_id: '',
    faction_id: ''
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await authService.listUsers();
      setUsers(response.users || []);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load users');
      console.error('[USERS] Error loading users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      setError('');
      
      // Validate form
      if (!formData.username || !formData.torn_id || !formData.faction_id) {
        setError('Username, torn_id, and faction_id are required');
        return;
      }
      
      const response = await authService.createUser(formData);
      
      // Show the temporary password
      setCreatedUser({
        username: response.user.username,
        temporary_password: response.temporary_password,
        message: response.note
      });
      
      // Reset form
      setFormData({
        username: '',
        email: '',
        torn_id: '',
        faction_id: ''
      });
      
      // Reload users list
      await loadUsers();
      
      // Hide the form after a moment
      setTimeout(() => setShowCreateForm(false), 500);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create user');
      console.error('[USERS] Error creating user:', err);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return <div className="users-container"><p>Loading users...</p></div>;
  }

  return (
    <div className="users-container">
      <div className="users-header">
        <h2>Login Profiles</h2>
        <button 
          className="btn btn-primary"
          onClick={() => {
            setShowCreateForm(!showCreateForm);
            setCreatedUser(null);
            setError('');
          }}
        >
          {showCreateForm ? 'Cancel' : '+ Add New Profile'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {createdUser && (
        <div className="success-message">
          <h3>✓ User Created Successfully</h3>
          <p><strong>Username:</strong> {createdUser.username}</p>
          <p><strong>Temporary Password:</strong> 
            <code className="password-display">
              {createdUser.temporary_password}
              <button 
                className="copy-btn"
                onClick={() => copyToClipboard(createdUser.temporary_password)}
                title="Copy to clipboard"
              >
                📋
              </button>
            </code>
          </p>
          <p className="note">{createdUser.message}</p>
        </div>
      )}

      {showCreateForm && (
        <form onSubmit={handleCreateUser} className="create-user-form">
          <h3>Create New Login Profile</h3>
          
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="Enter username"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email (optional)</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="Enter email"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="torn_id">Torn ID</label>
              <input
                type="number"
                id="torn_id"
                name="torn_id"
                value={formData.torn_id}
                onChange={handleInputChange}
                placeholder="Enter Torn ID"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="faction_id">Faction ID</label>
              <input
                type="number"
                id="faction_id"
                name="faction_id"
                value={formData.faction_id}
                onChange={handleInputChange}
                placeholder="Enter Faction ID"
                required
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-success">Create Profile</button>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => setShowCreateForm(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="users-list">
        <h3>Current Login Profiles ({users.length})</h3>
        
        {users.length === 0 ? (
          <p className="empty-message">No user profiles found</p>
        ) : (
          <table className="users-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Torn ID</th>
                <th>Faction ID</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.admin_id} className={!user.password_changed ? 'needs-password-change' : ''}>
                  <td><strong>{user.username}</strong></td>
                  <td>{user.email || '-'}</td>
                  <td>{user.torn_id}</td>
                  <td>{user.faction_id}</td>
                  <td>
                    <span className={`status-badge ${user.password_changed ? 'active' : 'pending'}`}>
                      {user.password_changed ? 'Active' : 'Pending Password Change'}
                    </span>
                  </td>
                  <td>{new Date(user.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Users;
