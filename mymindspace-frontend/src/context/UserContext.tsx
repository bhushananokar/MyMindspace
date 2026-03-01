import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export interface AppUser {
  /** AI Therapist API patient ID */
  patientId: number | null;
  /** Meditation API user ID (UUID string) */
  meditationUserId: string | null;
  /** Display name */
  name: string;
}

interface UserContextValue {
  user: AppUser;
  setUser: (u: AppUser) => void;
  clearUser: () => void;
  isLoggedIn: boolean;
}

const STORAGE_KEY = 'mymindspace_user';

const defaultUser: AppUser = {
  patientId: 1,
  meditationUserId: '3ec5376b-16ee-418a-b6cb-6604dbcb2277',
  name: 'Bhushan',
};

const UserContext = createContext<UserContextValue>({
  user: defaultUser,
  setUser: () => {},
  clearUser: () => {},
  isLoggedIn: false,
});

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<AppUser>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? (JSON.parse(stored) as AppUser) : defaultUser;
    } catch {
      return defaultUser;
    }
  });

  const setUser = useCallback((u: AppUser) => {
    setUserState(u);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
  }, []);

  const clearUser = useCallback(() => {
    setUserState(defaultUser);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const isLoggedIn = Boolean(user.patientId || user.meditationUserId);

  return (
    <UserContext.Provider value={{ user, setUser, clearUser, isLoggedIn }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
