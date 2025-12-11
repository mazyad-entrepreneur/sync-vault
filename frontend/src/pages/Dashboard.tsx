import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import { getAuthToken, formatCurrency } from '../utils';
import { useAuth } from '../hooks/useAuth';
import { useWebSocket } from '../hooks/useWebSocket';
import { Product, DashboardStats } from '../types';
import StatsCard from '../components/StatsCard';
import ProductCard from '../components/ProductCard';
import Navbar from '../components/Navbar';

const Dashboard = () => {
    const { user } = useAuth();
    const [products, setProducts] = useState<Product[]>([]);
    const [stats, setStats] = useState<DashboardStats>({
        total_products: 0,
        total_value: 0,
        low_stock_count: 0,
        recent_scans: []
    });

    // Real-time updates
    const wsMessage = useWebSocket(user?.id);

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        if (wsMessage) {
            if (wsMessage.type === 'inventory_update') {
                fetchData(); // Simplest way to sync is refetch, or update local state if payload has details
            }
        }
    }, [wsMessage]);

    const fetchData = async () => {
        try {
            const token = getAuthToken();
            // Fetch products
            const productsRes = await axios.get(`${API_URL}/inventory`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setProducts(productsRes.data);

            // Calculate stats (Mocking backend stats if not available, or assume simple logic)
            const currentProducts = productsRes.data as Product[];
            const totalValue = currentProducts.reduce((sum, p) => sum + (p.price * p.quantity), 0);
            const lowStock = currentProducts.filter(p => p.quantity < p.reorder_point * 1.5).length;

            setStats({
                total_products: currentProducts.length,
                total_value: totalValue,
                low_stock_count: lowStock,
                recent_scans: [] // Would need separate endpoint or track locally
            });

        } catch (error) {
            console.error('Failed to fetch dashboard data', error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <header className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white p-6 pb-24 rounded-b-[2rem] shadow-xl">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-bold">Dashboard</h1>
                    <div className="bg-white/20 p-2 rounded-full backdrop-blur-sm">
                        👤 {user?.store_name}
                    </div>
                </div>
            </header>

            <div className="-mt-20 px-4 space-y-4">
                {/* Stats Row */}
                <div className="grid grid-cols-1 gap-4">
                    <StatsCard
                        title="Total Inventory"
                        value={formatCurrency(stats.total_value)}
                        icon="💰"
                        trend={`${stats.total_products} Items`}
                    />
                    <div className="grid grid-cols-2 gap-4">
                        <StatsCard
                            title="Low Stock"
                            value={stats.low_stock_count}
                            icon="⚠️"
                            color="bg-yellow-500"
                        />
                        <StatsCard
                            title="Products"
                            value={stats.total_products}
                            icon="📦"
                            color="bg-purple-500"
                        />
                    </div>
                </div>

                {/* Quick Actions or Highlights */}
                <div className="bg-white rounded-xl p-4 shadow-sm">
                    <h2 className="font-bold text-gray-800 mb-4">Inventory Status</h2>
                    <div className="space-y-2">
                        {products.length === 0 ? (
                            <p className="text-gray-400 text-center py-4">No products found. Go to Products tab to upload.</p>
                        ) : (
                            products.map(p => (
                                <ProductCard key={p.id} product={p} />
                            ))
                        )}
                    </div>
                </div>
            </div>

            <Navbar />
        </div>
    );
};

export default Dashboard;
