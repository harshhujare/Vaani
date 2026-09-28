import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  HiOutlineArrowLeft, HiOutlinePhone, HiOutlineMapPin,
  HiOutlineCurrencyRupee, HiOutlineCalendar
} from 'react-icons/hi2';
import client from '../api/client';

export default function BeneficiaryDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [callLogs, setCallLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [benefRes, callRes] = await Promise.all([
        client.get(`/beneficiary/${id}`),
        client.get(`/call-logs/${id}`),
      ]);
      setData(benefRes.data.data);
      setCallLogs(callRes.data.data || []);
    } catch (err) {
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <div className="loading-skeleton" style={{ height: 100, marginBottom: 24 }} />
        <div className="loading-skeleton" style={{ height: 300 }} />
      </div>
    );
  }

  if (!data) {
    return <div className="empty-state"><h3>Beneficiary not found</h3></div>;
  }

  return (
    <div>
      {/* Back button */}
      <button
        className="btn btn-secondary btn-sm"
        onClick={() => navigate('/beneficiaries')}
        style={{ marginBottom: 20 }}
      >
        <HiOutlineArrowLeft /> Back to List
      </button>

      {/* Header */}
      <div className="detail-header">
        <div className="detail-avatar">
          {data.name?.charAt(0)?.toUpperCase()}
        </div>
        <div className="detail-info">
          <h2>{data.name}</h2>
          <div className="detail-meta">
            <span><HiOutlinePhone /> {data.phone}</span>
            <span><HiOutlineMapPin /> {data.district}, {data.state}</span>
            <span className={`badge ${data.status}`}>{data.status}</span>
          </div>
        </div>
      </div>

      <div className="detail-grid">
        {/* Personal Info */}
        <div className="panel">
          <div className="panel-title" style={{ marginBottom: 16 }}>Personal Information</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
            <div className="info-item">
              <label>Age</label>
              <span>{data.age || '—'}</span>
            </div>
            <div className="info-item">
              <label>Gender</label>
              <span style={{ textTransform: 'capitalize' }}>{data.gender || '—'}</span>
            </div>
            <div className="info-item">
              <label>Village</label>
              <span>{data.village || '—'}</span>
            </div>
            <div className="info-item">
              <label>Caste Category</label>
              <span>{data.casteCategory || '—'}</span>
            </div>
            <div className="info-item">
              <label>Education</label>
              <span>{data.educationLevel || '—'}</span>
            </div>
            <div className="info-item">
              <label>Monthly Income</label>
              <span>
                {data.monthlyIncome ? `₹${data.monthlyIncome.toLocaleString()}` : '—'}
              </span>
            </div>
            <div className="info-item">
              <label>Household Size</label>
              <span>{data.householdSize || '—'}</span>
            </div>
            <div className="info-item">
              <label>BPL Status</label>
              <span>{data.bplStatus ? 'Yes' : 'No'}</span>
            </div>
          </div>
        </div>

        {/* Skills */}
        <div className="panel">
          <div className="panel-title" style={{ marginBottom: 16 }}>
            Mapped Skills ({data.skills?.length || 0})
          </div>
          {data.skills?.length > 0 ? (
            <div className="skill-tags">
              {data.skills.map((s) => (
                <div key={s.id} className="skill-tag">
                  {s.skillName}
                  {s.nsqfLevel && <span className="nsqf">L{s.nsqfLevel}</span>}
                  {s.isPrimary && <span style={{ color: 'var(--success)', fontSize: '0.68rem' }}>★ Primary</span>}
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No skills mapped yet</p>
          )}

          {data.skills?.length > 0 && (
            <div style={{ marginTop: 16 }}>
              {data.skills.map((s) => (
                <div key={s.id} style={{
                  padding: '12px 0',
                  borderBottom: '1px solid var(--border)',
                }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{s.skillName}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: 16 }}>
                    <span>Sector: {s.sector || '—'}</span>
                    <span>Experience: {s.experienceYears || 0} yrs</span>
                    <span>Confidence: {s.confidenceScore ? `${(s.confidenceScore * 100).toFixed(0)}%` : '—'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Call Logs */}
      <div className="panel">
        <div className="panel-title" style={{ marginBottom: 16 }}>
          Call History ({callLogs.length})
        </div>
        {callLogs.length > 0 ? (
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Call ID</th>
                  <th>Type</th>
                  <th>Duration</th>
                  <th>Language</th>
                  <th>AI Confidence</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {callLogs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{log.callId}</td>
                    <td><span className="badge enrolled">{log.callType}</span></td>
                    <td>{log.durationSeconds ? `${Math.floor(log.durationSeconds / 60)}m ${log.durationSeconds % 60}s` : '—'}</td>
                    <td>{log.language?.toUpperCase() || '—'}</td>
                    <td>{log.aiConfidence ? `${(log.aiConfidence * 100).toFixed(0)}%` : '—'}</td>
                    <td>{log.createdAt ? new Date(log.createdAt).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No calls recorded yet</p>
        )}
      </div>
    </div>
  );
}
