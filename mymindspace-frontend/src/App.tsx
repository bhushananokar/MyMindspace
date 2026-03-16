/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { UserProvider } from './context/UserContext';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import GeminiLiveSession from './pages/GeminiLiveSession';
import Meditate from './pages/Meditate';
import Profile from './pages/Profile';
import Journal from './pages/Journal';

export default function App() {
  return (
    <UserProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sessions" element={<Sessions />} />
          <Route path="/live-session" element={<GeminiLiveSession />} />
          <Route path="/meditate" element={<Meditate />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/journal" element={<Journal />} />
        </Routes>
      </Router>
    </UserProvider>
  );
}
