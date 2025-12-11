import { useEffect, useRef, useState } from 'react';
import jsQR from 'jsqr';

export const useCamera = (onScan: (data: string) => void) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isScanning, setIsScanning] = useState(false);
    const requestRef = useRef<number>();

    const startCamera = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' }
            });

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                videoRef.current.setAttribute('playsinline', 'true');
                videoRef.current.play();
                setIsScanning(true);
                requestRef.current = requestAnimationFrame(tick);
            }
        } catch (err) {
            console.error("Camera access denied", err);
        }
    };

    const stopCamera = () => {
        if (videoRef.current && videoRef.current.srcObject) {
            (videoRef.current.srcObject as MediaStream).getTracks().forEach(t => t.stop());
            setIsScanning(false);
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
        }
    };

    const tick = () => {
        if (videoRef.current && videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA && canvasRef.current) {
            const canvas = canvasRef.current;
            const video = videoRef.current;

            canvas.height = video.videoHeight;
            canvas.width = video.videoWidth;

            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

                const code = jsQR(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: "dontInvert",
                });

                if (code) {
                    onScan(code.data);
                    // Optional: Pause scanning slightly after success to avoid duplicate readings
                }
            }
        }
        requestRef.current = requestAnimationFrame(tick);
    };

    useEffect(() => {
        return () => {
            stopCamera();
        };
    }, []);

    return { videoRef, canvasRef, startCamera, stopCamera, isScanning };
};
