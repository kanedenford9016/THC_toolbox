import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { warService, paymentService } from '../services/api';
import '../App.css';

function WarDetails() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [war, setWar] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('score'); // 'score', 'hits', 'name'
  const [showCalculator, setShowCalculator] = useState(false);
  const [totalEarnings, setTotalEarnings] = useState('');
  const [pricePerHit, setPricePerHit] = useState('');
  const [payouts, setPayouts] = useState(null);
  const [calculating, setCalculating] = useState(false);
  const [showOtherPayments, setShowOtherPayments] = useState(false);
  const [otherPayments, setOtherPayments] = useState([]);
  const [newPaymentAmount, setNewPaymentAmount] = useState('');
  const [newPaymentDescription, setNewPaymentDescription] = useState('');
  const [editingPaymentId, setEditingPaymentId] = useState(null);
  const [editingAmount, setEditingAmount] = useState('');
  const [editingDescription, setEditingDescription] = useState('');

  useEffect(() => {
    fetchWarDetails();
    fetchOtherPayments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const fetchOtherPayments = async () => {
    try {
      const data = await paymentService.getPayments(sessionId);
      setOtherPayments(data.payments || []);
    } catch (err) {
      console.error('Failed to load other payments:', err);
    }
  };

  const fetchWarDetails = async () => {
    try {
      setLoading(true);
      const data = await warService.getWarDetails(sessionId);
      setWar(data);
      setMembers(data.members || []);
      setError('');
    } catch (err) {
      setError('Failed to load war details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteWar = async () => {
    try {
      setCompleting(true);
      await warService.completeSession(sessionId);
      // Refresh war details to show updated status
      await fetchWarDetails();
      setError('');
    } catch (err) {
      setError('Failed to complete war');
      console.error(err);
    } finally {
      setCompleting(false);
    }
  };

  const handleCalculatePayouts = async () => {
    if (!totalEarnings || !pricePerHit) {
      setError('Please enter total earnings and price per hit');
      return;
    }

    try {
      setCalculating(true);
      const result = await warService.calculatePayouts(
        sessionId,
        parseFloat(totalEarnings),
        parseFloat(pricePerHit)
      );
      setPayouts(result);
      setError('');
    } catch (err) {
      console.error('[WAR-DETAILS] ✗ Failed to calculate payouts:', err);
      setError(`Failed to calculate payouts: ${err.response?.data?.error || err.message}`);
    } finally {
      setCalculating(false);
    }
  };

  const handleAddPayment = async () => {
    if (!newPaymentAmount || !newPaymentDescription) {
      setError('Please enter amount and description');
      return;
    }

    try {
      await paymentService.createPayment(sessionId, parseFloat(newPaymentAmount), newPaymentDescription);
      setNewPaymentAmount('');
      setNewPaymentDescription('');
      setError('');
      await fetchOtherPayments();
      // Recalculate payouts if they're showing
      if (payouts && totalEarnings && pricePerHit) {
        await handleCalculatePayouts();
      }
    } catch (err) {
      setError('Failed to add payment');
      console.error(err);
    }
  };

  const handleUpdatePayment = async (paymentId) => {
    if (!editingAmount || !editingDescription) {
      setError('Please enter amount and description');
      return;
    }

    try {
      await paymentService.updatePayment(paymentId, parseFloat(editingAmount), editingDescription);
      setEditingPaymentId(null);
      setEditingAmount('');
      setEditingDescription('');
      setError('');
      await fetchOtherPayments();
      // Recalculate payouts if they're showing
      if (payouts && totalEarnings && pricePerHit) {
        await handleCalculatePayouts();
      }
    } catch (err) {
      setError('Failed to update payment');
      console.error(err);
    }
  };

  const handleDeletePayment = async (paymentId) => {
    if (window.confirm('Are you sure you want to delete this payment?')) {
      try {
        await paymentService.deletePayment(paymentId);
        setError('');
        await fetchOtherPayments();
        // Recalculate payouts if they're showing
        if (payouts && totalEarnings && pricePerHit) {
          await handleCalculatePayouts();
        }
      } catch (err) {
        setError('Failed to delete payment');
        console.error(err);
      }
    }
  };

  const startEditPayment = (payment) => {
    setEditingPaymentId(payment.payment_id);
    setEditingAmount(payment.amount.toString());
    setEditingDescription(payment.description);
  };

  const sortMembers = (list) => {
    const sorted = [...list];
    switch (sortBy) {
      case 'score':
        return sorted.sort((a, b) => (b.score || 0) - (a.score || 0));
      case 'hits':
        return sorted.sort((a, b) => (b.hit_count || 0) - (a.hit_count || 0));
      case 'name':
        return sorted.sort((a, b) => a.name.localeCompare(b.name));
      default:
        return sorted;
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

  if (loading) {
    return <div className="loading">Loading war details...</div>;
  }

  if (!war) {
    return (
      <div className="container">
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <p style={{ color: '#718096' }}>War not found</p>
          <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const sortedMembers = sortMembers(members);

  return (
    <div>
      <div className="header">
        <h1>War Details</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>

      <div className="container">
        {error && <div className="error">{error}</div>}

        {/* War Info Card */}
        <div className="card" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
            <div>
              <h2 style={{ margin: '0 0 1rem 0', color: '#2d3748' }}>{war.war_name}</h2>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ margin: '0.5rem 0', color: '#718096' }}>
                  <strong>Status:</strong>{' '}
                  <span style={{
                    display: 'inline-block',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '4px',
                    backgroundColor: war.status === 'active' ? '#c6f6d5' : '#fed7d7',
                    color: war.status === 'active' ? '#22543d' : '#742a2a',
                    fontSize: '0.875rem',
                    fontWeight: '600'
                  }}>
                    {war.status.toUpperCase()}
                  </span>
                </p>
                <p style={{ margin: '0.5rem 0', color: '#718096' }}>
                  <strong>Opponent:</strong> {war.opposing_faction_name || 'N/A'}
                </p>
                <p style={{ margin: '0.5rem 0', color: '#718096' }}>
                  <strong>Members:</strong> {war.member_count}
                </p>
              </div>
            </div>

            <div>
              <h3 style={{ margin: '0 0 1rem 0', color: '#4299e1' }}>War Timeline</h3>
              <div style={{ marginBottom: '1rem' }}>
                <p style={{ margin: '0.5rem 0', color: '#718096', fontSize: '0.875rem' }}>
                  <strong>Created:</strong> {formatDate(war.created_timestamp)}
                </p>
                <p style={{ margin: '0.5rem 0', color: '#718096', fontSize: '0.875rem' }}>
                  <strong>War Start:</strong> {formatDate(war.war_start_timestamp)}
                </p>
                <p style={{ margin: '0.5rem 0', color: '#718096', fontSize: '0.875rem' }}>
                  <strong>War End:</strong> {formatDate(war.war_end_timestamp)}
                </p>
                {war.completed_timestamp && (
                  <p style={{ margin: '0.5rem 0', color: '#718096', fontSize: '0.875rem' }}>
                    <strong>Completed:</strong> {formatDate(war.completed_timestamp)}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Debug Info - Show collected data */}
          <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid #e2e8f0' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>Collected Data</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', fontSize: '0.75rem' }}>
              <div style={{ backgroundColor: '#f7fafc', padding: '0.75rem', borderRadius: '4px' }}>
                <p style={{ margin: 0, color: '#4a5568', fontWeight: '600' }}>Ranked War ID</p>
                <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontFamily: 'monospace' }}>
                  {war.ranked_war_id || 'N/A'}
                </p>
              </div>
              <div style={{ backgroundColor: '#f7fafc', padding: '0.75rem', borderRadius: '4px' }}>
                <p style={{ margin: 0, color: '#4a5568', fontWeight: '600' }}>Members Captured</p>
                <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontFamily: 'monospace' }}>
                  {members.length} members
                </p>
              </div>
              <div style={{ backgroundColor: '#f7fafc', padding: '0.75rem', borderRadius: '4px' }}>
                <p style={{ margin: 0, color: '#4a5568', fontWeight: '600' }}>Total Hits</p>
                <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontFamily: 'monospace' }}>
                  {members.reduce((sum, m) => sum + (parseInt(m.hit_count) || 0), 0)} hits
                </p>
              </div>
            </div>
          </div>

          {war.status === 'active' && (
            <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e2e8f0' }}>
              <button 
                className="btn btn-primary" 
                style={{ marginRight: '0.5rem' }}
                onClick={() => setShowOtherPayments(!showOtherPayments)}
              >
                {showOtherPayments ? 'Hide' : 'Manage'} Other Expenses
              </button>
              <button 
                className="btn btn-primary" 
                style={{ marginRight: '0.5rem' }}
                onClick={() => setShowCalculator(!showCalculator)}
              >
                {showCalculator ? 'Cancel' : 'Calculate Payouts'}
              </button>
              <button 
                className="btn btn-secondary"
                onClick={handleCompleteWar}
                disabled={completing}
              >
                {completing ? 'Completing...' : 'Complete War'}
              </button>
            </div>
          )}
        </div>

        {/* Other Payments Section */}
        {showOtherPayments && war.status === 'active' && (
          <div className="card" style={{ marginBottom: '2rem', backgroundColor: '#fef3c7', borderLeft: '4px solid #f59e0b' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#2d3748' }}>Other Expenses</h3>
            
            {/* Add Payment Form */}
            <div style={{ backgroundColor: '#fffaed', padding: '1rem', borderRadius: '4px', marginBottom: '1rem', border: '1px solid #fed7aa' }}>
              <h4 style={{ margin: '0 0 0.75rem 0', color: '#78350f', fontSize: '0.875rem', textTransform: 'uppercase' }}>Add Expense</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: '0.5rem', alignItems: 'flex-start' }}>
                <div>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={newPaymentAmount}
                    onChange={(e) => setNewPaymentAmount(e.target.value)}
                    placeholder="Amount"
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      borderRadius: '4px',
                      border: '1px solid #fcd34d',
                      fontSize: '0.875rem'
                    }}
                  />
                </div>
                <div>
                  <input
                    type="text"
                    value={newPaymentDescription}
                    onChange={(e) => setNewPaymentDescription(e.target.value)}
                    placeholder="Description (e.g., Supplies, Fee, Bonus)"
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      borderRadius: '4px',
                      border: '1px solid #fcd34d',
                      fontSize: '0.875rem'
                    }}
                  />
                </div>
                <button 
                  className="btn btn-primary"
                  onClick={handleAddPayment}
                  style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                >
                  Add
                </button>
              </div>
            </div>

            {/* Payments List */}
            {otherPayments.length === 0 ? (
              <p style={{ color: '#92400e', textAlign: 'center', padding: '1rem' }}>
                No other expenses added yet
              </p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #fed7aa' }}>
                      <th style={{ padding: '0.75rem', textAlign: 'left', color: '#92400e', fontWeight: '600', fontSize: '0.875rem' }}>Description</th>
                      <th style={{ padding: '0.75rem', textAlign: 'right', color: '#92400e', fontWeight: '600', fontSize: '0.875rem' }}>Amount</th>
                      <th style={{ padding: '0.75rem', textAlign: 'center', color: '#92400e', fontWeight: '600', fontSize: '0.875rem' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {otherPayments.map((payment) => (
                      <tr key={payment.payment_id} style={{ borderBottom: '1px solid #fed7aa' }}>
                        {editingPaymentId === payment.payment_id ? (
                          <>
                            <td style={{ padding: '0.75rem' }}>
                              <input
                                type="text"
                                value={editingDescription}
                                onChange={(e) => setEditingDescription(e.target.value)}
                                style={{
                                  width: '100%',
                                  padding: '0.4rem',
                                  borderRadius: '4px',
                                  border: '1px solid #fcd34d',
                                  fontSize: '0.875rem'
                                }}
                              />
                            </td>
                            <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={editingAmount}
                                onChange={(e) => setEditingAmount(e.target.value)}
                                style={{
                                  width: '120px',
                                  padding: '0.4rem',
                                  borderRadius: '4px',
                                  border: '1px solid #fcd34d',
                                  fontSize: '0.875rem'
                                }}
                              />
                            </td>
                            <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                              <button 
                                className="btn btn-primary" 
                                onClick={() => handleUpdatePayment(payment.payment_id)}
                                style={{ marginRight: '0.25rem', fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                              >
                                Save
                              </button>
                              <button 
                                className="btn btn-secondary" 
                                onClick={() => setEditingPaymentId(null)}
                                style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                              >
                                Cancel
                              </button>
                            </td>
                          </>
                        ) : (
                          <>
                            <td style={{ padding: '0.75rem', color: '#2d3748' }}>
                              {payment.description}
                            </td>
                            <td style={{ padding: '0.75rem', textAlign: 'right', color: '#2d3748', fontWeight: '600' }}>
                              ${payment.amount.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                            </td>
                            <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                              <button 
                                className="btn btn-primary" 
                                onClick={() => startEditPayment(payment)}
                                style={{ marginRight: '0.25rem', fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                              >
                                Edit
                              </button>
                              <button 
                                className="btn btn-danger" 
                                onClick={() => handleDeletePayment(payment.payment_id)}
                                style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', backgroundColor: '#dc2626', color: '#ffffff', border: 'none', cursor: 'pointer', borderRadius: '4px' }}
                              >
                                Delete
                              </button>
                            </td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Summary Line */}
        {otherPayments.length > 0 && (
          <div style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: '#fef3c7', borderRadius: '4px', border: '1px solid #fed7aa' }}>
            <p style={{ margin: 0, color: '#92400e', fontWeight: '600' }}>
              Total Other Expenses: ${otherPayments.reduce((sum, p) => sum + (p.amount || 0), 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}
            </p>
          </div>
        )}

        {/* Calculator Modal */}
        {showCalculator && (
          <div className="card" style={{ marginBottom: '2rem', backgroundColor: '#f0f4f8', borderLeft: '4px solid #4299e1' }}>
            <h3 style={{ margin: '0 0 1rem 0', color: '#2d3748' }}>Calculate Payouts</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#718096', fontWeight: '600' }}>
                  Total War Earnings ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={totalEarnings}
                  onChange={(e) => setTotalEarnings(e.target.value)}
                  placeholder="0.00"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #cbd5e0',
                    fontSize: '1rem'
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: '#718096', fontWeight: '600' }}>
                  Price Per Hit ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={pricePerHit}
                  onChange={(e) => setPricePerHit(e.target.value)}
                  placeholder="0.00"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #cbd5e0',
                    fontSize: '1rem'
                  }}
                />
              </div>
            </div>
            <button 
              className="btn btn-primary"
              onClick={handleCalculatePayouts}
              disabled={calculating}
            >
              {calculating ? 'Calculating...' : 'Calculate'}
            </button>
          </div>
        )}

        {/* Payouts Display */}
        {payouts && (
          <div className="card" style={{ marginBottom: '2rem', backgroundColor: '#f0fdf4', borderLeft: '4px solid #48bb78' }}>
            <h3 style={{ margin: '0 0 1.5rem 0', color: '#2d3748' }}>Payout Summary</h3>
            
            {/* Summary Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ backgroundColor: '#ffffff', padding: '1rem', borderRadius: '4px', border: '1px solid #dcfce7' }}>
                <p style={{ margin: 0, color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>Total Earnings</p>
                <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontSize: '1.5rem', fontWeight: '600' }}>
                  ${payouts.total_earnings.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div style={{ backgroundColor: '#ffffff', padding: '1rem', borderRadius: '4px', border: '1px solid #dcfce7' }}>
                <p style={{ margin: 0, color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>Member Payouts</p>
                <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontSize: '1.5rem', fontWeight: '600' }}>
                  ${payouts.total_member_payout.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div style={{ backgroundColor: '#ffffff', padding: '1rem', borderRadius: '4px', border: '1px solid #dcfce7' }}>
                <p style={{ margin: 0, color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>Other Payments</p>
                <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontSize: '1.5rem', fontWeight: '600' }}>
                  ${payouts.total_other_payments.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div style={{ backgroundColor: payouts.remaining_balance >= 0 ? '#dcfce7' : '#fee2e2', padding: '1rem', borderRadius: '4px', border: `1px solid ${payouts.remaining_balance >= 0 ? '#dcfce7' : '#fecaca'}` }}>
                <p style={{ margin: 0, color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>Remaining Balance</p>
                <p style={{ margin: '0.5rem 0 0 0', color: payouts.remaining_balance >= 0 ? '#2d3748' : '#dc2626', fontSize: '1.5rem', fontWeight: '600' }}>
                  ${payouts.remaining_balance.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                </p>
              </div>
            </div>

            {/* Member Payouts Table */}
            {payouts.member_payouts.length > 0 && (
              <div>
                <h4 style={{ margin: '0 0 1rem 0', color: '#2d3748' }}>Member Payouts</h4>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #dcfce7' }}>
                        <th style={{ padding: '0.75rem', textAlign: 'left', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>Name</th>
                        <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>Hits</th>
                        <th style={{ padding: '0.75rem', textAlign: 'right', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>Base Payout</th>
                        <th style={{ padding: '0.75rem', textAlign: 'right', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>Bonus</th>
                        <th style={{ padding: '0.75rem', textAlign: 'right', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {payouts.member_payouts.map((mp) => (
                        <tr key={mp.member_id} style={{ borderBottom: '1px solid #dcfce7' }}>
                          <td style={{ padding: '0.75rem', color: '#2d3748' }}>{mp.name}</td>
                          <td style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568' }}>{mp.hit_count}</td>
                          <td style={{ padding: '0.75rem', textAlign: 'right', color: '#4a5568' }}>
                            ${mp.base_payout.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                          </td>
                          <td style={{ padding: '0.75rem', textAlign: 'right', color: '#f97316', fontWeight: '600' }}>
                            {mp.bonus_amount > 0 ? `+$${mp.bonus_amount.toLocaleString('en-US', { maximumFractionDigits: 2 })}` : '-'}
                          </td>
                          <td style={{ padding: '0.75rem', textAlign: 'right', color: '#2d3748', fontWeight: '600' }}>
                            ${mp.total_payout.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Members Table */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 style={{ margin: 0, color: '#2d3748' }}>Members ({war.member_count})</h3>
            <div>
              <label style={{ marginRight: '0.5rem', color: '#718096' }}>Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                style={{
                  padding: '0.5rem',
                  borderRadius: '4px',
                  border: '1px solid #cbd5e0',
                  backgroundColor: '#ffffff'
                }}
              >
                <option value="score">Score</option>
                <option value="hits">Hits</option>
                <option value="name">Name</option>
              </select>
            </div>
          </div>

          {members.length === 0 ? (
            <p style={{ color: '#718096', textAlign: 'center', padding: '2rem' }}>
              No members in this war
            </p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                    <th style={{ padding: '0.75rem', textAlign: 'left', color: '#4a5568', fontWeight: '600' }}>
                      Name
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600' }}>
                      Hits
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600' }}>
                      Score
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600' }}>
                      Bonus
                    </th>
                    <th style={{ padding: '0.75rem', textAlign: 'left', color: '#4a5568', fontWeight: '600' }}>
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedMembers.map((member) => (
                    <tr
                      key={member.member_id}
                      style={{
                        borderBottom: '1px solid #e2e8f0',
                        cursor: 'pointer',
                        transition: 'background-color 0.2s'
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#f7fafc')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                    >
                      <td style={{ padding: '0.75rem', color: '#2d3748' }}>
                        {member.name}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568' }}>
                        {member.hit_count || 0}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600' }}>
                        {(member.score || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                      </td>
                      <td style={{ padding: '0.75rem', textAlign: 'center', color: '#48bb78' }}>
                        {member.bonus_amount ? `$${member.bonus_amount.toLocaleString()}` : '-'}
                      </td>
                      <td style={{ padding: '0.75rem', color: '#718096' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '3px',
                          backgroundColor: '#edf2f7',
                          fontSize: '0.75rem'
                        }}>
                          {member.member_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default WarDetails;
