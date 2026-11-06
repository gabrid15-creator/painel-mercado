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
    const cls = s < 40 ? 'bad' : s < 70 ? 'warn' : 'ok';
    const tag = s < 40 ? '🔴 NÃO operar contra' : s < 70 ? '🟡 cautela' : '🟢 bom p/ reversão';
    let t;
    if (hoje && I.estado === 'tendencia') t = '<b>Dia de tendência de ' + I.direcao + '.</b> Já andou ' + nf(Math.abs(I.mov_atr), 2) + '× o range médio desde a meia-noite e está na ponta. Não tente pegar topo/fundo; só a favor ou fora.';
    else if (hoje && I.estado === 'atencao') t = '<b>Começando a andar para ' + I.direcao + '</b> (' + nf(Math.abs(I.mov_atr), 2) + '× o range médio, na ponta). Mão menor; depois das 10h NY, acima de 0,6× vira tendência.';
    else if (s < 40) t = '<b>Véspera com cara de tendência:</b> opções esperando mais movimento do que o ouro vem fazendo. Evite operar contra.';
    else if (s < 70) t = '<b>Dia neutro.</b> Reversão só com confluência forte e mão reduzida.';
    else t = '<b>Dia favorável a reversão.</b> Opções calmas e o ouro sem disparar até agora.';
    el.querySelector('.od-n').textContent = s;
    el.querySelector('.od-tag').className = 'tl-chip od-tag ' + cls; el.querySelector('.od-tag').textContent = tag;
    el.style.borderLeft = '4px solid var(--color-' + cls + ')';
    el.querySelector('.od-txt').innerHTML = t;
    el.querySelector('.od-det').textContent = (hoje ? 'Hoje ' + I.hora_ny + ' NY · ' : '') + 'Mão sugerida ' + nf(j.mao.mult, 2) + '× o lote base · VRP ' + nf(j.vrp, 2) + ' · GVZ 5 dias ' + (j.gvz_var5 > 0 ? '+' : '') + nf(j.gvz_var5) + '% · CTA (info) ' + (j.cta.posicao > 0 ? '+' : '') + j.cta.posicao + '%';
  }
  const load = () => Promise.all([get('lab.json'), get('intraday.json')]).then(([j, I]) => draw(j, I));
  load(); setInterval(load, 10 * 60e3);
})();
