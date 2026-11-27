(() => {
  // ---------------------------------------------------------------- dados
  const IDS = ['mi_geral', 'mi_ativos', 'mi_sazon', 'mi_corr', 'mi_cot', 'mi_macro', 'mi_hist', 'mi_agenda', 'mi_noticias', 'mi_status', 'mi_ia', 'mi_eua', 'mi_dolar', 'mi_cta', 'mi_regime', 'mi_faixa', 'mi_paredes', 'goldbach_dias', 'toque_tabela', 'mi_validacao', 'faixa_backtest', 'rompimento', 'ouro_boletim', 'iene_boletim', 'lateralidade', 'padrao'];
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
        if (/^(mi|op|ouro|iene)_/.test(id)) { try { data = await pega(RAW + id + '.json?t=' + t); } catch (e) { data = await pega('data/' + id + '.json?t=' + t); } }
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
  if (['#sec-gb', '#sec-ai', '#sec-op'].includes(location.hash)) tabs(location.hash === '#sec-op' ? 'sec-mi' : 'sec-dias');
  else if (location.hash === '#sec-dias') tabs('sec-dias');

  // ---------------------------------------------------------------- mercado
  let atv = (() => { try { return localStorage.getItem('atv') || 'EURUSD'; } catch (e) { return 'EURUSD'; } })(), serie = 'Spread 2a EUA−Alemanha', jan = 10, nwF = 'ativo'; const vis = {};
  const bar = $('.ativos');
  // altura do topo fixo -> o seletor de ativo gruda logo abaixo dele
  { const tp = document.querySelector('.topo'), af = document.querySelector('.ativos-fixo');
    const upd = () => { document.documentElement.style.setProperty('--topo-h', tp.offsetHeight + 'px'); if (af) af.classList.toggle('preso', af.getBoundingClientRect().top <= tp.offsetHeight + 1); };
    new ResizeObserver(upd).observe(tp); window.addEventListener('scroll', upd, { passive: true }); upd(); }
  for (const a of ATV) {
    const b = document.createElement('button'); b.type = 'button'; b.dataset.a = a;
    b.innerHTML = '<span class="an"><b></b><small></small></span><span class="sv">—<small></small></span>';
    b.querySelector('.an b').textContent = a; b.querySelector('.an small').textContent = NOME[a];
    b.addEventListener('click', () => { atv = a; try { localStorage.setItem('atv', a); } catch (e) {} drawMI(); drawAtv(); }); bar.appendChild(b);
  }
  document.querySelectorAll('.mi-jan button').forEach((b) => b.addEventListener('click', () => {
    jan = Number(b.dataset.j); document.querySelectorAll('.mi-jan button').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); drawMI();
  }));
  const SIN = { alta: 'viés de alta (subiu em 60% ou mais, aprovado no teste)', baixa: 'viés de baixa (caiu em 60% ou mais, aprovado no teste)', inconclusivo: 'inconclusivo: sem vantagem' };

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
      const a0 = (D('mi_ativos').data || []).find((r) => r.ativo === x.dataset.a);
      const sv = x.querySelector('.sv'); const v1 = a0 ? a0.var_1d : null; sv.firstChild.textContent = v1 == null ? '—' : sg(v1, 2); sv.style.color = v1 > 0 ? 'var(--color-ok)' : v1 < 0 ? 'var(--color-bad)' : '';
      sv.querySelector('small').textContent = 'hoje';
    });
    const G = D('mi_geral'), A = D('mi_ativos'), S = D('mi_sazon'), C = D('mi_corr'), K = D('mi_cot'), M = D('mi_macro'), Hh = D('mi_hist'),
      AG = D('mi_agenda'), N = D('mi_noticias'), ST = D('mi_status'), IA = D('mi_ia');
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
    $('.mi-take').textContent = g ? 'Dados de ' + br(g.gerado_em) + ' (Brasília)' + (g.red_hoje ? ' · ' + g.red_hoje + ' evento(s) red folder hoje' : '') + cmeInfo() : 'Carregando…';
    $('.hj-up').textContent = g ? 'atualizado ' + br(g.gerado_em) : '';

    // score + IA
    const ia = (k) => (IA.status === 'ok' ? IA.data.find((r) => r.ativo === k) : null);
    const g0 = ia('GERAL'); $('.mi-ia-geral').textContent = g0 ? g0.texto : '—'; $('.mi-ia-geral-q').textContent = g0 ? 'escrita em ' + br(g0.gerado_em) : '';
    $('.sc-nome').textContent = atv + ' · ' + NOME[atv];
    { const sp = ((D('mi_geral').data || [])[0] || {}).ouro_spot; let e = $('.sc-spot'); if (!e) { e = document.createElement('span'); e.className = 'sc-spot'; $('.sc-nome').after(e); }
      e.textContent = atv === 'XAUUSD' && sp && sp.base_usd ? ' (régua da Vantage · futuro − US$ ' + nf(sp.base_usd, 1) + ')' : ''; }
    const ia1 = ia(atv); $('.mi-ia-atv').textContent = ia1 ? ia1.texto : '—'; $('.mi-ia-atv-q').textContent = ia1 ? 'escrita em ' + br(ia1.gerado_em) : '';
    drawMapa(); drawRS(); drawLat();

    // ativo
    const a = A.status === 'ok' ? A.data.find((r) => r.ativo === atv) : null; const cs = CASAS[atv];
    document.querySelectorAll('.mi-a').forEach((el) => {
      const f = el.dataset.f; const val = a ? a[f] : null;
      el.textContent = val == null ? '—' : (f === 'saz_mes_media' || f === 'saz_mes10_media') ? sg(val, 2) : (f === 'gb_extremos' || f === 'hp_extremos' || f === 'gb_sweep' || f === 'hp_sweep') ? nf(val, 1) + '%' : nf(val, ['atr14', 'preco', 'vj_valor'].includes(f) ? cs : 2);
    });
    const hm = new Date().getMonth();
    const L = (sel, rows) => { const ul = $(sel); ul.replaceChildren(); if (!a) return; for (const [k, v, c] of rows) if (v != null) { const e = document.createElement('li'); const x = document.createElement('span'); x.textContent = k; const y = document.createElement('b'); y.textContent = v; if (c) y.className = c; e.append(x, y); ul.appendChild(e); } };
    L('.mi-a-var', a ? [['Dia', sg(a.var_1d), cls(a.var_1d)], ['5 dias', sg(a.var_5d), cls(a.var_5d)], ['20 dias', sg(a.var_20d), cls(a.var_20d)], ['No ano', sg(a.var_ano), cls(a.var_ano)]] : []);
    L('.mi-a-vj', a && a.vj_valor != null ? [['Preço vs. justo', sg(a.vj_desvio_pct), cls(-a.vj_desvio_pct)], ['Esticamento (z)', nf(a.vj_z, 1), Math.abs(a.vj_z) >= 2 ? 'mi-neg' : ''], ['Fator', a.vj_fator], ['Confiança (R²)', nf(a.vj_r2, 2), a.vj_r2 >= 0.3 ? '' : 'mi-neg']] : []);
    L('.mi-a-saz', a && a.saz_mes10_media != null ? [['Subiu em (10 anos)', nf(a.saz_mes10_acerto, 0) + '%'], ['Leitura (10 anos)', a.saz_mes10_sinal === 'inconclusivo' ? 'sem vantagem' : 'viés de ' + a.saz_mes10_sinal, a.saz_mes10_sinal === 'alta' ? 'mi-pos' : a.saz_mes10_sinal === 'baixa' ? 'mi-neg' : ''], ['Comparação: 20 anos', nf(a.saz_mes_acerto, 0) + '% · média ' + sg(a.saz_mes_media, 2)]] : []);
    L('.mi-a-52', a ? [['Mínima 52 semanas', nf(a.min_52s, cs)], ['Máxima 52 semanas', nf(a.max_52s, cs)], ['ATR em % do preço', a.preco ? nf(a.atr14 / a.preco * 100, 2) + '%' : null]] : []);
    $('.mi-gbs-b').textContent = a && a.gb_sweep != null ? a.sweep_n + ' sweeps · base ' + nf(a.gb_base, 1) + '% · diferença ' + sg(a.gb_sweep - a.gb_base, 1, ' p.p.') : '—';
    $('.mi-hps-b').textContent = a && a.hp_sweep != null ? 'base ' + nf(a.hp_base, 1) + '% · diferença ' + sg(a.hp_sweep - a.hp_base, 1, ' p.p.') : '—';
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
      for (const s2 of todas) if (!(s2.nome in vis)) vis[s2.nome] = s2.nome === 'Média 10 anos' || s2.nome === 'Média 5 anos' || s2.nome.includes('até hoje');
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
    $('.mi-cot-n').textContent = 'Como ler: líquido = contratos comprados menos vendidos. Os nomes mudam entre relatórios (moedas e Nasdaq usam o TFF; ouro usa o desagregado), por isso o equivalente vem entre parênteses. "≈ hedge funds" (fundos alavancados ou managed money) = dinheiro especulativo grande, que costuma seguir tendência. "≈ commercials" (dealers; no ouro, produtores + swap dealers) = bancos e quem faz hedge, normalmente do lado oposto. Institucional = fundos de longo prazo. Varejo = só informativo. Índice 3a acima de 80 ou abaixo de 20 = posição esticada. É retrato, não sinal de direção. Toque na legenda para ligar ou desligar cada curva. Sai às sextas com dados da terça.' + (kr[0] ? ' Relatório de ' + br(kr[0].data) + '.' : '') + (kr[0] && kr[0].sinal_par < 0 ? ' Atenção: é o futuro da moeda contra o dólar, então comprado na moeda = vendido no ' + atv + '.' : '');
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
  let GBANT = false;   // Goldbach: mês anterior aberto?
  function drawGB() {
    const g = D('goldbach_dias'); const t = hojeISO();
    const [ty, tm, tdd] = t.split('-').map(Number);
    $('.hj-d').textContent = new Date(Date.UTC(ty, tm - 1, tdd)).toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' });
    if (g.status !== 'ok') return;
    const hj = g.data.find((r) => r.data === t);
    const hs = $('.hj-s'); hs.textContent = hj ? hj.resumo : 'Não é dia Goldbach nem Hopiplaka'; hs.classList.toggle('both', !!hj && hj.tipo === 'Goldbach + Hopiplaka');
    if ($('#sec-dias').hidden) return;
    const fut = g.data.filter((r) => r.data >= t);
    $('.gb-take').textContent = hj ? 'Hoje: ' + hj.resumo + (hj.goldbach ? ' — Goldbach por ' + hj.goldbach : '') : 'Hoje não é dia Goldbach nem Hopiplaka.';
    const a = fut.find((r) => r.tipo === 'Goldbach + Hopiplaka');
    $('.gb-next2').textContent = a ? br(a.data) + ' (' + a.dia_semana + ')' : '—'; $('.gb-next2-s').textContent = a ? 'Hopiplaka ' + a.hopiplaka : '—';
    const o = fut.find((r) => Number(r.dia_mes_hopiplaka) === 1); $('.gb-open').textContent = o ? br(o.data) + ' (' + o.dia_semana + ')' : '—';
    // calendário
    const box = $('#sec-gb .gb-cal'); box.replaceChildren(); const map = new Map(g.data.map((r) => [r.data, r]));
    for (let k = -1; k < 2; k++) {   // mês anterior recolhido; atual e seguinte abertos
      const y = ty + Math.floor((tm - 1 + k + 12) / 12) - 1, m = (((tm - 1 + k) % 12) + 12) % 12 + 1;
      if (k < 0 && ![...map.keys()].some((x) => x.startsWith(y + '-' + String(m).padStart(2, '0')))) continue;   // sem dados do mês anterior: não mostra
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
      if (k < 0) { const det = document.createElement('details'); det.className = 'gb-ant'; det.open = !!GBANT; const sm = document.createElement('summary'); sm.textContent = 'Mês anterior: ' + h.textContent; det.append(sm, grid);
        det.addEventListener('toggle', () => { GBANT = det.open; }); wrap.append(det); } else wrap.append(h, grid);
      box.appendChild(wrap);
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
  // compara com o mesmo número de casas que aparece na tela (ex.: 0,33% oficial vs. previsão 0,3% = em linha, não "acima")
  const surpresa = (r, e) => { if (!e || e.actual == null) return null; const f = prevNum(r, e); if (f == null) return 0;
    const dp = String(r.previsao || '').match(/[.,](\d+)/); const cs = dp ? dp[1].length : (e.digits != null ? e.digits : 2), p = Math.pow(10, cs);
    const d = Math.round(e.actual * p) - Math.round(f * p); return d === 0 ? 0 : d > 0 ? 1 : -1; };
  // botão "ver eventos de dias anteriores": fica numa barra ACIMA da tabela (dentro da tabela, o colspan quebrava o layout no celular)
  function barraAnt(tabela, n, aberto, aoClicar) {
    const caixa = tabela.closest('.op-tablebox, .tbl-x') || tabela.parentElement; let bar = caixa.previousElementSibling;
    if (!bar || !bar.classList.contains('ag-ant-bar')) { bar = document.createElement('div'); bar.className = 'ag-ant-bar'; caixa.before(bar); }
    bar.replaceChildren(); bar.hidden = !n; if (!n) return;
    const bt = document.createElement('button'); bt.type = 'button'; bt.className = 'op-btn ag-ant-btn'; bt.setAttribute('aria-expanded', String(!!aberto));
    bt.textContent = (aberto ? '▾ Esconder' : '▸ Ver') + ' ' + n + ' evento' + (n > 1 ? 's' : '') + ' de dias anteriores'; bt.onclick = aoClicar; bar.appendChild(bt);
  }
  let AGHIST = false;   // agenda: histórico (dias anteriores) aberto?
  function drawAgenda() {
    const AG = D('mi_agenda'); const at = $('.mi-ag-t tbody'); if (!at) return; at.replaceChildren(); const hj = hojeISO(); const agora = Date.now();
    let ultimo = null, primHoje = false, nAnt = 0;
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
      if (r.data < hj) { nAnt++; tr.classList.add('ag-ant'); tr.hidden = !AGHIST; }   // dias anteriores a hoje: recolhidos por padrão
      at.appendChild(tr);
    }
    barraAnt(at.closest('table'), nAnt, AGHIST, () => { AGHIST = !AGHIST; drawAgenda(); });
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


  // ---------------------------------------------------------------- alto impacto EUA (3 meses)
  var AI = { ev: [], t: 0, dia: null };
  async function aiTick() {
    const h = new Date(); const ini = new Date(Date.UTC(h.getFullYear(), h.getMonth() - 1, 1)), fim = new Date(Date.UTC(h.getFullYear(), h.getMonth() + 2, 0));
    try { const r = await fetch('https://biquote.io/api/calendar?countries=US&importance=high&from=' + ini.toISOString().slice(0, 10) + '&to=' + fim.toISOString().slice(0, 10), { cache: 'no-store' });
      if (r.ok) { const j = await r.json(); AI.ev = (Array.isArray(j) ? j : []).filter((e) => e.currency === 'USD' && e.importance === 'high'); AI.t = Date.now(); if (!$('#sec-dias').hidden) drawAI(); } } catch (e) { /* mantém */ }
  }
  const brt = (iso) => { const d = new Date(new Date(iso).getTime() - 3 * 3600e3); return [d.toISOString().slice(0, 10), d.toISOString().slice(11, 16)]; };
  function drawAI() {
    if (!AI || $('#sec-dias').hidden) return;
    const G = new Map((D('goldbach_dias').data || []).map((r) => [r.data, r])); const hj = hojeISO();
    const por = new Map(); for (const e of AI.ev) { const [d] = brt(e.time); if (!por.has(d)) por.set(d, []); por.get(d).push(e); }
    const nMes = [...por.keys()].filter((d) => d.slice(0, 7) === hj.slice(0, 7)).length;
    $('.ai-take').textContent = AI.t ? nMes + ' dia(s) com dado americano de alto impacto neste mês · próximo: ' + (() => { const p = AI.ev.filter((e) => new Date(e.time) > new Date()).sort((a, b) => a.time < b.time ? -1 : 1)[0]; if (!p) return '—'; const [d, h] = brt(p.time); return br(d) + ' ' + h + ' ' + p.name; })() : 'Carregando…';
    const box = $('.ai-cal'); box.replaceChildren(); const now = new Date();
    for (let k = -1; k <= 1; k++) {   // mês anterior entra recolhido (clique para abrir); atual e seguinte abertos
      const y = now.getFullYear() + Math.floor((now.getMonth() + k) / 12), m = (((now.getMonth() + k) % 12) + 12) % 12 + 1;
      const wrap = document.createElement('div'); wrap.className = 'gb-mes'; const h3 = document.createElement('h3');
      h3.textContent = new Date(Date.UTC(y, m - 1, 15)).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric', timeZone: 'UTC' });
      const grid = document.createElement('div'); grid.className = 'gb-grid';
      for (const w of ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']) { const c = document.createElement('div'); c.className = 'gb-wd'; c.textContent = w; grid.appendChild(c); }
      for (let i = 0; i < new Date(Date.UTC(y, m - 1, 1)).getUTCDay(); i++) grid.appendChild(document.createElement('div'));
      for (let d = 1; d <= new Date(Date.UTC(y, m, 0)).getUTCDate(); d++) {
        const iso = y + '-' + String(m).padStart(2, '0') + '-' + String(d).padStart(2, '0'); const ev = por.get(iso); const g = G.get(iso);
        const b = document.createElement('button'); b.type = 'button'; b.className = 'gb-day' + (ev ? ' ai-day' : '') + (iso === hj ? ' hj' : '') + (iso === AI.dia ? ' sel' : ''); b.textContent = d;
        const mk = []; if (ev) mk.push(ev.length); if (g) mk.push(g.tipo === 'Goldbach + Hopiplaka' ? '★' : g.tipo === 'Goldbach' ? 'G' : 'H');
        if (mk.length) { const s2 = document.createElement('small'); s2.className = 'ai-mk'; s2.textContent = mk.join(' '); b.appendChild(s2); }
        if (ev) b.addEventListener('click', () => { AI.dia = AI.dia === iso ? null : iso; drawAI(); });
        grid.appendChild(b);
      }
      if (k < 0) { const det = document.createElement('details'); det.className = 'gb-ant'; det.open = !!AI.antAberto; const sm = document.createElement('summary'); sm.textContent = 'Mês anterior: ' + h3.textContent; det.append(sm, grid);
        det.addEventListener('toggle', () => { AI.antAberto = det.open; }); wrap.append(det); } else wrap.append(h3, grid);
      box.appendChild(wrap);
    }
    const tb = $('.ai-t tbody'); tb.replaceChildren();
    const todos = AI.ev.filter((e) => !AI.dia || brt(e.time)[0] === AI.dia).sort((a, b) => (a.time < b.time ? -1 : 1));
    const nPass = AI.dia ? 0 : todos.filter((e) => brt(e.time)[0] < hj).length;   // eventos de dias anteriores a hoje: recolhidos por padrão
    const lista = AI.dia || AI.hist ? todos : todos.filter((e) => brt(e.time)[0] >= hj);
    barraAnt($('.ai-t'), nPass, AI.hist, () => { AI.hist = !AI.hist; drawAI(); });
    $('.ai-lt').textContent = AI.dia ? 'Eventos de ' + br(AI.dia) : 'Eventos de hoje em diante' + (AI.hist ? ' (com histórico)' : ''); $('.ai-all').hidden = !AI.dia; $('.ai-all').onclick = () => { AI.dia = null; drawAI(); };
    for (const e of lista) {
      const [d, h] = brt(e.time); const tr = document.createElement('tr'); if (d === hj) tr.className = 'ai-hoje';
      const g = G.get(d); td(tr, (d === hj ? 'hoje' : br(d).slice(0, 5)) + ' ' + h + (g ? (g.tipo === 'Goldbach + Hopiplaka' ? ' ★' : g.tipo === 'Goldbach' ? ' G' : ' H') : ''));
      td(tr, e.name); td(tr, e.forecast == null ? '—' : fmtLive(e, e.forecast), 'num'); td(tr, e.previous == null ? '—' : fmtLive(e, e.previous), 'num');
      const c = td(tr, '', 'num ag-at');
      if (e.actual != null) { const dd = e.forecast == null ? 0 : Math.sign(e.actual - e.forecast); const bx = document.createElement('span'); bx.className = 'ag-box ' + (dd > 0 ? 'ag-acima' : dd < 0 ? 'ag-abaixo' : 'ag-igual'); bx.textContent = (dd > 0 ? '▲ ' : dd < 0 ? '▼ ' : '') + fmtLive(e, e.actual); c.appendChild(bx); }
      else c.textContent = new Date(e.time) < new Date() ? '—' : 'aguarda';
      tb.appendChild(tr);
    }
    if (!lista.length) { const tr = document.createElement('tr'); td(tr, AI.t ? 'Sem eventos.' : 'Carregando…'); tb.appendChild(tr); }
  }


  // o que o movimento do dia de cada série favorece (relação testada no mesmo dia/semana; não é previsão)
  function djLeitura(r) {
    const d = r.d1, s = r.serie; if (d == null) return ['—', 0];
    const lim = r.unid === '% anualizado' ? 0.05 : 2; if (Math.abs(d) < lim) return ['<span class="op-note">neutro</span>', 0];
    // só pares que ela opera: verde = deve subir, vermelho = deve cair (pedido 17/11)
    const up = d > 0, P = (par, sobe) => `<span style="white-space:nowrap" class="${sobe ? 'mi-pos' : 'mi-neg'}">${par} ${sobe ? '↑' : '↓'}</span>`, J = (...x) => x.join('<br>');
    if (/^EUA|Fed Funds/.test(s)) return [J(P('Dólar', up), P('XAUUSD', !up)), up ? 1 : -1];
    if (/EUA − Japão/.test(s)) return [J(P('USDJPY', up), P('Iene', !up)), 0];
    if (/EUA − Alemanha/.test(s)) return [P('EURUSD', !up), 0];
    if (/JGB|Japão 10/.test(s)) return [J(P('Iene', up), P('USDJPY', !up)), 0];
    if (/Bund|Alemanha 10/.test(s)) return [P('EURUSD', up), 0];
    if (/GDPNow/.test(s)) return [J(P('Dólar', up), P('XAUUSD', !up)), 0];
    return ['—', 0];
  }

  function drawDJ() {
    const t = $('.dj-t tbody'); if (!t) return; t.replaceChildren(); const votos = [];
    for (const r of D('mi_dolar').data || []) {
      const tr = document.createElement('tr'); const bps = r.unid !== '% anualizado';
      { const c0 = td(tr, r.serie); if (r.vs_efetivo_bps != null) { const s = document.createElement('div'); s.style.cssText = 'font-size:12px;color:var(--color-fg-muted)'; s.textContent = sg(r.vs_efetivo_bps, 0, ' bps vs. efetivo'); c0.appendChild(s); } }
      td(tr, nf(r.valor, r.unid === 'p.p.' ? 2 : 2) + (r.unid === '% anualizado' ? '%' : r.unid === 'p.p.' ? ' p.p.' : '%'), 'num');
      td(tr, r.d1 == null ? '—' : sg(r.d1, bps ? 1 : 2, bps ? '' : ' p.p.'), 'num ' + cls(r.d1)); td(tr, r.d5 == null ? '—' : sg(r.d5, bps ? 1 : 2, bps ? '' : ' p.p.'), 'num ' + cls(r.d5));   // unidade (bps) no cabeçalho: número não quebra no celular
      const [txt, voto] = djLeitura(r); const c = document.createElement('td'); c.style.fontSize = '12px';
      c.innerHTML = txt; tr.appendChild(c); if (voto) votos.push(voto);
      t.appendChild(tr);
    }
    const dts = (D('mi_dolar').data || []).filter((r) => /^EUA \d/.test(r.serie)).map((r) => r.data).filter(Boolean).sort(), dt0 = dts[dts.length - 1];
    const hojeBR = new Date(Date.now() - 3 * 3600000).toISOString().slice(0, 10);
    const quando = dt0 === hojeBR ? '<b>Juros dos EUA hoje (ao vivo):</b> ' : dt0 ? '<b>Juros dos EUA, fechamento de ' + ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'][new Date(dt0 + 'T12:00:00').getDay()] + ' ' + dt0.slice(8, 10) + '/' + dt0.slice(5, 7) + ':</b> ' : '<b>Último fechamento:</b> ';
    const sobe = votos.filter((v) => v > 0).length, desce = votos.filter((v) => v < 0).length, rs = $('.dj-resumo');
    if (rs) rs.innerHTML = !votos.length ? quando + 'juros praticamente parados, sem pressão clara sobre o dólar.'
      : quando + (sobe > desce ? `juros americanos subindo (${sobe} de ${votos.length} séries) → <b class="mi-pos">Dólar ↑</b>: <b class="mi-neg">XAUUSD ↓ · EURUSD ↓</b> · <b class="mi-pos">USDJPY ↑ · USDCHF ↑</b>.`
        : desce > sobe ? `juros americanos caindo (${desce} de ${votos.length} séries) → <b class="mi-neg">Dólar ↓</b>: <b class="mi-pos">XAUUSD ↑ · EURUSD ↑</b> · <b class="mi-neg">USDJPY ↓ · USDCHF ↓</b>.`
        : 'juros mistos → sem direção clara para o dólar.') + (dt0 === hojeBR ? ' Explica o dia; não prevê o próximo.' : ' O mercado de juros americano ainda não abriu hoje: isto explica aquele dia, não o de hoje, e não prevê o próximo.');
    drawAtv();
  }


  // mapa de probabilidades: níveis em σ a partir da abertura do dia/semana, com a frequência real de toque (2 anos, 1 h)
  // boletim da CME: de que pregão é e quando chegou (para ver que o robô do PC está pegando de madrugada)
  function cmeInfo() {
    const b = (D('ouro_boletim').data || [])[0]; if (!b || !b.data_pregao) return '';
    const sit = b.situacao === 'FINAL' ? 'final' : 'preliminar';
    return ' · CME: boletim de ' + br(b.data_pregao).slice(0, 5) + ' (' + sit + ')' + (b.recebido_em ? ', chegou ' + b.recebido_em.slice(8, 10) + '/' + b.recebido_em.slice(5, 7) + ' ' + b.recebido_em.slice(11, 16) : '');
  }
  // números fixos do painel (fonte única: docs/data/padrao.json); os literais abaixo só valem se o arquivo não carregar
  const QN0 = { XAUUSD: [0.44, 1.35, 1.05], USDJPY: [0.43, 1.20, 0.97], EURUSD: [0.54, 1.40, 1.16], USDCHF: [0.54, 1.37, 1.15], GBPUSD: [0.57, 1.50, 1.13] };
  const CC0 = { XAUUSD: [0.81, 1.22, 0.75, 0.79, 0.95, 65, 39], USDJPY: [0.73, 1.08, 0.44, 0.57, 0.79, 73, 30], EURUSD: [0.77, 1.18, 0.69, 0.79, 0.97, 68, 35], USDCHF: [0.76, 1.11, 0.69, 0.74, 0.90, 61, 42], GBPUSD: [0.83, 1.18, 0.72, 0.82, 1.00, 68, 35] };
  const qNormal = (a) => { const d = ((D('padrao').data || {}).dia_normal || {})[a]; return d ? [d.q50, d.q90, d.amplitude_tipica] : QN0[a]; };
  const cCedo = (a) => { const d = ((D('padrao').data || {}).cedo || {})[a]; return d ? [d.corte_baixo, d.corte_alto, d.resto_se_baixo, d.resto_se_medio, d.resto_se_alto, d.p_grande_se_alto, d.p_grande_se_baixo] : CC0[a]; };
  const hOuro = () => ((D('padrao').data || {}).hora_ouro_sigma_dia) || [0.231, 0.190, 0.274, 0.280, 0.288, 0.296, 0.267, 0.263, 0.290, 0.393, 0.482, 0.481, 0.399, 0.322, 0.271, 0.254, 0.243, 0.210, 0.215, 0.242, 0.231, 0.281, 0.377, 0.288];
  // Mapa de lateralidade: igual para os 5 ativos (testes/lateralidade.py e lateralidade2.py, 24/11/2026)
  function drawLat() {
    const bx = $('.lat-corpo'); if (!bx) return; bx.replaceChildren(); $('.lat-nome').textContent = atv + ' · ' + NOME[atv];
    const L = (D('lateralidade').data || {})[atv]; if (!L) { bx.textContent = 'Sem mapa para este ativo.'; return; }
    const fr = (D('mi_faixa').data || []).find((r) => r.ativo === atv), lat = fr && fr.lateral;
    const lin = (html) => { const p = document.createElement('p'); p.className = 'lat-l'; p.innerHTML = html; bx.appendChild(p); }, f0 = (x) => nf(x, 0) + '%';
    const normal = Math.round(100 - L.pct_estreito - L.pct_largo);
    lin('<b>De cada 100 dias:</b> <b>' + f0(L.pct_estreito) + '</b> estreitos (laterais) · ' + f0(normal) + ' normais · <b>' + f0(L.pct_largo) + '</b> largos. <b>' + f0(L.pct_corpo_pequeno) + '</b> fecham perto da abertura (vai-e-volta). Base: ' + nf(L.dias, 0) + ' dias desde ' + L.desde.slice(0, 4) + '.');
    // ontem → hoje
    const P = L.persistencia || {}, base = L.pct_estreito;
    if (lat && lat.estado) { const pe = lat.estado === 'estreito' ? P.estreito_hoje_dado_estreito_ontem : lat.estado === 'largo' ? P.estreito_hoje_dado_largo_ontem : null;
      lin('<b>Ontem foi ' + lat.estado + '</b> (' + nf(lat.rel * 100, 0) + '% do normal)' + (pe != null ? ' → chance de hoje ser estreito: <b>' + f0(pe) + '</b> (média ' + f0(base) + ').' : ' → sem vantagem: a chance de hoje ser estreito fica perto da média (' + f0(base) + ').')); }
    lin('<span class="op-note">Depois de um dia estreito: ' + f0(P.estreito_hoje_dado_estreito_ontem) + ' de chance de outro dia estreito. Depois de um dia largo: ' + f0(P.estreito_hoje_dado_largo_ontem) + '.</span>');
    // payroll / calendário de hoje (data de Brasília)
    const hj = new Date(Date.now() - 3 * 3600000), dsem = hj.getUTCDay(), dia = hj.getUTCDate();
    const diaPay = dsem === 5 && dia <= 7, semPay = dsem >= 1 && dsem <= 5 && new Date(hj.getTime() + (5 - dsem) * 86400000).getUTCDate() <= 7;   // 1ª sexta do mês (dia ≤ 7) e a semana dela
    const pd = L.payroll_dia;
    if (pd && pd.comprovado) lin(diaPay ? '<b>Hoje é dia de payroll (1ª sexta):</b> dia estreito em só <b>' + f0(pd.estreito['1ª sexta']) + '</b> das vezes (normal ' + f0(pd.estreito.outros) + ') e largo em <b>' + f0(pd.largo['1ª sexta']) + '</b> (normal ' + f0(pd.largo.outros) + '). Lateralidade é rara hoje.'
      : '<span class="op-note">Dia de payroll (1ª sexta do mês): estreito só ' + f0(pd.estreito['1ª sexta']) + ' das vezes (normal ' + f0(pd.estreito.outros) + '); largo ' + f0(pd.largo['1ª sexta']) + ' (normal ' + f0(pd.largo.outros) + ').' + (semPay ? ' <b>Esta é a semana do payroll.</b>' : '') + '</span>');
    const ps = L.payroll_semana; if (ps && ps.comprovado) lin('<span class="op-note">Semana do payroll: dias estreitos ' + f0(ps.estreito['semana do payroll']) + ' (outras semanas ' + f0(ps.estreito.outras) + ')' + (semPay ? ' <b>(esta semana)</b>' : '') + '.</span>');
    const vs = L.vencimento_semana; if (vs && vs.comprovado) lin('<span class="op-note">Semana do vencimento mensal das opções: estreito ' + f0(vs.estreito['semana do vencimento']) + ' (outras ' + f0(vs.estreito.outras) + ').</span>');
    const um = L.ultima_semana_mes; if (um && um.comprovado) lin('<span class="op-note">Última semana do mês: estreito ' + f0(um.estreito['última semana']) + ' (outras ' + f0(um.estreito.outras) + ').</span>');
    // horas (Brasília)
    const hs = Object.entries(L.horas || {}), hb = String(hj.getUTCHours()).padStart(2, '0') + 'h', hn = (L.horas || {})[hb];
    if (hs.length) { const par = hs.slice().sort((a, b) => b[1].parada - a[1].parada).slice(0, 3), ag = hs.slice().sort((a, b) => b[1].agitada - a[1].agitada).slice(0, 3);
      lin('<b>Horas (Brasília):</b> mais paradas <b>' + par.map((x) => x[0] + ' (' + f0(x[1].parada) + ')').join(', ') + '</b> · mais agitadas <b>' + ag.map((x) => x[0] + ' (' + f0(x[1].agitada) + ')').join(', ') + '</b>.' + (hn ? ' Agora (' + hb + '): parada em ' + f0(hn.parada) + ' das vezes, agitada em ' + f0(hn.agitada) + '.' : ''));
      const tb = document.createElement('table'); tb.className = 'op-table lat-t'; tb.innerHTML = '<thead><tr><th>Hora</th>' + hs.map((x) => '<th class="num">' + x[0].slice(0, 2) + '</th>').join('') + '</tr></thead><tbody><tr><th>% parada</th>' + hs.map((x) => '<td class="num" style="' + (x[1].parada >= 25 ? 'font-weight:700;color:var(--color-pos,#1f8a5b)' : '') + '">' + nf(x[1].parada, 0) + '</td>').join('') + '</tr><tr><th>% agitada</th>' + hs.map((x) => '<td class="num" style="' + (x[1].agitada >= 25 ? 'font-weight:700;color:var(--color-neg,#c8443a)' : '') + '">' + nf(x[1].agitada, 0) + '</td>').join('') + '</tr></tbody>';
      const w = document.createElement('div'); w.className = 'tbl-x'; w.appendChild(tb); bx.appendChild(w); }
    if (L.mes_estreito) { const ms = Object.entries(L.mes_estreito).map(([m, v]) => [+m, v]), nm = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
      const alto = ms.filter((x) => x[1] >= base + 6).map((x) => nm[x[0] - 1] + ' ' + f0(x[1])), baixo = ms.filter((x) => x[1] <= base - 6).map((x) => nm[x[0] - 1] + ' ' + f0(x[1]));
      lin('<b>Meses (só neste ativo passou no teste):</b> mais laterais ' + (alto.join(', ') || '—') + ' · menos laterais ' + (baixo.join(', ') || '—') + ' (média ' + f0(base) + ').'); }
    lin('<span class="op-note">Dia da semana, semana do mês' + (L.mes_estreito ? '' : ' e mês') + ': nenhuma diferença comprovada em teste. Notícias (FOMC, CPI): em medição, o painel registra todo dia.</span>');
  }

  // "O que olhar hoje": resumo de 1 card só com o que passou em teste (pedido dela 20/11)
  function drawRS() {
    const bx = $('.rs-corpo'); if (!bx) return; bx.replaceChildren(); $('.rs-nome').textContent = atv + ' · ' + NOME[atv];
    const fr = (D('mi_faixa').data || []).find((r) => r.ativo === atv), m = fr && fr.mapa;
    if (!m && fr && fr.faixas) {   // sem mapa (NAS100): só a faixa da volatilidade, a partir do preço de agora
      const k0 = CASAS[atv], lin0 = (html) => { const p = document.createElement('p'); p.className = 'rs-l'; p.innerHTML = html; bx.appendChild(p); };
      for (const f of fr.faixas.slice(0, 2)) lin0('<b>Faixa ' + (f.prazo === 'dia' ? 'do dia' : 'da semana') + ' (±1σ, ±' + nf(f.pct, 2) + '%):</b> <span class="rs-n">' + nf(f.s1[0], k0) + ' – ' + nf(f.s1[1], k0) + '</span> · ±2σ ' + nf(f.s2[0], k0) + ' – ' + nf(f.s2[1], k0));
      lin0('Preço agora <b>' + nf(fr.preco, k0) + '</b> · ' + fr.fonte + '. A faixa parte do preço atual e muda junto com ele.');
      lin0('<span class="op-note">Em teste desde 2001, o dia fechou dentro de ±1σ em 77% das vezes e de ±2σ em 98%. Dia normal, chances e rompimento ainda não foram testados neste índice.</span>');
      lin0('<b>Direção (compra ou venda):</b> <span class="mi-neg">nenhum sinal comprovado</span>.'); return; }
    if (!m) { bx.textContent = 'Sem dados para este ativo.'; return; }
    const sd = m.sd_dia, ab = m.ab_dia, k = CASAS[atv], P = m.preco || fr.preco;
    const Q = qNormal(atv) || [0.5, 1.4];
    const pip = atv === 'XAUUSD' ? 1 : atv.includes('JPY') ? 0.01 : 0.0001, un = atv === 'XAUUSD' ? '' : ' pips', us = atv === 'XAUUSD' ? 'US$ ' : '';
    const pp = (x) => us + nf(ab * (Math.exp(x * sd) - 1) / pip, 0) + un, L = (x) => ab * Math.exp(x * sd);
    const lin = (html) => { const p = document.createElement('p'); p.className = 'rs-l'; p.innerHTML = html; bx.appendChild(p); };
    const est = !!m.ab_estimada;
    if (est) lin('<span class="mi-neg"><b>Abertura estimada:</b></span> a fonte ainda não entregou o candle das 20h. Os níveis são aproximados e o painel não marca toque, máxima, mínima nem rompimento.');
    lin('<b>σ (sigma) do dia:</b> <span class="rs-n">±' + pp(1) + '</span> · dia forte (' + (atv === 'XAUUSD' ? '82% dos dias fecham dentro; medido em 3.770 dias com o GVZ' : 'cerca de 8 em cada 10 dias fecham dentro') + ')');
    lin('<b>Dia normal:</b> <span class="rs-n">±' + pp(Q[0]) + '</span> · metade dos dias fecha dentro: <b>tamanho da grade</b>. Stop além de ±' + pp(Q[1]) + ' (só 1 em cada 10 dias fecha além).');
    // níveis do dia
    const tb = document.createElement('table'); tb.className = 'op-table rs-t'; const tr1 = document.createElement('tr'), tr2 = document.createElement('tr');
    for (const [x, nm, c] of [[-1, '−1σ', 'lv-pw'], [-Q[0], 'normal −', 'lv-s1'], [0, m.ab_estimada ? 'abertura (estimada)' : 'abertura', 'lv-now'], [Q[0], 'normal +', 'lv-s1'], [1, '+1σ', 'lv-cw']]) {
      const th = document.createElement('th'); th.className = 'num'; th.innerHTML = '<span class="lv ' + c + '">' + nm + '</span>'; tr1.appendChild(th);
      const v = L(x), toc = est ? false : x > 0 ? m.max_dia >= v : x < 0 ? m.min_dia <= v : false; td(tr2, nf(v, k) + (toc ? ' ✓' : ''), 'num').style.fontWeight = 600; }
    tb.innerHTML = '<thead></thead><tbody></tbody>'; tb.tHead.appendChild(tr1); tb.tBodies[0].appendChild(tr2);
    const w = document.createElement('div'); w.className = 'tbl-x'; w.appendChild(tb); bx.appendChild(w);
    // agora: posição em σ e o que costuma acontecer (rompimento medido)
    const R = (D('rompimento').data || {})[atv], z = Math.log(P / ab) / sd, eU = Math.log(m.max_dia / ab) / sd, eD = -Math.log(m.min_dia / ab) / sd, e = Math.max(eU, eD);
    const pc = (x) => (x ? nf(x[0], 0) + '%' : '—');
    const sit = !R ? '' : e >= 1.5 ? 'passou de 1,5σ: rompimento forte, <b>' + pc(R.passou_15_fecha_fora) + '</b> das vezes fecha fora do 1σ' : e >= 1.25 ? 'passou de 1,25σ: rompimento confirmado, <b>' + pc(R.passou_125_fecha_fora) + '</b> fecha fora do 1σ (tendência; cuidado com a grade)' : e >= 1 ? 'tocou o 1σ: cara ou coroa, ' + pc(R.tocou_1s_fecha_fora) + ' fecha fora' : 'ainda dentro do 1σ: dia normal até agora';
    lin('<b>Agora:</b> ' + nf(P, k) + (est ? '.' : ' (' + (z >= 0 ? '+' : '') + nf(z, 2) + 'σ da abertura) · ' + sit + '.'));
    // tamanho do resto do dia (Ásia + Londres) e hora (ouro)
    const Cc = cCedo(atv), C = Cc && [Cc[0], Cc[1], Cc[5], Cc[6]];
    if (C && m.amp_cedo != null) { const g = m.amp_cedo >= C[1] ? 2 : m.amp_cedo < C[0] ? 0 : 1;
      lin('<b>Resto do dia:</b> ' + ['tende a ser <b>pequeno</b> (Ásia e Londres andaram pouco; só ' + C[3] + '% de chance de ser grande)', 'tamanho <b>normal</b>', 'tende a ser <b>grande</b> (Ásia e Londres andaram muito; ' + C[2] + '% de chance)'][g] + '.'); }
    else lin('<b>Resto do dia:</b> a leitura sai às 11h de Brasília.');
    if (atv === 'XAUUSD') { const HR = hOuro();
      const hb = +new Date(Date.now() - 3 * 3600000).toISOString().slice(11, 13), v = HR[hb];
      lin('<b>Esta hora (' + hb + 'h):</b> ' + (v < 0.25 ? 'parada' : v > 0.35 ? 'agitada' : 'normal') + ', costuma andar ~' + pp(v) + '. Mais agitado 10h–12h; mais parado 17h–1h.'); }
    { const w = (D('mi_paredes').data || []).find((r) => r.ativo === atv);
      if (w) lin('<b>Paredes das opções</b> (CME, <b>referência, sem teste</b>): ' + (w.sem_dado ? '<b>sem dado</b>.' : [['call', 'call wall', 'lv-cw'], ['put', 'put wall', 'lv-pw']].map(([l, nm, c]) => { const x = w[l], x2 = w[l + '2'];
        return '<span class="lv ' + c + '">' + nm + '</span> <b>' + (x ? nf(x.nivel, k) : 'sem dado') + '</b>' + (w['rompida_' + l] ? ' (rompida; 2ª: ' + (x2 ? '<b>' + nf(x2.nivel, k) + '</b>' : 'nenhuma dentro de 1σ da semana') + ')' : ''); }).join(' · ') + '.')); }
    lin('<b>Direção (compra ou venda):</b> <span class="mi-neg">nenhum sinal comprovado</span>. Opere pelos níveis da faixa; as paredes e os demais cards são referência, não previsão.');
  }

  function drawMapa() {
    const fr = (D('mi_faixa').data || []).find((r) => r.ativo === atv), tb = (D('toque_tabela').data || {})[atv];
    const ok = fr && fr.mapa && tb; $('.mp-wrap').hidden = !ok; $('.mp-teste').hidden = !ok; $('.mp-resumo').hidden = !ok;
    $('.mp-chip').textContent = ok ? 'chances medidas em ' + tb.n_dias + ' dias' + (tb.sigma === 'DTCC' ? ' (σ das opções de balcão)' : '') : 'sem mapa para este ativo';
    if (!ok) return;
    const m = fr.mapa, sd = m.sd_dia, sw = m.sd_sem || sd * Math.sqrt(5), k = CASAS[atv];
    const lv = (txt, c) => { const s = document.createElement('span'); s.className = 'lv ' + c; s.textContent = txt; return s; };
    const leit = (p) => (p >= 50 ? 'alvo provável' : p >= 20 ? 'alvo possível' : p >= 8 ? 'difícil' : 'raro');
    const ks = [2, 1.5, 1, 0.5], ix = (x) => tb.k.indexOf(x), fx = (x) => nf(x, x % 1 ? 1 : 0);
    // chance "agora": a partir do preço atual e do tempo que falta (curva medida em 2 anos de 1 h; ver toque_tabela.agora_*)
    const P = m.preco || fr.preco, agoraMs = Date.now();
    const curva = (z) => { const Z = [0].concat(tb.agora_z || []), C = [100].concat(tb.agora_p || []); if (Z.length < 2) return null;
      if (z >= Z[Z.length - 1]) return C[C.length - 1]; let i = 0; while (Z[i + 1] < z) i++; return Math.round(C[i] + (z - Z[i]) / (Z[i + 1] - Z[i]) * (C[i + 1] - C[i])); };
    const resta = (ini, fim) => (ini && fim ? Math.max(0, Math.min(1, (fim - agoraMs) / (fim - ini))) : 1);
    const chAgora = (L, s, ini, fim) => { const r = resta(ini, fim); if (r <= 0) return 0; return curva(Math.abs(Math.log(L / P)) / (s * Math.sqrt(r))); };
    const hrs = (fim) => { const h = Math.max(0, (fim - agoraMs) / 3600000); return h >= 24 ? nf(h / 24, 1) + ' dias' : nf(h, h < 10 ? 1 : 0) + ' h'; };
    const mxd = m.ab_estimada ? -Infinity : m.max_dia, mnd = m.ab_estimada ? Infinity : m.min_dia;   // abertura estimada: nada conta como tocado
    const tabela = (sel, ab, s, mx, mn, cima, baixo, ini, fim) => {
      const t = $(sel + ' tbody'); t.replaceChildren(); const lin = [];
      for (const x of ks) { const L = ab * Math.exp(x * s); lin.push(['+' + fx(x) + 'σ', x >= 1.5 ? 'lv-cw' : 'lv-gf', L, cima[ix(x)], mx >= L, chAgora(L, s, ini, fim)]); }
      lin.push(['Abertura', 'lv-now', ab, null, false, null]);
      for (const x of ks.slice().reverse()) { const L = ab * Math.exp(-x * s); lin.push(['−' + fx(x) + 'σ', x >= 1.5 ? 'lv-pw' : 'lv-s1', L, baixo[ix(x)], mn <= L, chAgora(L, s, ini, fim)]); }
      for (const [nm, c, pr, ch0, toc, ch] of lin) {
        const tr = document.createElement('tr'); const c0 = document.createElement('td'); c0.appendChild(lv(nm, c)); tr.appendChild(c0);
        td(tr, nf(pr, k), 'num').style.fontWeight = 600;
        if (ch0 == null) { td(tr, ''); td(tr, 'ponto de partida'); tr.style.background = 'var(--color-bg)'; }
        else { const cc = td(tr, toc ? '—' : (ch == null ? ch0 : ch) + '%', 'num'); cc.style.fontWeight = 600;
          const sm = document.createElement('div'); sm.style.fontSize = '11px'; sm.style.fontWeight = 400; sm.style.color = 'var(--color-fg-muted)'; sm.textContent = 'abertura ' + ch0 + '%'; cc.appendChild(sm);
          const l = document.createElement('td'); if (toc) l.appendChild(lv('✓ já tocou', 'lv-pw')); else l.textContent = leit(ch == null ? ch0 : ch); tr.appendChild(l); }
        t.appendChild(tr);
      }
    };
    tabela('.mp-dia', m.ab_dia, sd, mxd, mnd, tb.dia_toca_cima, tb.dia_toca_baixo, m.ts_dia_ini, m.ts_dia_fim);
    tabela('.mp-sem', m.ab_sem, sw, m.max_sem, m.min_sem, tb.sem_toca_cima, tb.sem_toca_baixo, m.ts_sem_ini, m.ts_sem_fim);
    $('.mp-dia-q').textContent = 'Projetado na abertura de ' + (m.dia_ini || '—') + ' · vale até ' + (m.dia_fim || '—') + (m.ts_dia_fim ? ' · faltam ' + hrs(m.ts_dia_fim) : '') + (m.proj_dia ? ' (calculado ' + m.proj_dia + ')' : '');
    $('.mp-sem-q').textContent = 'Projetado na abertura de ' + (m.sem_ini || '—') + ' · vale até ' + (m.sem_fim || '—') + (m.ts_sem_fim ? ' · faltam ' + hrs(m.ts_sem_fim) : '') + (m.proj_sem ? ' (calculado ' + m.proj_sem + ')' : '');
    // resumo com a chance de agora: nível mais próximo ainda não tocado de cada lado
    const lado = (sgn) => { for (const x of [0.5, 1, 1.5, 2]) { const L = m.ab_dia * Math.exp(sgn * x * sd); if (sgn > 0 ? mxd < L : mnd > L) return [x, L, chAgora(L, sd, m.ts_dia_ini, m.ts_dia_fim)]; } return null; };
    const up = lado(1), dn = lado(-1), fr1 = (r, s) => (r ? `<b>${nf(r[1], k)}</b> (${s}${fx(r[0])}σ): <b>${r[2]}%</b>` : `todos os níveis ${s === '+' ? 'acima' : 'abaixo'} já tocados`);
    // dia normal: quanto o dia anda de verdade, em σ do painel (testes/dia_tipico.py, futuros da CME, 15 anos, ~3.750 dias cada)
    { const Q = qNormal(atv), bx = $('.mp-normal');   // moedas: σ das opções DTCC (testes/vol_dtcc.py, 2 anos)
      if (bx) { bx.replaceChildren(); bx.hidden = !Q; if (Q) {
        const pip = atv === 'XAUUSD' ? 1 : atv.includes('JPY') ? 0.01 : 0.0001, un = atv === 'XAUUSD' ? '' : ' pips', us = atv === 'XAUUSD' ? 'US$ ' : '';
        const pp = (x) => us + nf(m.ab_dia * (Math.exp(x * sd) - 1) / pip, 0) + un, L = (x) => nf(m.ab_dia * Math.exp(x * sd), k);
        const amp = Math.log(m.max_dia / m.min_dia) / sd;
        const h = document.createElement('div'); h.className = 'mp-romp-t'; h.innerHTML = '<b>Dia normal</b> · quanto o dia anda de verdade (' + (atv === 'XAUUSD' ? 'futuros da CME, 15 anos' : 'futuros da CME, 2 anos, com o σ das opções de balcão') + ')'; bx.appendChild(h);
        const a1 = document.createElement('p'); a1.innerHTML = '<b>Metade dos dias</b> fecha entre <b>' + L(-Q[0]) + '</b> e <b>' + L(Q[0]) + '</b> (±' + pp(Q[0]) + ' da abertura, ' + nf(Q[0], 2) + 'σ). <b>9 em cada 10</b> fecham entre ' + L(-Q[1]) + ' e ' + L(Q[1]) + ' (±' + pp(Q[1]) + ').'; bx.appendChild(a1);
        const a2 = document.createElement('p'); a2.innerHTML = 'Distância típica entre a máxima e a mínima do dia: <b>' + pp(Q[2]) + '</b>.' + (m.ab_estimada ? '' : ' <b>Hoje até agora:</b> ' + us + nf((m.max_dia - m.min_dia) / pip, 0) + un + ' (' + nf(amp / Q[2] * 100, 0) + '% do típico).'); bx.appendChild(a2);
        if (atv === 'XAUUSD') {   // quanto o ouro anda em cada hora (testes/horas_lateral.py, GC 1 h, 2 anos, em σ do dia; hora de Brasília)
          const HR = hOuro();
          const hb = +new Date(Date.now() - 3 * 3600000).toISOString().slice(11, 13), v = HR[hb];
          const a4 = document.createElement('p'); a4.innerHTML = '<b>Agora (' + hb + 'h):</b> hora ' + (v < 0.25 ? '<b>parada</b>' : v > 0.35 ? '<b>agitada</b>' : '<b>normal</b>') + ', o ouro costuma andar cerca de <b>' + pp(v) + '</b> nesta hora. Mais agitado: 10h–12h (' + pp(0.48) + '/h); mais parado: 17h–1h (' + pp(0.21) + '/h). Mostra o tamanho, não o formato: nenhum horário é mais "vai e volta" que outro.';
          bx.appendChild(a4); }
        const C = cCedo(atv);
        const a3 = document.createElement('p');
        if (C && m.amp_cedo != null) { const ce = m.amp_cedo, g = ce >= C[1] ? 2 : ce < C[0] ? 0 : 1;
          a3.innerHTML = '<b>Ásia + Londres (até 11h BRT):</b> andou ' + nf(ce, 2) + 'σ, ' + ['<b>pouco</b>', '<b>normal</b>', '<b>muito</b>'][g] + '. Daqui até o fim, o típico em dias assim é <b>' + pp(C[2 + g]) + '</b> entre a máxima e a mínima' + (g === 2 ? ' (' + C[5] + '% de chance de o resto do dia ser grande)' : g === 0 ? ' (só ' + C[6] + '% de chance de o resto do dia ser grande)' : '') + '.'; }
        else a3.innerHTML = '<b>Ásia + Londres:</b> a leitura do resto do dia aparece às 11h BRT.';
        bx.appendChild(a3);
        const n = document.createElement('p'); n.className = 'op-note ajuda'; n.innerHTML = '<b>Como ler:</b> o σ mostra o limite de um dia forte; o dia comum anda mais ou menos metade disso. Use a faixa da metade dos dias como tamanho de um dia normal para a grade do robô, e o ±1σ como o dia forte. A linha da Ásia + Londres usa o quanto o preço andou até as 11h de Brasília: quando andou muito, o resto do dia também tende a ser grande; quando andou pouco, tende a ser pequeno (medido em 2 anos de futuros a cada hora, estável). Medido em 15 anos dos futuros da CME, com o mesmo σ do mapa e estável no tempo. Mostra o tamanho do dia, não a direção.' + (atv === 'XAUUSD' ? ' A linha da hora vem de 2 anos de candles de 1 h do futuro; no horário de verão americano (mar–nov) os horários vêm 1 h mais cedo.' : ''); bx.appendChild(n);
      } } }
    // rompimento do σ do dia (medido em futuros da CME, mesma régua do mapa): o que costuma acontecer depois de cada gatilho
    { const R = (D('rompimento').data || {})[atv], bx = $('.mp-romp');
      if (bx) { bx.replaceChildren(); if (R) {
        const eU = Math.log(m.max_dia / m.ab_dia) / sd, eD = -Math.log(m.min_dia / m.ab_dia) / sd, pc = (x) => nf(x[0], 0) + '%';
        const L = (x, s) => nf(m.ab_dia * Math.exp(s * x * sd), k);
        const est = (e) => (e >= 1.5 ? 3 : e >= 1.25 ? 2 : e >= 1 ? 1 : 0);
        const sit = (e, nome) => ['ainda dentro do 1σ', 'tocou o 1σ: cara ou coroa (' + pc(R.tocou_1s_fecha_fora) + ' fecha fora)', 'passou de 1,25σ: rompimento confirmado (' + pc(R.passou_125_fecha_fora) + ' fecha fora)', 'passou de 1,5σ: rompimento forte (' + pc(R.passou_15_fecha_fora) + ' fecha fora)'][est(e)];
        const h = document.createElement('div'); h.className = 'mp-romp-t'; h.innerHTML = '<b>Rompimento do σ do dia</b> · o que costuma acontecer depois de cada gatilho (futuros da CME desde ' + R.desde + ', ' + nf(R.dias, 0) + ' dias' + (R.sigma === 'DTCC' ? ', com o σ das opções de balcão' : '') + ')'; bx.appendChild(h);
        const ag = document.createElement('p'); ag.className = 'mp-romp-agora'; ag.innerHTML = m.ab_estimada ? '<b>Hoje:</b> abertura estimada, o rompimento não é marcado.' : '<b>Hoje:</b> em cima ' + nf(Math.max(0, eU), 2) + 'σ → <b>' + sit(eU) + '</b> · embaixo ' + nf(Math.max(0, eD), 2) + 'σ → <b>' + sit(eD) + '</b>'; bx.appendChild(ag);
        const tb = document.createElement('table'); tb.className = 'op-table romp-t'; tb.innerHTML = '<thead><tr><th>Passou de</th><th class="num">Cima</th><th class="num">Baixo</th><th class="num">Depois</th></tr></thead>';
        const bd = document.createElement('tbody'); tb.appendChild(bd);
        for (const [x, nome, fora, alem] of [[1, '±1σ', R.tocou_1s_fecha_fora, null], [1.25, '±1,25σ', R.passou_125_fecha_fora, ['1,5σ', R.passou_125_chega_15]], [1.5, '±1,5σ', R.passou_15_fecha_fora, ['2σ', R.passou_15_chega_2]]]) {
          const tr = document.createElement('tr'); td(tr, nome).style.fontWeight = 600; td(tr, L(x, 1), 'num'); td(tr, L(x, -1), 'num'); const dd = td(tr, '', 'num'); dd.innerHTML = '<b>' + pc(fora) + '</b> fecha fora do 1σ' + (alem ? '<br><small>' + pc(alem[1]) + ' chega a ' + alem[0] + '</small>' : '');
          if (!m.ab_estimada && (est(eU) === [1, 1.25, 1.5].indexOf(x) + 1 || est(eD) === [1, 1.25, 1.5].indexOf(x) + 1)) tr.style.background = 'color-mix(in srgb, #c98a12 14%, transparent)'; bd.appendChild(tr); }
        const w = document.createElement('div'); w.className = 'tbl-x'; w.appendChild(tb); bx.appendChild(w);
        const n = document.createElement('p'); n.className = 'op-note ajuda'; n.innerHTML = '<b>Como ler:</b> níveis a partir da abertura do dia, com o mesmo σ do mapa. <b>Tocou o ±1σ</b> = cara ou coroa: metade das vezes fecha de volta dentro (às vezes só "sambou" e voltou). <b>Passou de ±1,25σ</b> = rompimento confirmado: ~70% fecha fora do 1σ e ~2 em cada 3 chegam a 1,5σ. <b>Passou de ±1,5σ</b>: ~80% fecha fora. A linha dourada é a situação de hoje. Medido nos futuros da CME (máximas e mínimas limpas)' + (R.sigma === 'DTCC' ? ', em 2 anos, com o mesmo σ das opções de balcão que o mapa usa; amostra menor que a do ouro, então os números variam alguns pontos.' : '; estável desde 2016.') + ' É estatística do que já aconteceu, não garantia.'; bx.appendChild(n);
      } } }
    $('.mp-resumo').innerHTML = `<b>Agora</b> (preço ${nf(P, k)}, faltam ${m.ts_dia_fim ? hrs(m.ts_dia_fim) : '—'} para fechar o dia): chance de chegar ao próximo nível acima ${fr1(up, '+')}; abaixo ${fr1(dn, '−')}.`;
    const inp = $('.mp-in'), out = $('.mp-out'); inp.placeholder = 'ex.: ' + nf(P * 1.004, k);
    inp.oninput = () => {
      const s0 = inp.value.trim(), cands = [parseFloat(s0.replace(/\./g, '').replace(',', '.')), parseFloat(s0.replace(/,/g, '.')), parseFloat(s0.replace(/,/g, ''))].filter((x) => x > 0);   // ponto/vírgula: fica a leitura mais perto do preço
      const v = cands.sort((x, y) => Math.abs(Math.log(x / P)) - Math.abs(Math.log(y / P)))[0]; if (!v) { out.textContent = ''; return; }
      const ch = (s, mx, mn, ini, fim) => { if (v >= P ? mx >= v : mn <= v) return 'já tocou'; return chAgora(v, s, ini, fim) + '%'; };
      out.textContent = 'chance de o preço chegar a ' + nf(v, k) + ' a partir de agora: hoje ' + ch(sd, mxd, mnd, m.ts_dia_ini, m.ts_dia_fim) + ' · nesta semana ' + ch(sw, m.max_sem, m.min_sem, m.ts_sem_ini, m.ts_sem_fim);
    };
    inp.oninput();
    // backtest diário: o que o painel projetou x o que aconteceu (dias e semanas já fechados, desde 13/11/2026)
    const vd = ((D('mi_validacao').data || [])[0]) || {}, vm = (vd.mapa || []).filter((r) => r.ativo === atv), vf = (vd.faixa || []).find((r) => r.ativo === atv);
    const lin = (r) => { if (!r) return ''; const n = r.niveis.filter((x) => x.k === 0.5 || x.k === 1);
      return `<b>${r.tipo === 'dia' ? 'Dias' : 'Semanas'}</b> (${r.n}): ` + n.map((x) => `±${nf(x.k, x.k % 1 ? 1 : 0)}σ previsto ${x.prev_cima}%/${x.prev_baixo}% · real ${nf(x.real_cima, 0)}%/${nf(x.real_baixo, 0)}%`).join(' — '); };
    const tx = [lin(vm.find((r) => r.tipo === 'dia')), lin(vm.find((r) => r.tipo === 'sem'))].filter(Boolean);
    if (vf) tx.push(`<b>Faixa das opções</b> (${vf.n} dias): fechou dentro de ±1σ em ${nf(vf.dentro_1s, 0)}% (esperado ~68%) e de ±2σ em ${nf(vf.dentro_2s, 0)}% (~95%)`);
    $('.mp-val').innerHTML = tx.length ? `<b>Conferência diária</b> (cima/baixo; atualizado ${vd.atualizado}): ` + tx.join('. ') + '. <span class="ajuda"><b>Como ler:</b> compara a chance que o painel mostrou com o que de fato aconteceu nos dias e semanas já fechados. Real perto do previsto = mapa confiável; muito acima = o preço anda mais que o esperado (níveis largos ficam mais alcançáveis); muito abaixo = mercado mais parado. Com menos de ~30 dias, ainda é amostra pequena.</span>' : '<b>Conferência diária:</b> acumulando (começa a mostrar depois do primeiro dia fechado).';
  }


  // cards do ativo selecionado (aparecem só quando há dado para ele)
  function drawAtv() {
    const mostra = (sel, ok) => { const e = $(sel); if (e) e.hidden = !ok; return ok; };
    const casas = (v) => { const s = String(v).split('.')[1]; return s ? Math.min(s.length, 5) : 2; };
    const lv = (txt, c) => { const s = document.createElement('span'); s.className = 'lv ' + c; s.textContent = txt; return s; };
    const cel = (tr, el, c) => { const e = document.createElement('td'); if (c) e.className = c; e.appendChild(el); tr.appendChild(e); return e; };
    // CTA
    const ct = (D('mi_cta').data || []).filter((r) => r.ativo === atv);
    if (mostra('.op-card.cta', ct.length)) { const c = $('.cta-t tbody'); c.replaceChildren();
      for (const r of ct) {
        const tr = document.createElement('tr'); td(tr, r.ativo);
        const p = td(tr, sg(r.posicao, 0, '%'), 'num ' + cls(r.posicao)); p.style.fontWeight = 600;
        const g = r.gatilho_proximo; td(tr, g ? nf(g.nivel, casas(g.nivel)) + ' (' + g.janela + ', ' + (g.lado > 0 ? 'abaixo vira venda' : 'acima vira compra') + ')' : '—');
        td(tr, g ? sg(g.dist_pct, 2) : '—', 'num'); c.appendChild(tr);
      } }
    // Regime
    const rr = (D('mi_regime').data || []).find((r) => r.ativo === atv);
    if (mostra('.op-card.rg', rr)) { const t = $('.rg-t tbody'); t.replaceChildren();
      for (const f of rr.fatores) {
        const tr = document.createElement('tr'); td(tr, f.fator + (f.fator === rr.principal ? ' ★' : '')).style.fontWeight = 600;
        td(tr, nf(f.corr26, 2), 'num ' + cls(f.corr26)); td(tr, f.corr52 == null ? '—' : nf(f.corr52, 2), 'num');
        td(tr, sg(f.beta, 2) + (f.fator === 'DXY' ? ' / +1%' : ' / +10 bps'), 'num');
        cel(tr, f.quebrou ? lv('⚠ quebrou', 'lv-cw') : lv(f.forca, f.forca === 'forte' ? 'lv-pw' : f.forca === 'média' ? 'lv-gf' : 'lv-now')); t.appendChild(tr);
      } }
    // Faixa das opções
    const fr = (D('mi_faixa').data || []).find((r) => r.ativo === atv);
    if (mostra('.mp-fx', fr)) { const t = $('.fx-t tbody'); t.replaceChildren(); const k = casas(fr.preco);
      const linha = (f) => { const tr = document.createElement('tr'); td(tr, f.prazo + ' (±' + nf(f.pct, 2) + '%)').style.fontWeight = 600;
        cel(tr, lv(nf(f.s1[0], k) + ' – ' + nf(f.s1[1], k), 'lv-s1'), 'num'); cel(tr, lv(nf(f.s2[0], k) + ' – ' + nf(f.s2[1], k), 'lv-s2'), 'num'); t.appendChild(tr); };
      const fonte = (txt) => { const tr = document.createElement('tr'); const e = td(tr, txt); e.colSpan = 3; e.style.fontSize = '12px'; e.style.color = 'var(--color-fg-muted)'; t.appendChild(tr); return e; };
      // linha da fonte: vol. de hoje contra a média, com a etiqueta e o que ela significa
      const f0 = fonte(fr.fonte + ' · vol. hoje ' + nf(fr.iv, 1) + '%'); const nv = fr.nivel;
      if (nv) { const cl = /bem acima/.test(nv.txt) ? 'lv-cw' : /acima/.test(nv.txt) ? 'lv-gf' : /abaixo/.test(nv.txt) ? 'lv-rg' : 'lv-now';
        const sig = /bem acima/.test(nv.txt) ? 'faixas largas' : /acima/.test(nv.txt) ? 'um pouco largas' : /bem abaixo/.test(nv.txt) ? 'faixas bem estreitas' : /abaixo/.test(nv.txt) ? 'faixas estreitas' : 'tamanho de sempre';
        f0.append(' contra a média ' + nf(nv.media, 1) + '% → ', lv(nv.txt, cl), ' ' + sig + ' (média 1a ' + nf(nv.m1, 1) + ' · 3a ' + nf(nv.m3, 1) + ' · 5a ' + nf(nv.m5, 1) + '%)'); }
      fr.faixas.forEach(linha);
      // precisão medida (backtest longo, mesmo método do painel): visível, sem precisar abrir o ?
      const bt = (D('faixa_backtest').data || {})[atv], bx = $('.fx-bt');
      const dt = bt && bt.dtcc && /DTCC/.test(fr.fonte || ''), B = dt ? bt.dtcc : bt;   // moedas com σ da DTCC: mostra a precisão medida com ela
      if (bx) { bx.replaceChildren(); if (bt) {
        const tit = document.createElement('div'); tit.className = 'fx-bt-t'; tit.innerHTML = '<b>Precisão medida</b> · quantas vezes o preço <b>fechou dentro</b> da faixa (' + (atv === 'XAUUSD' ? 'GVZ' : atv === 'NAS100' ? 'VXN' : dt ? 'opções de balcão DTCC' : 'vol. 21d × 1,09') + ', desde ' + B.dia.desde + ', ' + nf(B.dia.n, 0) + ' dias)'; bx.appendChild(tit);
        const tb = document.createElement('table'); tb.className = 'op-table'; tb.innerHTML = '<thead><tr><th>Prazo</th><th class="num"><span class="lv lv-s1">±1σ</span><br><small>ideal 68%</small></th><th class="num"><span class="lv lv-s2">±2σ</span><br><small>ideal 95%</small></th><th class="num">Nem tocou<br><small>±1σ</small></th><th class="num">Ano<br><small>±1σ</small></th></tr></thead>';
        const bd = document.createElement('tbody'); tb.appendChild(bd);
        for (const p of ['dia', 'semana', 'mês']) { const r = B[p]; if (!r) continue; const tr = document.createElement('tr'); td(tr, p).style.fontWeight = 600;
          td(tr, nf(r.s1, 0) + '%', 'num').style.fontWeight = 700; td(tr, nf(r.s2, 0) + '%', 'num').style.fontWeight = 700; td(tr, r.nunca_saiu_s1 == null ? '—' : nf(r.nunca_saiu_s1, 0) + '%', 'num'); td(tr, r.s1_ano ? r.s1_ano[0] + '–' + r.s1_ano[1] + '%' : '—', 'num'); bd.appendChild(tr); }
        const w = document.createElement('div'); w.className = 'tbl-x'; w.appendChild(tb); bx.appendChild(w); } }
    }
    // call wall e put wall da CME (ouro e iene): fixas desde a chegada do boletim; referência, sem teste
    const w = (D('mi_paredes').data || []).find((r) => r.ativo === atv);
    if (mostra('.op-card.pw', w)) { const t = $('.pw-t tbody'); t.replaceChildren(); const cs = atv === 'XAUUSD' ? 0 : 3;
      const dm = (s) => br(s).slice(0, 5);
      $('.pw-chip').textContent = w.sem_dado ? 'sem dado' : 'referência, sem teste · boletim de ' + dm(w.pregao) + ' · fixas desde ' + w.fixado_em;
      const lin = (nome, c, valor, det) => { const tr = document.createElement('tr'); if (c) cel(tr, lv(nome, c)); else td(tr, nome); td(tr, valor, 'num').style.fontWeight = 700; td(tr, det); t.appendChild(tr); };
      if (w.sem_dado) { const tr = document.createElement('tr'); td(tr, 'Sem dado: ' + w.sem_dado); t.appendChild(tr); }
      else {
        const det = (x) => 'strike ' + (atv === 'XAUUSD' ? nf(x.strike, 0) : nf(x.strike * 1e6, 0) + ' (iene)') + ' · ' + nf(x.oi, 0) + ' contratos';
        const lado = (l, nome, c) => { const x = w[l], r = w['rompida_' + l], x2 = w[l + '2'], out = [];
          out.push([nome, c, x ? nf(x.nivel, cs) : 'sem dado', x ? det(x) + (r ? ' · ROMPIDA em ' + r.hora + ' (preço ' + nf(r.preco, cs) + ')' : '') : 'nenhum contrato dentro de 1σ da semana']);
          if (r) out.push(['2ª ' + nome.toLowerCase(), c, x2 ? nf(x2.nivel, cs) : '—', x2 ? det(x2) : 'nenhuma outra dentro de 1σ da semana']);
          return out; };
        const linhas = [...lado('call', 'Call wall', 'lv-cw'), [NOME[atv] + ' agora', 'lv-now', nf(w.preco, cs), ''], ...lado('put', 'Put wall', 'lv-pw')];
        const num = (x) => parseFloat(String(x[2]).replace(/\./g, '').replace(',', '.'));
        linhas.sort((a, b) => (isNaN(num(b)) ? -1e12 : num(b)) - (isNaN(num(a)) ? -1e12 : num(a))).forEach((x) => lin(...x));
      }
    }
  }

  // ---------------------------------------------------------------- ajuda: "Como ler" e explicações ficam escondidos; botão "?" em cada card e um geral no topo
  function prepAjuda() {
    document.querySelectorAll('.op-card h2').forEach((h) => { if (h.querySelector(':scope > .h2-t')) return; const s = document.createElement('span'); s.className = 'h2-t'; while (h.firstChild) s.appendChild(h.firstChild); h.appendChild(s); });
    const eAjuda = (e) => e.matches('.mi-exp, .fx-ler, .mi-how') || (e.matches('p.op-note') && (/^(Como ler|Como funciona|Contratos por strike|Contratos em aberto por strike)/.test(e.textContent.trim()) || (e.classList.length === 1 && e.textContent.trim().length > 60)))   // texto fixo longo = explicação;
    document.querySelectorAll('.mi-exp, .fx-ler, .mi-how, p.op-note').forEach((e) => { if (eAjuda(e)) e.classList.add('ajuda'); });
    document.querySelectorAll('.op-card, .rd-c').forEach((c) => {
      const minha = [...c.querySelectorAll('.ajuda')].filter((a) => a.closest('.op-card, .rd-c') === c || (c.matches('.radar') && a.closest('.op-card') === c));
      if (!minha.length || c.querySelector(':scope > .ag-top .aj-bt, :scope > .tl-h .aj-bt, :scope .aj-bt-own')) return;
      const b = document.createElement('button'); b.type = 'button'; b.className = 'aj-bt aj-bt-own'; b.textContent = '?'; b.title = 'Como ler'; b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', () => { const on = c.classList.toggle('abre'); b.setAttribute('aria-pressed', String(on)); });
      const lugar = c.querySelector(':scope > .ag-top, :scope > .tl-h, :scope > .ia-h') || c.querySelector(':scope > h2, :scope > .tl-k');
      if (lugar && lugar.matches('.ag-top, .tl-h, .ia-h')) { const t0 = lugar.firstElementChild; if (t0 && t0.matches('h2')) t0.appendChild(b); else t0 ? t0.after(b) : lugar.appendChild(b); }   // ? colado no título (quebra junto com ele)
      else if (lugar) { const w = document.createElement('div'); w.className = 'ag-top'; lugar.before(w); w.append(lugar, b); }
      else c.prepend(b);
    });
    const g = $('.aj-geral'); const set = (on) => { document.body.classList.toggle('ver-ajuda', on); if (g) g.setAttribute('aria-pressed', String(on)); try { localStorage.setItem('verAjuda', on ? '1' : ''); } catch (e) {} };
    if (g) g.addEventListener('click', () => { set(!document.body.classList.contains('ver-ajuda')); drawAll(); });
    try { set(!!localStorage.getItem('verAjuda')); } catch (e) {}
    document.querySelectorAll('details.mais').forEach((d) => d.addEventListener('toggle', () => { if (d.open) drawAll(); }));   // gráficos escondidos desenham ao abrir
  }
  prepAjuda();
  document.querySelectorAll('table.op-table').forEach((t) => { if (t.closest('.op-tablebox, .tbl-x')) return; const w = document.createElement('div'); w.className = 'tbl-x'; t.before(w); w.appendChild(t); });   // tabela larga rola dentro do card, nunca vaza

  window.APP = { D, nf, sg, br, td, tip, show, axisStyle, COLORS, $ };
  function drawAll() { drawGB(); if (!$('#sec-mi').hidden) { drawMI(); drawRadar(); drawDJ(); } drawAI(); }
  let rz; window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(drawAll, 150); });
  // atualização automática: dados a cada 2 min; ao voltar para a tela (celular/aba em segundo plano), na hora;
  // versão nova do site publicada → recarrega sozinho (mantém o ativo escolhido, guardado no navegador)
  let ultLoad = 0; const carrega = () => { ultLoad = Date.now(); return load(); };
  const versao = (document.querySelector('script[src*="app.js"]') || {}).src || '';
  const confereVersao = async () => { try { const h = await (await fetch('index.html?t=' + Date.now(), { cache: 'no-store' })).text();
    const m = h.match(/app\.js\?v=[^"']+/); if (m && versao && !versao.includes(m[0])) location.reload(); } catch (e) {} };
  document.addEventListener('visibilitychange', () => { if (!document.hidden) { if (Date.now() - ultLoad > 60000) carrega(); confereVersao(); } });
  setInterval(() => { if (!document.hidden) confereVersao(); }, 10 * 60 * 1000);
  carrega().then(() => { liveTick(); surpTick(); aiTick(); }); setInterval(carrega, 2 * 60 * 1000); setInterval(surpTick, 10 * 60 * 1000); setInterval(aiTick, 10 * 60 * 1000);
})();
