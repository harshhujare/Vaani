import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HiOutlineUsers, HiOutlineAcademicCap, HiOutlineCheckBadge,
  HiOutlineBriefcase, HiOutlineArrowTrendingUp, HiOutlineClipboardDocumentCheck
} from 'react-icons/hi2';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import client from '../api/client';

const COLORS = ['#6c5ce7', '#00cec9', '#fdcb6e', '#ff6b6b', '#a29bfe', '#55efc4', '#fd79a8', '#74b9ff'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const [statsRes, funnelRes] = await Promise.all([
        client.get('/analytics/dashboard'),
        client.get('/analytics/funnel'),
      ]);
      setStats(statsRes.data.data);
      setFunnel(funnelRes.data.data);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <div className="stats-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="loading-skeleton" style={{ height: 130 }} />
          ))}
        </div>
        <div className="charts-grid">
          <div className="loading-skeleton" style={{ height: 320 }} />
          <div className="loading-skeleton" style={{ height: 320 }} />
        </div>
      </div>
    );
  }

  const statCards = [
    {
      label: 'Total Beneficiaries',
      value: stats?.totalBeneficiaries || 0,
      icon: HiOutlineUsers,
      color: 'purple',
      sub: `${stats?.totalSkillsMapped || 0} skills mapped`,
    },
    {
      label: 'Enrolled in Training',
      value: stats?.totalEnrolled || 0,
      icon: HiOutlineAcademicCap,
      color: 'green',
      sub: `${stats?.activePrograms || 0} active programs`,
    },
    {
      label: 'Completed Training',
      value: stats?.totalCompleted || 0,
      icon: HiOutlineCheckBadge,
      color: 'yellow',
      sub: `${stats?.totalCertified || 0} certified`,
    },
    {
      label: 'Attendance Rate',
      value: `${stats?.attendanceRate || 0}%`,
      icon: HiOutlineClipboardDocumentCheck,
      color: 'pink',
      sub: `₹${stats?.avgIncomeChange || 0} avg income change`,
    },
  ];

  // Status breakdown for pie chart
  const statusData = stats?.statusBreakdown
    ? Object.entries(stats.statusBreakdown).map(([name, value]) => ({ name, value: Number(value) }))
    : [];

  // Funnel data for bar chart
  const funnelData = funnel?.funnel || [];

  return (
    <div>
      {/* ── Stat Cards ── */}
      <div className="stats-grid">
        {statCards.map((card) => (
          <div key={card.label} className={`stat-card ${card.color}`}>
            <div className="stat-card-header">
              <span className="stat-card-label">{card.label}</span>
              <div className={`stat-card-icon ${card.color}`}>
                <card.icon />
              </div>
            </div>
            <div className="stat-card-value">{card.value}</div>
            <div className="stat-card-sub">{card.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Charts ── */}
      <div className="charts-grid">
        {/* Conversion Funnel */}
        <div className="chart-panel">
          <div className="panel-title">Conversion Funnel</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={funnelData} layout="vertical" margin={{ left: 20 }}>
              <XAxis type="number" stroke="#6b7280" fontSize={12} />
              <YAxis type="category" dataKey="stage" stroke="#6b7280" fontSize={12} width={80} />
              <Tooltip
                contentStyle={{
                  background: '#1e2130',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8,
                  color: '#f0f1f5'
                }}
              />
              <Bar dataKey="count" fill="#6c5ce7" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        <div className="chart-panel">
          <div className="panel-title">Status Distribution</div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={3}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {statusData.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: '#1e2130',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: 8,
                  color: '#f0f1f5'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Quick Actions ── */}
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">Quick Actions</div>
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={() => navigate('/beneficiaries')}>
            <HiOutlineUsers /> View All Beneficiaries
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/programs')}>
            <HiOutlineAcademicCap /> Manage Programs
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/analytics')}>
            <HiOutlineArrowTrendingUp /> View Analytics
          </button>
        </div>
      </div>
    </div>
  );
}
