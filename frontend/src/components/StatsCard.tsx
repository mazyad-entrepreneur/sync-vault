

interface Props {
    title: string;
    value: string | number;
    icon: string;
    trend?: string;
    color?: string;
}

const StatsCard = ({ title, value, icon, trend, color = "bg-indigo-500" }: Props) => {
    return (
        <div className="bg-white/90 backdrop-blur-xl p-4 rounded-2xl shadow-lg flex items-center space-x-4">
            <div className={`p-3 rounded-xl ${color} text-white text-xl`}>
                {icon}
            </div>
            <div>
                <p className="text-gray-500 text-sm font-medium">{title}</p>
                <h4 className="text-2xl font-bold text-gray-900">{value}</h4>
                {trend && <p className="text-xs text-green-500">{trend}</p>}
            </div>
        </div>
    );
};

export default StatsCard;
