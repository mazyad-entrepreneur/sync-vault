import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Navbar from '../components/Navbar';

const Profile = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <div className="bg-white p-6 shadow-sm mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Store Profile</h1>
            </div>

            <div className="px-4 space-y-4">
                <div className="bg-white rounded-xl shadow-sm p-6 flex items-center space-x-4">
                    <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                        {user?.store_name?.charAt(0) || 'S'}
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900">{user?.store_name}</h2>
                        <p className="text-gray-500">{user?.phone}</p>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm overflow-hidden">
                    <button className="w-full text-left px-6 py-4 border-b border-gray-100 hover:bg-gray-50 flex justify-between">
                        <span>🔔 Notifications</span>
                        <span>›</span>
                    </button>
                    <button className="w-full text-left px-6 py-4 border-b border-gray-100 hover:bg-gray-50 flex justify-between">
                        <span>⚙️ Settings</span>
                        <span>›</span>
                    </button>
                    <button className="w-full text-left px-6 py-4 border-b border-gray-100 hover:bg-gray-50 flex justify-between">
                        <span>❓ Help & Support</span>
                        <span>›</span>
                    </button>
                </div>

                <button
                    onClick={handleLogout}
                    className="w-full bg-red-50 text-red-600 font-bold py-4 rounded-xl shadow-sm hover:bg-red-100 transition-colors"
                >
                    Logout
                </button>
            </div>

            <Navbar />
        </div>
    );
};

export default Profile;
