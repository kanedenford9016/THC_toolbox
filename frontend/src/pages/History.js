import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { warService, paymentService, exportService } from '../services/api';
import '../App.css';

function History() {
  const navigate = useNavigate();
  const [completedWars, setCompletedWars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedWar, setSelectedWar] = useState(null);
  const [warMembers, setWarMembers] = useState([]);
  const [warPayments, setWarPayments] = useState([]);
  const [sortBy, setSortBy] = useState('hits'); // 'hits', 'score', 'name'
  const [expandedWar, setExpandedWar] = useState(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchCompletedWars();
  }, []);

  const fetchCompletedWars = async () => {
    try {
      setLoading(true);
      const data = await warService.getHistory();
      setCompletedWars(data.sessions || []);
      setError('');
    } catch (err) {
      setError('Failed to load war history');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = async (war) => {
    try {
      setSelectedWar(war);
      const warDetails = await warService.getWarDetails(war.session_id);
      setWarMembers(warDetails.members || []);
      
      // Load member payouts for this war
      try {
        const payouts = await warService.getMemberPayouts(war.session_id);
        setWarMembers(payouts.member_payouts || warDetails.members || []);
      } catch {
        // If no payouts saved, use member data from war details
        setWarMembers(warDetails.members || []);
      }
      
      // Load other payments for this war
      try {
        const payments = await paymentService.getPayments(war.session_id);
        setWarPayments(payments.payments || []);
      } catch {
        setWarPayments([]);
      }
      
      setExpandedWar(war.session_id);
    } catch (err) {
      setError('Failed to load war details');
      console.error(err);
    }
  };

  const handleCloseDetails = () => {
    setSelectedWar(null);
    setWarMembers([]);
    setWarPayments([]);
    setExpandedWar(null);
  };

  const handleExportPDF = async (war) => {
    try {
      setExporting(true);
      const userName = localStorage.getItem('userName') || 'Administrator';
      await exportService.exportPDF(war.session_id, userName);
      setError('');
    } catch (err) {
      setError('Failed to export PDF');
      console.error(err);
    } finally {
      setExporting(false);
    }
  };

  const sortMembers = (list) => {
    const sorted = [...list];
    switch (sortBy) {
      case 'hits':
        return sorted.sort((a, b) => (b.hit_count || 0) - (a.hit_count || 0));
      case 'score':
        return sorted.sort((a, b) => (b.score || 0) - (a.score || 0));
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

  const getTotalHits = (members) => {
    return members.reduce((sum, m) => sum + (parseInt(m.hit_count) || 0), 0);
  };

  const getTotalScore = (members) => {
    return members.reduce((sum, m) => sum + (parseFloat(m.score) || 0), 0);
  };

  const hasPayoutData = (members) => {
    return members.length > 0 && members[0].base_payout !== undefined;
  };

  if (loading) {
    return <div className="loading">Loading war history...</div>;
  }

  const sortedMembers = sortMembers(warMembers);

  return (
    <div>
      <div className="header">
        <h1>War Session History</h1>
        <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>

      <div className="container">
        {error && <div className="error">{error}</div>}

        {completedWars.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
            <p style={{ color: '#718096' }}>No completed war sessions yet</p>
            <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </button>
          </div>
        ) : (
          <>
            <div className="card" style={{ marginBottom: '2rem' }}>
              <h2 style={{ margin: '0 0 1rem 0', color: '#2d3748' }}>Completed Wars ({completedWars.length})</h2>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
                      <th style={{ padding: '0.75rem', textAlign: 'left', color: '#4a5568', fontWeight: '600' }}>
                        War Name
                      </th>
                      <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600' }}>
                        Members
                      </th>
                      <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600' }}>
                        Total Hits
                      </th>
                      <th style={{ padding: '0.75rem', textAlign: 'left', color: '#4a5568', fontWeight: '600' }}>
                        Completed
                      </th>
                      <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600' }}>
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {completedWars.map((war) => (
                      <React.Fragment key={war.session_id}>
                        <tr style={{ borderBottom: '1px solid #e2e8f0', cursor: 'pointer' }}>
                          <td style={{ padding: '0.75rem', color: '#2d3748', fontWeight: '500' }}>
                            {war.war_name}
                          </td>
                          <td style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568' }}>
                            {war.member_count}
                          </td>
                          <td style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600' }}>
                            {war.total_hits || 0}
                          </td>
                          <td style={{ padding: '0.75rem', color: '#718096', fontSize: '0.875rem' }}>
                            {formatDate(war.completed_timestamp)}
                          </td>
                          <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                            <button
                              className="btn btn-primary"
                              onClick={() => expandedWar === war.session_id ? handleCloseDetails() : handleViewDetails(war)}
                              style={{ fontSize: '0.875rem', padding: '0.5rem 1rem', marginRight: '0.5rem' }}
                            >
                              {expandedWar === war.session_id ? 'Hide' : 'View'} Details
                            </button>
                            <button
                              className="btn btn-secondary"
                              onClick={() => handleExportPDF(war)}
                              disabled={exporting}
                              style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                            >
                              {exporting ? 'Exporting...' : 'Export PDF'}
                            </button>
                          </td>
                        </tr>

                        {/* Expanded Details */}
                        {expandedWar === war.session_id && selectedWar && (
                          <tr style={{ backgroundColor: '#f7fafc', borderBottom: '2px solid #e2e8f0' }}>
                            <td colSpan="5" style={{ padding: '1.5rem' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                                <div>
                                  <h3 style={{ margin: '0 0 0.5rem 0', color: '#2d3748' }}>{selectedWar.war_name}</h3>
                                  <p style={{ margin: 0, color: '#718096', fontSize: '0.875rem' }}>
                                    {formatDate(selectedWar.completed_timestamp)}
                                  </p>
                                </div>
                                <button
                                  className="btn btn-secondary"
                                  onClick={() => handleExportPDF(selectedWar)}
                                  disabled={exporting}
                                  style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                                >
                                  {exporting ? 'Exporting...' : 'Export as PDF'}
                                </button>
                              </div>
                              <div>
                                {/* War Summary */}
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
                                  <div style={{ backgroundColor: '#ffffff', padding: '1rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                                    <p style={{ margin: 0, color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>Total Members</p>
                                    <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontSize: '1.5rem', fontWeight: '600' }}>
                                      {warMembers.length}
                                    </p>
                                  </div>
                                  <div style={{ backgroundColor: '#ffffff', padding: '1rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                                    <p style={{ margin: 0, color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>Total Hits</p>
                                    <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontSize: '1.5rem', fontWeight: '600' }}>
                                      {getTotalHits(warMembers)}
                                    </p>
                                  </div>
                                  <div style={{ backgroundColor: '#ffffff', padding: '1rem', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                                    <p style={{ margin: 0, color: '#718096', fontSize: '0.875rem', textTransform: 'uppercase' }}>Total Score</p>
                                    <p style={{ margin: '0.5rem 0 0 0', color: '#2d3748', fontSize: '1.5rem', fontWeight: '600' }}>
                                      {getTotalScore(warMembers).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                                    </p>
                                  </div>
                                </div>

                                {/* Members/Payouts Table */}
                                <div style={{ marginBottom: '1.5rem' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                    <h4 style={{ margin: 0, color: '#2d3748' }}>
                                      {hasPayoutData(warMembers) ? 'Member Payouts' : `Members (${warMembers.length})`}
                                    </h4>
                                    {!hasPayoutData(warMembers) && (
                                      <div>
                                        <label style={{ marginRight: '0.5rem', color: '#718096', fontSize: '0.875rem' }}>Sort by:</label>
                                        <select
                                          value={sortBy}
                                          onChange={(e) => setSortBy(e.target.value)}
                                          style={{
                                            padding: '0.4rem',
                                            borderRadius: '4px',
                                            border: '1px solid #cbd5e0',
                                            backgroundColor: '#ffffff',
                                            fontSize: '0.875rem'
                                          }}
                                        >
                                          <option value="hits">Hits</option>
                                          <option value="score">Score</option>
                                          <option value="name">Name</option>
                                        </select>
                                      </div>
                                    )}
                                  </div>

                                  <div style={{ overflowX: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: '#ffffff', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                                      <thead>
                                        <tr style={{ borderBottom: '2px solid #e2e8f0', backgroundColor: '#f7fafc' }}>
                                          <th style={{ padding: '0.75rem', textAlign: 'left', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>
                                            Name
                                          </th>
                                          <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>
                                            Hits
                                          </th>
                                          {!hasPayoutData(warMembers) && (
                                            <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>
                                              Score
                                            </th>
                                          )}
                                          {hasPayoutData(warMembers) && (
                                            <>
                                              <th style={{ padding: '0.75rem', textAlign: 'right', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>
                                                Base Payout
                                              </th>
                                              <th style={{ padding: '0.75rem', textAlign: 'right', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>
                                                Bonus
                                              </th>
                                              <th style={{ padding: '0.75rem', textAlign: 'right', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>
                                                Total Payout
                                              </th>
                                            </>
                                          )}
                                          {!hasPayoutData(warMembers) && (
                                            <th style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>
                                              Bonus
                                            </th>
                                          )}
                                          <th style={{ padding: '0.75rem', textAlign: 'left', color: '#4a5568', fontWeight: '600', fontSize: '0.875rem' }}>
                                            Status
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {sortedMembers.map((member) => (
                                          <tr
                                            key={member.member_id || member.payout_id}
                                            style={{
                                              borderBottom: '1px solid #e2e8f0'
                                            }}
                                          >
                                            <td style={{ padding: '0.75rem', color: '#2d3748' }}>
                                              {member.name}
                                            </td>
                                            <td style={{ padding: '0.75rem', textAlign: 'center', color: '#2d3748', fontWeight: '600' }}>
                                              {member.hit_count || 0}
                                            </td>
                                            {!hasPayoutData(warMembers) && (
                                              <td style={{ padding: '0.75rem', textAlign: 'center', color: '#4a5568' }}>
                                                {(member.score || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
                                              </td>
                                            )}
                                            {hasPayoutData(warMembers) && (
                                              <>
                                                <td style={{ padding: '0.75rem', textAlign: 'right', color: '#4a5568' }}>
                                                  ${(member.base_payout || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}
                                                </td>
                                                <td style={{ padding: '0.75rem', textAlign: 'right', color: '#f97316', fontWeight: '600' }}>
                                                  {member.bonus_amount > 0 ? `+$${(member.bonus_amount || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}` : '-'}
                                                </td>
                                                <td style={{ padding: '0.75rem', textAlign: 'right', color: '#2d3748', fontWeight: '600' }}>
                                                  ${(member.total_payout || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}
                                                </td>
                                              </>
                                            )}
                                            {!hasPayoutData(warMembers) && (
                                              <td style={{ padding: '0.75rem', textAlign: 'center', color: '#48bb78' }}>
                                                {member.bonus_amount ? `$${member.bonus_amount.toLocaleString()}` : '-'}
                                              </td>
                                            )}
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
                                </div>

                                {/* Other Payments */}
                                {warPayments.length > 0 && (
                                  <div>
                                    <h4 style={{ margin: '0 0 1rem 0', color: '#2d3748' }}>Other Expenses ({warPayments.length})</h4>
                                    <div style={{ overflowX: 'auto' }}>
                                      <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: '#ffffff', borderRadius: '4px', border: '1px solid #fcd34d' }}>
                                        <thead>
                                          <tr style={{ borderBottom: '2px solid #fcd34d', backgroundColor: '#fffaed' }}>
                                            <th style={{ padding: '0.75rem', textAlign: 'left', color: '#92400e', fontWeight: '600', fontSize: '0.875rem' }}>
                                              Description
                                            </th>
                                            <th style={{ padding: '0.75rem', textAlign: 'right', color: '#92400e', fontWeight: '600', fontSize: '0.875rem' }}>
                                              Amount
                                            </th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                          {warPayments.map((payment) => (
                                            <tr key={payment.payment_id} style={{ borderBottom: '1px solid #fcd34d' }}>
                                              <td style={{ padding: '0.75rem', color: '#2d3748' }}>
                                                {payment.description}
                                              </td>
                                              <td style={{ padding: '0.75rem', textAlign: 'right', color: '#2d3748', fontWeight: '600' }}>
                                                ${payment.amount.toLocaleString('en-US', { maximumFractionDigits: 2 })}
                                              </td>
                                            </tr>
                                          ))}
                                          <tr style={{ borderTop: '2px solid #fcd34d', backgroundColor: '#fffaed' }}>
                                            <td style={{ padding: '0.75rem', color: '#92400e', fontWeight: '600' }}>
                                              Total Other Expenses
                                            </td>
                                            <td style={{ padding: '0.75rem', textAlign: 'right', color: '#92400e', fontWeight: '600' }}>
                                              ${warPayments.reduce((sum, p) => sum + (p.amount || 0), 0).toLocaleString('en-US', { maximumFractionDigits: 2 })}
                                            </td>
                                          </tr>
                                        </tbody>
                                      </table>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default History;
