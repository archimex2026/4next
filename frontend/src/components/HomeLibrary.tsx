'use client';
import { useAuth } from './AuthProvider';
import Library from './Library';
import { Loading } from './UI';
export default function HomeLibrary() { const { user, loading } = useAuth(); return loading ? <Loading /> : <Library compact isPublic={!user}/>; }
