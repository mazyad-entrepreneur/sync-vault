import { useEffect, useRef, useState } from 'react';
import { WS_URL } from '../config';
import { getAuthToken } from '../utils';
import { toast } from 'react-hot-toast';

export const useWebSocket = (storeId?: number) => {
    const ws = useRef<WebSocket | null>(null);
    const [lastMessage, setLastMessage] = useState<any>(null);

    useEffect(() => {
        if (!storeId) return;

        const connect = () => {
            const token = getAuthToken();
            // WebSocket URL might need token in query param if headers not supported in browser WS
            // or headers if using a library, but native WS doesn't support headers easily.
            // Usually passed in query string: ?token=...
            const url = `${WS_URL}/${storeId}?token=${token}`;

            ws.current = new WebSocket(url);

            ws.current.onopen = () => {
                console.log('WS Connected');
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setLastMessage(data);
                    if (data.type === 'inventory_update') {
                        toast('Inventory Updated', { icon: '🔄' });
                    }
                } catch (e) {
                    console.error(e);
                }
            };

            ws.current.onerror = (e) => {
                console.error('WS Error', e);
            };

            ws.current.onclose = () => {
                console.log('WS Closed, retrying...');
                setTimeout(connect, 3000);
            };
        };

        connect();

        return () => {
            ws.current?.close();
        };
    }, [storeId]);

    return lastMessage;
};
