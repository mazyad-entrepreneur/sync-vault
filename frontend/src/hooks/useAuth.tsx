import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import { getAuthToken, setAuthToken, removeAuthToken } from '../utils';
import { User, AuthResponse } from '../types';
import { toast } from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (phone: string, password: string) => Promise<void>;
  signup: (data: any) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);
const { Provider } = AuthContext;

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = getAuthToken();
    if (token) {
      try {
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
          setUser(JSON.parse(savedUser));
        } else {
          // Token exists but user details missing -> invalid state
          logout();
        }
      } catch (error) {
        logout();
      }
    }
    setLoading(false);
  };

  const login = async (phone: string, password: string) => {
    try {
      const { data } = await axios.post<AuthResponse>(`${API_URL}/auth/login`, { phone, password });
      setAuthToken(data.access_token);
      const userObj = data.user || { id: 1, phone, store_name: 'My Store' };
      setUser(userObj);
      localStorage.setItem('user', JSON.stringify(userObj));
      toast.success('Welcome back!');
    } catch (error) {
      toast.error('Invalid credentials');
      throw error;
    }
  };

  const signup = async (formData: any) => {
    try {
      await axios.post(`${API_URL}/auth/signup`, formData);
      toast.success('Account created! Please login.');
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      if (Array.isArray(detail)) {
        // Validation error - show first one
        toast.error(detail[0]?.msg || 'Signup failed');
      } else if (typeof detail === 'string') {
        toast.error(detail);
      } else {
        toast.error('Signup failed');
      }
      throw error;
    }
  };

  const logout = () => {
    removeAuthToken();
    localStorage.removeItem('user');
    setUser(null);
    toast.success('Logged out');
  };

  const authContextValue = { user, loading, login, signup, logout };

  return (
    <Provider value={authContextValue}>
      {children}
    </Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
