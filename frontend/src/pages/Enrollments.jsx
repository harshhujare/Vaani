import { useState, useEffect } from 'react';
import { HiOutlineClipboardDocumentList } from 'react-icons/hi2';
import client from '../api/client';

export default function Enrollments() {
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({});

  useEffect(() => { fetchEnrollments(); }, [page, statusFilter]);

  const fetchEnrollments = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 15 };
      if (statusFilter) params.status = statusFilter;
      const { data } = await client.get('/enrollments', { params });
      setEnrollments(data.data || []);
      setMeta(data.meta || {});
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const statuses = ['enrolled', 'attending', 'completed', 'dropped', 'certified'];

  return (
    <div>
      <div className="filters-row">
        <select
          className="filter-select"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Status</option>
          {statuses.map((s) => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
      </div>

      <div className="panel">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Enrollment ID</th>
                <th>Beneficiary</th>
                <th>Program</th>
                <th>Status</th>
                <th>Match Score</th>
                <th>Enrolled At</th>
                <th>Completed At</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j}><div className="loading-skeleton" style={{ height: 16, width: '80%' }} /></td>
                    ))}
                  </tr>
                ))
              ) : enrollments.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state">
                      <HiOutlineClipboardDocumentList style={{ fontSize: '2rem' }} />
                      <h3>No enrollments found</h3>
                    </div>
                  </td>
                </tr>
              ) : (
                enrollments.map((e) => (
                  <tr key={e.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.78rem' }}>
                      {e.id?.slice(0, 8)}...
                    </td>
                    <td>{e.beneficiaryId?.slice(0, 8)}...</td>
                    <td>{e.programId?.slice(0, 8)}...</td>
                    <td><span className={`badge ${e.status}`}>{e.status}</span></td>
                    <td>
                      {e.matchScore ? (
                        <span style={{
                          color: e.matchScore > 0.7 ? 'var(--success)' : 'var(--warning)'
                        }}>
                          {(e.matchScore * 100).toFixed(0)}%
                        </span>
                      ) : '—'}
                    </td>
                    <td>{e.enrolledAt ? new Date(e.enrolledAt).toLocaleDateString() : '—'}</td>
                    <td>{e.completedAt ? new Date(e.completedAt).toLocaleDateString() : '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {meta.totalPages > 1 && (
          <div className="pagination">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>←</button>
            {Array.from({ length: Math.min(meta.totalPages, 5) }).map((_, i) => (
              <button key={i + 1} className={page === i + 1 ? 'active' : ''} onClick={() => setPage(i + 1)}>
                {i + 1}
              </button>
            ))}
            <button disabled={page >= meta.totalPages} onClick={() => setPage(page + 1)}>→</button>
          </div>
        )}
      </div>
    </div>
  );
}
