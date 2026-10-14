import { useEffect } from 'react';
export function useInterval(callback:()=>void, delay:number|null) {
  useEffect(()=>{ if(delay===null)return; const id=window.setInterval(callback,delay); return ()=>window.clearInterval(id); },[callback,delay]);
}
