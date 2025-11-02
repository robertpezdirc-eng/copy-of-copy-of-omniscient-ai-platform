import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnection?: boolean;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
}

interface UseWebSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  error: Error | null;
  emit: (event: string, data?: any) => void;
  on: (event: string, handler: (data: any) => void) => void;
  off: (event: string, handler?: (data: any) => void) => void;
}

export const useWebSocket = (options: UseWebSocketOptions): UseWebSocketReturn => {
  const {
    url,
    autoConnect = true,
    reconnection = true,
    reconnectionAttempts = 5,
    reconnectionDelay = 1000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    if (!autoConnect) return;

    // Initialize socket connection
    socketRef.current = io(url, {
      reconnection,
      reconnectionAttempts,
      reconnectionDelay,
      transports: ['websocket', 'polling'],
    });

    const socket = socketRef.current;

    // Connection event handlers
    socket.on('connect', () => {
      console.log('WebSocket connected:', socket.id);
      setIsConnected(true);
      setError(null);
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setIsConnected(false);
    });

    socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err);
      setError(err);
      setIsConnected(false);
    });

    socket.on('error', (err) => {
      console.error('WebSocket error:', err);
      setError(err);
    });

    // Cleanup on unmount
    return () => {
      if (socket) {
        socket.removeAllListeners();
        socket.close();
      }
    };
  }, [url, autoConnect, reconnection, reconnectionAttempts, reconnectionDelay]);

  const emit = (event: string, data?: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('Socket not connected, cannot emit:', event);
    }
  };

  const on = (event: string, handler: (data: any) => void) => {
    socketRef.current?.on(event, handler);
  };

  const off = (event: string, handler?: (data: any) => void) => {
    if (handler) {
      socketRef.current?.off(event, handler);
    } else {
      socketRef.current?.off(event);
    }
  };

  return {
    socket: socketRef.current,
    isConnected,
    error,
    emit,
    on,
    off,
  };
};
