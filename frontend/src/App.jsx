import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login/Login.jsx';
import Register from './pages/Register/Register.jsx';
import OwnerDashboard from './pages/OwnerDashboard/OwnerDashboard';
import ProtectedEmployeeDashboard from './pages/EmployeeDashboard/ProtectedEmployeeDashboard';

function NotFound() {
  return (
    <div className="min-h-screen grid place-items-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-3xl font-bold">404</h1>
        <p className="text-gray-500 mt-2">Страница не найдена</p>
        <a className="text-indigo-600 underline mt-4 inline-block" href="/login">На страницу входа</a>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/employeedashboard" element={<ProtectedEmployeeDashboard />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
