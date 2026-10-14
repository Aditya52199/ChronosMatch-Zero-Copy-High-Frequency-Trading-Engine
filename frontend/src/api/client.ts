const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';

export async function fetchHealth(): Promise<{status:string}> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error('Gateway health check failed');
  return response.json();
}

export async function fetchMarkets(): Promise<{symbol:string; price:number; change:number}[]> {
  const response = await fetch(`${API_BASE}/api/markets`);
  if (!response.ok) throw new Error('Market request failed');
  return response.json();
}

export async function submitPaperOrder(order: {symbol:string; side:'buy'|'sell'; quantity:number; type:'market'|'limit'; limitPrice?:number}) {
  const response = await fetch(`${API_BASE}/api/orders`, {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(order),
  });
  if (!response.ok) throw new Error((await response.text()) || 'Order rejected');
  return response.json();
}
