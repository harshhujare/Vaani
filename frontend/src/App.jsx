import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import MainLayout from './components/Layout/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import BeneficiaryList from './pages/BeneficiaryList';
import BeneficiaryDetail from './pages/BeneficiaryDetail';
import Programs from './pages/Programs';
import Enrollments from './pages/Enrollments';
import Analytics from './pages/Analytics';

// Auth guard
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('vanisetu_token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e2130',
            color: '#f0f1f5',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '12px',
          },
        }}
      />

      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/beneficiaries" element={<BeneficiaryList />} />
          <Route path="/beneficiaries/:id" element={<BeneficiaryDetail />} />
          <Route path="/programs" element={<Programs />} />
          <Route path="/enrollments" element={<Enrollments />} />
          <Route path="/analytics" element={<Analytics />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
