export interface User {
    id: number;
    phone: string;
    store_name: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface Product {
    id: number;
    name: string;
    barcode: string;
    price: number;
    quantity: number;
    category: string;
    reorder_point: number;
    unit?: string;
}

export interface ScanResult {
    product: Product;
    action: 'sale' | 'restock';
    quantity: number;
    timestamp: string;
}

export interface DashboardStats {
    total_products: number;
    total_value: number;
    low_stock_count: number;
    recent_scans: ScanResult[];
}
