# Painel de mercado — MEGA RESUMO (estado atual)

> Lido automaticamente em toda conversa nova (via `CLAUDE.md`). **Manter atualizado** a cada mudança no painel, nos cálculos ou nos dados.
> Detalhe completo, números antigos e o porquê de cada decisão: **`HISTORICO.md`** (consultar só quando precisar).
> Última revisão: 16/11/2026.

**Site:** https://gabrid15-creator.github.io/painel-mercado/ · **Repo:** `gabrid15-creator/painel-mercado` (commit e push direto na `main`) · **Horário:** sempre Brasília.
**Usuária:** opera **XAUUSD (Vantage), USDJPY, USDCHF, EURUSD**; tem um robô de compra e venda/DCA que ganha em dia de **ping-pong** (lado a lado) e sofre em dia de **tendência**. Quer: estatística com extremo rigor, foco em **opções diárias (0DTE)**, painel limpo.

---

## 1. Como funciona

| Peça | O que faz | Onde |
|---|---|---|
| Coleta | a cada 5 min (disparo pelo cron-job.org) grava JSON na branch `dados` | `coletor.py`, `.github/workflows/coleta.yml` |
| Balcão DTCC | passo próprio da coleta (≤ 150 s), só grava | `dtcc.py` → `dtcc_estado.json`, `mi_otc*.json` |
| Site | HTML/JS estático no GitHub Pages; publica **só em push**; lê os dados da branch `dados` | `docs/index.html`, `docs/app.js` |
| IA | Haiku 5.5 escreve a leitura geral e por ativo (sem viés) | `ia.py` (segredo `ANTHROPIC_API_KEY`) |
| CME (PDFs) | usuária manda os PDFs → leitores → **`confere_cme.py`** → `cme/*.json` → coleta carrega (`cme_local.py`) | ver §2 |
| Testes | scripts de backtest reproduzíveis | `testes/`, `faixa_backtest.py`, `confere_dtcc.py` |

**Site se atualiza sozinho:** dados a cada 2 min, na hora ao voltar para a tela, e recarrega sozinho quando sai versão nova (guarda o ativo escolhido).

---

## 2. Rotina diária (CME) — regra de ouro: **extremo rigor**

