import { Product } from './types';

export const getAuthToken = () => localStorage.getItem('token');
export const setAuthToken = (token: string) => localStorage.setItem('token', token);
export const removeAuthToken = () => localStorage.removeItem('token');

export const getStockStatus = (product: Product) => {
    if (product.quantity < product.reorder_point) {
        return { color: 'bg-red-500', text: 'CRITICAL', status: 'critical' };
    }
    if (product.quantity < product.reorder_point * 1.5) {
        return { color: 'bg-yellow-500', text: 'Low Stock', status: 'low' };
    }
    return { color: 'bg-green-500', text: 'Healthy', status: 'good' };
};

export const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
    }).format(amount);
};
