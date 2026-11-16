# Painel de mercado — MEGA RESUMO (estado atual)

> Memória entre conversas, lida sozinha via `CLAUDE.md`. **Atualizar a cada mudança** no painel, cálculos ou dados (e anexar o detalhe no `HISTORICO.md`).
> `HISTORICO.md` = diário completo (números antigos, o porquê de cada decisão). Só abrir se precisar.
> Última revisão: 16/11/2026.

**Site:** https://gabrid15-creator.github.io/painel-mercado/ · **Repo:** `gabrid15-creator/painel-mercado` · commit e push direto na `main` · **Horário:** sempre Brasília (BRT).

---

## 0. A usuária e o objetivo

- Opera **XAUUSD na Vantage Markets**, USDJPY, USDCHF, EURUSD (o painel também mostra GBPUSD e Nasdaq em partes).
- Tem um **robô de grade/DCA** (compra e vende lado a lado): ganha em dia de **ping-pong**, sofre em dia de **tendência**.
- Quer descobrir com estatística: (1) **dia de ping-pong × tendência** (ligar ou não o robô); (2) **o lado do dia** (mais comprado × vendido), para alongar compras ou vendas e ajustar o stop.
- Foco: **opções diárias (0DTE)**, sempre **CME junto com GLD**. Exige **extremo rigor**: conferir tudo; nada sem teste entra como sinal.
- Tom: português, curto, para leigo. Ela é direta e se irrita com rodeio e erro bobo. Pensar como trader: o que importa é onde o dia **fecha** (pode "sambar" um pouco além do nível e voltar).

---

## 1. Arquitetura

| Peça | Detalhe |
|---|---|
| Coleta | `coletor.py` a cada 5 min. Disparo real: **cron-job.org → `workflow_dispatch`** do `.github/workflows/coleta.yml` (o `schedule` do GitHub é reserva). Passos: `timeout 300 coletor.py out` → `timeout 150 dtcc.py out` → `timeout 180 ia.py out` → grava tudo como **1 commit forçado na branch `dados`**. Job: 11 min. |
| Site | `docs/index.html` + `docs/app.js` (D3). Pages publica **só em push** (ou execução manual marcando "site"). `index.html` usa `app.js?v=<SHA>`. Lê dados de `raw.githubusercontent.com/.../dados/`; `docs/data/*.json` é reserva antiga (teste local sem rede engana). |
| Auto-atualização | Dados a cada 2 min; ao voltar para a aba (se > 60 s); confere versão nova a cada 10 min e recarrega; ativo escolhido e estado da ajuda ficam no `localStorage`. |
| IA | `ia.py`, modelo `claude-haiku-5-5` (variável `IA_MODELO`), segredo `ANTHROPIC_API_KEY`. Leitura geral e por ativo, sem viés. |
| CME | PDFs → `cme_pdf.py` (ouro) / `cme_pdf_iene.py` (iene) → `confere_cme.py` → `cme/opcoes_<pregão>.json`, `cme/iene_<pregão>.json` → `cme_local.py` carrega na coleta (só se o pregão for ≥ o atual). |
| CME pelo PC | `pc/` (`baixar_cme.sh`, `painel-cme.service/.timer`, `LEIAME.md`): Ubuntu, seg–sáb 3h30–8h de 30 em 30 min, curl simples (para no 403), envia à branch `pdfs` (commit órfão) e dispara `.github/workflows/cme_pdfs.yml` (lê, confere, só grava na main com 0 erro). Token fine-grained em `~/.config/painel-cme/token` (Contents + Actions RW, só este repo). **Ela ainda não instalou.** |
| DTCC | `dtcc.py` (≤ 150 s): balcão de opções de câmbio; estado `dtcc_estado.json` → `mi_otc.json`, `mi_otc_hist.json`. Card escondido. |
| 1 min | `minutos.py` 1×/dia ~01h UTC → branch `minutos` (`AAAA-MM-DD.csv.gz`: GC, SI, DXY, 6E, 6J, 6S). |
| Branches | `main` (código), `dados` (coleta), `minutos`, `pdfs`. |

