import type { ReactNode } from 'react';
export function Panel({title, children, action}:{title:string; children:ReactNode; action?:ReactNode}) {
  return <section className="panel"><div className="panel-heading"><h2>{title}</h2>{action}</div>{children}</section>;
}
