// Card "Ouro — diagnóstico do dia" (vem do Laboratório; só o que passou na validação de 06/11/2026).
// Para remover: apagar este arquivo, a <section id="ouro-dia"> e a linha <script src="ouro-dia.js"> do index.html.
(() => {
  const B = 'https://raw.githubusercontent.com/gabrid15-creator/painel-mercado/lab-dados/';
  const el = document.getElementById('ouro-dia'); if (!el) return;
  const nf = (v, d = 1) => v == null ? '–' : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  const get = f => fetch(B + f + '?t=' + Date.now(), { cache: 'no-store' }).then(r => r.ok ? r.json() : null).catch(() => null);
  function draw(j, I) {
    if (!j) { el.querySelector('.od-txt').textContent = 'Sem dados do laboratório ainda.'; return; }
    let s = j.score;
    const hoje = I && I.estado && I.estado !== 'cedo' && (Date.now() - new Date(I.atualizado + '-05:00')) < 6 * 3600e3;
    if (hoje && I.estado === 'tendencia') s = Math.min(s, 20); else if (hoje && I.estado === 'atencao') s = Math.min(s, 50);
    const dNY = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
    const ev = j.evento && j.evento_data === dNY ? j.evento : null;
    if (ev === 'NFP') s = Math.min(s, 35); else if (ev === 'FOMC') s = Math.min(s, 50);
    const cls = s < 40 ? 'bad' : s < 70 ? 'warn' : 'ok';
    const tag = s < 40 ? '🔴 NÃO operar contra' : s < 70 ? '🟡 cautela' : '🟢 bom p/ reversão';
    let t;
    if (hoje && I.estado === 'tendencia') t = '<b>Dia de tendência de ' + I.direcao + '.</b> Já andou ' + nf(Math.abs(I.mov_atr), 2) + '× o range médio desde a meia-noite e está na ponta. Não tente pegar topo/fundo; só a favor ou fora.';
    else if (hoje && I.estado === 'atencao') t = '<b>Começando a andar para ' + I.direcao + '</b> (' + nf(Math.abs(I.mov_atr), 2) + '× o range médio, na ponta). Mão menor; depois das 10h NY, acima de 0,6× vira tendência.';
    else if (ev === 'NFP') t = '<b>Dia de payroll (NFP, 8h30 NY).</b> Historicamente 2× mais dias de tendência. Não opere contra o movimento que sair do dado.';
    else if (ev === 'FOMC') t = '<b>Dia de FOMC (14h NY).</b> Range costuma ser ~1,5× o normal e com chicote para os dois lados. Mão menor e stop mais largo.';
    else if (s < 40) t = '<b>Véspera com cara de tendência:</b> opções esperando mais movimento do que o ouro vem fazendo. Evite operar contra.';
    else if (s < 70) t = '<b>Dia neutro.</b> Reversão só com confluência forte e mão reduzida.';
    else t = '<b>Dia favorável a reversão.</b> Opções calmas e o ouro sem disparar até agora.';
    el.querySelector('.od-n').textContent = s;
    el.querySelector('.od-tag').className = 'tl-chip od-tag ' + cls; el.querySelector('.od-tag').textContent = tag;
    el.style.borderLeft = '4px solid var(--color-' + cls + ')';
    el.querySelector('.od-txt').innerHTML = t;
    el.querySelector('.od-det').textContent = (hoje ? 'Hoje ' + I.hora_ny + ' NY · ' : '') + 'Mão sugerida ' + nf(j.mao.mult, 2) + '× o lote base · VRP ' + nf(j.vrp, 2) + ' · GVZ 5 dias ' + (j.gvz_var5 > 0 ? '+' : '') + nf(j.gvz_var5) + '% · CTA (info) ' + (j.cta.posicao > 0 ? '+' : '') + j.cta.posicao + '%';
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