**Funções do `coletor.py`:**
- Preços e macro: `b_precos` (preços + régua Vantage), `b_tsy`, `b_liq`, `b_bund`, `b_fred`, `b_macro`, `b_ativos`, `b_cot`, `b_dolar`.
- Regime e faixa: `b_cta`, `b_regime`, `b_faixa`.
- Opções: `b_0dte` (ouro GLD+CME, PCR, diário), `b_0dte_iene`.
- Conferência diária: `b_valid`.
- Agenda e notícias: `b_fg`, `b_agenda`, `b_eua`, `b_surpresa`, `b_news`.
- `b_score`: score removido da tela.
- `spot_ouro()`: conversão teórica para o à vista; não é usada como régua.

**Arquivos de dados (branch `dados`):**
- Geral: `mi_geral` (inclui `ouro_spot` com fator, base_usd e calibrado), `mi_ativos`, `mi_macro`, `mi_dolar`, `mi_regime`, `mi_cta`, `mi_ia`, `mi_status`.
- Faixa e mapa: `mi_faixa`, `mi_faixa_hist`, `mi_mapa_hist`, `mapa_fixo`, `mi_validacao`.
- Opções: `mi_0dte`, `mi_0dte_dia` (gravado, sem uso na tela), `mi_0dte_hist`, `mi_0dte_iene`, `mi_0dte_iene_hist`, `mi_pcr_hist`, `mi_diario_ouro`.
- CME: `ouro_cadeia` e `ouro_boletim`, `iene_cadeia` e `iene_boletim`.
- Outros: `mi_cot`, `mi_corr`, `mi_sazon`, `mi_agenda`, `mi_eua`, `mi_surpresa_hist`, `cleveland_nowcast`, `mi_noticias`, `mi_otc`, `mi_otc_hist`.
- Fixos em `docs/data/`: `faixa_backtest.json`, `rompimento.json`, `toque_tabela.json`, `goldbach_dias.json`.

---

## 2. Rotina diária da CME — regra de ouro: extremo rigor

