import { useNavigate, useLocation } from 'react-router-dom';

const Navbar = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const tabs = [
        { name: 'Dashboard', path: '/dashboard', icon: '🏠' },
        { name: 'Scan', path: '/scan', icon: '📷' },
        { name: 'Products', path: '/products', icon: '📦' },
        { name: 'Profile', path: '/profile', icon: '👤' },
    ];

    return (
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 pb-safe">
            <div className="flex justify-around items-center h-16">
                {tabs.map((tab) => {
                    const isActive = location.pathname === tab.path;
                    return (
                        <button
                            key={tab.name}
                            onClick={() => navigate(tab.path)}
                            className={`flex flex-col items-center justify-center w-full h-full ${isActive ? 'text-indigo-600' : 'text-gray-500'
                                }`}
                        >
                            <span className="text-2xl mb-1">{tab.icon}</span>
                            <span className="text-xs font-medium">{tab.name}</span>
                        </button>
                    );
                })}
            </div>
        </nav>
    );
};

export default Navbar;
