(() => {
  const { D, nf, sg, br, td, tip, show, axisStyle, COLORS, $ } = window.APP;
  let sub = 'eur';
  const fmtK = (v) => (v == null || isNaN(v) ? '—' : Number(v).toFixed(4).replace('.', ','));
  const fmtN = (v) => Number(v).toLocaleString('pt-BR');
  document.querySelectorAll('.op-sub button').forEach((b) => b.addEventListener('click', () => {
    sub = b.dataset.o; document.querySelectorAll('.op-sub button').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); window.drawOP();
  }));
  document.querySelectorAll('.op-copy').forEach((b) => b.addEventListener('click', () => {
    const box = $(b.dataset.c); const ok = () => { b.textContent = 'Copiado'; setTimeout(() => { b.textContent = 'Copiar código'; }, 1800); };
    const selc = () => { const r = document.createRange(); r.selectNodeContents(box); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = 'Selecionado: use Ctrl+C'; };
    if (navigator.clipboard) navigator.clipboard.writeText(box.textContent).then(ok).catch(selc); else selc();
  }));
  const tile = (box, lab, val, sub2, cls) => {
    const d = document.createElement('div'); d.className = 'op-card op-tile';
    const a = document.createElement('span'); a.className = 's'; a.textContent = lab;
    const v = document.createElement('span'); v.className = 'v'; v.textContent = val; if (cls) v.style.color = cls;
    const s = document.createElement('span'); s.className = 's'; s.textContent = sub2 || '';
    d.append(a, v, s); box.appendChild(d);
  };

  // ---------------- cálculos do euro (mesma lógica do painel do Claude)
  // ---------------- cálculo genérico (euro e ouro): paredes, gamma (Black-76) e código do TradingView
  const MES3 = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
  // vencimento como data (opções semanais: "2026-11-13"); senão código mensal ("DEC26")
  const venData = (v) => (/^\d{4}-\d{2}-\d{2}$/.test(String(v)) ? new Date(String(v) + 'T21:00:00Z') : null);
  const venEur = (v) => { const dd = venData(v); if (dd) return dd; return venEur0(v); };
  const venEur0 = (v) => { const mm = MES3.indexOf(String(v).slice(0, 3)); const y = 2000 + Number(String(v).slice(3)); const wd = new Date(Date.UTC(y, mm, 1)).getUTCDay(); return new Date(Date.UTC(y, mm, 1 + ((3 - wd + 7) % 7) + 2)); };
  // ouro (OG): 4 dias úteis antes do fim do mês anterior ao do contrato
  const venOuro = (v) => { const dd = venData(v); if (dd) return dd; return venOuro0(v); };
  const venOuro0 = (v) => { const mm = MES3.indexOf(String(v).slice(0, 3)); const y = 2000 + Number(String(v).slice(3)); let d = new Date(Date.UTC(y, mm, 0)); let n = 0;
    while (true) { if (d.getUTCDay() % 6 !== 0) { if (n === 4) return d; n++; } d = new Date(d.getTime() - 864e5); } };
  function calcGamma(cad, cfg) {
    const ninv = (p) => { let lo = -8, hi = 8; for (let i = 0; i < 80; i++) { const mid = (lo + hi) / 2; const z = Math.abs(mid) / Math.SQRT2; const k = 1 / (1 + 0.3275911 * z); const e = 1 - (((((1.061405429 * k - 1.453152027) * k) + 1.421413741) * k - 0.284496736) * k + 0.254829592) * k * Math.exp(-z * z); const c = 0.5 * (1 + (mid < 0 ? -e : e)); if (c < p) lo = mid; else hi = mid; } return (lo + hi) / 2; };
    const phi = (x) => Math.exp(-x * x / 2) / Math.sqrt(2 * Math.PI);
    const rows0 = cad.map((r) => ({ ...r, strike: Number(r.strike), oi: Number(r.oi), futuro: Number(r.futuro), delta: r.delta == null || r.delta === '' ? null : Number(r.delta) }));
    const gam = { rows: [], flip: null, kx: null, ky: null }; if (!rows0.length) return gam;
    const today = new Date(String(rows0[0].data_pregao).slice(0, 10) + 'T00:00:00Z'); const vencs = {};
    for (const r of rows0) if (!vencs[r.venc]) vencs[r.venc] = { F: r.futuro, T: Math.max(1 / 365, (cfg.venc(r.venc) - today) / (365 * 864e5)), iv: [] };
    for (const r of rows0) {
      const g = vencs[r.venc]; const otm = (r.tipo === 'Call' && r.strike >= g.F) || (r.tipo === 'Put' && r.strike <= g.F);
      if (!otm || r.delta == null || r.delta < 0.05 || r.delta > 0.40) continue;
      const x = ninv(r.tipo === 'Call' ? r.delta : 1 - r.delta); const L = Math.log(g.F / r.strike); const disc = x * x - 2 * L; if (disc < 0) continue;
      const s = L < 0 ? x + Math.sqrt(disc) : x - Math.sqrt(disc); if (s > 0) g.iv.push([r.strike, s / Math.sqrt(g.T)]);
    }
    const sig = (g, K) => { const a = g.iv.sort((p, q) => p[0] - q[0]); if (!a.length) return cfg.vol; if (K <= a[0][0]) return a[0][1]; if (K >= a[a.length - 1][0]) return a[a.length - 1][1]; for (let i = 1; i < a.length; i++) if (K <= a[i][0]) return a[i - 1][1] + (a[i][1] - a[i - 1][1]) * (K - a[i - 1][0]) / (a[i][0] - a[i - 1][0]); return cfg.vol; };
    const legs = rows0.filter((r) => r.oi > 0).map((r) => { const g = vencs[r.venc]; return { K: r.strike, oi: r.oi, sgn: r.tipo === 'Call' ? 1 : -1, T: g.T, s: sig(g, r.strike) }; });
    const gamL = (S, l) => { const v = l.s * Math.sqrt(l.T); const d1 = (Math.log(S / l.K) + 0.5 * v * v) / v; return l.sgn * l.oi * phi(d1) / (S * v) * cfg.mult * S * S * 0.01; };
    const gex = (S) => legs.reduce((a, l) => a + gamL(S, l), 0);
    const F = Math.max(...Object.values(vencs).map((g) => g.F)); const rd = (x) => Number(x.toFixed(cfg.casas));
    for (let i = -60; i <= 60; i++) { const S = rd(F + i * cfg.passo); gam.rows.push({ preco: S, gex: gex(S) }); }
    let best = Infinity;
    for (let i = 1; i < gam.rows.length; i++) { const a = gam.rows[i - 1], b = gam.rows[i]; if ((a.gex <= 0) !== (b.gex <= 0)) { const x = a.preco + (b.preco - a.preco) * (0 - a.gex) / (b.gex - a.gex); if (Math.abs(x - F) < best) { best = Math.abs(x - F); gam.flip = rd(x); } } }
    const byK = new Map(); for (const l of legs) byK.set(l.K, (byK.get(l.K) || 0) + gamL(F, l));
    let vx = -Infinity, vy = Infinity; for (const [k, v] of byK) { if (v > vx) { vx = v; gam.kx = k; } if (v < vy) { vy = v; gam.ky = k; } }
    return gam;
  }
  // ouro: tudo calculado dos dados brutos (cadeia da CME + ETFs); sem eles, usa os arquivos antigos
  function calcOuro() {
    let cad = D('ouro_cadeia').status === 'ok' ? D('ouro_cadeia').data : []; const bol = D('ouro_boletim').status === 'ok' ? D('ouro_boletim').data[0] : null;
    if (!cad.length || !bol) return null;
    const perto = faixa('XAUUSD', Number(bol.futuro), 300); cad = cad.filter((r) => perto(r.strike));
    const m = new Map(); const add = (k, c, v) => { k = Number(k); if (!m.has(k)) m.set(k, { strike: k, cme_call: 0, cme_put: 0, etf_call: 0, etf_put: 0 }); m.get(k)[c] += Number(v) || 0; };
    for (const r of cad) add(r.strike, r.tipo === 'Call' ? 'cme_call' : 'cme_put', r.oi);
    for (const r of (D('ouro_etf').status === 'ok' ? D('ouro_etf').data : []).filter((x) => perto(x.strike))) { add(Math.round(Number(r.strike) / 5) * 5, 'etf_call', r.call); add(Math.round(Number(r.strike) / 5) * 5, 'etf_put', r.put); }
    const ps = [...m.values()].sort((a, b) => b.strike - a.strike);
    const top = (k) => ps.reduce((a, b) => (b[k] > (a ? a[k] : -1) ? b : a), null);
    const gam = calcGamma(cad, { venc: venOuro, vol: 0.2, mult: 100, passo: 5, casas: 1 });
    const pick = (key, tag, n) => ps.filter((r) => r[key] > 0).sort((a, b) => b[key] - a[key]).slice(0, n).map((r) => tag + ' ' + r.strike + ' ' + r[key]);
    const extra = []; if (gam.flip != null) extra.push('Z ' + gam.flip.toFixed(1)); if (gam.kx != null) extra.push('X ' + gam.kx); if (gam.ky != null) extra.push('Y ' + gam.ky);
    return { bol, ps, gam, cC: top('cme_call'), cP: top('cme_put'), eC: top('etf_call'), eP: top('etf_put'),
      codigo: [...pick('cme_call', 'C', 12), ...pick('cme_put', 'P', 12), ...pick('etf_call', 'K', 8), ...pick('etf_put', 'Q', 8), ...extra].join(' | ') };
  }

  // só strikes perto do preço: futuro ± 6 × ATR14 (mínimo 300 pips no euro, US$ 300 no ouro)
  const faixa = (ativo, F, minimo) => { const a = (D('mi_ativos').data || []).find((r) => r.ativo === ativo); const w = Math.max(minimo, 6 * ((a && a.atr14) || 0)); return (k) => Math.abs(Number(k) - F) <= w; };
  function calcEur() {
    const bol0 = (D('op_boletim').data || [])[0]; const F0 = bol0 ? Number(bol0.futuro) : null; const perto = F0 ? faixa('EURUSD', F0, 0.03) : () => true;
    const par = D('op_paredes').data.filter((r) => perto(r.strike)), cad = D('op_cadeia').data.filter((r) => perto(r.strike));
    const m = new Map();
    for (const r of par) { const k = Number(r.strike); if (!m.has(k)) m.set(k, { strike: k, call: 0, put: 0 }); const o = m.get(k); if (r.tipo === 'Call') o.call += Number(r.open_interest); else o.put += Number(r.open_interest); }
    const ps = [...m.values()].sort((a, b) => b.strike - a.strike);
    const top = (k) => ps.reduce((a, b) => (b[k] > (a ? a[k] : -1) ? b : a), null);
    const gam = calcGamma(cad, { venc: venEur, vol: 0.07, mult: 125000, passo: 0.0005, casas: 4 });
    const pick = (key, tag) => ps.filter((r) => r[key] > 0).sort((a, b) => b[key] - a[key]).slice(0, 12).map((r) => tag + ' ' + r.strike.toFixed(4) + ' ' + r[key]);
    const extra = []; if (gam.flip != null) extra.push('Z ' + gam.flip.toFixed(4)); if (gam.kx != null) extra.push('X ' + gam.kx.toFixed(4)); if (gam.ky != null) extra.push('Y ' + gam.ky.toFixed(4));
    return { ps, c: top('call'), p: top('put'), gam, codigo: [...pick('call', 'C'), ...pick('put', 'P'), ...extra].join(' | ') };
  }

  function linha(el, rows, flip, fut, fmt) {
    el.replaceChildren(); if (!rows.length) return;
    const W = Math.max(280, el.clientWidth), H = 220, m = { t: 12, r: 10, b: 24, l: 10 };
    const xs = d3.scaleLinear(d3.extent(rows, (d) => d.preco), [m.l, W - m.r]); const e = d3.max(rows, (d) => Math.abs(d.gex)) || 1; const ys = d3.scaleLinear([-e, e], [H - m.b, m.t]);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`);
    svg.append('rect').attr('x', m.l).attr('width', W - m.l - m.r).attr('y', m.t).attr('height', ys(0) - m.t).style('fill', 'var(--color-ok)').style('opacity', 0.05);
    svg.append('rect').attr('x', m.l).attr('width', W - m.l - m.r).attr('y', ys(0)).attr('height', H - m.b - ys(0)).style('fill', 'var(--color-bad)').style('opacity', 0.05);
    svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', ys(0)).attr('y2', ys(0)).style('stroke', 'var(--cds-chart-axis)');
    svg.append('path').datum(rows).attr('d', d3.line().x((d) => xs(d.preco)).y((d) => ys(d.gex))).style('fill', 'none').style('stroke', COLORS[0]).style('stroke-width', 2);
    const mark = (v, txt, dy) => { if (v == null || isNaN(v)) return; svg.append('line').attr('x1', xs(v)).attr('x2', xs(v)).attr('y1', m.t).attr('y2', H - m.b).style('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '4 4'); const left = xs(v) > W - 110; svg.append('text').attr('x', xs(v) + (left ? -4 : 4)).attr('y', m.t + dy).attr('text-anchor', left ? 'end' : 'start').style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text(txt + ' ' + fmt(v)); };
    mark(flip, 'flip', 10); mark(fut, 'futuro', 24);
    svg.append('text').attr('x', m.l + 2).attr('y', m.t + 10).style('fill', 'var(--color-ok)').style('font-size', '11px').text('gamma + (segura)');
    svg.append('text').attr('x', m.l + 2).attr('y', H - m.b - 4).style('fill', 'var(--color-bad)').style('font-size', '11px').text('gamma − (acelera)');
    axisStyle(svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(xs).ticks(Math.max(2, Math.floor(W / 100))).tickFormat(fmt)));
    const t = tip(el);
    svg.append('rect').attr('x', m.l).attr('y', m.t).attr('width', W - m.l - m.r).attr('height', H - m.t - m.b).attr('fill', 'transparent')
      .on('mousemove', (ev) => { const p = xs.invert(d3.pointer(ev, svg.node())[0]); const n = rows.reduce((a, b) => (Math.abs(b.preco - p) < Math.abs(a.preco - p) ? b : a)); show(el, t, ev, ['Preço ' + fmt(n.preco), 'Gamma ' + (n.gex / 1e6).toLocaleString('pt-BR', { maximumFractionDigits: 0 }) + ' mi US$ por 1%']); })
      .on('mouseleave', () => { t.hidden = true; });
  }

  function borboleta(el, data, fut, fmt, seg) {
    el.replaceChildren(); if (!data.length) return;
    const W = Math.max(280, el.clientWidth), rowH = data.length > 40 ? 15 : 20, m = { t: 6, b: 22 }, lab = 58;
    const H = m.t + m.b + data.length * rowH; const half = (W - lab) / 2 - 6; const cx = W / 2;
    const mx = d3.max(data, (d) => Math.max(...seg.map((s) => s.call(d)), ...seg.map((s) => s.put(d)))) || 1;
    const tot = (d, k) => seg.reduce((a, s) => a + s[k](d), 0);
    const mx2 = d3.max(data, (d) => Math.max(tot(d, 'call'), tot(d, 'put'))) || mx;
    const x = d3.scaleLinear([0, mx2], [0, half]); const y = d3.scaleBand(data.map((d) => d.k), [m.t, H - m.b]).padding(0.2);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`); const t = tip(el);
    for (const d of data) {
      const yy = y(d.k), bh = y.bandwidth(); let oc = 0, op = 0;
      for (const s of seg) {
        const c = s.call(d), p = s.put(d);
        if (c) svg.append('rect').attr('x', cx + lab / 2 + x(oc)).attr('y', yy).attr('width', x(c)).attr('height', bh).attr('rx', 2).style('fill', s.corC);
        if (p) svg.append('rect').attr('x', cx - lab / 2 - x(op) - x(p)).attr('y', yy).attr('width', x(p)).attr('height', bh).attr('rx', 2).style('fill', s.corP);
        oc += c; op += p;
      }
      svg.append('text').attr('x', cx).attr('y', yy + bh / 2).attr('dy', '0.35em').attr('text-anchor', 'middle').style('fill', 'var(--color-fg)').style('font-size', '11px').style('font-variant-numeric', 'tabular-nums').text(fmt(d.k));
      svg.append('rect').attr('x', 0).attr('y', yy).attr('width', W).attr('height', bh).attr('fill', 'transparent')
        .on('mousemove', (ev) => show(el, t, ev, ['Strike ' + fmt(d.k), 'Calls: ' + fmtN(tot(d, 'call')), 'Puts: ' + fmtN(tot(d, 'put'))])).on('mouseleave', () => { t.hidden = true; });
    }
    if (fut != null) { const ks = data.map((d) => d.k); for (let i = 0; i < ks.length - 1; i++) if (ks[i] >= fut && ks[i + 1] <= fut) { const a = y(ks[i]) + y.bandwidth() / 2, b = y(ks[i + 1]) + y.bandwidth() / 2; const yy = a + (b - a) * (ks[i] - fut) / (ks[i] - ks[i + 1]); svg.append('line').attr('x1', 0).attr('x2', W).attr('y1', yy).attr('y2', yy).style('stroke', 'var(--cds-chart-reference)').attr('stroke-dasharray', '4 4'); svg.append('text').attr('x', W).attr('y', yy - 3).attr('text-anchor', 'end').style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text('futuro ' + fmt(fut)); } }
    svg.append('text').attr('x', 0).attr('y', H - 5).style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text('← puts');
    svg.append('text').attr('x', W).attr('y', H - 5).attr('text-anchor', 'end').style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text('calls →');
  }

  window.drawOP = () => {
    $('#op-eur').hidden = sub !== 'eur'; $('#op-xau').hidden = sub !== 'xau';
    if (sub === 'eur') {
      if (D('op_paredes').status !== 'ok' || D('op_cadeia').status !== 'ok') return;
      const bol = D('op_boletim').status === 'ok' ? D('op_boletim').data[0] : null; const E = calcEur();
      $('.op-dt').textContent = bol ? 'Euro: pregão de ' + br(bol.data_pregao) + ' (' + String(bol.situacao).toLowerCase() + ').' : '';
      $('.op-take').textContent = bol ? 'Euro: maior call wall em ' + fmtK(E.c && E.c.strike) + ' e maior put wall em ' + fmtK(E.p && E.p.strike) + '; gamma flip em ' + fmtK(E.gam.flip) + ' com o futuro em ' + fmtK(bol.futuro) + ' (' + (bol.futuro < E.gam.flip ? 'abaixo do flip: o hedge acelera' : 'acima do flip: o hedge segura') + ').' : '—';
      const tb = $('.op-tiles-eur'); tb.replaceChildren();
      tile(tb, 'Pregão lido', bol ? br(bol.data_pregao) : '—', bol ? bol.situacao + ' · os dados abaixo são deste pregão' : '');
      tile(tb, 'Futuro de euro (' + (bol ? bol.futuro_vencimento : '') + ')', bol ? fmtK(bol.futuro) : '—', 'referência do EURUSD');
      tile(tb, 'Maior call wall', fmtK(E.c && E.c.strike), (E.c ? fmtN(E.c.call) : '—') + ' contratos · resistência (USDCHF: suporte)', 'var(--color-ok)');
      tile(tb, 'Maior put wall', fmtK(E.p && E.p.strike), (E.p ? fmtN(E.p.put) : '—') + ' contratos · suporte (USDCHF: resistência)', 'var(--color-bad)');
      $('.op-code-eur').textContent = E.codigo || '—';
      const gt = $('.op-gtiles'); gt.replaceChildren();
      tile(gt, 'Gamma flip', fmtK(E.gam.flip), 'acima segura, abaixo acelera'); tile(gt, 'Gamma + máximo', fmtK(E.gam.kx), 'strike que mais segura', 'var(--color-ok)'); tile(gt, 'Gamma − máximo', fmtK(E.gam.ky), 'strike que mais acelera', 'var(--color-bad)');
      linha($('.op-gchart'), E.gam.rows, E.gam.flip, bol ? bol.futuro : null, fmtK);
      borboleta($('.op-bfly'), E.ps.map((r) => ({ k: r.strike, call: r.call, put: r.put })), bol ? Number(bol.futuro) : null, fmtK, [{ call: (d) => d.call, put: (d) => d.put, corC: 'var(--color-ok)', corP: 'var(--color-bad)' }]);
      const MES = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
      const ord = (v) => Number(String(v).slice(3)) * 12 + MES.indexOf(String(v).slice(0, 3));
      const pt = $('.op-par-t tbody'); pt.replaceChildren();
      for (const r of [...D('op_paredes').data].sort((a, b) => (a.vencimento === b.vencimento ? (a.tipo === b.tipo ? b.open_interest - a.open_interest : a.tipo.localeCompare(b.tipo)) : ord(a.vencimento) - ord(b.vencimento)))) {
        const tr = document.createElement('tr'); const c = r.tipo === 'Call' ? 'mi-pos' : 'mi-neg';
        td(tr, r.vencimento); td(tr, r.tipo, c); td(tr, fmtK(r.strike), 'num'); td(tr, fmtN(r.open_interest), 'num'); td(tr, Number(r.variacao) === 0 ? 'sem mudança' : sg(r.variacao, 0, ''), 'num'); td(tr, r.leitura_usdchf, c); pt.appendChild(tr);
      }
    } else {
      // dados novos (cadeia bruta) -> tudo calculado aqui; sem eles, arquivos antigos de resumo
      const O = calcOuro(); let X;
      if (O) {
        X = { dp: O.bol.data_pregao, sit: O.bol.situacao, F: Number(O.bol.futuro), venc: O.bol.futuro_vencimento, cC: O.cC && O.cC.strike, cP: O.cP && O.cP.strike, eC: O.eC && O.eC.strike, eP: O.eP && O.eP.strike,
          flip: O.gam.flip, gx: O.gam.kx, gn: O.gam.ky, codigo: O.codigo, par: O.ps, gamma: O.gam.rows };
      } else {
        if (D('ouro_resumo').status !== 'ok') return;
        const R = D('ouro_resumo').data[0]; const GX = (D('ouro_gamma').status === 'ok' ? D('ouro_gamma').data : []).map((r) => ({ preco: Number(r.preco), gex: Number(r.gex) }));
        const gmax = GX.length ? GX.reduce((a, b) => (b.gex > a.gex ? b : a)) : null, gmin = GX.length ? GX.reduce((a, b) => (b.gex < a.gex ? b : a)) : null;
        const base = String(R.codigo || '').split(' | ').filter((x) => x && !/^[ZXY] /.test(x));
        if (R.flip != null) base.push('Z ' + Number(R.flip).toFixed(1)); if (gmax) base.push('X ' + gmax.preco.toFixed(1)); if (gmin) base.push('Y ' + gmin.preco.toFixed(1));
        X = { dp: R.data_pregao, sit: R.situacao, F: Number(R.futuro_dec), venc: 'DEC26', cC: R.maior_call_cme, cP: R.maior_put_cme, eC: R.maior_call_etf, eP: R.maior_put_etf,
          flip: Number(R.flip), gx: gmax && gmax.preco, gn: gmin && gmin.preco, codigo: base.join(' | '), par: D('ouro_paredes').status === 'ok' ? D('ouro_paredes').data : [], gamma: GX };
      }
      const n0 = (v) => nf(v, 1);
      $('.op-dt').textContent = 'Ouro: pregão de ' + br(X.dp) + ' (' + X.sit + ').';
      $('.op-take').textContent = 'Ouro: futuro (' + X.venc + ') em ' + n0(X.F) + ', gamma flip em ' + n0(X.flip) + ' (' + (X.F < X.flip ? 'abaixo do flip: o hedge acelera' : 'acima do flip: o hedge segura') + ').';
      const tb = $('.op-tiles-xau'); tb.replaceChildren();
      tile(tb, 'Pregão lido', br(X.dp), X.sit + ' · os dados abaixo são deste pregão');
      tile(tb, 'Futuro de ouro (' + X.venc + ')', n0(X.F), 'referência do XAUUSD');
      tile(tb, 'Maior call wall (CME)', n0(X.cC), 'resistência', 'var(--color-ok)'); tile(tb, 'Maior put wall (CME)', n0(X.cP), 'suporte', 'var(--color-bad)');
      tile(tb, 'Maior call · put GLD+IAU', n0(X.eC), 'put ' + n0(X.eP) + ' · ETFs convertidos para o preço do ouro');
      const xg = $('.op-xgtiles'); xg.replaceChildren();
      tile(xg, 'Gamma flip', n0(X.flip), 'acima segura, abaixo acelera'); tile(xg, 'Gamma + máximo', n0(X.gx), 'onde o hedge mais segura', 'var(--color-ok)'); tile(xg, 'Gamma − máximo', n0(X.gn), 'onde o hedge mais acelera', 'var(--color-bad)');
      $('.op-code-xau').textContent = X.codigo || '—';
      const F = X.F; const m = new Map();
      for (const r of X.par) {
        const k = Number(r.strike); if (Math.abs(k / F - 1) > 0.10) continue; const b = Math.round(k / 25) * 25;
        if (!m.has(b)) m.set(b, { k: b, cme_call: 0, cme_put: 0, etf_call: 0, etf_put: 0 }); const o = m.get(b); for (const c of ['cme_call', 'cme_put', 'etf_call', 'etf_put']) o[c] += Number(r[c]) || 0;
      }
      borboleta($('.op-xmap'), [...m.values()].sort((a, b) => b.k - a.k), F, (v) => nf(v, 0),
        [{ call: (d) => d.cme_call, put: (d) => d.cme_put, corC: COLORS[0], corP: COLORS[0] }, { call: (d) => d.etf_call, put: (d) => d.etf_put, corC: COLORS[2], corP: COLORS[2] }]);
      linha($('.op-xg'), X.gamma, X.flip, F, (v) => nf(v, 0));
    }
  };
})();