1. Seg–sex de manhã ela manda 3 PDFs (https://www.cmegroup.com/daily_bulletin/current/; a versão preliminar sai ~3h BRT): `Section64_Metals_Option_Products.pdf` (ouro), `Section33_Japanese_Yen_Call_Options.pdf`, `Section34_Japanese_Yen_Put_Options.pdf`.
2. Comandos:
   - `python3 cme_pdf.py <Section64>`
   - `python3 cme_pdf_iene.py <Section33> <Section34>`
   - **obrigatório:** `python3 confere_cme.py --ouro <Section64> cme/opcoes_<pregão>.json --iene <Section33> <Section34> cme/iene_<pregão>.json`
3. **Só commit e push com 0 erro.** Explicar cada aviso em uma linha.

**O que o `confere_cme.py` checa:**
- Cada linha do JSON existe no PDF, no bloco/vencimento certo (strike, ajuste, contratos em aberto).
- A paridade call − put fecha entre os 3 strikes mais no dinheiro (vencimentos ≤ 35 dias; tolerância ouro 0,04%, iene 0,05%).
- Nenhum ajuste abaixo do valor intrínseco.
- Futuro comparado com o GC=F às 13h30 NY e com o 6J=F/JPY=X às 15h NY (gera aviso).

**Regras dos leitores:**
- **Nunca usar o "FUTURES SETT." do cabeçalho.** No iene de 12/11, o cabeçalho dizia 0,006259 e a paridade dava 0,006273: os níveis saíram ~0,36 iene errados.
- **Futuro = mediana de `K + C − P` nos 3 strikes mais no dinheiro.** Dá erro se a dispersão passar de 0,05% (vencimentos ≤ 35 dias). Série fina herda o futuro da data mais próxima com o mesmo cabeçalho.
- **Iene:** as séries ficam na parte "ADDITIONAL":
  - 1JY–5JY = sexta da semana N;
  - MJ = seg, TJ = ter, WJ = qua, SJ = qui;
  - JPU = mensal.
  - Opções de nov. usam o futuro de dez.; as de 11/12, jan. e fev. usam o de mar.
  - FX vence às 9h CT (12h BRT).
- **Ouro, sexta:** séries OG1–OG5, em blocos separados.
- **Ouro, seg–qui:** séries GMW/GWT/GWW/GWR vêm **misturadas** (calls, puts e 2 ou mais vencimentos no mesmo bloco). Regras para separar:
  - só entra a série que vence em ≤ 2 dias úteis;
  - tipo pelo delta (ITM > 0,5);
  - vencimento pela vol. implícita do prazo (grupo de 0,8 a 1,5× a menor vol. no dinheiro);
  - trava de 0,5 a 1,6× a vol. da sexta;
  - paridade ≤ US$ 3;
  - linha duplicada: fica a de menor prêmio.
- **A CME bloqueia robôs** (servidor, GitHub, Claude). Não driblar. Se o PC dela também tomar 403, volta ao manual.
- **01/01/2027:** a CME reorganiza o boletim → conferir os leitores.

---

## 3. Réguas de preço (crítico)

- **Ouro no painel = régua da Vantage = GC=F − US$ 6,5.**
  - O fator `f = 1 − 6,5 ÷ GC` vale para TUDO do ouro: série, barras de 1 h do mapa, razão do GLD e régua da CME.
  - No código: `VANTAGE_USD = 6.5` e `CALIB = "16/11/2026"`, em `b_precos()`.
  - Calibrado com pares simultâneos ditados por ela: GC 3.882 × Vantage 3.875; 3.880 × 3.874.
  - O à vista teórico (~−US$ 20) **não** bate com a Vantage.
  - **Recalibrar na troca de contrato do GC=F (dez → fev, fim de nov.):** pedir a ela 2 pares de preços simultâneos GC × Vantage.
- **GLD → ouro:** razão ouro ÷ GLD congelada no `last_trade_time` do GLD (ouro do GC 5 min × fator, naquele horário).
  - GLD fechado ou parado → usa o `close` oficial (a Cboe manda preço de pré-mercado com horário antigo).
  - Gamma (regime e flip) é recalculado com o ouro ao vivo na escala do GLD (`Sv = ouro / r`).
  - Bug antigo: esse cálculo deslocava ~US$ 38 à noite.
- **CME ouro → painel:** nível × (GC=F 5 min às 13h30 NY do pregão ÷ futuro pela paridade) × fator.
- **CME iene → USDJPY:** strike 1/K (call de iene = put de USDJPY); régua = JPY=X às 15h NY ÷ (1/F).
- **CME em equivalente GLD:** contratos × ouro ÷ GLD (~10,9 GLD por contrato de ouro).
- **Testes de toque e de máx./mín.: só FUTUROS da CME (GC, 6J, 6E, 6S, 6B).** O Yahoo FX (`JPY=X` etc.) tem picos falsos nas máximas/mínimas e já inventou uma "defesa" de 70% que era só sujeira. Fechamentos do Yahoo FX servem.
- **Sessão do dia:** abre às 18h NY (moedas 19h BRT, ouro 20h BRT). O σ do mapa congela na 1ª coleta da sessão/semana (`mapa_fixo.json`). Chave da semana = `ativo|sem|segunda` (corrigido 16/11: na segunda o σ da semana saía igual ao do dia).

---

## 4. O que está no painel (aba Mercado, de cima para baixo)

1. **Panorama do dia:** leitura da IA; Fear & Greed, red folder, VIX, DXY.
2. **Macro, o que move o dólar:**
   - Radar institucional: liquidez, estresse, surpresa, regime EUA.
   - Dólar e juros: bps no cabeçalho, coluna Leitura, EUA − Alemanha → EURUSD. Descreve o dia, não prevê.
   - Fed Funds usa o contrato fixo do mês (ex.: ZQZ26.CBT).
3. **Ativo, níveis e opções** (o seletor gruda no topo):
   - **Mapa "até onde o preço deve ir":**
     - tabelas Hoje e Semana, níveis ±0,5/1/1,5/2σ a partir da abertura;
     - "chance agora": z = distância log ÷ (σ × √fração restante), com a curva real medida em 2 anos de 1 h (`toque_tabela.json`);
     - leitura em palavras: alvo provável ≥ 50%, possível 20–49%, difícil 8–19%, raro < 8%;
     - "Teste um preço" aceita vírgula e ponto.
   - **Rompimento do σ do dia** (`.mp-romp`, `rompimento.json`): preço de cada gatilho (±1σ/±1,25σ/±1,5σ), o que costuma acontecer depois e a linha "Hoje: em cima Xσ → …".
   - **Faixa esperada:**
     - ouro = GVZ, mais a CME (straddle no dinheiro da 1ª série com ≥ 3 dias úteis);
     - moedas = vol. realizada de 21 dias × 1,09;
     - etiqueta da vol. contra a média de 1/3/5 anos (pesos 50/30/20);
     - tabela **Precisão medida** visível (`faixa_backtest.json`).
   - **Conferência diária** (`mi_validacao.json`): toque real × chance prevista, faixa e 0DTE (GLD e CME separados).
   - **0DTE ouro:** só a **borboleta** (`drawBorb`).
     - Grade de strikes do GLD em ±max(1,3%, 1,15σ).
     - Barras: clara = contratos em aberto GLD + CME (equivalente GLD); escura = volume do dia do GLD (ao vivo). Verde = calls, vermelho = puts.
     - Níveis do GLD tracejados, mais ±1σ; níveis da CME pontilhados.
     - Faixa dourada ✓ onde GLD e CME concordam (tolerância = 1 strike do GLD ≈ US$ 11).
     - "Fora do gráfico" para nível fora da escala.
     - Dois PCR em número grande: > 1,05 = +Puts vermelho; < 0,95 = +Calls verde. É retrato, não prevê.
     - Tabela GLD × CME: teto, flip, max pain, piso, faixa, ±1σ.
     - No celular, só contratos em aberto.
   - **0DTE iene:** o mesmo card, só com CME (vencimento mais próximo com ≥ 10 strikes; PCR em ±2%).
   - **Balcão (DTCC):** escondido (`MOSTRA_OTC = false` no `app.js`), só grava.
   - **"Mais sobre o ativo e o mercado"** (`details.mais`, recolhido): Regime, CTA (só ouro), preço/ATR, sazonalidade, COT, correlações, Goldbach, tabela macro.
4. **Agenda e notícias:** Forex Factory com "Atual" ao vivo (biquote/BLS/FRED); notícias com filtro.
- **Aba Dias de alto impacto:** calendário EUA + Goldbach/Hopiplaka (`goldbach_gen.py`).
- **Cores dos níveis:** teto vermelho, piso verde, flip âmbar, max pain roxo, faixa azul, ±1σ verde-água, ±2σ marrom.

**Convenções do front (`app.js`):**
- `drawBorb(el, rows, lv, o)` desenha a borboleta:
  - `rows` = `[k, calls, puts, extras, volC?, volP?]`;
  - `lv` = `{preco, teto, piso, gamma, mp, faixa, s1}`;
  - opções: `o.lv2` (níveis da CME), `o.tol` (faixa de concordância), `o.pcrs`, `o.pcr`, `o.pcrRot`, `o.dec`.
- `drawZ0b` desenha o 0DTE do ouro; `drawZ0j`, o do iene.
- `prepAjuda()` põe o "?" dentro do h2, com o texto do título em `span.h2-t`.
- Textos de ajuda ficam em `div.op-note.ajuda.guia` (introdução em `<p>` + itens em `<ul>`, sem bolinha). Abrem com `.abre` no card ou com `body.ver-ajuda` (botão "? Explicações").
- Tabelas vão dentro de `.tbl-x`; divisórias de seção usam `.sec-t`.
- Cabeçalhos usam `text-transform: none` (em maiúsculas, σ vira Σ).
- `IDS` lista os JSON carregados.

---

## 5. Resultados dos testes (só entra o que passa; corte |t| ≥ 2,5 quando há muitos testes, estável nas metades)

### Passou (está no painel)
| Teste | Números |
|---|---|
| Faixa σ acerta o **fechamento** (`faixa_backtest.py`) | Ouro (GVZ, 2008+, 4.640 dias): dia ±1σ 78% / ±2σ 96%; semana 77/97; mês 72/96. Moedas: 73–74% / 95%. Estável por ano; futuros confirmam. |
| Chance de **tocar** os níveis | Curva real (2 anos de 1 h). A fórmula teórica superestimava no meio (prevista 45%, real 33–40%). |
| **Rompimento** (`testes/rompimento.py`, futuros, 18–26 anos) | Tocou ±1σ → fecha fora 49–51%. Passou de ±1,25σ → fecha fora 68–71%, chega a 1,5σ 62–67%. Passou de ±1,5σ → fecha fora 80–84%, chega a 2σ 37–45%. |
| **σ das opções × tamanho do dia** (`testes/pingpong_sigma.py`, 559 dias de GC 1 h) | σ curto (~US$ 30) → andou US$ 21, range US$ 41; médio (~US$ 50) → 37 / 75; longo (~US$ 83) → 62 / 126. r = 0,44 (t 11,6) e 0,70 (t 23). Estável. Deslocamento médio ≈ 0,75σ. **Uso: medir grade e stop em σ do dia.** |
| Regime forte | Mantém a direção por 13 semanas: DXY 91–100%, juros 57–90%. |

### Não passou (não usar como sinal)
| Teste | Resultado |
|---|---|
| **σ das opções × formato do dia** (hipótese dela: σ curto = lateral) | Formato igual em qualquer σ: ~1/3 ping-pong, ~1/3 tendência (t = −1,3). O σ diz **quanto** o preço anda, não **como**. |
| Ping-pong × tendência (eficiência = \|fech − abert\| ÷ caminho percorrido; ping-pong ≤ 0,12, tendência ≥ 0,30) | Nada antecipa com dado grátis: eficiência da véspera, GVZ (nível, variação, prêmio), gap, dia da semana, Ásia + Londres até 10h BRT → todos ~33%. |
| σ como ponto de reversão | 40–53% em todos os níveis; o 1σ não é especial. |
| "Defesa" (passou e voltou) | Nos futuros: 44–52% (acaso = 50%). Os 70% eram sujeira do Yahoo FX. |
| Momentum do fim do dia no ouro, sem gamma (Baltussen; `testes/momentum_fim.py`, GC 1 h 2 anos + 5 min 60 dias) | Retorno 18h→13h/15h/16h25 NY não prevê o trecho final (melhor t −2,3, metades instáveis; 4 testes). Com gamma: esperar o diário. |
| "Sambou e voltou" | Depois de passar do 1σ: 1/3 só samba (≤ 0,25σ além) e fecha dentro 82–90%; 2/3 seguem e fecham dentro só ~30%. Igual em 0,8σ e 1,2σ → é geometria, não defesa. |
| Paredes do balcão DTCC (2 anos, 1.192 vencimentos; e só ≤ 2 dias, 921) | Ímã, range e parada = acaso (atração 42,3% × 46,3%, t −2,3). |
| Direção por opções (210 testes: PCR da Cboe, GVZ, SKEW, VIX/VIX3M) | Melhor t = 3,0, abaixo do corte de 3,7; instável. |
| Macro de prazo maior (52 + 40 testes + intradiário) | Nenhum prevê direção → score e viés removidos. |
| Calendário/sessão (67 testes) | Só o franco na Ásia (t 4,0), que some no futuro 6S → falha do Yahoo. |
| SMT (diário, 1 h, 1/5/15 min, versões 1 e 2; ~750 testes) | Nada passou. |
| Termômetro do dólar, estoque do GLD, PCR dos ETFs de moeda, IAU | Descartados. |
| Qual σ é mais preciso | GVZ é largo no 1σ (78%) e certo no 2σ (96%). Nenhuma escala acerta 68% e 95% juntos (caudas grossas). |

### Pesquisa externa (hipóteses para testar)
- Golez & Jackwerth: o futuro do S&P era puxado ao strike no dinheiro no vencimento das opções sobre futuro (1992–2009); o efeito sumiu em 2016–2025.
- Baltussen et al. (JFE 2021): com gamma negativo, há momentum nos últimos 30 min do pregão.
- SpotGamma: o S&P fecha dentro do movimento esperado em 76% dos dias (bate com os nossos 73–78%).

---

## 6. Gravando agora e testes marcados

| O quê | Arquivo | Quando testar |
|---|---|---|
| **Diário do ouro** (desde 16/11). De manhã (9h30–10h30 NY): regime de gamma GLD/CME, flip, teto/piso, faixa %, PCR 0DTE. Depois das 17h NY: abertura, fechamento, máx., mín., eficiência, se cruzou a abertura, retorno. | `mi_diario_ouro.json` | **~60 dias (meados de fev/2027)**, pré-registrado: gamma +/−, distância ao flip, faixa 0DTE e PCR/skew preveem (1) ping-pong × tendência e (2) o lado do dia? Corte \|t\| ≥ 2,5. Desde 16/11 também grava (sem tela, pedido dela, 1ª contagem com 30 dias ~fim de dez.): **gregas D+0** GLD e CME (GEX por +1%, charm até o vencimento, vanna por −1 ponto de vol., em US$ mi; função `gregas()`; só contratos em aberto do vencimento do dia), strike mais carregado (`pin_*`, para ímã), PCR OI da CME D+0, e preços GC às 9h30, 10h30, 13h, 13h30, 15h30, 16h NY (1ª hora, ajuste CME, fim do GLD). Obs.: `regime` do GLD usa OI+volume; `greg_gld.gex` só OI — podem divergir (16/11: regime + , gex −6,5). Dias até agora: 12/11 negativo (eficiência 0,45), 13/11 negativo (0,02), 16/11 positivo (0,10). |
| 0DTE GLD × CME e iene | `mi_0dte_hist`, `mi_0dte_iene_hist` | ~30 vencimentos (~fim de dez.) |
| Put/call + skew 25Δ GLD e CME (desde 13/11) | `mi_pcr_hist` | 17/05/2027 (tarefa agendada no Claude, Sonnet) |
| Candles de 1 min | branch `minutos` | fev/2027, 4 hipóteses de SMT pré-registradas |
| Surpresas EUA + nowcast do Fed de Cleveland | `mi_surpresa_hist`, `cleveland_nowcast` | ~mai/2027 |
| DTCC | `mi_otc_hist` (a DTCC guarda ≥ 2 anos) | retestar quando quiser |

- Não há histórico grátis de skew, delta ou curva de vol. → só gravando.
- **Databento** (pago, CME histórico e ao vivo, a partir de ~US$ 199/mês) daria 1–2 anos de dados na hora. Ela disse que vai assinar "nos próximos dias".
- Licença da CME: não exibir dado em tempo real em site público.

---

## 7. Regras de qualidade

- **Dados:** conferir antes de publicar. Dizer "retrato" quando é retrato e "não sei" quando não sabe.
- **Visual:** nada sobreposto nem vazando. Antes de publicar mudança visual, rodar a varredura Playwright:
  - medir os retângulos dos textos: sobreposição e saída do card;
  - larguras 1200, 390 e 340 px; tema claro e escuro;
  - os 5 ativos, com e sem ajuda aberta;
  - usar **cópia dos dados atuais da branch `dados`**;
  - Playwright e Chromium já vêm instalados (não reinstalar).
- **Texto:** "Como ler" em todo card novo, no "?": o que é, como usar, como impacta o preço. Itens em frases naturais, sem bolinha, pouco "=" e "→". Texto de borda a borda no PC.
- **Estatística:** baseline/placebo, janelas sem sobreposição, sem olhar o futuro, t corrigido pelo número de testes, metades estáveis. Script reproduzível em `testes/`.
- **Commits:** sem identificador de modelo; terminar com as linhas de atribuição pedidas pelo sistema.

---

## 8. Próximos passos

1. Ela instalar a automação dos PDFs (`pc/LEIAME.md`) e ver se a CME bloqueia o PC dela.
2. Recalibrar a régua da Vantage na troca do GC (fim de nov.).
3. Euro e franco na CME: achar as seções no boletim; seguir o molde do iene.
4. Rodar os testes da §6 nas datas. Ideias anotadas: rompimento por horário (Ásia/Londres/NY), rompimento com × sem red folder, gamma × rompimento, rompimento no σ da semana, grade do robô medida em σ.
5. Pergunta sem resposta: suavizar o gamma flip do GLD (média de 15 min)?
6. Conferir os leitores em 01/01/2027. Databento quando ela assinar.

---

## 9. Contas e serviços

- GitHub: repo, Actions, Pages.
- cron-job.org: dispara a coleta.
- Anthropic Console: chave da IA.
- Google Drive, pasta "painel-mercado-opcoes": fluxo antigo (`opcoes_drive.py`).
- DTCC (`pddata.dtcc.com`, grátis).
- Ambiente Claude "painel-mercado". Rede liberada: Yahoo, FRED, CFTC, Cboe, SPDR, CME, DTCC.
- Repo privado `Jireh-dados`: cadeia do GLD de 31/10 a 12/11, sem uso.
- Tarefas agendadas no Claude: teste de put/call + skew em 17/05/2027.
