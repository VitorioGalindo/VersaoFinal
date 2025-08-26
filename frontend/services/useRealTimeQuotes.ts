import { useState, useEffect, useRef } from 'react';
import io, { Socket } from 'socket.io-client';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001';

export interface RealTimeQuote {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  volume: number;
  time: string;
  source: string;
  price: number;
  flags: number;
  volume_real: number;
  is_realtime: boolean;
  price_change?: number;
  price_change_percent?: number;
  open_price?: number;
  high_price?: number;
  low_price?: number;
}

export function useRealTimeQuotes(symbols: string[]) {
  const [quotes, setQuotes] = useState<Record<string, RealTimeQuote>>({});
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Conectar ao WebSocket
    console.log('Initializing WebSocket connection');
    const socket = io(API_BASE, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity
    });
    
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('Conectado ao WebSocket para cotações em tempo real');
      setConnected(true);
      
      // Inscrever nos símbolos solicitados
      if (symbols.length > 0) {
        console.log('Subscribing to quotes on connect:', symbols);
        socket.emit('subscribe_quotes', { tickers: symbols });
      }
    });

    socket.on('disconnect', () => {
      console.log('Desconectado do WebSocket');
      setConnected(false);
    });

    socket.on('price_update', (data: RealTimeQuote) => {
      // Atualizar o estado com a nova cotação
      console.log('Received price update:', data);
      setQuotes(prev => ({
        ...prev,
        [data.symbol]: data
      }));
    });

    socket.on('connect_error', (error) => {
      console.error('Erro na conexão WebSocket:', error);
    });

    return () => {
      console.log('Closing WebSocket connection');
      socket.close();
    };
  }, []);

  // Efeito para atualizar as subscrições quando os símbolos mudarem
  useEffect(() => {
    if (socketRef.current && connected && symbols.length > 0) {
      console.log('Subscribing to quotes:', symbols);
      socketRef.current.emit('subscribe_quotes', { tickers: symbols });
    }
    
    // Tentar novamente a subscrição se não estiver conectado
    if (socketRef.current && !connected && symbols.length > 0) {
      console.log('Not connected, will retry subscription when connected');
    }
  }, [symbols.join(','), connected]);

  return { quotes, connected };
}