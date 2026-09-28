import { useState, useEffect } from 'react';
import {
  HiOutlineMagnifyingGlass, HiOutlinePlus,
  HiOutlineAcademicCap, HiOutlineXMark
} from 'react-icons/hi2';
import toast from 'react-hot-toast';
import client from '../api/client';

export default function Programs() {
  const [programs, setPrograms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    name: '', sector: '', sub_sector: '', nsqf_level: '',
    duration_days: '', district: '', state: '', training_center: '',
    provider: '', capacity: '', start_date: '', end_date: '', certification: ''
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => { fetchPrograms(); }, [sectorFilter]);

  const fetchPrograms = async () => {
    setLoading(true);
    try {
      const params = {};
      if (search) params.search = search;
      if (sectorFilter) params.sector = sectorFilter;
      const { data } = await client.get('/programs', { params });
      setPrograms(data.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { ...form };
      if (payload.nsqf_level) payload.nsqf_level = parseInt(payload.nsqf_level);
      if (payload.duration_days) payload.duration_days = parseInt(payload.duration_days);
      if (payload.capacity) payload.capacity = parseInt(payload.capacity);

      await client.post('/programs', payload);
      toast.success('Program created!');
      setShowModal(false);
      setForm({ name: '', sector: '', sub_sector: '', nsqf_level: '', duration_days: '', district: '', state: '', training_center: '', provider: '', capacity: '', start_date: '', end_date: '', certification: '' });
      fetchPrograms();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to create program');
    } finally {
      setSaving(false);
    }
  };

  const sectors = ['Construction', 'Agriculture', 'Textiles', 'Electronics', 'Beauty & Wellness', 'Automotive'];

  return (
    <div>
      {/* Filters */}
      <div className="filters-row">
        <form onSubmit={(e) => { e.preventDefault(); fetchPrograms(); }} className="search-bar">
          <HiOutlineMagnifyingGlass />
          <input
            placeholder="Search programs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </form>

        <select
          className="filter-select"
          value={sectorFilter}
          onChange={(e) => setSectorFilter(e.target.value)}
        >
          <option value="">All Sectors</option>
          {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>

        <button className="btn btn-primary btn-sm" onClick={() => setShowModal(true)}>
          <HiOutlinePlus /> Add Program
        </button>
      </div>

      {/* Table */}
      <div className="panel">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Program Name</th>
                <th>Sector</th>
                <th>NSQF</th>
                <th>Duration</th>
                <th>District</th>
                <th>Capacity</th>
                <th>Enrolled</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 8 }).map((_, j) => (
                      <td key={j}><div className="loading-skeleton" style={{ height: 16, width: '80%' }} /></td>
                    ))}
                  </tr>
                ))
              ) : programs.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    <div className="empty-state">
                      <HiOutlineAcademicCap style={{ fontSize: '2rem' }} />
                      <h3>No programs found</h3>
                      <p>Create a new training program to get started</p>
                    </div>
                  </td>
                </tr>
              ) : (
                programs.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{p.name}</td>
                    <td>{p.sector || '—'}</td>
                    <td>
                      {p.nsqfLevel && (
                        <span className="badge assessed">Level {p.nsqfLevel}</span>
                      )}
                    </td>
                    <td>{p.durationDays ? `${p.durationDays} days` : '—'}</td>
                    <td>{p.district || '—'}</td>
                    <td>{p.capacity || '—'}</td>
                    <td>
                      <span style={{
                        color: p.capacity && p.enrolledCount >= p.capacity * 0.8
                          ? 'var(--danger)' : 'var(--success)'
                      }}>
                        {p.enrolledCount || 0}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${p.isActive ? 'attending' : 'dropped'}`}>
                        {p.isActive ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      {showModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 200
        }}>
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 'var(--radius-xl)', padding: 32, width: '100%',
            maxWidth: 600, maxHeight: '85vh', overflowY: 'auto',
            boxShadow: 'var(--shadow-lg)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Add Training Program</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setShowModal(false)}>
                <HiOutlineXMark />
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label className="form-label">Program Name *</label>
                <input className="form-input" required value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Sector</label>
                  <select className="form-select" value={form.sector}
                    onChange={(e) => setForm({ ...form, sector: e.target.value })}>
                    <option value="">Select Sector</option>
                    {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">NSQF Level</label>
                  <select className="form-select" value={form.nsqf_level}
                    onChange={(e) => setForm({ ...form, nsqf_level: e.target.value })}>
                    <option value="">Select Level</option>
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((l) => <option key={l} value={l}>Level {l}</option>)}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">District</label>
                  <input className="form-input" value={form.district}
                    onChange={(e) => setForm({ ...form, district: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">State</label>
                  <input className="form-input" value={form.state}
                    onChange={(e) => setForm({ ...form, state: e.target.value })} />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Duration (days)</label>
                  <input className="form-input" type="number" value={form.duration_days}
                    onChange={(e) => setForm({ ...form, duration_days: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">Capacity</label>
                  <input className="form-input" type="number" value={form.capacity}
                    onChange={(e) => setForm({ ...form, capacity: e.target.value })} />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Training Center</label>
                <input className="form-input" value={form.training_center}
                  onChange={(e) => setForm({ ...form, training_center: e.target.value })} />
              </div>

              <div className="form-group">
                <label className="form-label">Provider</label>
                <input className="form-input" value={form.provider}
                  onChange={(e) => setForm({ ...form, provider: e.target.value })} />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Start Date</label>
                  <input className="form-input" type="date" value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
                </div>
                <div className="form-group">
                  <label className="form-label">End Date</label>
                  <input className="form-input" type="date" value={form.end_date}
                    onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Creating...' : 'Create Program'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
