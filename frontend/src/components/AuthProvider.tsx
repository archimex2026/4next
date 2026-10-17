'use client';
import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { request } from '@/lib/api';
import { User } from '@/lib/types';
const AuthContext = createContext<{
    user: User | null;
    loading: boolean;
    error: string;
    refresh: () => Promise<void>;
}>({ user: null, loading: true, error: '', refresh: async () => { } });
export function AuthProvider({ children }: {
    children: React.ReactNode;
}) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const refresh = useCallback(() => request<{
        user: User | null;
    }>('/api/auth/me')
        .then(result => { setUser(result.user); setError(''); })
        .catch(() => { setUser(null); setError('Conexiunea cu serverul este indisponibilă.'); })
        .finally(() => setLoading(false)), []);
    useEffect(() => { void refresh(); }, [refresh]);
    return <AuthContext.Provider value={{ user, loading, error, refresh }}>{children}</AuthContext.Provider>;
}
export function useAuth() { return useContext(AuthContext); }
