/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { UserProvider } from './context/UserContext';
import Welcome from './pages/Welcome';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import Meditate from './pages/Meditate';
import Profile from './pages/Profile';
import Journal from './pages/Journal';

export default function App() {
  return (
    <UserProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/sessions" element={<Sessions />} />
          <Route path="/meditate" element={<Meditate />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/journal" element={<Journal />} />
        </Routes>
      </Router>
    </UserProvider>
  );
}
