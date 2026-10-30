import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AlertTriangle, BarChart3, CalendarClock, Database, Download, FileSpreadsheet } from 'lucide-react';
import './styles.css';
import { getJson, postJson } from './api';

type Dashboard = {
  total_itens: number;
  total_softwares_distintos: number;
  por_status: Record<string, number>;
  por_modalidade: Record<string, number>;
  por_prioridade: Record<string, number>;
  vencimentos: Record<string, number>;
  vencidos: number;
  itens_sem_processo_sei: number;
  itens_sem_quantidade_definida: number;
};

type Named = { id: number; nome: string };
type Area = { id: number; sigla: string; nome: string };
type Processo = { id: number; numero: string };
type Contrato = { id: number; numero: string; fornecedor: string };
type Item = { id: number; software?: Named; status: string; modalidade: string; prioridade: string; quantidade_solicitada?: number; areas: Area[]; processos: Processo[] };

function App() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [softwares, setSoftwares] = useState<Named[]>([]);
  const [areas, setAreas] = useState<Area[]>([]);
  const [ciclos, setCiclos] = useState<Named[]>([]);
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [itens, setItens] = useState<Item[]>([]);
  const [view, setView] = useState('dashboard');

  async function load() {
    const [dash, sw, ar, ci, co, it] = await Promise.all([
      getJson<Dashboard>('/dashboard'),
      getJson<Named[]>('/softwares'),
      getJson<Area[]>('/areas'),
      getJson<Named[]>('/ciclos'),
      getJson<Contrato[]>('/contratos'),
      getJson<Item[]>('/itens'),
    ]);
    setDashboard(dash); setSoftwares(sw); setAreas(ar); setCiclos(ci); setContratos(co); setItens(it);
  }

  useEffect(() => { load(); }, []);

  return <div className="min-h-screen bg-slate-100 text-slate-900">
    <div className="bg-[#7e1819] text-white text-sm"><div className="mx-auto flex max-w-7xl justify-end gap-4 px-4 py-2"><span>Acessibilidade</span><span>Alto contraste</span></div></div>
    <header className="bg-white border-b"><div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-5"><div className="border-b-4 border-yellow-600 bg-[#003f6b] px-4 py-3 font-bold text-white">SWP</div><div><p className="text-sm text-slate-600">Tribunal de Justiça do Estado de Minas Gerais</p><h1 className="text-2xl font-bold text-[#002b49]">Controle de Ciclo de Contratações de Software de Prateleira</h1></div></div><nav className="bg-[#003f6b]"><div className="mx-auto flex max-w-7xl flex-wrap px-4">{['dashboard','itens','softwares','areas','contratos','relatorios'].map(v => <button key={v} onClick={() => setView(v)} className={`px-4 py-3 font-semibold text-white ${view === v ? 'bg-yellow-600 text-[#002b49]' : ''}`}>{v}</button>)}</div></nav></header>
    <main className="mx-auto max-w-7xl px-4 py-6">
      {view === 'dashboard' && dashboard && <DashboardView dashboard={dashboard} />}
      {view === 'itens' && <ItemsView itens={itens} ciclos={ciclos} softwares={softwares} areas={areas} contratos={contratos} reload={load} />}
      {view === 'softwares' && <SimpleCreate title="Softwares" endpoint="/softwares" fields={[['nome','Nome'],['fabricante','Fabricante'],['categoria','Categoria'],['tipo_licenca','Tipo de licença']]} rows={softwares} reload={load} />}
      {view === 'areas' && <SimpleCreate title="Áreas" endpoint="/areas" fields={[['sigla','Sigla'],['nome','Nome'],['responsavel','Responsável'],['email','E-mail']]} rows={areas} reload={load} />}
      {view === 'contratos' && <ContractsView contratos={contratos} softwares={softwares} reload={load} />}
      {view === 'relatorios' && <ReportsView />}
    </main>
  </div>;
}

function DashboardView({ dashboard }: { dashboard: Dashboard }) {
  return <div className="space-y-6"><section className="grid gap-4 md:grid-cols-4"><Metric icon={<Database />} label="Itens" value={dashboard.total_itens} /><Metric icon={<BarChart3 />} label="Softwares distintos" value={dashboard.total_softwares_distintos} /><Metric icon={<AlertTriangle />} label="Vencidos" value={dashboard.vencidos} /><Metric icon={<CalendarClock />} label="Sem processo SEI" value={dashboard.itens_sem_processo_sei} /></section><Panel title="Alertas de vencimento"><div className="grid gap-3 md:grid-cols-5">{Object.entries(dashboard.vencimentos).map(([k,v]) => <Metric key={k} label={k.replace('ate_','Até ').replace('_dias',' dias')} value={v} />)}</div></Panel><Breakdown title="Por status" data={dashboard.por_status} /><Breakdown title="Por modalidade" data={dashboard.por_modalidade} /><Breakdown title="Por prioridade" data={dashboard.por_prioridade} /></div>;
}
function Metric({ label, value, icon }: { label: string; value: number; icon?: React.ReactNode }) { return <div className="border-l-4 border-yellow-600 bg-white p-4 shadow-sm"><div className="flex items-center gap-2 text-[#003f6b]">{icon}<span className="text-sm font-semibold">{label}</span></div><strong className="text-3xl text-[#002b49]">{value}</strong></div>; }
function Panel({ title, children }: { title: string; children: React.ReactNode }) { return <section className="bg-white p-5 shadow-sm border"><h2 className="mb-4 text-xl font-bold text-[#002b49]">{title}</h2>{children}</section>; }
function Breakdown({ title, data }: { title: string; data: Record<string, number> }) { return <Panel title={title}><div className="grid gap-2 md:grid-cols-3">{Object.entries(data).map(([k,v]) => <div className="flex justify-between border bg-slate-50 p-3" key={k}><span>{k}</span><strong>{v}</strong></div>)}</div></Panel>; }

