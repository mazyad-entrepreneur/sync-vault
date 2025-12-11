import { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';
import { getAuthToken } from '../utils';
import { useCamera } from '../hooks/useCamera';
import Navbar from '../components/Navbar';
import { toast } from 'react-hot-toast';

const Scan = () => {
    const [lastScan, setLastScan] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [scannedCode, setScannedCode] = useState<string | null>(null);

    // Separate effect to handle the API call and camera stopping after a scan
    useEffect(() => {
        if (scannedCode && !loading) {
            processScan(scannedCode);
        }
    }, [scannedCode]);

    const processScan = async (barcode: string) => {
        stopCamera(); // Stop camera immediately
        setLoading(true);
        toast.loading('Processing Scan...', { id: 'scan' });

        try {
            const token = getAuthToken();
            // Default to "sale" action as per user flow
            const { data } = await axios.post(
                `${API_URL}/inventory/scan`,
                { barcode, action: 'sale', quantity: 1 },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            setLastScan({
                barcode,
                product: data.product_name || 'Unknown Product',
                status: 'success',
                timestamp: new Date()
            });

            toast.success(`Scanned: ${data.product_name || barcode}`, { id: 'scan' });

        } catch (error) {
            console.error(error);
            toast.error('Scan Failed: Product not found?', { id: 'scan' });
            setLastScan({ barcode, status: 'error' });
        } finally {
            setLoading(false);
            setScannedCode(null); // Reset for next valid scan trigger (manual or auto)
        }
    };

    const onScan = (code: string) => {
        // Only set if not already processing to avoid spam
        if (!loading && !lastScan) {
            setScannedCode(code);
        }
    };

    const { videoRef, canvasRef, startCamera, stopCamera, isScanning } = useCamera(onScan);

    const handleManualScan = () => {
        setLastScan(null);
        startCamera();
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <div className="bg-gradient-to-r from-indigo-800 to-purple-800 p-4 text-white text-center shadow-lg">
                <h1 className="font-bold text-lg">Scanner</h1>
            </div>

            <div className="flex-1 flex flex-col items-center justify-start pt-4 px-4 space-y-6">
                {/* Camera Viewport */}
                <div className="relative w-full max-w-sm aspect-square bg-black rounded-3xl overflow-hidden shadow-2xl border-4 border-white">
                    <video ref={videoRef} className="absolute inset-0 w-full h-full object-cover" />
                    <canvas ref={canvasRef} className="hidden" />

                    {!isScanning && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                            <button
                                onClick={startCamera}
                                className="bg-white text-indigo-600 px-8 py-3 rounded-full font-bold shadow-lg hover:scale-105 transition-transform"
                            >
                                📷 Start Camera
                            </button>
                        </div>
                    )}

                    {isScanning && (
                        <div className="absolute inset-0 border-2 border-green-400 opacity-50 animate-pulse pointer-events-none"></div>
                    )}
                </div>

                {/* Last Scan Result */}
                {lastScan && (
                    <div className="w-full max-w-sm bg-white p-6 rounded-2xl shadow-xl transform transition-all">
                        <p className="text-gray-400 text-xs uppercase tracking-wider font-bold mb-2">Last Scan</p>
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-xl font-bold text-gray-900">{lastScan.product}</h3>
                                <code className="bg-gray-100 px-2 py-1 rounded text-sm text-gray-600">{lastScan.barcode}</code>
                            </div>
                            <div className={`p-3 rounded-full ${lastScan.status === 'success' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                                {lastScan.status === 'success' ? '✓' : '✕'}
                            </div>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-100 text-center">
                            <button
                                onClick={handleManualScan}
                                className="text-indigo-600 font-semibold"
                            >
                                ↻ Scan Another
                            </button>
                        </div>
                    </div>
                )}

                {/* Manual Input Fallback */}
                {!isScanning && !lastScan && (
                    <div className="w-full max-w-sm text-center">
                        <p className="text-gray-400 text-sm">Point camera at a barcode to scan</p>
                    </div>
                )}

            </div>
            <div className="h-20"></div>
            <Navbar />
        </div>
    );
};

export default Scan;
