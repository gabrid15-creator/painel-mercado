// Card "Ouro — diagnóstico do dia" (vem do Laboratório; só o que passou na validação de 06/11/2026).
// Para remover: apagar este arquivo, a <section id="ouro-dia"> e a linha <script src="ouro-dia.js"> do index.html.
(() => {
  const B = 'https://raw.githubusercontent.com/gabrid15-creator/painel-mercado/lab-dados/';
  const el = document.getElementById('ouro-dia'); if (!el) return;
  const nf = (v, d = 1) => v == null ? '–' : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const get = f => fetch(B + f + '?t=' + Date.now(), { cache: 'no-store' }).then(r => r.ok ? r.json() : null).catch(() => null);
  function draw(j, I) {
    if (!j) { el.querySelector('.od-txt').textContent = 'Sem dados do laboratório ainda.'; return; }
    const dNY = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
    const hoje = I && I.p != null && I.atualizado && I.atualizado.slice(0, 10) === dNY;
    const p = hoje ? I.p : (j.evento_data === dNY ? j.p0 : null);
    const base = j.base_pct || 9.5, ev = j.evento_data === dNY ? j.evento : null;
    if (p == null) { el.querySelector('.od-txt').textContent = 'Aguardando dados de hoje.'; return; }
    const cls = p >= 25 ? 'bad' : p >= 12 ? 'warn' : 'ok';
    const tag = p >= 25 ? '🔴 não operar contra' : p >= 12 ? '🟡 cautela' : '🟢 bom p/ reversão';
    let t = p >= 25 ? '<b>Alta chance de dia de tendência.</b> Não tente pegar topo/fundo; só a favor ou fora.'
      : p >= 12 ? '<b>Chance de tendência acima do normal.</b> Mão menor e reversão só com confluência forte.'
      : '<b>Dia com cara de lateral/reversão.</b> Chance de tendência abaixo do normal.';
    if (hoje && I.p_hora >= 8 && Math.abs(I.mov_atr) >= 0.3) t += ' Se virar tendência, deve ser de <b>' + I.direcao + '</b> (o dia fecha no sentido da manhã em ~97% dos dias de tendência).';
    if (ev === 'NFP') t += ' Hoje tem payroll (8h30 NY).'; else if (ev === 'FOMC') t += ' Hoje tem FOMC (14h NY): range costuma ser maior, com chicote.';
    el.querySelector('.od-n').textContent = nf(p, 0) + '%';
    el.querySelector('.od-tag').className = 'tl-chip od-tag ' + cls; el.querySelector('.od-tag').textContent = tag;
    el.style.borderLeft = '4px solid var(--color-' + cls + ')';
    el.querySelector('.od-txt').innerHTML = t;
    el.querySelector('.od-det').textContent = 'Chance de dia de tendência (normal ' + nf(base, 0) + '%) · ' + (hoje && I.p_hora ? 'calculada com o movimento até ' + I.hora_ny + ' NY' : 'pré-mercado (véspera + calendário)') + ' · mão sugerida ' + nf(j.mao.mult, 2) + '× · VRP ' + nf(j.vrp, 2) + ' · GVZ 5 dias ' + (j.gvz_var5 > 0 ? '+' : '') + nf(j.gvz_var5) + '%';
  }
  // Janelas institucionais (out/2020–out/2026, XAUUSD M1): chance do minuto ser topo/fundo de ±60 min x média; range dos 15 min seguintes x média
  const JAN = [['America/New_York', 8, 20, 'Abertura COMEX', '3,0×', '2,0×'], ['America/New_York', 8, 30, 'Dados EUA', '6,6×', '2,0×'],
    ['America/New_York', 10, 0, 'Dados EUA', '3,5×', '2,0×'], ['Europe/London', 15, 0, 'Leilão LBMA tarde', '3,5×', '1,9×'],
    ['America/New_York', 13, 29, 'Fechamento oficial COMEX', '3,0×', '1,0×'], ['Europe/London', 10, 30, 'Leilão LBMA manhã', '2,1×', '0,9×']];
  function zoned(tz, y, mo, d, h, mi) {
    const g = Date.UTC(y, mo - 1, d, h, mi), p = {};
    new Intl.DateTimeFormat('en-US', { timeZone: tz, hourCycle: 'h23', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
      .formatToParts(new Date(g)).forEach(x => p[x.type] = x.value);
    return g - (Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute) - g);
  }
  function janelas() {
    const box = el.querySelector('.od-jan'); if (!box) return;
    const [y, mo, d] = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' }).split('-').map(Number);
    const now = Date.now(), br = ms => new Date(ms).toLocaleTimeString('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit' });
    const L = JAN.map(j => ({ t: zoned(j[0], y, mo, d, j[1], j[2]), n: j[3], x: j[4], r: j[5] })).sort((a, b) => a.t - b.t);
    const prox = L.find(j => j.t + 15 * 60e3 > now);
    box.innerHTML = '<tr><th>Brasília</th><th>Janela</th><th class="num">Topo/fundo</th><th class="num">Range 15 min</th></tr>' + L.map(j => {
      const on = now >= j.t && now < j.t + 15 * 60e3, nx = prox === j;
      return '<tr style="' + (on ? 'background:color-mix(in srgb,var(--color-warn) 22%,transparent);font-weight:600' : nx ? 'font-weight:600' : now > j.t ? 'opacity:.5' : '') + '"><td>' + br(j.t) + (on ? ' ● agora' : nx ? ' ← próxima' : '') + '</td><td>' + j.n + '</td><td class="num">' + j.x + '</td><td class="num">' + j.r + '</td></tr>';
    }).join('');
  }
  janelas(); setInterval(janelas, 60e3);
  const load = () => Promise.all([get('lab.json'), get('intraday.json')]).then(([j, I]) => draw(j, I));
  load(); setInterval(load, 10 * 60e3);
})();
