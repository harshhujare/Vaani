import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, FunnelChart, Funnel, LabelList
} from 'recharts';
import client from '../api/client';

const COLORS = ['#6c5ce7', '#00cec9', '#fdcb6e', '#ff6b6b', '#a29bfe', '#55efc4', '#fd79a8', '#74b9ff'];

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchAll(); }, []);

  const fetchAll = async () => {
    try {
      const [statsRes, funnelRes, heatmapRes] = await Promise.all([
        client.get('/analytics/dashboard'),
        client.get('/analytics/funnel'),
        client.get('/analytics/skills-heatmap'),
      ]);
      setStats(statsRes.data.data);
      setFunnel(funnelRes.data.data);
      setHeatmap(heatmapRes.data.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <div className="stats-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="loading-skeleton" style={{ height: 100 }} />
          ))}
        </div>
        <div className="charts-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="loading-skeleton" style={{ height: 320 }} />
          ))}
        </div>
      </div>
    );
  }

  // Status breakdown for pie chart
  const statusData = stats?.statusBreakdown
    ? Object.entries(stats.statusBreakdown).map(([name, value]) => ({ name, value: Number(value) }))
    : [];

  // Funnel data
  const funnelData = funnel?.funnel || [];

  // Group heatmap by district
  const districtData = heatmap.reduce((acc, item) => {
    const existing = acc.find(d => d.district === item.district);
    if (existing) {
      existing.total += Number(item.count);
    } else {
      acc.push({ district: item.district, total: Number(item.count) });
    }
    return acc;
  }, []).sort((a, b) => b.total - a.total).slice(0, 10);

  // Group heatmap by sector
  const sectorData = heatmap.reduce((acc, item) => {
    const existing = acc.find(d => d.sector === item.sector);
    if (existing) {
      existing.count += Number(item.count);
    } else {
      acc.push({ sector: item.sector, count: Number(item.count) });
    }
    return acc;
  }, []).sort((a, b) => b.count - a.count);

  const tooltipStyle = {
    contentStyle: {
      background: '#1e2130',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 8,
      color: '#f0f1f5',
      fontSize: '0.85rem'
    }
  };

  return (
    <div>
      {/* Summary Cards */}
      <div className="stats-grid">
        <div className="stat-card purple">
          <div className="stat-card-label">Total Beneficiaries</div>
          <div className="stat-card-value">{stats?.totalBeneficiaries || 0}</div>
        </div>
        <div className="stat-card green">
          <div className="stat-card-label">Total Enrolled</div>
          <div className="stat-card-value">{stats?.totalEnrolled || 0}</div>
        </div>
        <div className="stat-card yellow">
          <div className="stat-card-label">Avg Income Change</div>
          <div className="stat-card-value">₹{(stats?.avgIncomeChange || 0).toLocaleString()}</div>
        </div>
        <div className="stat-card pink">
          <div className="stat-card-label">Attendance Rate</div>
          <div className="stat-card-value">{stats?.attendanceRate || 0}%</div>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="charts-grid">
        {/* Conversion Funnel */}
        <div className="chart-panel">
          <div className="panel-title">Conversion Funnel</div>
          <p className="panel-subtitle">Beneficiary lifecycle stages</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={funnelData} layout="vertical" margin={{ left: 30 }}>
              <XAxis type="number" stroke="#6b7280" fontSize={12} />
              <YAxis type="category" dataKey="stage" stroke="#6b7280" fontSize={11} width={85}
                tick={{ textTransform: 'capitalize' }} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                {funnelData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="chart-panel">
          <div className="panel-title">Status Distribution</div>
          <p className="panel-subtitle">Current beneficiary status breakdown</p>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={95}
                paddingAngle={3}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {statusData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="charts-grid">
        {/* District Distribution */}
        <div className="chart-panel">
          <div className="panel-title">Skills by District</div>
          <p className="panel-subtitle">Top 10 districts by mapped skills</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={districtData} margin={{ bottom: 20 }}>
              <XAxis dataKey="district" stroke="#6b7280" fontSize={11} angle={-30} textAnchor="end" />
              <YAxis stroke="#6b7280" fontSize={12} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="total" fill="#a29bfe" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Sector Distribution */}
        <div className="chart-panel">
          <div className="panel-title">Skills by Sector</div>
          <p className="panel-subtitle">Distribution across NSQF sectors</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sectorData} layout="vertical" margin={{ left: 40 }}>
              <XAxis type="number" stroke="#6b7280" fontSize={12} />
              <YAxis type="category" dataKey="sector" stroke="#6b7280" fontSize={11} width={120} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="count" fill="#00cec9" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="panel">
        <div className="panel-title" style={{ marginBottom: 16 }}>Key Metrics Summary</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <div className="info-item">
            <label>Skills Mapped</label>
            <span>{stats?.totalSkillsMapped || 0}</span>
          </div>
          <div className="info-item">
            <label>Active Programs</label>
            <span>{stats?.activePrograms || 0}</span>
          </div>
          <div className="info-item">
            <label>Completed Training</label>
            <span>{stats?.totalCompleted || 0}</span>
          </div>
          <div className="info-item">
            <label>Certified</label>
            <span>{stats?.totalCertified || 0}</span>
          </div>
          <div className="info-item">
            <label>Dropped Out</label>
            <span style={{ color: 'var(--danger)' }}>{funnel?.dropped || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