1. Seg–sex de manhã a usuária manda 3 PDFs: `Section64_Metals_Option_Products.pdf` (ouro), `Section33_Japanese_Yen_Call_Options.pdf`, `Section34_Japanese_Yen_Put_Options.pdf` (https://www.cmegroup.com/daily_bulletin/current/). Preliminar sai ~3h de Brasília.
2. Rodar: `python3 cme_pdf.py <ouro>` · `python3 cme_pdf_iene.py <calls> <puts>` · **obrigatório** `python3 confere_cme.py --ouro <pdf> cme/opcoes_<pregão>.json --iene <calls> <puts> cme/iene_<pregão>.json`.
3. **Só publica com 0 erro.** Explicar avisos. Commit dos `cme/*.json` + push.
- A CME **bloqueia robôs** (servidores, GitHub, Claude). Não driblar.
- **Nunca confiar no "FUTURES SETT." do cabeçalho:** futuro sempre pela paridade call − put. (Iene: opções de nov. usam o futuro de dez.; 11/12, jan., fev. usam o de mar.)
- Ouro: séries de sexta (OG) separadas no PDF; seg–qui (GMW/GWT/GWW/GWR) vêm misturadas → só a série que vence em ≤ 2 dias úteis, separada pela vol. implícita, com travas de vol. e paridade.
- **Automação pelo PC da usuária (pronta, falta ela instalar):** `pc/LEIAME.md` (Ubuntu, systemd 3h30–8h) baixa os PDFs → branch `pdfs` → dispara `.github/workflows/cme_pdfs.yml` (lê, confere, só grava com 0 erro). Se a CME bloquear o PC também, volta ao manual.

---

## 3. Réguas de preço (crítico)

- **Ouro = régua da Vantage = futuro ativo (GC=F) − US$ 6,5** (calibrado em 16/11 com preços simultâneos: GC 3.882 × Vantage 3.875). `VANTAGE_USD` em `b_precos()`. **Recalibrar** quando o GC=F trocar de contrato (dez → fev, fim de nov.): pedir 2 pares de preços simultâneos. O à vista teórico (−US$ 20) **não** bate com a Vantage.
- **GLD → ouro:** razão ouro ÷ GLD no horário do último negócio do GLD; fora do pregão usa o `close` oficial (a Cboe manda preço de pré-mercado com horário antigo).
- **CME ouro → painel:** GC=F às 13h30 NY do pregão ÷ futuro (paridade), × fator da Vantage.
- **CME iene → USDJPY à vista:** strike 1/K (call de iene = put de USDJPY); régua = USDJPY às 15h NY ÷ (1/F).
- **Dados para testes de toque/máx./mín.: usar FUTUROS da CME (GC, 6J, 6E, 6S, 6B).** O câmbio do Yahoo (`JPY=X` etc.) tem picos falsos nas máximas/mínimas (inventou uma "defesa" que não existe). Fechamentos do Yahoo FX servem.

---

## 4. O que está no painel (aba Mercado, de cima para baixo)

- **Panorama:** leitura da IA; Fear & Greed, red folder, VIX, DXY.
- **Macro:** Radar institucional (liquidez, estresse, surpresa, regime EUA); Dólar e juros (bps no cabeçalho, coluna Leitura).
- **Ativo** (seletor gruda no topo):
  - **Mapa** ("até onde o preço deve ir"): níveis ±0,5/1/1,5/2σ do dia e da semana a partir da abertura (moedas 19h, ouro 20h de Brasília), chance real de toque **agora**, teste de preço, **Rompimento do σ do dia** (gatilhos ±1σ/±1,25σ/±1,5σ, o que costuma acontecer depois e a situação de hoje), **Faixa esperada** (GVZ no ouro, vol. 21d × 1,09 nas moedas, + CME) com **Precisão medida** visível, **Conferência diária**.
  - **0DTE ouro:** só a **borboleta** (barra clara = em aberto GLD + CME em equivalente GLD; escura = volume do dia GLD), níveis GLD tracejados + ±1σ, CME pontilhados, faixa dourada ✓ onde concordam, dois PCR. Tabela GLD × CME.
  - **0DTE iene:** mesma estrutura, só CME (vencimento mais próximo com ≥ 10 strikes).
  - **Balcão (DTCC):** card **escondido** (`MOSTRA_OTC = false`), só gravando.
  - **"Mais sobre o ativo e o mercado"** (recolhido): Regime, CTA (só ouro), preço/ATR, sazonalidade, COT, correlações, Goldbach, tabela macro.
- **Agenda e notícias:** Forex Factory com "Atual" ao vivo (biquote/BLS/FRED); notícias com filtro.
- **Aba Dias de alto impacto:** calendário EUA + Goldbach/Hopiplaka.
- **Visual:** "?" no título de cada card abre o "Como ler" (textos em itens, sem bolinha); "? Explicações" abre todos. Texto de borda a borda no PC.

---

## 5. O que foi testado (só entra no painel o que passa; corte |t| ≥ 2,5 quando há muitos testes)

| Pergunta | Resultado | Uso |
|---|---|---|
| Faixa de σ acerta o **fechamento**? | **Sim.** Fecha dentro de ±1σ: ouro 78% (GVZ, 2008+), moedas 73–74%; ±2σ ~95–96%. Estável por ano. Futuros confirmam. | Faixa + "Precisão medida" |
| Chance de **tocar** os níveis | Curva real medida (2 anos 1 h) | Mapa "chance agora" |
| **Rompimento** do σ (futuros, 18–26 anos) | Tocou ±1σ → fecha fora 49–51% (cara ou coroa). Passou de ±1,25σ → fecha fora **68–71%**, chega a 1,5σ 62–67%. Passou de ±1,5σ → fecha fora **80–84%**, chega a 2σ 37–45%. | Bloco "Rompimento" |
| "Sambou e voltou" | Depois de passar do 1σ: 1/3 só samba (≤ 0,25σ além) e fecha dentro 82–90%; 2/3 seguem e fecham dentro só ~30%. Igual em 0,8σ/1,2σ (geometria, não "defesa" do 1σ). | Contexto |
| σ como **ponto de reversão** | Não (40–53% em todos os níveis; histograma de extremos liso). | — |
| Paredes de **balcão (DTCC)**, 2 anos, inclusive só 0–2 dias | **Nada** (ímã, range, parada nas paredes = acaso). | Card escondido |
| Sinais de direção (PCR, GVZ, SKEW, juros, score, SMT, calendário…) | **Nenhum** prevê direção com segurança. | Não entra |
| **Ping-pong × tendência** no ouro (2 anos 1 h; eficiência = |fech − abert| ÷ caminho percorrido) | Nada antecipa com dado grátis: dia anterior, GVZ (nível, variação, prêmio), gap, dia da semana, madrugada até 10h → todos ~1/3 por lado. | Aguardando opções (§6) |
| Qual σ é mais preciso (ouro) | GVZ: largo no 1σ (78%), certo no 2σ (96%). Nenhuma escala acerta 68% e 95% juntos (caudas grossas). | Mapa usa GVZ |
| Pesquisa | S&P: futuro puxado ao strike no dinheiro no vencimento das opções sobre o futuro (1992–2009), não mais em 2016–2025. Gamma negativo → momentum no fim do dia (Baltussen 2021). SpotGamma: S&P fecha no movimento esperado em 76%. | Hipóteses a testar |

---

## 6. Gravando (para testar depois) e testes marcados

- **Diário do ouro** (`mi_diario_ouro.json`, desde 16/11): de manhã (9h30–10h30 NY) regime de gamma GLD e CME, flip, teto/piso, faixa, PCR; depois das 17h NY eficiência, cruzamentos, máx./mín., retorno. **Teste pré-registrado com ~60 dias (meados de fev/2027):** (1) gamma positivo/negativo, distância ao flip, faixa 0DTE, PCR/skew preveem **ping-pong × tendência**? (2) preveem o **lado** do dia (mais comprado × vendido)? Corte |t| ≥ 2,5.
- **0DTE GLD × CME** (`mi_0dte_hist.json`) e **iene** (`mi_0dte_iene_hist.json`): validação com ~30 vencimentos (~fim de dez.).
- **Put/call + skew 25Δ** GLD e CME (`mi_pcr_hist.json`): teste agendado 17/05/2027 (Sonnet).
- **Candles de 1 min** (branch `minutos`): 4 hipóteses de SMT pré-registradas (fev/2027).
- **Surpresas EUA** e nowcast do Fed de Cleveland: teste em ~6 meses.
- **DTCC** (balcão): estado e retrato diário; a própria DTCC guarda ≥ 2 anos (dá para retestar).
- O que a usuária quer descobrir: **dia de ping-pong** (ligar o robô) × **dia de tendência** (evitar) e **o lado** (para alongar compras ou vendas e ajustar o stop). Dados que faltam de graça: skew/delta/curva de vol. históricos → só gravando; **Databento** (pago, CME histórico e ao vivo) daria 1–2 anos na hora quando ela assinar.

---

## 7. Preferências e regras da usuária

- Português, curto, para leigo, **horário de Brasília**. Chamar o que é "retrato" de retrato; dizer "não sei" quando não sabe.
- **Extremo rigor:** conferir dados antes de publicar; nada sem teste estatístico entra como sinal.
- **Opções:** sempre CME junto com GLD; foco no 0DTE.
- **Visual:** nada sobreposto nem vazando. Antes de publicar: varredura de sobreposição **e** vazamento (texto linha a linha) em PC 1200, celular 390 e 340 px, claro e escuro, 5 ativos, com e sem ajuda, **com cópia dos dados atuais da branch `dados`** (o teste local sem rede usa a reserva antiga e esconde problemas). Cabeçalho em maiúsculas transforma σ em Σ → usar `text-transform: none`.
- "Como ler" em todo card novo (no "?"), em itens, frases naturais.

---

## 8. Próximos passos

1. Usuária instalar a automação dos PDFs no PC (`pc/LEIAME.md`).
2. Recalibrar a régua da Vantage na troca de contrato do ouro (fim de nov.).
3. Euro e franco na CME (achar seções no boletim; mesmo molde do iene).
4. Testes da §6 nas datas. Ideias anotadas: horário do rompimento (Ásia/Londres/NY), rompimento com × sem red folder, gamma × rompimento, tabela de rompimento para o σ da semana.
5. CME reorganiza o boletim em 01/01/2027: conferir os leitores.
6. Databento quando a usuária assinar.

---

## 9. Contas e serviços

GitHub (repo, Actions, Pages) · cron-job.org (dispara a coleta) · Anthropic Console (chave da IA) · Google Drive (pasta "painel-mercado-opcoes", fluxo antigo) · DTCC (`pddata.dtcc.com`, grátis) · ambiente Claude "painel-mercado" (rede: Yahoo, FRED, CFTC, Cboe, SPDR, CME, DTCC).
