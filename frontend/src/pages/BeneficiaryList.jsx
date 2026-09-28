import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { HiOutlineMagnifyingGlass, HiOutlineUsers } from 'react-icons/hi2';
import client from '../api/client';

export default function BeneficiaryList() {
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    fetchBeneficiaries();
  }, [page, statusFilter]);

  const fetchBeneficiaries = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 15 };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;

      const { data } = await client.get('/beneficiaries', { params });
      setBeneficiaries(data.data || []);
      setMeta(data.meta || {});
    } catch (err) {
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchBeneficiaries();
  };

  const statuses = ['registered', 'assessed', 'enrolled', 'attending', 'completed', 'certified', 'employed', 'dropped'];

  return (
    <div>
      {/* Filters */}
      <div className="filters-row">
        <form onSubmit={handleSearch} className="search-bar">
          <HiOutlineMagnifyingGlass />
          <input
            placeholder="Search by name or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>

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

        <button className="btn btn-primary btn-sm" onClick={handleSearch}>
          Search
        </button>
      </div>

      {/* Table */}
      <div className="panel">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>District</th>
                <th>State</th>
                <th>Status</th>
                <th>Income</th>
                <th>Registered</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j}>
                        <div className="loading-skeleton" style={{ height: 16, width: '80%' }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : beneficiaries.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state">
                      <HiOutlineUsers style={{ fontSize: '2rem' }} />
                      <h3>No beneficiaries found</h3>
                      <p>Try changing your search or filters</p>
                    </div>
                  </td>
                </tr>
              ) : (
                beneficiaries.map((b) => (
                  <tr key={b.id} onClick={() => navigate(`/beneficiaries/${b.id}`)}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{b.name}</td>
                    <td>{b.phone}</td>
                    <td>{b.district || '—'}</td>
                    <td>{b.state || '—'}</td>
                    <td><span className={`badge ${b.status}`}>{b.status}</span></td>
                    <td>{b.monthlyIncome ? `₹${b.monthlyIncome.toLocaleString()}` : '—'}</td>
                    <td>{b.createdAt ? new Date(b.createdAt).toLocaleDateString() : '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {meta.totalPages > 1 && (
          <div className="pagination">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              ←
            </button>
            {Array.from({ length: Math.min(meta.totalPages, 5) }).map((_, i) => (
              <button
                key={i + 1}
                className={page === i + 1 ? 'active' : ''}
                onClick={() => setPage(i + 1)}
              >
                {i + 1}
              </button>
            ))}
            <button
              disabled={page >= meta.totalPages}
              onClick={() => setPage(page + 1)}
            >
              →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
