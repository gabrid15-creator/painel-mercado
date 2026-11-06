(() => {
  // ---------------------------------------------------------------- dados
  const IDS = ['mi_geral', 'mi_ativos', 'mi_sazon', 'mi_corr', 'mi_cot', 'mi_macro', 'mi_hist', 'mi_agenda', 'mi_noticias', 'mi_status', 'mi_score', 'mi_ia', 'mi_eua', 'goldbach_dias', 'op_cadeia', 'op_paredes', 'op_boletim', 'ouro_paredes', 'ouro_resumo', 'ouro_gamma'];
  const store = {};
  const D = (id) => store[id] || { status: 'loading', data: [] };
  const COLORS = ['#3b7dd8', '#e07b39', '#2a9d8f', '#d64f8f', '#8e6bd1', '#b58a1b', '#5b8c3a', '#7a7a7a'];
  // dados da coleta (mi_*) vêm da branch "dados", atualizada a cada 5 min sem depender do deploy do Pages;
  // se falhar, usa a cópia publicada junto com o site (data/)
  const RAW = (() => {
    const h = location.hostname, seg = location.pathname.split('/').filter(Boolean)[0];
    const [dono, repo] = h.endsWith('.github.io') && seg ? [h.split('.')[0], seg] : ['gabrid15-creator', 'painel-mercado'];
    return `https://raw.githubusercontent.com/${dono}/${repo}/dados/`;
  })();
  const pega = async (url) => { const r = await fetch(url, { cache: 'no-store' }); if (!r.ok) throw 0; return r.json(); };
  async function load() {
    const t = Math.floor(Date.now() / 60e3);
    await Promise.all(IDS.map(async (id) => {
      try {
        let data;
        if (id.startsWith('mi_')) { try { data = await pega(RAW + id + '.json?t=' + t); } catch (e) { data = await pega('data/' + id + '.json?t=' + t); } }
        else data = await pega('data/' + id + '.json?t=' + t);
        store[id] = { status: 'ok', data };
      } catch (e) { if (!store[id]) store[id] = { status: 'error', data: [] }; }
    }));
    drawAll();
  }

  // ---------------------------------------------------------------- utilidades
  const ATV = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'XAUUSD', 'NAS100'];
  const NOME = { EURUSD: 'Euro', GBPUSD: 'Libra', USDJPY: 'Dólar-iene', USDCHF: 'Dólar-franco', XAUUSD: 'Ouro', NAS100: 'Nasdaq 100' };
  const CASAS = { EURUSD: 5, GBPUSD: 5, USDJPY: 3, USDCHF: 5, XAUUSD: 2, NAS100: 1 };
  const MES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  const WDL = { seg: 'segunda', ter: 'terça', qua: 'quarta', qui: 'quinta', sex: 'sexta', 'sáb': 'sábado', dom: 'domingo' };
  const $ = (s) => document.querySelector(s);
  const nf = (v, c = 2) => (v == null || v === '' || isNaN(v) ? '—' : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: c, maximumFractionDigits: c }));
  const sg = (v, c = 2, suf = '%') => (v == null || isNaN(v) ? '—' : (v > 0 ? '+' : '') + nf(v, c) + suf);
  const br = (s) => { const [d, h] = String(s).split(' '); return d.split('-').reverse().join('/') + (h ? ' ' + h : ''); };
  const cls = (v) => (v > 0 ? 'mi-pos' : v < 0 ? 'mi-neg' : '');
  const hojeISO = () => { const d = new Date(); return new Date(d.getTime() - d.getTimezoneOffset() * 6e4).toISOString().slice(0, 10); };
  const td = (tr, txt, c) => { const e = document.createElement('td'); if (c) e.className = c; e.textContent = txt; tr.appendChild(e); return e; };
  const tip = (el) => { const t = document.createElement('div'); t.className = 'op-tip'; t.hidden = true; el.appendChild(t); return t; };
  const show = (el, t, ev, lines) => {
    t.replaceChildren(...lines.map((s, i) => { const d = document.createElement('div'); d.textContent = s; if (!i) d.className = 't'; return d; }));
    t.hidden = false; const [px, py] = d3.pointer(ev, el);
    t.style.left = Math.min(Math.max(0, px + 12), el.clientWidth - t.offsetWidth) + 'px'; t.style.top = (py + 12) + 'px';
  };
  const axisStyle = (g) => { g.attr('font-size', null).attr('font-family', null); g.selectAll('text').style('fill', 'var(--color-fg-muted)').style('font-size', '11px'); g.selectAll('line,path').style('stroke', 'var(--cds-chart-axis)'); };

  // ---------------------------------------------------------------- abas
  const tabs = (name) => {
    document.querySelectorAll('button.op-tab').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.tab === name)));
    document.querySelectorAll('.op-sec').forEach((s) => { s.hidden = s.id !== name; });
    drawAll();
  };
  document.querySelectorAll('button.op-tab').forEach((b) => b.addEventListener('click', () => { tabs(b.dataset.tab); history.replaceState(null, '', '#' + b.dataset.tab); }));
  if (['#sec-gb', '#sec-op'].includes(location.hash)) tabs(location.hash.slice(1));

  // ---------------------------------------------------------------- mercado
  let atv = 'EURUSD', serie = 'Spread 2a EUA−Alemanha', jan = 20, nwF = 'ativo'; const vis = {};
  const bar = $('.ativos');
  // altura do topo fixo -> o seletor de ativo gruda logo abaixo dele
  { const tp = document.querySelector('.topo'), af = document.querySelector('.ativos-fixo');
    const upd = () => { document.documentElement.style.setProperty('--topo-h', tp.offsetHeight + 'px'); if (af) af.classList.toggle('preso', af.getBoundingClientRect().top <= tp.offsetHeight + 1); };
    new ResizeObserver(upd).observe(tp); window.addEventListener('scroll', upd, { passive: true }); upd(); }
  for (const a of ATV) {
    const b = document.createElement('button'); b.type = 'button'; b.dataset.a = a;
    b.innerHTML = '<span class="an"><b></b><small></small></span><span class="sv">—<small></small></span>';
    b.querySelector('.an b').textContent = a; b.querySelector('.an small').textContent = NOME[a];
    b.addEventListener('click', () => { atv = a; drawMI(); }); bar.appendChild(b);
  }
  document.querySelectorAll('.mi-jan button').forEach((b) => b.addEventListener('click', () => {
    jan = Number(b.dataset.j); document.querySelectorAll('.mi-jan button').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); drawMI();
  }));
  const SIN = { alta: 'viés de alta (subiu em 60% ou mais)', baixa: 'viés de baixa (caiu em 60% ou mais)', inconclusivo: 'inconclusivo: sem vantagem' };

  const bars = (el, rows, lab, hi) => {
    el.replaceChildren(); if (!rows.length) return;
    const W = Math.max(240, el.clientWidth), H = el.classList.contains('mi-chart') ? 200 : 120, m = { t: 8, r: 6, b: 20, l: 6 };
    const x = d3.scaleBand(rows.map((r) => r.chave), [m.l, W - m.r]).padding(0.2);
    const e = d3.max(rows, (r) => Math.abs(r.media)) || 1;
    const y = d3.scaleLinear([-e, e], [H - m.b, m.t]);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`);
    svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(0)).attr('y2', y(0)).style('stroke', 'var(--cds-chart-axis)');
    const t = tip(el);
    svg.selectAll('rect').data(rows).join('rect').attr('x', (r) => x(r.chave)).attr('width', x.bandwidth())
      .attr('y', (r) => Math.min(y(0), y(r.media))).attr('height', (r) => Math.abs(y(r.media) - y(0))).attr('rx', 2)
      .style('fill', (r) => (r.sinal === 'inconclusivo' ? 'var(--color-fg-muted)' : r.media >= 0 ? 'var(--color-ok)' : 'var(--color-bad)'))
      .style('opacity', (r) => (r.sinal === 'inconclusivo' ? 0.3 : 1) * (hi == null || r.chave === hi ? 1 : 0.6))
      .attr('stroke', (r) => (r.chave === hi ? 'var(--color-fg)' : 'none')).attr('stroke-width', 1.5)
      .on('mousemove', (ev, r) => show(el, t, ev, [lab(r.chave), 'Média ' + sg(r.media, 2) + ' · subiu em ' + nf(r.acerto, 0) + '% (' + r.n + (r.n > 30 ? ' dias' : ' anos') + ')', SIN[r.sinal] || '']))
      .on('mouseleave', () => { t.hidden = true; });
    const ax = svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).tickFormat(lab).tickSize(0)); axisStyle(ax); ax.select('path').remove();
  };

  const line = (el, pts, fmtY, label, refY) => {
    el.replaceChildren(); if (pts.length < 2) return;
    const W = Math.max(260, el.clientWidth), H = 200, m = { t: 10, r: 10, b: 22, l: 52 };
    const x = d3.scaleTime().domain(d3.extent(pts, (p) => p.x)).range([m.l, W - m.r]);
    const ext = d3.extent(pts, (p) => p.y); if (refY != null) { ext[0] = Math.min(ext[0], refY); ext[1] = Math.max(ext[1], refY); }
    const y = d3.scaleLinear(ext, [H - m.b, m.t]).nice();
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`);
    if (refY != null) svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(refY)).attr('y2', y(refY)).style('stroke', 'var(--cds-chart-axis)');
    svg.append('path').datum(pts).attr('d', d3.line().x((p) => x(p.x)).y((p) => y(p.y))).style('fill', 'none').style('stroke', COLORS[0]).style('stroke-width', 2);
    const ax = svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(Math.max(2, Math.floor(W / 90))).tickFormat(d3.timeFormat('%m/%y'))); axisStyle(ax);
    const ay = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(4).tickFormat(fmtY)); axisStyle(ay);
    const t = tip(el);
    svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
      .on('mousemove', (ev) => { const xv = x.invert(d3.pointer(ev, svg.node())[0]); const p = pts.reduce((a, b) => (Math.abs(b.x - xv) < Math.abs(a.x - xv) ? b : a)); show(el, t, ev, [label(p.x), fmtY(p.y)]); })
      .on('mouseleave', () => { t.hidden = true; });
  };

  function drawMI() {
    if ($('#sec-mi').hidden) return;
    const corS0 = (s) => (s >= 60 ? 'var(--color-ok)' : s <= 40 ? 'var(--color-bad)' : 'var(--color-warn)');
    bar.querySelectorAll('button').forEach((x) => {
      x.setAttribute('aria-pressed', String(x.dataset.a === atv));
      const s0 = D('mi_score').status === 'ok' ? D('mi_score').data.find((r) => r.ativo === x.dataset.a) : null;
      const sv = x.querySelector('.sv'); sv.firstChild.textContent = s0 ? s0.score : '—'; sv.style.color = s0 ? corS0(s0.score) : '';
      sv.querySelector('small').textContent = s0 ? (s0.score >= 60 ? '▲ alta' : s0.score <= 40 ? '▼ baixa' : '■ neutro') : '';
    });
    const G = D('mi_geral'), A = D('mi_ativos'), S = D('mi_sazon'), C = D('mi_corr'), K = D('mi_cot'), M = D('mi_macro'), Hh = D('mi_hist'),
      AG = D('mi_agenda'), N = D('mi_noticias'), ST = D('mi_status'), SC = D('mi_score'), IA = D('mi_ia');
    const g = G.status === 'ok' ? G.data[0] : null;
    const mrow = (k) => (M.status === 'ok' ? M.data.find((r) => r.serie === k) : null);
    const FGT = { 'extreme fear': 'medo extremo', fear: 'medo', neutral: 'neutro', greed: 'ganância', 'extreme greed': 'ganância extrema' };
    // ---- cards do topo
    const li = (ul, k, v, c) => { const e = document.createElement('li'); const a = document.createElement('span'); a.textContent = k; const b = document.createElement('b'); b.textContent = v; if (c) b.className = c; e.append(a, b); ul.appendChild(e); };
    const chip = (sel, txt, tom) => { const e = $(sel); e.textContent = txt; e.className = 'tl-chip ' + sel.slice(1) + (tom ? ' ' + tom : ''); };
    const faixa = (k, v) => { const h = Hh.status === 'ok' ? Hh.data.filter((r) => r.serie === k).map((r) => Number(r.valor)) : []; if (!h.length || v == null) return null; const lo = Math.min(...h), hi = Math.max(...h); return hi > lo ? Math.max(0, Math.min(100, (v - lo) / (hi - lo) * 100)) : null; };
    {
      const ul = $('.mi-fgs'); ul.replaceChildren(); const f = g && g.fg != null ? Number(g.fg) : null;
      $('.mi-fg').textContent = f != null ? nf(f, 0) : '—';
      chip('.mi-fg-chip', f != null ? (FGT[g.fg_txt] || g.fg_txt) : '—', f == null ? '' : f < 25 ? 'bad' : f < 45 ? 'warn' : f <= 55 ? '' : 'ok');
      $('.mi-fg-pt').style.left = (f != null ? f : 50) + '%';
      if (g) for (const [k, v] of [['Ontem', g.fg_ontem], ['1 semana atrás', g.fg_semana], ['1 mês atrás', g.fg_mes], ['1 ano atrás', g.fg_ano]]) if (v != null) li(ul, k, nf(v, 0));
    }
    {
      const ul = $('.mi-red-t'); ul.replaceChildren(); const hj = hojeISO(); const agora = Date.now();
      const ev = (AG.status === 'ok' ? AG.data : []).filter((r) => r.data === hj && r.impacto === 'Alto');
      $('.mi-red-n').textContent = AG.status === 'ok' ? ev.length : (g ? nf(g.red_hoje, 0) : '—');
      const prox = ev.find((r) => new Date(r.quando.replace(' ', 'T') + ':00-03:00').getTime() > agora);
      chip('.mi-red-chip', !ev.length ? 'dia livre' : prox ? 'próximo ' + prox.hora : 'todos já saíram', !ev.length ? 'ok' : prox ? 'bad' : '');
      for (const r of ev) {
        const e = document.createElement('li'); if (new Date(r.quando.replace(' ', 'T') + ':00-03:00').getTime() <= agora) e.className = 'foi';
        const h = document.createElement('span'); h.className = 'hr'; h.textContent = r.hora; const c = document.createElement('span'); c.className = 'cur'; c.textContent = r.moeda;
        const t = document.createElement('span'); t.textContent = r.evento; e.append(h, c, t); ul.appendChild(e);
      }
      if (!ev.length) { const e = document.createElement('li'); e.className = 'vazio'; e.textContent = 'Nenhum evento de alto impacto hoje.'; ul.appendChild(e); }
    }
    const vx = mrow('VIX'), dx = mrow('DXY');
    {
      const ul = $('.mi-vixs'); ul.replaceChildren(); const v = vx ? Number(vx.valor) : null;
      $('.mi-vix').textContent = vx ? nf(v, 2) : '—';
      const d = $('.mi-vix-d'); d.textContent = vx ? sg(vx.var_1d) + ' hoje' : ''; d.className = 'tl-u mi-vix-d ' + (vx ? (vx.var_1d > 0 ? 'mi-neg' : vx.var_1d < 0 ? 'mi-pos' : '') : '');
      chip('.mi-vix-chip', v == null ? '—' : v < 15 ? 'calmo' : v < 20 ? 'normal' : v < 30 ? 'nervoso' : 'pânico', v == null ? '' : v < 15 ? 'ok' : v < 20 ? '' : v < 30 ? 'warn' : 'bad');
      const fx = faixa('VIX', v); $('.mi-vix-bar').style.width = (fx != null ? fx : (vx ? vx.pctil_1a : 0)) + '%';
      if (vx) { li(ul, '5 dias', sg(vx.var_5d), cls(-vx.var_5d)); li(ul, '20 dias', sg(vx.var_20d), cls(-vx.var_20d)); li(ul, 'Percentil no ano', nf(vx.pctil_1a, 0) + '%'); }
    }
    {
      const ul = $('.mi-dxys'); ul.replaceChildren(); const v = dx ? Number(dx.valor) : null;
      $('.mi-dxy').textContent = dx ? nf(v, 2) : '—';
      const d = $('.mi-dxy-d'); d.textContent = dx ? sg(dx.var_1d) + ' hoje' : ''; d.className = 'tl-u mi-dxy-d ' + (dx ? cls(dx.var_1d) : '');
      const t20 = dx ? dx.var_20d : null;
      chip('.mi-dxy-chip', t20 == null ? '—' : t20 > 0.5 ? '▲ dólar forte' : t20 < -0.5 ? '▼ dólar fraco' : '■ dólar de lado', t20 == null ? '' : t20 > 0.5 ? 'ok' : t20 < -0.5 ? 'bad' : '');
      const fx = faixa('DXY', v); $('.mi-dxy-bar').style.width = (fx != null ? fx : (dx ? dx.pctil_1a : 0)) + '%';
      if (dx) { li(ul, '5 dias', sg(dx.var_5d), cls(dx.var_5d)); li(ul, '20 dias (tendência)', sg(dx.var_20d), cls(dx.var_20d)); li(ul, 'Percentil no ano', nf(dx.pctil_1a, 0) + '%'); }
    }
    $('.mi-take').textContent = g ? 'Dados de ' + br(g.gerado_em) + ' (Brasília)' + (g.red_hoje ? ' · ' + g.red_hoje + ' evento(s) red folder hoje' : '') : 'Carregando…';
    $('.hj-up').textContent = g ? 'atualizado ' + br(g.gerado_em) : '';

    // score + IA
    const ia = (k) => (IA.status === 'ok' ? IA.data.find((r) => r.ativo === k) : null);
    const corS = (s) => (s >= 60 ? 'var(--color-ok)' : s <= 40 ? 'var(--color-bad)' : 'var(--color-warn)');
    const vies = (sel, r) => { const e = $(sel); const v = r && r.vies; e.hidden = !v; if (!v) return;
      e.textContent = v === 'bullish' ? '▲ Bullish' : v === 'bearish' ? '▼ Bearish' : '■ Neutro'; e.className = 'tl-chip ia-vies ' + sel.slice(1) + ' ' + (v === 'bullish' ? 'ok' : v === 'bearish' ? 'bad' : 'warn'); };
    const g0 = ia('GERAL'); vies('.mi-ia-geral-v', g0); $('.mi-ia-geral').textContent = g0 ? g0.texto : '—'; $('.mi-ia-geral-q').textContent = g0 ? 'escrita em ' + br(g0.gerado_em) : '';
    const sc = SC.status === 'ok' ? SC.data.find((r) => r.ativo === atv) : null;
    {
      const el = $('.sc-ring'); el.replaceChildren(); const R = 80, sw = 16, val = sc ? sc.score : 50, cor = sc ? corS(sc.score) : 'var(--color-border-line)';
      const svg = d3.select(el).append('svg').attr('viewBox', '0 0 200 200').attr('width', '100%');
      const arc = d3.arc().innerRadius(R - sw).outerRadius(R).cornerRadius(8);
      const g = svg.append('g').attr('transform', 'translate(100,100)');
      const a0 = -Math.PI * 0.75, a1 = Math.PI * 0.75;
      g.append('path').attr('d', arc({ startAngle: a0, endAngle: a1 })).style('fill', 'var(--color-border-line)');
      g.append('path').attr('d', arc({ startAngle: a0, endAngle: a0 + (a1 - a0) * val / 100 })).style('fill', cor);
      for (const t0 of [40, 60]) { const ang = a0 + (a1 - a0) * t0 / 100; g.append('line').attr('x1', Math.sin(ang) * (R - sw - 2)).attr('y1', -Math.cos(ang) * (R - sw - 2)).attr('x2', Math.sin(ang) * (R + 2)).attr('y2', -Math.cos(ang) * (R + 2)).style('stroke', 'var(--color-panel)').style('stroke-width', 3); }
      g.append('text').attr('text-anchor', 'middle').attr('dy', '0.1em').style('font-family', 'var(--font-anthropic-serif)').style('font-size', '52px').style('fill', cor).text(sc ? sc.score : '—');
      g.append('text').attr('text-anchor', 'middle').attr('y', 34).style('font-size', '13px').style('font-weight', 600).style('fill', cor).text(sc ? sc.vies.toUpperCase() : '');
      g.append('text').attr('x', -62).attr('y', 82).attr('text-anchor', 'middle').style('font-size', '10px').style('fill', 'var(--color-fg-muted)').text('baixista');
      g.append('text').attr('x', 62).attr('y', 82).attr('text-anchor', 'middle').style('font-size', '10px').style('fill', 'var(--color-fg-muted)').text('altista');
    }
    $('.sc-nome').textContent = atv + ' · ' + NOME[atv];
    $('.sc-vies').textContent = sc ? (sc.score >= 60 ? '▲ Viés altista · os fatores somados puxam para cima' : sc.score <= 40 ? '▼ Viés baixista · os fatores somados puxam para baixo' : '■ Neutro · fatores divididos, sem direção clara') : '—';
    $('.sc-vies').style.color = sc ? corS(sc.score) : '';
    const sb = $('.sc-bars'); sb.replaceChildren();
    for (const c of sc ? sc.componentes : []) {
      const row = document.createElement('div'); row.className = 'sc-b';
      const l = document.createElement('span'); l.textContent = c.fator; const tr = document.createElement('span'); tr.className = 'tr'; const i = document.createElement('i');
      const w = Math.abs(c.sinal) * 50; i.style.width = w + '%'; i.style.left = (c.sinal >= 0 ? 50 : 50 - w) + '%'; i.style.background = c.sinal >= 0 ? 'var(--color-ok)' : 'var(--color-bad)'; tr.appendChild(i);
      const p = document.createElement('span'); p.className = 'num ' + cls(c.pontos); p.textContent = sg(c.pontos, 1, '');
      row.append(l, tr, p); sb.appendChild(row);
    }
    const ia1 = ia(atv); vies('.mi-ia-atv-v', ia1); $('.mi-ia-atv').textContent = ia1 ? ia1.texto : '—'; $('.mi-ia-atv-q').textContent = ia1 ? 'escrita em ' + br(ia1.gerado_em) + ' · score atualiza a cada 5 min' : '';
    const tb0 = $('.mi-sc-t tbody'); tb0.replaceChildren();
    for (const c of sc ? sc.componentes : []) { const tr = document.createElement('tr'); td(tr, c.fator + ' (' + c.peso + ')'); td(tr, sg(c.pontos, 1, ''), 'num ' + cls(c.pontos)); td(tr, c.leitura); tb0.appendChild(tr); }

    // ativo
    const a = A.status === 'ok' ? A.data.find((r) => r.ativo === atv) : null; const cs = CASAS[atv];
    document.querySelectorAll('.mi-a').forEach((el) => {
      const f = el.dataset.f; const val = a ? a[f] : null;
      el.textContent = val == null ? '—' : f === 'saz_mes_media' ? sg(val, 2) : (f === 'gb_extremos' || f === 'hp_extremos') ? nf(val, 1) + '%' : nf(val, ['atr14', 'preco', 'vj_valor'].includes(f) ? cs : 2);
    });
    const hm = new Date().getMonth();
    const L = (sel, rows) => { const ul = $(sel); ul.replaceChildren(); if (!a) return; for (const [k, v, c] of rows) if (v != null) { const e = document.createElement('li'); const x = document.createElement('span'); x.textContent = k; const y = document.createElement('b'); y.textContent = v; if (c) y.className = c; e.append(x, y); ul.appendChild(e); } };
    L('.mi-a-var', a ? [['Dia', sg(a.var_1d), cls(a.var_1d)], ['5 dias', sg(a.var_5d), cls(a.var_5d)], ['20 dias', sg(a.var_20d), cls(a.var_20d)], ['No ano', sg(a.var_ano), cls(a.var_ano)]] : []);
    L('.mi-a-vj', a && a.vj_valor != null ? [['Preço vs. justo', sg(a.vj_desvio_pct), cls(-a.vj_desvio_pct)], ['Esticamento (z)', nf(a.vj_z, 1), Math.abs(a.vj_z) >= 2 ? 'mi-neg' : ''], ['Fator', a.vj_fator], ['Confiança (R²)', nf(a.vj_r2, 2), a.vj_r2 >= 0.3 ? '' : 'mi-neg']] : []);
    L('.mi-a-saz', a && a.saz_mes_media != null ? [['Subiu em (20 anos)', nf(a.saz_mes_acerto, 0) + '% de ' + a.saz_mes_n + ' anos'], ['Subiu em (10 anos)', nf(a.saz_mes10_acerto, 0) + '%'], ['Leitura', a.saz_mes_sinal === 'inconclusivo' ? 'sem vantagem' : 'viés de ' + a.saz_mes_sinal, a.saz_mes_sinal === 'alta' ? 'mi-pos' : a.saz_mes_sinal === 'baixa' ? 'mi-neg' : '']] : []);
    L('.mi-a-52', a ? [['Mínima 52 semanas', nf(a.min_52s, cs)], ['Máxima 52 semanas', nf(a.max_52s, cs)], ['ATR em % do preço', a.preco ? nf(a.atr14 / a.preco * 100, 2) + '%' : null]] : []);
    $('.mi-gb-b').textContent = a && a.gb_base != null ? 'base ' + nf(a.gb_base, 1) + '% · diferença ' + sg(a.gb_extremos - a.gb_base, 1, ' p.p.') : '—';
    $('.mi-hp-b').textContent = a && a.hp_base != null ? 'base ' + nf(a.hp_base, 1) + '% · diferença ' + sg(a.hp_extremos - a.hp_base, 1, ' p.p.') : '—';

    // sazonalidade
    const sz = S.status === 'ok' ? S.data.filter((r) => r.ativo === atv) : [];
    const szj = (tp) => sz.filter((r) => r.tipo === tp && Number(r.janela) === jan);
    bars($('.mi-saz-m'), szj('mes'), (k) => MES[k - 1], hm + 1);
    bars($('.mi-saz-d'), szj('dia_semana'), (k) => ['seg', 'ter', 'qua', 'qui', 'sex'][k - 1], ((new Date().getDay() + 6) % 7) + 1);
    bars($('.mi-saz-w'), szj('semana_mes'), (k) => k + 'ª', Math.floor((new Date().getDate() - 1) / 7) + 1);
    {
      const el = $('.mi-saz-p'); el.replaceChildren();
      const anoAt = new Date().getFullYear();
      const anos = [...new Set(sz.filter((r) => r.tipo === 'perfil_ano').map((r) => r.ano))].sort();
      const base = [{ nome: 'Média 20 anos', cor: 'var(--color-fg)', w: 2.5, j: 20 }, { nome: 'Média 10 anos', cor: COLORS[0], w: 2.5, j: 10 }, { nome: 'Média 5 anos', cor: COLORS[5], w: 2, j: 5 }]
        .map((b) => ({ ...b, pts: sz.filter((r) => r.tipo === 'perfil_mes' && Number(r.janela) === b.j).map((r) => ({ x: r.chave, y: r.media })) }));
      const anosS = anos.map((a2, i) => ({ nome: a2 === anoAt ? a2 + ' (até hoje)' : String(a2), cor: a2 === anoAt ? COLORS[3] : [COLORS[1], COLORS[2], COLORS[4], COLORS[6], COLORS[7]][i % 5], w: a2 === anoAt ? 2.5 : 1.25, pts: sz.filter((r) => r.tipo === 'perfil_ano' && r.ano === a2).map((r) => ({ x: r.chave, y: r.media })) }));
      const todas = [...base, ...anosS].filter((s2) => s2.pts.length);
      for (const s2 of todas) if (!(s2.nome in vis)) vis[s2.nome] = s2.nome === 'Média 20 anos' || s2.nome === 'Média 10 anos' || s2.nome.includes('até hoje');
      const lg = $('.mi-saz-lg'); lg.replaceChildren();
      for (const s2 of todas) {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'mi-lgb'; b.setAttribute('aria-pressed', String(vis[s2.nome]));
        const i2 = document.createElement('i'); i2.className = 'op-sw'; i2.style.background = s2.cor; b.append(i2, document.createTextNode(s2.nome));
        b.addEventListener('click', () => { vis[s2.nome] = !vis[s2.nome]; drawMI(); }); lg.appendChild(b);
      }
      const ser = todas.filter((s2) => vis[s2.nome]);
      if (ser.length) {
        const all = ser.flatMap((s2) => s2.pts);
        const W = Math.max(260, el.clientWidth), H = 220, m = { t: 10, r: 10, b: 22, l: 48 };
        const x = d3.scaleLinear(d3.extent(all, (p) => p.x), [m.l, W - m.r]);
        const y = d3.scaleLinear(d3.extent([...all.map((p) => p.y), 0]), [H - m.b, m.t]).nice();
        const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`);
        svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(0)).attr('y2', y(0)).style('stroke', 'var(--cds-chart-axis)');
        for (const s2 of [...ser].reverse()) svg.append('path').datum(s2.pts).attr('d', d3.line().x((p) => x(p.x)).y((p) => y(p.y))).style('fill', 'none').style('stroke', s2.cor).style('stroke-width', s2.w).style('opacity', s2.w > 2 ? 1 : 0.85);
        const ax = svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(Math.min(10, Math.floor(W / 50))).tickFormat((v2) => v2 + 'º')); axisStyle(ax);
        const ay = svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(4).tickFormat((v2) => sg(v2, 1))); axisStyle(ay);
        const t = tip(el);
        svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
          .on('mousemove', (ev) => { const d0 = Math.round(x.invert(d3.pointer(ev, svg.node())[0])); show(el, t, ev, [d0 + 'º dia útil', ...ser.map((s2) => { const p = s2.pts.find((q) => q.x === d0); return p ? s2.nome + ': ' + sg(p.y, 2) : null; }).filter(Boolean)]); })
          .on('mouseleave', () => { t.hidden = true; });
      }
    }

    // COT
    const kt = $('.mi-cot-t tbody'); kt.replaceChildren();
    const kr = K.status === 'ok' ? K.data.filter((r) => r.ativo === atv) : [];
    for (const r of kr) {
      const tr = document.createElement('tr'); td(tr, r.grupo); td(tr, nf(r.liquido, 0), 'num ' + cls(r.liquido)); td(tr, sg(r.var_semana, 0, ''), 'num ' + cls(r.var_semana));
      const c = td(tr, nf(r.indice_3a, 0), 'num'); if (r.indice_3a >= 80 || r.indice_3a <= 20) c.style.fontWeight = 600; kt.appendChild(tr);
    }
    $('.mi-cot-n').textContent = 'Como ler: líquido = contratos comprados menos vendidos. Os nomes mudam entre relatórios (moedas e Nasdaq usam o TFF; ouro usa o desagregado), por isso o equivalente vem entre parênteses. "≈ hedge funds" (fundos alavancados ou managed money) = dinheiro especulativo grande, segue tendência: é o que o score usa. "≈ commercials" (dealers; no ouro, produtores + swap dealers) = bancos e quem faz hedge, ficam do lado oposto e costumam acertar nos extremos. Institucional = fundos de longo prazo. Varejo = só informativo, fora do score: quando o varejo está muito de um lado, o big money costuma provocar squeeze contra ele. Índice 3a acima de 80 ou abaixo de 20 = esticado. Toque na legenda para ligar ou desligar cada curva. Sai às sextas com dados da terça.' + (kr[0] ? ' Relatório de ' + br(kr[0].data) + '.' : '') + (kr[0] && kr[0].sinal_par < 0 ? ' Atenção: é o futuro da moeda contra o dólar, então comprado na moeda = vendido no ' + atv + '.' : '');
    {
      const el = $('.mi-cot-c'); el.replaceChildren(); const lg = $('.mi-cot-lg'); lg.replaceChildren();
      const CC = { especulativo: COLORS[0], commercial: COLORS[1], institucional: COLORS[2], varejo: COLORS[7] };
      const ser = kr.map((r) => ({ nome: r.grupo, cor: CC[r.papel] || COLORS[4], pts: r.hist.map(([d, val]) => ({ x: new Date(d + 'T12:00:00'), y: val })) }));
      for (const s2 of ser) if (!(('cot:' + s2.nome) in vis)) vis['cot:' + s2.nome] = true;
      for (const s2 of ser) {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'mi-lgb'; b.setAttribute('aria-pressed', String(vis['cot:' + s2.nome]));
        const i2 = document.createElement('i'); i2.className = 'op-sw'; i2.style.background = s2.cor; b.append(i2, document.createTextNode(s2.nome));
        b.addEventListener('click', () => { vis['cot:' + s2.nome] = !vis['cot:' + s2.nome]; drawMI(); }); lg.appendChild(b);
      }
      const on = ser.filter((s2) => vis['cot:' + s2.nome]);
      if (on.length) {
        const all = on.flatMap((s2) => s2.pts);
        const W = Math.max(260, el.clientWidth), H = 220, m = { t: 10, r: 10, b: 22, l: 52 };
        const x = d3.scaleTime(d3.extent(all, (p) => p.x), [m.l, W - m.r]);
        const y = d3.scaleLinear(d3.extent([...all.map((p) => p.y), 0]), [H - m.b, m.t]).nice();
        const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`);
        svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(0)).attr('y2', y(0)).style('stroke', 'var(--cds-chart-axis)');
        for (const s2 of on) svg.append('path').datum(s2.pts).attr('d', d3.line().x((p) => x(p.x)).y((p) => y(p.y))).style('fill', 'none').style('stroke', s2.cor).style('stroke-width', 2);
        axisStyle(svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(Math.max(2, Math.floor(W / 90))).tickFormat(d3.timeFormat('%m/%y'))));
        axisStyle(svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(4).tickFormat((v2) => nf(v2 / 1000, 0) + ' mil')));
        const t = tip(el);
        svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
          .on('mousemove', (ev) => {
            const xv = x.invert(d3.pointer(ev, svg.node())[0]); const lines = [];
            for (const s2 of on) { const p = s2.pts.reduce((a2, b2) => (Math.abs(b2.x - xv) < Math.abs(a2.x - xv) ? b2 : a2)); if (!lines.length) lines.push(p.x.toLocaleDateString('pt-BR')); lines.push(s2.nome.split(' (')[0] + ': ' + nf(p.y, 0)); }
            show(el, t, ev, lines);
          })
          .on('mouseleave', () => { t.hidden = true; });
      }
    }

    // correlações
    const ct = $('.mi-corr-t tbody'); ct.replaceChildren();
    const cr = C.status === 'ok' ? C.data.filter((r) => r.ativo === atv) : [];
    const c20 = (f) => Math.abs((cr.find((r) => r.fator === f && r.janela === 20) || {}).corr || 0);
    for (const f of [...new Set(cr.map((r) => r.fator))].sort((p, q) => c20(q) - c20(p))) {
      const tr = document.createElement('tr'); td(tr, f);
      for (const w of [20, 60, 250]) {
        const r = cr.find((x) => x.fator === f && x.janela === w); const c = td(tr, r ? nf(r.corr, 2) : '—', 'num');
        if (r && r.corr != null) c.style.background = `color-mix(in srgb, ${r.corr >= 0 ? 'var(--color-ok)' : 'var(--color-bad)'} ${Math.round(Math.abs(r.corr) * 45)}%, transparent)`;
      }
      ct.appendChild(tr);
    }

    // macro
    const mt = $('.mi-macro-t tbody'); mt.replaceChildren(); let grp = '';
    for (const r of M.status === 'ok' ? M.data : []) {
      if (r.grupo !== grp) { grp = r.grupo; const tr = document.createElement('tr'); td(tr, grp, 'grp').colSpan = 6; mt.appendChild(tr); }
      const tr = document.createElement('tr'); if (r.serie === serie) tr.className = 'sel';
      const u = r.unidade_var === 'p.p.' ? ' p.p.' : '%';
      td(tr, r.serie); td(tr, nf(r.valor, r.unidade_var === 'p.p.' ? 2 : r.valor > 1000 ? 0 : 2), 'num');
      for (const k of ['var_1d', 'var_5d', 'var_20d']) td(tr, sg(r[k], 2, u), 'num ' + cls(r[k]));
      td(tr, nf(r.pctil_1a, 0), 'num');
      tr.addEventListener('click', () => { serie = r.serie; drawMI(); }); mt.appendChild(tr);
    }
    $('.mi-hist-t').textContent = serie + ' — último ano';
    line($('.mi-hist'), Hh.status === 'ok' ? Hh.data.filter((r) => r.serie === serie).map((r) => ({ x: new Date(r.data + 'T12:00:00'), y: Number(r.valor) })) : [], (val) => nf(val, 2), (x) => x.toLocaleDateString('pt-BR'));

    drawAgenda();
    // notícias
    const REL = { EURUSD: ['BCE', 'Euro', 'Fed', 'Dólar', 'Juros', 'Dados'], GBPUSD: ['BoE', 'Libra', 'Fed', 'Dólar', 'Dados'], USDJPY: ['BoJ', 'Fed', 'Dólar', 'Juros', 'Dados'],
      USDCHF: ['SNB', 'Fed', 'Dólar', 'Euro', 'Dados'], XAUUSD: ['Ouro', 'Fed', 'Juros', 'Dólar', 'Dados'], NAS100: ['Nasdaq', 'Fed', 'Juros', 'Dados'] };
    const nfb = $('.nw-f'); nfb.replaceChildren();
    for (const [k, lb] of [['ativo', 'Só o que mexe com ' + atv], ['todas', 'Todas']]) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'op-btn'; b.textContent = lb; b.setAttribute('aria-pressed', String(nwF === k));
      b.addEventListener('click', () => { nwF = k; drawMI(); }); nfb.appendChild(b);
    }
    const ul = $('.mi-news-l'); ul.replaceChildren();
    const lista = (N.status === 'ok' ? N.data : []).filter((r) => nwF === 'todas' || (r.tags || []).some((t) => REL[atv].includes(t)));
    for (const r of lista.slice(0, 50)) {
      const li = document.createElement('li'); const aa = document.createElement('a'); aa.href = r.link; aa.target = '_blank'; aa.rel = 'noopener'; aa.textContent = r.titulo;
      const sm = document.createElement('small');
      for (const t of r.tags || []) { const sp = document.createElement('span'); sp.className = 'nw-tag'; sp.textContent = t; sm.appendChild(sp); }
      sm.appendChild(document.createTextNode(r.fonte + (r.quando ? ' · ' + br(r.quando) : ''))); li.append(aa, sm); ul.appendChild(li);
    }
    if (!lista.length) { const li = document.createElement('li'); li.textContent = 'Nenhuma manchete recente ligada a ' + atv + '.'; ul.appendChild(li); }
    const bad = ST.status === 'ok' ? ST.data.filter((r) => !r.ok) : [];
    $('.mi-status').textContent = ST.status !== 'ok' ? '—' : bad.length ? 'Fontes que falharam na última coleta: ' + bad.map((r) => r.bloco).join(', ') + ' (os dados anteriores continuam).' : 'Todas as fontes responderam na última coleta.';
  }

  // ---------------------------------------------------------------- Goldbach
  let filtro = 'todos', selD = null;
  const corGB = { 'Goldbach': () => COLORS[0], 'Hopiplaka': () => COLORS[2], 'Goldbach + Hopiplaka': () => 'var(--color-warn)' };
  const clsGB = { 'Goldbach': 't-g', 'Hopiplaka': 't-h', 'Goldbach + Hopiplaka': 't-2' };
  $('.gb-sw-g').style.background = COLORS[0]; $('.gb-sw-h').style.background = COLORS[2]; $('.gb-sw-2').style.background = 'var(--color-warn)';
  document.querySelectorAll('.gb-f').forEach((b) => b.addEventListener('click', () => {
    filtro = b.dataset.f; document.querySelectorAll('.gb-f').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); drawGB();
  }));
  function drawGB() {
    const g = D('goldbach_dias'); const t = hojeISO();
    const [ty, tm, tdd] = t.split('-').map(Number);
    $('.hj-d').textContent = new Date(Date.UTC(ty, tm - 1, tdd)).toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' });
    if (g.status !== 'ok') return;
    const hj = g.data.find((r) => r.data === t);
    const hs = $('.hj-s'); hs.textContent = hj ? hj.resumo : 'Não é dia Goldbach nem Hopiplaka'; hs.classList.toggle('both', !!hj && hj.tipo === 'Goldbach + Hopiplaka');
    if ($('#sec-gb').hidden) return;
    const fut = g.data.filter((r) => r.data >= t);
    $('.gb-take').textContent = hj ? 'Hoje: ' + hj.resumo + (hj.goldbach ? ' — Goldbach por ' + hj.goldbach : '') : 'Hoje não é dia Goldbach nem Hopiplaka.';
    const a = fut.find((r) => r.tipo === 'Goldbach + Hopiplaka');
    $('.gb-next2').textContent = a ? br(a.data) + ' (' + a.dia_semana + ')' : '—'; $('.gb-next2-s').textContent = a ? 'Hopiplaka ' + a.hopiplaka : '—';
    const o = fut.find((r) => Number(r.dia_mes_hopiplaka) === 1); $('.gb-open').textContent = o ? br(o.data) + ' (' + o.dia_semana + ')' : '—';
    // calendário
    const box = $('.gb-cal'); box.replaceChildren(); const map = new Map(g.data.map((r) => [r.data, r]));
    for (let k = 0; k < 2; k++) {
      const y = ty + Math.floor((tm - 1 + k) / 12), m = ((tm - 1 + k) % 12) + 1;
      const wrap = document.createElement('div'); wrap.className = 'gb-mes';
      const h = document.createElement('h3'); h.textContent = new Date(Date.UTC(y, m - 1, 15)).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric', timeZone: 'UTC' });
      const grid = document.createElement('div'); grid.className = 'gb-grid';
      for (const w of ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']) { const c = document.createElement('div'); c.className = 'gb-wd'; c.textContent = w; grid.appendChild(c); }
      for (let i = 0; i < new Date(Date.UTC(y, m - 1, 1)).getUTCDay(); i++) grid.appendChild(document.createElement('div'));
      for (let d = 1; d <= new Date(Date.UTC(y, m, 0)).getUTCDate(); d++) {
        const iso = y + '-' + String(m).padStart(2, '0') + '-' + String(d).padStart(2, '0'); const r = map.get(iso);
        const b = document.createElement('button'); b.type = 'button';
        b.className = 'gb-day' + (r ? ' ' + clsGB[r.tipo] : '') + (iso === t ? ' hj' : '') + (iso === selD ? ' sel' : '');
        b.textContent = d;
        if (r && r.hopiplaka) { const s2 = document.createElement('small'); s2.className = 'gb-hn'; s2.textContent = 'H' + r.dia_mes_hopiplaka; b.appendChild(s2); }
        if (r) { b.style.background = corGB[r.tipo](); if (r.tipo === 'Goldbach + Hopiplaka') b.style.color = '#1a1a1a'; }
        b.addEventListener('click', () => { selD = iso; $('.gb-det').textContent = r ? br(r.data) + ' (' + WDL[r.dia_semana] + '): ' + r.resumo + (r.goldbach ? ' — Goldbach por ' + r.goldbach : '') : br(iso) + ': não é dia Goldbach nem Hopiplaka.'; drawGB(); });
        grid.appendChild(b);
      }
      wrap.append(h, grid); box.appendChild(wrap);
    }
    // tabela
    const tb = $('.gb-table tbody'); tb.replaceChildren();
    for (const r of fut.filter((r) => filtro === 'todos' || r.tipo === filtro).slice(0, 60)) {
      const tr = document.createElement('tr'); const both = r.tipo === 'Goldbach + Hopiplaka';
      tr.className = (both ? 'gb-both' : '') + (r.data === t ? ' gb-hoje' : '');
      td(tr, br(r.data) + (r.data === t ? ' (hoje)' : '')); td(tr, WDL[r.dia_semana] || r.dia_semana); td(tr, r.resumo, both ? 'gb-star' : ''); td(tr, r.goldbach || '—');
      tb.appendChild(tr);
    }
  }


  // ---------------------------------------------------------------- agenda + "Atual" ao vivo (biquote.io: grátis, sem chave, CORS liberado)
  const LIVE = { ev: [], ok: false, quando: null, vistos: new Set(), timer: null };
  const LIVE_BASE = 'https://biquote.io/api/calendar?countries=US,EU,GB,JP,CH';
  // janela = a semana da agenda (sem from/to a API só devolve de ontem em diante)
  const liveURL = () => {
    const ds = (D('mi_agenda').data || []).map((r) => r.data).filter(Boolean).sort();
    if (!ds.length) return LIVE_BASE;
    const fim = new Date(ds[ds.length - 1] + 'T12:00:00Z'); fim.setUTCDate(fim.getUTCDate() + 1);
    const ini = new Date(ds[0] + 'T12:00:00Z'); ini.setUTCDate(ini.getUTCDate() - 1);
    return LIVE_BASE + '&from=' + ini.toISOString().slice(0, 10) + '&to=' + fim.toISOString().slice(0, 10);
  };
  // o Forex Factory e o biquote dão nomes diferentes ao mesmo dado: normaliza antes de comparar
  const APELIDOS = [
    [/non-?farm employment change/, 'nonfarm payrolls'], [/adp non-?farm employment change/, 'adp nonfarm employment change'],
    [/unemployment claims/, 'initial jobless claims'], [/official bank rate/, 'interest rate decision'],
    [/federal funds rate|fomc statement/, 'fed interest rate decision'], [/main refinancing rate/, 'ecb interest rate decision'],
    [/snb policy rate/, 'snb interest rate decision'], [/boj policy rate/, 'boj interest rate decision'],
    [/ism services/, 'ism non-manufacturing'], [/(prelim |revised )?uom/, 'michigan'], [/flash estimate |flash |prelim |advance |final /g, ''],
    [/non-?farm/g, 'nonfarm'], [/cpi y\/y$/, 'cpi y/y'], [/average earnings index 3m\/y/, 'average earnings index'], [/claimant count change/, 'claimant count change'],
  ];
  const normal = (s) => APELIDOS.reduce((t, [re, by]) => t.replace(re, by), String(s || '').toLowerCase());
  const tok = (s) => normal(s).replace(/[()]/g, ' ').split(/[\s,]+/).filter((w) => w && !['the', 'of', 'and', 's&p', 'global', 'boe', 'ecb', 'boj', 'snb', 'fed', 'speaks', 'speech'].includes(w));
  const MULT = { thousands: [1e3, 'K'], millions: [1e6, 'M'], billions: [1e9, 'B'], trillions: [1e12, 'T'] };
  const fmtLive = (e, v) => {
    if (v == null) return '—';
    const d = e.digits != null ? e.digits : 2; const [, suf] = MULT[e.multiplier] || [1, ''];
    return Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d }) + suf + (e.unit === 'percent' ? '%' : '');
  };
  // valor da previsão em escala comparável ao "actual" do biquote
  // previsão na mesma escala do "actual": a do próprio biquote; senão a do Forex Factory (só o número, sem K/M/%)
  // compara com a previsão mostrada na tabela (Forex Factory); se não houver, com a do próprio biquote
  const prevNum = (r, e) => {
    const m = String(r.previsao || '').replace(',', '.').match(/^\s*-?\d+(\.\d+)?/);
    if (m) { const x = parseFloat(m[0]); const a = Math.abs(e.actual), b = Math.abs(x); if (!(a && b && (a / b > 50 || b / a > 50))) return x; }   // escalas diferentes: ignora
    return e.forecast != null ? e.forecast : null;
  };
  const casar = (r) => {
    if (!LIVE.ok || /votes?\b/i.test(r.evento)) return null;   // placar de votos (7-0-2) não tem número comparável
    const t = new Date(r.quando.replace(' ', 'T') + ':00-03:00').getTime(); const a = tok(r.evento); let best = null, bs = 0;
    for (const e of LIVE.ev) {
      if (e.currency !== r.moeda || Math.abs(new Date(e.time).getTime() - t) > 2 * 60e3) continue;
      const b = tok(e.name); const com = a.filter((w) => b.includes(w)).length;
      const sc = com / Math.max(a.length, 1) + com / Math.max(b.length, 1) / 10;   // prefere o nome mais parecido nos dois sentidos
      if (sc > bs) { bs = sc; best = e; }
    }
    return bs >= 0.5 ? best : null;
  };
  // reserva oficial dos EUA (BLS/FRED, coletada a cada 5 min): só vale se o período for o desta divulgação
  const euaDe = (r) => {
    if (r.moeda !== 'USD') return null;
    const EU = D('mi_eua').status === 'ok' ? D('mi_eua').data : [];
    const x = EU.find((z) => z.evento === r.evento) || (/gdp q\/q/i.test(r.evento) ? EU.find((z) => /gdp/i.test(z.evento)) : null); if (!x) return null;
    const t = new Date(r.quando.replace(' ', 'T') + ':00-03:00');
    if (/claims/i.test(r.evento)) { const dias = (t - new Date(x.periodo + 'T12:00:00Z')) / 864e5; if (dias < 3 || dias > 10) return null; }
    else if (/gdp/i.test(r.evento)) { const dias = (t - new Date(x.periodo + '-01T12:00:00Z')) / 864e5; if (dias < 60 || dias > 150) return null; }
    else { const m = new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth() - (/jolts/i.test(r.evento) ? 2 : 1), 1)); if (x.periodo !== m.toISOString().slice(0, 7)) return null; }
    return { id: 'eua:' + x.evento + x.periodo, actual: x.valor, forecast: null, previous: null, digits: x.casas, fonte: x.fonte,
      multiplier: x.unidade === 'K' ? 'thousands' : x.unidade === 'M' ? 'millions' : 'none', unit: x.unidade === '%' ? 'percent' : 'none' };
  };
  // ---- tempo real direto da fonte oficial (BLS libera o navegador): busca no segundo da divulgação
  const BLS_RT = { 'Non-Farm Employment Change': ['CES0000000001', 'diff', 'K', 0], 'Unemployment Rate': ['LNS14000000', 'lvl', '%', 1],
    'Average Hourly Earnings m/m': ['CES0500000003', 'pct', '%', 1], 'CPI m/m': ['CUSR0000SA0', 'pct', '%', 1], 'Core CPI m/m': ['CUSR0000SA0L1E', 'pct', '%', 1],
    'CPI y/y': ['CUUR0000SA0', 'yoy', '%', 1], 'PPI m/m': ['WPSFD4', 'pct', '%', 1], 'Core PPI m/m': ['WPSFD49104', 'pct', '%', 1] };
  const BLS = { res: {}, prox: {}, busy: false };
  const blsCota = () => { const k = 'blsq-' + hojeISO(); const n = +(localStorage.getItem(k) || 0); return [k, n]; };
  async function blsSerie(sid) {
    const [k, n] = blsCota(); if (n >= 23) throw new Error('cota diária do BLS'); localStorage.setItem(k, n + 1);
    const r = await fetch('https://api.bls.gov/publicAPI/v2/timeseries/data/' + sid, { cache: 'no-store' }); const j = await r.json();
    const d = (((j.Results || {}).series || [])[0] || {}).data || [];
    return d.filter((x) => /^M(0[1-9]|1[0-2])$/.test(x.period) && x.value !== '-').map((x) => [x.year + '-' + x.period.slice(1), +x.value]).sort((a, b) => (a[0] < b[0] ? -1 : 1));
  }
  const blsCalc = (pts, modo) => { const n = pts.length; if (n < 14) return null; const v = pts[n - 1][1];
    return [pts[n - 1][0], modo === 'lvl' ? v : modo === 'diff' ? v - pts[n - 2][1] : modo === 'pct' ? (v / pts[n - 2][1] - 1) * 100 : (v / pts[n - 13][1] - 1) * 100]; };
  const mesAnt = (t) => new Date(Date.UTC(t.getUTCFullYear(), t.getUTCMonth() - 1, 1)).toISOString().slice(0, 7);
  async function blsTick() {
    if (BLS.busy) return; const agora = Date.now(); const ag = D('mi_agenda').data || [];
    // agrupa os eventos do BLS por horário; consulta só a série principal de cada horário até virar o mês esperado
    const slots = {};
    for (const r of ag) { if (r.moeda !== 'USD' || !BLS_RT[r.evento]) continue; const t = new Date(r.quando.replace(' ', 'T') + ':00-03:00');
      const dt0 = agora - t.getTime(); if (dt0 < 0 || dt0 > 150e3) continue; (slots[r.quando] = slots[r.quando] || { t, evs: [] }).evs.push(r.evento); }
    for (const [q, { t, evs }] of Object.entries(slots)) {
      const esperado = mesAnt(t); if (evs.every((ev) => BLS.res[q + ev])) continue;
      if ((BLS.prox[q] || 0) > agora) continue; BLS.prox[q] = agora + (agora - t.getTime() < 30e3 ? 3e3 : 10e3);
      BLS.busy = true;
      try {
        const [sid, modo] = BLS_RT[evs[0]]; const pts = await blsSerie(sid); const c = blsCalc(pts, modo);
        if (c && c[0] === esperado) {
          BLS.res[q + evs[0]] = c;
          for (const ev of evs.slice(1)) { const [s2, m2] = BLS_RT[ev]; const c2 = blsCalc(await blsSerie(s2), m2); if (c2 && c2[0] === esperado) BLS.res[q + ev] = c2; }
          if (!$('#sec-mi').hidden) drawAgenda();
        }
      } catch (e) { /* sem cota ou fora do ar: fica a coleta oficial */ } finally { BLS.busy = false; }
    }
  }
  setInterval(blsTick, 1000);
  const blsDe = (r) => { const c = BLS.res[r.quando + r.evento]; if (!c) return null; const [, , un, cs] = BLS_RT[r.evento];
    return { id: 'bls:' + r.quando + r.evento, actual: Math.round(c[1] * 1000) / 1000, forecast: null, previous: null, digits: cs, multiplier: un === 'K' ? 'thousands' : 'none', unit: un === '%' ? 'percent' : 'none' }; };
  const surpresa = (r, e) => { if (!e || e.actual == null) return null; const f = prevNum(r, e); if (f == null) return 0; const d = e.actual - f; return Math.abs(d) < 1e-9 ? 0 : d > 0 ? 1 : -1; };
  function drawAgenda() {
    const AG = D('mi_agenda'); const at = $('.mi-ag-t tbody'); if (!at) return; at.replaceChildren(); const hj = hojeISO(); const agora = Date.now();
    let ultimo = null, primHoje = false;
    for (const r of AG.status === 'ok' ? AG.data : []) {
      let e = casar(r); if (!e || e.actual == null) e = blsDe(r) || euaDe(r) || e; const quando = new Date(r.quando.replace(' ', 'T') + ':00-03:00').getTime(); const passou = quando < agora;
      const tr = document.createElement('tr'); tr.className = (r.impacto === 'Alto' ? 'mi-red' : '') + (r.data === hj ? ' mi-hoje' + (primHoje ? '' : ' mi-hoje-1') : '') + (passou ? ' ag-passou' : '');
      if (r.data === hj) primHoje = true;
      const [d, h] = r.quando.split(' ');
      td(tr, (d === hj ? 'hoje' : d.slice(8, 10) + '/' + d.slice(5, 7)) + ' ' + h); td(tr, r.moeda);
      const ev = td(tr, r.evento); if (r.impacto === 'Alto') { const b = document.createElement('span'); b.className = 'ag-red'; b.title = 'Alto impacto'; ev.prepend(b); }
      const cur = document.createElement('small'); cur.className = 'ag-cur'; cur.textContent = r.moeda; ev.prepend(cur);
      td(tr, r.previsao || (e && e.forecast != null ? fmtLive(e, e.forecast) : '—'), 'num'); td(tr, r.anterior || '—', 'num');
      const c = td(tr, '', 'num ag-at');
      if (e && e.actual != null) {
        const s = surpresa(r, e); const box = document.createElement('span');
        box.className = 'ag-box ' + (s > 0 ? 'ag-acima' : s < 0 ? 'ag-abaixo' : 'ag-igual');
        box.textContent = (s > 0 ? '▲ ' : s < 0 ? '▼ ' : '') + fmtLive(e, e.actual);
        box.title = s > 0 ? 'Acima da previsão' : s < 0 ? 'Abaixo da previsão' : 'Igual à previsão / sem previsão';
        if (!LIVE.vistos.has(e.id)) { if (LIVE.quando) box.classList.add('ag-novo'); LIVE.vistos.add(e.id); }
        c.appendChild(box);
        if (passou && (!ultimo || quando > ultimo.quando)) ultimo = { quando, itens: [] };
        if (passou && quando === ultimo.quando) ultimo.itens.push({ r, e, s });
      } else if (passou && agora - quando < 20 * 60e3) {
        const sp = document.createElement('span'); sp.className = 'ag-wait'; sp.textContent = 'saindo…'; c.appendChild(sp);
      } else if (passou && r.url) { const l = document.createElement('a'); l.href = r.url; l.target = '_blank'; l.rel = 'noopener'; l.textContent = 'ver ↗'; c.appendChild(l); }
      else c.textContent = passou ? '—' : 'aguarda';
      at.appendChild(tr);
    }
    // destaque dos últimos dados divulgados (mesmo horário; últimas 3 horas)
    const hl = $('.ag-hl');
    if (hl) {
      hl.hidden = !(ultimo && agora - ultimo.quando < 3 * 3600e3);
      if (!hl.hidden) {
        const r0 = ultimo.itens[0].r; hl.querySelector('.ag-hl-k').textContent = 'Acabou de sair · ' + r0.moeda + ' · ' + r0.hora;
        const box = hl.querySelector('.ag-hl-l'); box.replaceChildren();
        for (const { r, e, s } of ultimo.itens) {
          const c = document.createElement('div'); c.className = 'ag-hl-c ' + (s > 0 ? 'ag-acima' : s < 0 ? 'ag-abaixo' : 'ag-igual');
          const ev = document.createElement('span'); ev.className = 'ag-hl-ev'; ev.textContent = r.evento;
          const v = document.createElement('span'); v.className = 'ag-hl-v'; v.textContent = (s > 0 ? '▲ ' : s < 0 ? '▼ ' : '') + fmtLive(e, e.actual);
          const sub = document.createElement('span'); sub.className = 'ag-hl-s';
          sub.textContent = (s > 0 ? 'acima da' : s < 0 ? 'abaixo da' : 'em linha com a') + ' previsão (' + (r.previsao || fmtLive(e, e.forecast)) + ') · anterior ' + (r.anterior || fmtLive(e, e.previous));
          c.append(ev, v, sub); box.appendChild(c);
        }
      }
    }
    const st = $('.ag-live');
    if (st) { st.className = 'ag-live' + (LIVE.ok ? ' on' : ''); st.textContent = LIVE.ok ? 'ao vivo · ' + new Date(LIVE.quando).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : 'ao vivo indisponível: use o link "ver"'; }
  }
  // perto de um horário de divulgação, consulta a cada 15 s; fora disso, a cada 60 s
  function proximoIntervalo() {
    const AG = D('mi_agenda'); const agora = Date.now();
    const quente = (AG.status === 'ok' ? AG.data : []).some((r) => { const t = new Date(r.quando.replace(' ', 'T') + ':00-03:00').getTime(); return t - agora < 2 * 60e3 && agora - t < 20 * 60e3 && (casar(r) || {}).actual == null; });
    return quente ? 15e3 : 60e3;
  }
  async function euaTick() {   // sem cache (API do GitHub), só perto de divulgações americanas
    try { const r = await fetch('https://api.github.com/repos/' + RAW.split('/').slice(3, 5).join('/') + '/contents/mi_eua.json?ref=dados', { headers: { Accept: 'application/vnd.github.raw' }, cache: 'no-store' }); if (r.ok) store.mi_eua = { status: 'ok', data: await r.json() }; } catch (e) { /* segue */ }
  }
  async function liveTick() {
    if (proximoIntervalo() < 60e3 && (D('mi_agenda').data || []).some((r) => r.moeda === 'USD' && Math.abs(Date.now() - new Date(r.quando.replace(' ', 'T') + ':00-03:00').getTime()) < 30 * 60e3)) await euaTick();
    try {
      const r = await fetch(liveURL(), { cache: 'no-store' }); if (!r.ok) throw 0;
      const j = await r.json(); LIVE.ev = Array.isArray(j) ? j : (j.events || []); LIVE.ok = true; LIVE.quando = Date.now();
    } catch (e) { LIVE.ok = LIVE.ev.length > 0; }
    if (!$('#sec-mi').hidden) drawAgenda();
    clearTimeout(LIVE.timer); LIVE.timer = setTimeout(liveTick, document.hidden ? 120e3 : proximoIntervalo());
  }
  document.addEventListener('visibilitychange', () => { if (!document.hidden) { clearTimeout(LIVE.timer); liveTick(); } });


  // ---------------------------------------------------------------- radar institucional
  const SURP = { ev: [], t: 0 };
  async function surpTick() {
    try {
      const fim = new Date(), ini = new Date(Date.now() - 92 * 864e5);
      const r = await fetch(LIVE_BASE + '&from=' + ini.toISOString().slice(0, 10) + '&to=' + fim.toISOString().slice(0, 10), { cache: 'no-store' });
      if (r.ok) { const j = await r.json(); SURP.ev = Array.isArray(j) ? j : []; SURP.t = Date.now(); drawRadar(); }
    } catch (e) { /* mantém o anterior */ }
  }
  const INV = /unemployment|jobless|claims|claimant/i, INF = /cpi|ppi|pce|inflation|price|hicp|deflator|earnings/i;
  const surpresaIdx = (cur, inflacao) => {
    let s = 0, w = 0; const agora = Date.now();
    for (const e of SURP.ev) {
      if (e.currency !== cur || e.actual == null || e.forecast == null || e.type === 'event' || !['high', 'medium'].includes(e.importance)) continue;
      if (INF.test(e.name) !== inflacao) continue;
      const d = e.actual - e.forecast; if (!d) continue;
      const peso = (e.importance === 'high' ? 2 : 1) * Math.pow(0.5, (agora - new Date(e.time).getTime()) / (30 * 864e5));
      s += Math.sign(d) * (INV.test(e.name) ? -1 : 1) * peso; w += peso;
    }
    return w ? 100 * s / w : null;
  };
  function drawRadar() {
    if (!$('.radar')) return;
    const M = D('mi_macro'); const row = (k) => (M.status === 'ok' ? M.data.find((r) => r.serie === k) : null);
    const li = (ul, k, v, c, ch) => { const e = document.createElement('li'); const a = document.createElement('span'); a.textContent = k; const b = document.createElement('b'); b.textContent = v; if (c) b.className = c; if (ch) { const x = document.createElement('span'); x.className = 'tl-chip ' + ch[1]; x.textContent = ch[0]; b.appendChild(x); } e.append(a, b); ul.appendChild(e); };
    const lq = row('Liquidez líquida Fed'); const ul = $('.rd-liq-l'); ul.replaceChildren();
    $('.rd-liq').textContent = lq ? 'US$ ' + nf(lq.valor / 1000, 2) + ' tri' : '—';
    const d = $('.rd-liq-d'); d.textContent = lq ? sg(lq.var_1d) + ' no dia' : ''; d.className = 'tl-u rd-liq-d ' + (lq ? cls(lq.var_1d) : '');
    const c = $('.rd-liq-chip'); const t20 = lq ? lq.var_20d : null;
    c.textContent = t20 == null ? 'aguardando dados' : t20 > 1 ? '▲ injetando liquidez' : t20 < -1 ? '▼ drenando liquidez' : '■ estável'; c.className = 'tl-chip rd-liq-chip ' + (t20 == null ? '' : t20 > 1 ? 'ok' : t20 < -1 ? 'bad' : '');
    if (lq) { li(ul, '5 dias', sg(lq.var_5d), cls(lq.var_5d)); li(ul, '20 dias', sg(lq.var_20d), cls(lq.var_20d)); li(ul, 'Percentil no ano', nf(lq.pctil_1a, 0) + '%'); }
    const st = $('.rd-st'); st.replaceChildren();
    const vr = row('VIX ÷ VIX 3 meses'), mv = row('MOVE (vol. de Treasuries)'), nc = row('Condições financeiras (NFCI)');
    li(st, 'VIX ÷ VIX 3 meses', vr ? nf(vr.valor, 2) : '—', '', vr ? (vr.valor >= 1 ? ['pânico agudo', 'bad'] : vr.valor >= 0.92 ? ['atenção', 'warn'] : ['calmo', 'ok']) : null);
    li(st, 'MOVE', mv ? nf(mv.valor, 0) : '—', '', mv ? (mv.pctil_1a >= 80 ? ['alto no ano', 'bad'] : mv.pctil_1a <= 20 ? ['baixo no ano', 'ok'] : ['normal', '']) : null);
    li(st, 'NFCI · condições financeiras' + (nc ? ' (' + br(nc.data).slice(0, 5) + ')' : ''), nc ? nf(nc.valor, 2) : '—', '', nc ? (nc.valor > 0 ? ['apertadas', 'bad'] : ['frouxas', 'ok']) : null);
    const sp = $('.rd-sp'); sp.replaceChildren();
    for (const cur of ['USD', 'EUR', 'GBP', 'JPY', 'CHF']) {
      const v = surpresaIdx(cur, false); const r = document.createElement('div'); r.className = 'rd-b';
      const a = document.createElement('span'); a.textContent = cur; const tr = document.createElement('span'); tr.className = 'tr'; const i = document.createElement('i');
      const w = Math.min(Math.abs(v || 0), 100) / 2; i.style.width = w + '%'; i.style.left = ((v || 0) >= 0 ? 50 : 50 - w) + '%'; i.style.background = (v || 0) >= 0 ? 'var(--color-ok)' : 'var(--color-bad)'; tr.appendChild(i);
      const n = document.createElement('span'); n.className = 'num ' + cls(v); n.textContent = v == null ? '—' : sg(v, 0, ''); r.append(a, tr, n); sp.appendChild(r);
    }
    const gU = surpresaIdx('USD', false), iU = surpresaIdx('USD', true); const rg = $('.rd-reg');
    const Q = gU == null || iU == null ? null : gU >= 0 ? (iU >= 0 ? ['EUA: reaquecendo (crescimento ▲ inflação ▲)', 'warn'] : ['EUA: cenário ideal (crescimento ▲ inflação ▼)', 'ok']) : (iU >= 0 ? ['EUA: estagflação (crescimento ▼ inflação ▲)', 'bad'] : ['EUA: desaceleração (crescimento ▼ inflação ▼)', '']);
    rg.textContent = Q ? Q[0] : (SURP.t ? 'regime: dados insuficientes' : 'carregando…'); rg.className = 'tl-chip rd-reg ' + (Q ? Q[1] : '');
  }

  window.APP = { D, nf, sg, br, td, tip, show, axisStyle, COLORS, $ };
  function drawAll() { drawGB(); if (!$('#sec-mi').hidden) { drawMI(); drawRadar(); } if (!$('#sec-op').hidden && window.drawOP) window.drawOP(); }
  let rz; window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(drawAll, 150); });
  load().then(() => { liveTick(); surpTick(); }); setInterval(load, 2 * 60 * 1000); setInterval(surpTick, 10 * 60 * 1000);
})();
