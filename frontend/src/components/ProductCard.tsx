import { Product } from '../types';
import { getStockStatus, formatCurrency } from '../utils';

interface Props {
    product: Product;
}

const ProductCard = ({ product }: Props) => {
    const { color, text } = getStockStatus(product);

    return (
        <div className="bg-white rounded-xl shadow-sm p-4 flex justify-between items-center mb-3">
            <div>
                <h3 className="font-semibold text-gray-900">{product.name}</h3>
                <p className="text-sm text-gray-500">Barcode: {product.barcode}</p>
                <p className="font-bold text-indigo-600 mt-1">{formatCurrency(product.price)}</p>
            </div>
            <div className="text-right">
                <div className={`px-3 py-1 rounded-full text-xs font-bold text-white mb-2 ${color}`}>
                    {product.quantity} left
                </div>
                <span className="text-xs text-gray-400 block">{text}</span>
            </div>
        </div>
    );
};

export default ProductCard;
