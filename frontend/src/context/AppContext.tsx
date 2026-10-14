import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
type AppState = { selectedSymbol:string; setSelectedSymbol:(s:string)=>void };
const Context = createContext<AppState | null>(null);
export function AppProvider({children}:{children:ReactNode}) {
  const [selectedSymbol,setSelectedSymbol] = useState('BTC-USD');
  const value = useMemo(()=>({selectedSymbol,setSelectedSymbol}),[selectedSymbol]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}
export function useAppState() {
  const value = useContext(Context);
  if (!value) throw new Error('useAppState must be used inside AppProvider');
  return value;
}
