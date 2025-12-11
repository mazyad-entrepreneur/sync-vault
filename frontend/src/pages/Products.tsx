import { useState, ChangeEvent } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import { getAuthToken } from '../utils';
import Navbar from '../components/Navbar';
import { toast } from 'react-hot-toast';

const Products = () => {
    const [uploading, setUploading] = useState(false);

    const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files?.[0]) return;

        const file = e.target.files[0];
        const formData = new FormData();
        formData.append('csv_file', file); // Field name matches backend 'csv_file'

        setUploading(true);
        const toastId = toast.loading('Uploading Products...');

        try {
            const token = getAuthToken();
            await axios.post(`${API_URL}/products/bulk-upload`, formData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data',
                },
            });
            toast.success('Products Uploaded Successfully!', { id: toastId });
        } catch (error) {
            console.error(error);
            toast.error('Upload Failed', { id: toastId });
        } finally {
            setUploading(false);
            // Clear input
            e.target.value = '';
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-6 pb-12 rounded-b-[2rem] shadow-lg text-white">
                <h1 className="text-2xl font-bold">Product Management</h1>
                <p className="opacity-80">Upload and manage your inventory</p>
            </div>

            <div className="-mt-8 px-4">
                {/* Upload Card */}
                <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
                    <div className="text-center">
                        <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                            📂
                        </div>
                        <h3 className="text-lg font-bold text-gray-900 mb-2">Bulk Upload</h3>
                        <p className="text-gray-500 text-sm mb-6">
                            Upload a CSV file to add multiple products at once.
                        </p>

                        <label className={`block w-full cursor-pointer ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
                            <span className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-bold py-3 px-6 rounded-xl shadow-lg block hover:shadow-xl transition-all">
                                {uploading ? 'Uploading...' : 'Select CSV File'}
                            </span>
                            <input
                                type="file"
                                accept=".csv"
                                className="hidden"
                                onChange={handleFileUpload}
                                disabled={uploading}
                            />
                        </label>

                        <a href="#" className="text-xs text-indigo-400 mt-4 block underline">Download Sample CSV</a>
                    </div>
                </div>

                {/* Feature Placeholder */}
                <div className="text-center py-10 opacity-50">
                    <p>More management features coming soon...</p>
                </div>
            </div>
            <Navbar />
        </div>
    );
};

export default Products;
