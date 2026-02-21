import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import { Toaster } from './components/ui/sonner';
import { Login } from './components/Login';
import { Layout } from './components/Layout';
import { Bookshelf } from './components/Bookshelf';
import { BookDetail } from './components/BookDetail';
import { Profile } from './components/Profile';
import { Chatbot } from './components/Chatbot';
import { AdminPanel } from './components/AdminPanel';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  const handleLogin = (admin: boolean) => {
    setIsAuthenticated(true);
    setIsAdmin(admin);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setIsAdmin(false);
  };

  if (!isAuthenticated) {
    return (
      <BrowserRouter>
        <Login onLogin={handleLogin} />
        <Toaster />
      </BrowserRouter>
    );
  }

  return (
    <BrowserRouter>
      <Layout isAdmin={isAdmin} onLogout={handleLogout}>
        <Routes>
          <Route path="/" element={<Navigate to="/bookshelf" replace />} />
          <Route path="/bookshelf" element={<Bookshelf />} />
          <Route path="/book/:bookId" element={<BookDetail />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/chatbot" element={<Chatbot />} />
          <Route path="/admin" element={isAdmin ? <AdminPanel /> : <Navigate to="/bookshelf" replace />} />
          <Route path="*" element={<Navigate to="/bookshelf" replace />} />
        </Routes>
      </Layout>
      <Toaster />
    </BrowserRouter>
  );
}