function SimpleCreate({ title, endpoint, fields, rows, reload }: any) { const [form,setForm]=useState<Record<string,string>>({}); async function save(){ await postJson(endpoint, form); setForm({}); reload(); } return <Panel title={title}><div className="mb-4 grid gap-3 md:grid-cols-4">{fields.map(([k,l]: string[]) => <input className="border p-2" key={k} placeholder={l} value={form[k]||''} onChange={e=>setForm({...form,[k]:e.target.value})}/>)}<button className="bg-[#003f6b] p-2 font-bold text-white" onClick={save}>Salvar</button></div><table className="w-full border-collapse"><tbody>{rows.map((r:any)=><tr className="border-b" key={r.id}><td className="p-2 font-semibold">{r.nome || r.sigla}</td><td className="p-2">{r.fabricante || r.responsavel || ''}</td></tr>)}</tbody></table></Panel>; }

function ItemsView({ itens, ciclos, softwares, areas, contratos, reload }: any) { const [form,setForm]=useState<any>({tipo_movimentacao:'novo_pedido', modalidade:'a_definir', prioridade:'media', status:'cadastrado', unidade_medida:'licenca'}); async function save(){ await postJson('/itens', {...form, ciclo_id:+form.ciclo_id, software_id:+form.software_id, contrato_id: form.contrato_id ? +form.contrato_id : null, quantidade_solicitada: form.quantidade_solicitada ? +form.quantidade_solicitada : null, area_ids:[+form.area_id], processo_ids:[]}); reload(); } return <Panel title="Itens do ciclo"><div className="mb-4 grid gap-3 md:grid-cols-[minmax(28rem,2.2fr)_minmax(18rem,1.4fr)_minmax(10rem,.8fr)_minmax(12rem,.8fr)]"><Select label="Ciclo" items={ciclos} className="min-w-[28rem]" onChange={v=>setForm({...form,ciclo_id:v})}/><Select label="Software" items={softwares} className="min-w-[18rem]" onChange={v=>setForm({...form,software_id:v})}/><Select label="Área" items={areas.map((a:any)=>({id:a.id,nome:a.sigla}))} onChange={v=>setForm({...form,area_id:v})}/><Select label="Contrato" items={contratos.map((c:any)=>({id:c.id,nome:c.numero}))} onChange={v=>setForm({...form,contrato_id:v})}/><input className="border p-2" placeholder="Quantidade" onChange={e=>setForm({...form,quantidade_solicitada:e.target.value})}/><input className="border p-2" placeholder="Justificativa" onChange={e=>setForm({...form,justificativa:e.target.value})}/><button className="bg-[#003f6b] p-2 font-bold text-white" onClick={save}>Salvar item</button></div><table className="w-full"><tbody>{itens.map((i:any)=><tr className="border-b" key={i.id}><td className="p-2">{i.software?.nome}</td><td>{i.modalidade}</td><td>{i.status}</td><td>{i.areas?.map((a:any)=>a.sigla).join(', ')}</td></tr>)}</tbody></table></Panel>; }
function Select({ label, items, onChange, className = "" }: any) { return <select className={`border p-2 ${className}`} title={label} onChange={e=>onChange(e.target.value)}><option>{label}</option>{items.map((i:any)=><option key={i.id} value={i.id}>{i.nome}</option>)}</select>; }
function ContractsView({ contratos, softwares, reload }: any) { const [form,setForm]=useState<any>({status:'vigente'}); async function save(){ await postJson('/contratos', {...form, software_id:+form.software_id}); reload(); } return <Panel title="Contratos"><div className="grid gap-3 md:grid-cols-4"><Select label="Software" items={softwares} onChange={v=>setForm({...form,software_id:v})}/>{['numero','fornecedor','data_inicio','data_fim','vencimento_subscricao'].map(k=><input key={k} className="border p-2" placeholder={k} type={k.includes('data')||k.includes('vencimento')?'date':'text'} onChange={e=>setForm({...form,[k]:e.target.value})}/>) }<button className="bg-[#003f6b] p-2 font-bold text-white" onClick={save}>Salvar</button></div><table className="mt-4 w-full"><tbody>{contratos.map((c:any)=><tr className="border-b" key={c.id}><td className="p-2">{c.numero}</td><td>{c.fornecedor}</td><td>{c.vencimento_subscricao}</td></tr>)}</tbody></table></Panel>; }
function ReportsView() { const links=['itens','consolidado-softwares','por-area','vencimentos']; return <Panel title="Relatórios e exportações"><div className="grid gap-3 md:grid-cols-2">{links.map(l=><div className="flex items-center justify-between border p-3" key={l}><span>{l}</span><div className="flex gap-2"><a className="font-bold text-[#003f6b]" href={`/api/v1/export/${l}?formato=csv`}><Download className="inline" /> CSV</a><a className="font-bold text-[#003f6b]" href={`/api/v1/export/${l}?formato=xlsx`}><FileSpreadsheet className="inline" /> XLSX</a></div></div>)}</div></Panel>; }

createRoot(document.getElementById('root')!).render(<App />);
