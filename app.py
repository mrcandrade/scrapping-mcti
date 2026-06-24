"""
Página web interativa para consultar as empresas habilitadas na Lei de Informática,
com foco em parcerias de P&D para um Instituto de Física.

Uso:
    1. No notebook:  exportar_para_site(resultado_df, "empresas.json")
    2. Servidor:     python app.py            (http://127.0.0.1:5050)
    3. Público:      ngrok http 5050          (em outro terminal)

O servidor relê o empresas.json a cada requisição e a página se atualiza sozinha
(polling), então o site reflete o processamento em tempo real.
"""
import os
import json
from flask import Flask, Response, send_from_directory, abort

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.environ.get("EMPRESAS_JSON", "empresas.json")

# logos servidas por nomes seguros (evita servir arquivos arbitrários do diretório)
LOGOS = {"ufrgs": "UFRGS.png", "if": "IF-UFRGS_-logo.png", "ceenf": "images.jpg"}


def carregar_dados():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


PAGINA = r"""<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Empresas Habilitadas — Parcerias de P&D (Instituto de Física)</title>
<style>
  :root{
    --bg:#f4f6f9; --panel:#ffffff; --line:#e2e6ec; --txt:#1d2330; --muted:#6b7384;
    --accent:#15396b; --accent-soft:#e7eef9;
    --brand:#0c2c5c; --red:#ec3237; --red-soft:#fdeaea;
    --alto:#16a34a; --alto-bg:#e7f6ec; --medio:#d97706; --medio-bg:#fbf0df; --baixo:#64748b; --baixo-bg:#eef1f5;
    --chip:#f0f2f6;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;font-size:14px;line-height:1.5}
  a{color:var(--accent);text-decoration:none}
  .ribbon{height:4px;background:var(--red)}
  header{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.95);
    backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:14px 22px}
  .title-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
  h1{font-size:18px;margin:0;font-weight:700;letter-spacing:-.01em;border-left:4px solid var(--red);padding-left:10px}
  .sub{color:var(--muted);font-size:13px}
  .sub b{color:var(--red);font-weight:700}
  .controls{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
  .controls input,.controls select{
    background:var(--panel);color:var(--txt);border:1px solid var(--line);
    border-radius:9px;padding:9px 12px;font-size:14px;outline:none}
  .controls input{flex:1;min-width:240px}
  .controls input:focus,.controls select:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
  .controls button{background:var(--panel);border:1px solid var(--line);border-radius:9px;
    padding:9px 12px;font-size:14px;cursor:pointer;color:var(--txt)}
  .controls button:hover{border-color:var(--red);color:var(--red)}
  .auto{display:flex;align-items:center;gap:6px;color:var(--muted);font-size:13px;white-space:nowrap}
  main{max-width:1180px;margin:0 auto;padding:20px 22px 40px}
  .brand{display:flex;align-items:center;justify-content:space-between;gap:16px;background:#fff;
    border-bottom:3px solid var(--brand);padding:10px 22px;flex-wrap:wrap}
  .brand-logos{display:flex;align-items:center;gap:20px}
  .brand img{height:48px;width:auto;object-fit:contain;display:block}
  .brand img.if-logo{height:38px}
  .rodape{background:var(--brand);color:#cdddf2;text-align:center;font-size:13px;padding:18px 22px;margin-top:24px;
    border-top:3px solid var(--red)}
  .rodape b{color:#fff}
  @media(max-width:560px){ .brand img{height:38px} .brand-logos{gap:12px} }

  /* ---- KPIs ---- */
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-bottom:18px}
  .kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 15px;border-top:3px solid var(--accent)}
  .kpi .num{font-size:24px;font-weight:800;letter-spacing:-.02em}
  .kpi .lab{font-size:11.5px;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:.03em}
  .kpi.destaque{border-top-color:var(--red)} .kpi.destaque .num{color:var(--red)}

  /* ---- gráficos ---- */
  .charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px;margin-bottom:20px}
  .chart{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}
  .chart h3{margin:0 0 12px;font-size:13px;font-weight:650;color:var(--txt);border-left:3px solid var(--red);padding-left:8px}
  .bar-row{display:grid;grid-template-columns:130px 1fr 34px;gap:8px;align-items:center;margin:6px 0;font-size:12px}
  .bar-label{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--muted)}
  .bar-track{background:#eef1f5;border-radius:6px;height:16px;overflow:hidden}
  .bar-fill{height:100%;border-radius:6px;background:var(--accent);min-width:2px;transition:width .3s}
  .bar-val{text-align:right;color:var(--txt);font-variant-numeric:tabular-nums}
  .fill-alto{background:var(--alto)} .fill-medio{background:var(--medio)} .fill-baixo{background:var(--baixo)}
  .fill-seg{background:var(--red)} .fill-nicho{background:var(--accent)}

  /* ---- lista horizontal ---- */
  .lista{display:flex;flex-direction:column;gap:10px}
  .item{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--line);
    border-radius:14px;overflow:hidden;transition:box-shadow .15s,transform .15s}
  .item:hover{box-shadow:0 8px 22px rgba(12,44,92,.10)}
  .item.alto{border-left-color:var(--alto)} .item.medio{border-left-color:var(--medio)} .item.baixo{border-left-color:var(--baixo)}
  .row{display:grid;grid-template-columns:46px 1.15fr 1.7fr 215px;gap:16px;align-items:center;padding:14px 18px}
  .rank{font-weight:800;color:var(--muted);font-size:14px}
  .rank.top{color:var(--red)}
  .nome{font-weight:650;font-size:15px}
  .razao{color:var(--muted);font-size:12px;margin-top:1px}
  .loc{color:var(--muted);font-size:12px;margin-top:3px}
  .meta{display:flex;flex-direction:column;gap:7px;min-width:0}
  .meta-top{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .setor{font-size:13px;font-weight:600}
  .nicho{font-size:12px;color:var(--muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
  .chips{display:flex;flex-wrap:wrap;gap:5px}
  .chip{font-size:11px;padding:2px 8px;border-radius:999px;background:var(--chip);border:1px solid var(--line);color:#445}
  .pot{font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;white-space:nowrap}
  .pot-alto{background:var(--alto-bg);color:var(--alto)}
  .pot-medio{background:var(--medio-bg);color:var(--medio)}
  .pot-baixo{background:var(--baixo-bg);color:var(--baixo)}
  .pot-na{background:var(--chip);color:var(--muted)}
  .acts{display:flex;flex-direction:column;gap:6px;align-items:stretch}
  .btn{font-size:12.5px;padding:7px 10px;border-radius:8px;border:1px solid var(--line);
    background:var(--panel);color:var(--txt);text-align:center;white-space:nowrap;
    overflow:hidden;text-overflow:ellipsis;transition:background .12s,border-color .12s}
  .btn.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
  .btn.primary:hover{background:var(--red);border-color:var(--red)}
  .btn:hover{filter:brightness(.98)}
  .toggle{background:none;border:none;color:var(--accent);cursor:pointer;font-size:12.5px;padding:4px 0}
  .toggle:hover{color:var(--red)}
  .details{display:none;gap:12px;border-top:1px solid var(--line);padding:14px 18px;background:#fbfcfe}
  .details.open{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
  .sec h4{margin:0 0 3px;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
  .sec p{margin:0;font-size:13px}
  .opp{grid-column:1/-1;background:var(--red-soft);border:1px solid #f6c9ca;border-left:4px solid var(--red);
    border-radius:10px;padding:10px 12px}
  .opp h4{color:var(--red);margin:0 0 3px;font-size:11px;text-transform:uppercase;letter-spacing:.04em}
  .opp p{margin:0;font-size:13px}
  .empty{color:var(--muted);text-align:center;padding:60px 20px;font-size:15px}
  @media(max-width:860px){
    .row{grid-template-columns:1fr;gap:10px}
    .rank{display:inline}
    .acts{flex-direction:row;flex-wrap:wrap}
  }
</style>
</head>
<body>
<div class="ribbon"></div>
<div class="brand">
  <div class="brand-logos">
    <img src="/logo/ufrgs" alt="UFRGS">
    <img src="/logo/if" class="if-logo" alt="Instituto de Física - UFRGS">
  </div>
  <div class="brand-logos">
    <img src="/logo/ceenf" alt="CEENF">
  </div>
</div>
<header>
  <div class="title-row">
    <h1>Empresas Habilitadas Parcerias de P&D</h1>
    <span class="sub" id="count"></span>
  </div>
  <div class="controls">
    <input id="busca" type="search" placeholder="Buscar por empresa, setor, nicho, tecnologia, oportunidade…" autocomplete="off">
    <select id="seg"><option value="">Todos os setores</option></select>
    <select id="pot">
      <option value="">Potencial P&amp;D (todos)</option>
      <option value="alto">Alto</option><option value="medio">Médio</option><option value="baixo">Baixo</option>
    </select>
    <select id="ordenar">
      <option value="pot">Ordenar: Potencial P&amp;D ▼</option>
      <option value="nome">Ordenar: Nome (A→Z)</option>
      <option value="setor">Ordenar: Setor</option>
    </select>
    <button id="limpar" type="button">Limpar</button>
    <label class="auto"><input type="checkbox" id="auto" checked> Tempo real</label>
  </div>
</header>
<main>
  <div class="kpis" id="kpis"></div>
  <div class="charts">
    <div class="chart"><h3>Potencial de parceria em P&D</h3><div id="ch-pot"></div></div>
    <div class="chart"><h3>Setores de atuação</h3><div id="ch-seg"></div></div>
    <div class="chart"><h3>Nichos de atuação (top 10)</h3><div id="ch-nicho"></div></div>
  </div>
  <div id="lista" class="lista"></div>
</main>
<footer class="rodape"><b>Instituto de Física — UFRGS</b> · CEENF · Prospecção de parcerias de P&D · empresas habilitadas na Lei de Informática</footer>

<script>
let EMPRESAS = __DADOS__;

const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function txt(v){ if(v==null) return ''; if(Array.isArray(v)) return v.join(', '); return String(v).trim(); }
function lista(v){
  if(v==null) return [];
  if(Array.isArray(v)) return v.map(x=>String(x).trim()).filter(Boolean);
  let s=String(v).trim(); if(!s) return [];
  if(s.startsWith('[')){ try{ const a=JSON.parse(s); if(Array.isArray(a)) return a.map(x=>String(x).trim()).filter(Boolean);}catch(e){} }
  return s.split(/[;,]/).map(x=>x.trim()).filter(Boolean);
}
function url(u){ u=txt(u); if(!u) return ''; if(!/^https?:\/\//i.test(u)) u='https://'+u; return u; }
function potClass(p){ p=txt(p).toLowerCase();
  if(p.includes('baix')) return 'baixo';
  if(p.includes('méd')||p.includes('med')) return 'medio';   // 'médio-alto' conta como médio
  if(p.includes('alto')) return 'alto'; return 'na'; }
function potLabel(p){   // só a classificação (Alto/Médio/Baixo), sem a justificativa
  let s=txt(p); if(!s) return '—';
  s=s.split(/\s+[—–-]+\s+|[(:]/)[0].trim();
  if(s.length>24) s=s.slice(0,24)+'…';
  return s || '—';
}
const POT_PESO = {alto:3, medio:2, baixo:1, na:0};

/* ---------- KPIs ---------- */
const kpisEl=document.getElementById('kpis');
function renderKpis(itens){
  const pc={alto:0,medio:0,baixo:0}; let comSite=0;
  itens.forEach(e=>{ const c=potClass(e.potencial_de_parceria_pd); if(c in pc) pc[c]++; if(txt(e.principal_site)) comSite++; });
  const cards=[
    ['', itens.length, 'Empresas'],
    ['destaque', pc.alto, 'Potencial Alto'],
    ['', pc.medio, 'Potencial Médio'],
    ['', pc.baixo, 'Potencial Baixo'],
    ['', comSite, 'Com site'],
  ];
  kpisEl.innerHTML = cards.map(([cls,n,lab]) =>
    `<div class="kpi ${cls}"><div class="num">${n}</div><div class="lab">${lab}</div></div>`).join('');
}

/* ---------- gráficos (barras CSS) ---------- */
function contagem(itens, getter){
  const m=new Map();
  itens.forEach(e=>{ const v=txt(getter(e)); if(v) m.set(v,(m.get(v)||0)+1); });
  return [...m.entries()].sort((a,b)=>b[1]-a[1]);
}
function barras(elId, dados, classeFill=''){
  const el=document.getElementById(elId);
  if(!dados.length){ el.innerHTML='<div class="sub">sem dados</div>'; return; }
  const max=Math.max(...dados.map(d=>d[1]));
  el.innerHTML=dados.map(([lab,n])=>{
    const cls = classeFill || ('fill-'+potClass(lab));
    return `<div class="bar-row"><span class="bar-label" title="${esc(lab)}">${esc(lab)}</span>
      <span class="bar-track"><span class="bar-fill ${cls}" style="width:${(n/max*100).toFixed(1)}%"></span></span>
      <span class="bar-val">${n}</span></div>`;
  }).join('');
}
function renderCharts(itens){
  const pc={alto:0,medio:0,baixo:0};
  itens.forEach(e=>{ const c=potClass(e.potencial_de_parceria_pd); if(c in pc) pc[c]++; });
  barras('ch-pot', [['Alto',pc.alto],['Médio',pc.medio],['Baixo',pc.baixo]]);
  barras('ch-seg', contagem(itens, e=>e.segmento).slice(0,12), 'fill-seg');
  barras('ch-nicho', contagem(itens, e=>e.nicho_de_atuacao).slice(0,10), 'fill-nicho');
}

/* ---------- item (linha horizontal) ---------- */
function sec(label,v){ const t=txt(v); return t?`<div class="sec"><h4>${esc(label)}</h4><p>${esc(t)}</p></div>`:''; }
function chipsSec(label,v){ const a=lista(v); return a.length
  ?`<div class="sec"><h4>${esc(label)}</h4><div class="chips">${a.map(x=>`<span class="chip">${esc(x)}</span>`).join('')}</div></div>`:''; }

function item(e, rank, idx){
  const nome=esc(txt(e.nome_da_empresa)||txt(e.razao_social)||'Empresa');
  const razao=txt(e.razao_social);
  const loc=[txt(e.municipio),txt(e.uf)].filter(Boolean).join(' / ');
  const pc=potClass(e.potencial_de_parceria_pd);
  const potTxt=potLabel(e.potencial_de_parceria_pd);  // badge curto; justificativa fica nos detalhes
  const setor=txt(e.segmento);
  const chaves=lista(e.setores_chave);

  const site=url(e.principal_site), email=txt(e.email_contato),
        tel=txt(e.telefone_contato), pg=url(e.pagina_contato);
  let acts='';
  if(site) acts+=`<a class="btn primary" href="${esc(site)}" target="_blank" rel="noopener">Visitar site ↗</a>`;
  if(email) acts+=`<a class="btn" href="mailto:${esc(email)}" title="${esc(email)}">✉ E-mail</a>`;
  if(tel) acts+=`<a class="btn" href="tel:${esc(tel.replace(/[^+\d]/g,''))}" title="${esc(tel)}">☎ ${esc(tel)}</a>`;
  if(pg) acts+=`<a class="btn" href="${esc(pg)}" target="_blank" rel="noopener">Contato ↗</a>`;
  acts+=`<button class="toggle" data-i="${idx}">Ver detalhes ▾</button>`;

  const opp=txt(e.oportunidades_de_projetos_pd);
  const detalhes = [
    opp?`<div class="opp"><h4>Oportunidades de P&D</h4><p>${esc(opp)}</p></div>`:'',
    sec('Potencial de parceria (P&D)', e.potencial_de_parceria_pd),
    sec('Nicho de atuação', e.nicho_de_atuacao),
    sec('Principais produtos e serviços', e.principais_produtos_e_servicos),
    chipsSec('Setores-chave', e.setores_chave),
    chipsSec('Tecnologias', e.tecnologias_utilizadas),
    chipsSec('Áreas de P&D', e.areas_de_pd),
    sec('Linhas de pesquisa e inovação', e.linhas_de_pesquisa_e_inovacao),
    sec('Status na Lei de Informática', e.status_habilitacao_lei_informatica),
    sec('Público alvo', e.publico_alvo),
    sec('Diferenciais', e.diferenciais_da_empresa),
    sec('Relevância para o mercado', e.visao_e_relevancia_para_o_mercado),
    chipsSec('Redes sociais', e.redes_sociais_principais),
    sec('Pessoa / área de contato', e.pessoa_contato),
    sec('CNPJ', e.cnpj_da_empresa),
    sec('Endereço', e.endereco),
    chipsSec('Palavras-chave', e.palavras_chaves_de_definicao_da_empresa),
  ].join('');

  return `<article class="item ${pc}">
    <div class="row">
      <div class="rank${rank<=3?' top':''}">#${rank}</div>
      <div>
        <div class="nome">${nome}</div>
        ${razao && razao!==nome?`<div class="razao">${esc(razao)}</div>`:''}
        ${loc?`<div class="loc">📍 ${esc(loc)}</div>`:''}
      </div>
      <div class="meta">
        <div class="meta-top">
          <span class="pot pot-${pc}">P&D: ${esc(potTxt)}</span>
          ${setor?`<span class="setor">${esc(setor)}</span>`:''}
        </div>
        ${chaves.length?`<div class="chips">${chaves.map(x=>`<span class="chip">${esc(x)}</span>`).join('')}</div>`:''}
        ${txt(e.nicho_de_atuacao)?`<div class="nicho">${esc(txt(e.nicho_de_atuacao))}</div>`:''}
      </div>
      <div class="acts">${acts}</div>
    </div>
    <div class="details" id="det-${idx}">${detalhes}</div>
  </article>`;
}

/* ---------- controles ---------- */
const lst=document.getElementById('lista'), busca=document.getElementById('busca'),
      segSel=document.getElementById('seg'), potSel=document.getElementById('pot'),
      ordSel=document.getElementById('ordenar'), contador=document.getElementById('count');

function repovoarSelect(){
  const atual=segSel.value, ph=segSel.options[0];
  segSel.innerHTML=''; segSel.appendChild(ph);
  [...new Set(EMPRESAS.map(e=>txt(e.segmento)).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pt'))
    .forEach(v=>{ const o=document.createElement('option'); o.value=v; o.textContent=v; segSel.appendChild(o); });
  segSel.value=atual; if(segSel.value!==atual) segSel.value='';
}

function casa(e){
  const q=busca.value.toLowerCase().trim();
  if(q){
    const hay=[e.nome_da_empresa,e.razao_social,e.segmento,e.nicho_de_atuacao,e.municipio,
      e.oportunidades_de_projetos_pd, lista(e.setores_chave).join(' '),
      lista(e.tecnologias_utilizadas).join(' '), lista(e.palavras_chaves_de_definicao_da_empresa).join(' ')]
      .map(x=>txt(x).toLowerCase()).join(' ');
    if(!hay.includes(q)) return false;
  }
  if(segSel.value && txt(e.segmento)!==segSel.value) return false;
  if(potSel.value && potClass(e.potencial_de_parceria_pd)!==potSel.value) return false;
  return true;
}
function ordena(a,b){
  const o=ordSel.value;
  if(o==='nome') return txt(a.nome_da_empresa).localeCompare(txt(b.nome_da_empresa),'pt');
  if(o==='setor') return txt(a.segmento).localeCompare(txt(b.segmento),'pt')
      || txt(a.nome_da_empresa).localeCompare(txt(b.nome_da_empresa),'pt');
  const d=POT_PESO[potClass(b.potencial_de_parceria_pd)]-POT_PESO[potClass(a.potencial_de_parceria_pd)];
  return d || txt(a.nome_da_empresa).localeCompare(txt(b.nome_da_empresa),'pt');
}

function render(){
  if(!EMPRESAS.length){
    lst.innerHTML='<div class="empty">Nenhuma empresa carregada.<br>Gere o <code>empresas.json</code> no notebook (exportar_para_site) — a página atualiza sozinha.</div>';
    contador.textContent=''; renderCharts([]); renderKpis([]); return;
  }
  const filtradas=EMPRESAS.filter(casa).sort(ordena);
  renderKpis(filtradas);
  renderCharts(filtradas);
  contador.innerHTML=`<b>${filtradas.length}</b> de ${EMPRESAS.length} empresas`;
  lst.innerHTML = filtradas.length
    ? filtradas.map((e,i)=>item(e, i+1, EMPRESAS.indexOf(e))).join('')
    : '<div class="empty">Nenhuma empresa encontrada para os filtros aplicados.</div>';
}

lst.addEventListener('click', ev=>{
  const b=ev.target.closest('.toggle'); if(!b) return;
  const d=document.getElementById('det-'+b.dataset.i);
  const aberto=d.classList.toggle('open');
  b.textContent = aberto ? 'Ocultar detalhes ▴' : 'Ver detalhes ▾';
});
let _tBusca; busca.addEventListener('input',()=>{ clearTimeout(_tBusca); _tBusca=setTimeout(render,150); });
[segSel,potSel,ordSel].forEach(el=>el.addEventListener('input',render));
document.getElementById('limpar').addEventListener('click',()=>{
  busca.value='';segSel.value='';potSel.value='';ordSel.value='pot';render();
});

repovoarSelect();
render();

// atualização em tempo real: relê /dados e re-renderiza só quando muda
async function puxar(){
  try{
    const r=await fetch('/dados',{cache:'no-store'}); if(!r.ok) return;
    const novo=await r.json();
    if(JSON.stringify(novo)!==JSON.stringify(EMPRESAS)){ EMPRESAS=novo; repovoarSelect(); render(); }
  }catch(e){}
}
setInterval(()=>{ if(document.getElementById('auto').checked) puxar(); }, 6000);
</script>
</body>
</html>"""


@app.route("/")
def index():
    dados = carregar_dados()
    # "</" -> "<\/" evita que algum campo com "</script>" feche o bloco <script>
    payload = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    html = PAGINA.replace("__DADOS__", payload)
    return Response(html, mimetype="text/html")


@app.route("/dados")
def dados():
    return Response(json.dumps(carregar_dados(), ensure_ascii=False),
                    mimetype="application/json")


@app.route("/logo/<chave>")
def logo(chave):
    nome = LOGOS.get(chave)
    if not nome:
        abort(404)
    return send_from_directory(BASE_DIR, nome)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, threaded=True)
