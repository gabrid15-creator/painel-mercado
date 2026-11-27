# Painel de mercado — MEGA RESUMO (estado atual)

> Memória entre conversas, lida sozinha via `CLAUDE.md`. **Atualizar a cada mudança** no painel, cálculos ou dados (e anexar o detalhe no `HISTORICO.md`).
> `HISTORICO.md` = diário completo (números antigos, o porquê de cada decisão). Só abrir se precisar.
> Última revisão: 27/11/2026.

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
| CME pelo PC | `pc/` (`baixar_cme.sh`, `painel-cme.service/.timer`, `LEIAME.md`): Ubuntu, seg–sáb 3h30–8h de 30 em 30 min, curl dá 403 até no PC dela (17/11) → baixa abrindo o **Brave dela num perfil separado** (`~/.config/painel-cme/brave`, PDF direto para pasta temporária, fecha depois; precisa sessão logada; testado com Chromium + Xvfb), envia à branch `pdfs` (commit órfão) e dispara `.github/workflows/cme_pdfs.yml` (lê, confere, só grava na main com 0 erro). Token fine-grained em `~/.config/painel-cme/token` (Contents + Actions RW, só este repo). **Instalado no PC dela em 17/11 (Linux Mint): 1º teste ok, leitura automática conferida e publicada.** Roda 3h–8h de 30 em 30 min + 10h e 12h, abre o Brave só até pegar o boletim (estado em `~/.config/painel-cme/estado`). 18/11: confere a DATA do boletim (pdftotext) e só marca o dia como feito se for o último pregão (às 3h a CME ainda servia o de 16/11); o script se auto-atualiza pelo GitHub (raw) a cada execução. 26/11: ao sair (com ou sem erro) manda as últimas 60 linhas do log para a branch `log` (`painel-cme.log`). Falhou em 25 e 26/11 até 12h ("o Brave não baixou"); à mão e pelo systemd funcionou em 26/11 19h20. Suspeita: janela do chaveiro; desde 26/11 o Brave do robô usa `--password-store=basic`. Confirmar pelo log de 27/11. |
| GLD (0DTE) | Cboe `cdn.cboe.com/.../GLD.json` (bloqueou o servidor com 403 Cloudflare em 20–23/11/2026, não driblar) → reserva `gld_yahoo()` (Yahoo options + crumb). Se as duas falharem, o card 0DTE mostra "⚠ sem atualizar". **P6 (26/11, Code):** pela reserva Yahoo, delta por Black-Scholes com a vol. implícita do Yahoo (juro 0), todos os vencimentos (antes ≤ 40 dias) e `fonte_gld` no `mi_pcr_hist` → `gld_skew25` volta a gravar (26/11: +2,87 pts, venc. 24/12). Put/call de contratos em aberto total pelo Yahoo = 0,43 mesmo com todos os vencimentos (Cboe dava 0,29): diferença é do contrato em aberto do Yahoo, não da janela; comparar dias só da mesma fonte. |
| DTCC | `dtcc.py` (≤ 150 s): balcão de opções de câmbio; estado `dtcc_estado.json` → `mi_otc.json`, `mi_otc_hist.json`. Card escondido. **P7 (26/11, Code):** dia só vira coberto com o arquivo fechado lido (404 recente = tenta de novo; > 4 dias = feriado); dia lido só pelos pacotes fica em `prov` até o arquivo sair; `erros` = só da rodada (`erros_total` acumula); vol. implícita exige 10 negócios, alarga para 48 h/72 h (`janela`), < 5 em 72 h = sem vol. (`testes/min_negocios_dtcc.py`). |
| Liquidez | `b_liq`: TGA pelo Tesouro (fiscaldata, 25 s); se falhar (27/11: 504/lento), TGA semanal pelo FRED (WTREGEN) com aviso no status; RRP, SOFR e Fed funds (Fed de NY) não caem mais junto. |
| Proteções | `coleta.yml` para se não ler a branch `dados` (não apaga históricos). `b_boletim` marca no status quando o boletim não chegou até 12h30 do dia útil seguinte; `alarme_cme.yml` (12h45) falha nesse caso para o GitHub avisar por e-mail (e-mail não testado). |
| 1 min | `minutos.py` 1×/dia ~01h UTC → branch `minutos` (`AAAA-MM-DD.csv.gz`: GC, SI, DXY, 6E, 6J, 6S). |
| Branches | `main` (código), `dados` (coleta), `minutos`, `pdfs`, `log` (log do robô do PC), `regua` (sem uso, pode apagar). |

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

- **RÉGUA ATUAL (27/11/2026, vale sobre o histórico abaixo):** GC fev. − XAUUSD Vantage = **US$ 27,6** medido no mesmo minuto (25/11 18:30 UTC), encolhendo em linha reta até 24/02/2027 (`REGUA` e `base_vantage()` no `coletor.py`; mesmas constantes no `confere_opcoes.py`). **Remedir 1 vez por semana** (candle M1 do MT5) e a cada troca; passou de 7 dias, o `mi_status` avisa. CME: nível = strike − régua quando a opção é sobre o contrato do GC=F; o preço do ajuste é a barra que TERMINA às 13h30 NY (antes usava 13h35: ~US$ 7 de erro).
- **Trava das opções do ouro (27/11/2026):** `travas_0dte()` no `coletor.py`: sem contratos em aberto, GLD parado ou sem o ouro do mesmo instante → nenhum nível do GLD é publicado, fixado, gravado ou mandado à IA (`sem_dado_gld`); teto abaixo/piso acima do preço, faixa sem o preço, max pain a > 10% e régua da CME fora de US$ 3 também caem; aviso no `mi_status`. Conferente independente: `confere_opcoes.py <pasta dados>`. Registros inválidos marcados por `b_limpa()` (originais em `mi_invalidos.json`). Janela de 3% no preço atual; cadeia da CME inteira (max pain); flip da CME guardado na escala do futuro; charm = variação real do delta até o vencimento; `preco_hora` na tela.
- Histórico (substituído): **Ouro no painel = régua da Vantage = GC=F − US$ 6,5.**
  - O fator `f = 1 − 6,5 ÷ GC` vale para TUDO do ouro: série, barras de 1 h do mapa, razão do GLD e régua da CME.
  - No código: `VANTAGE_USD = 6.5` e `CALIB = "16/11/2026"`, em `b_precos()`.
  - Calibrado com pares simultâneos ditados por ela: GC 3.882 × Vantage 3.875; 3.880 × 3.874.
  - O à vista teórico (~−US$ 20) **não** bate com a Vantage.
  - **Troca de contrato feita em 25/11/2026:** o Yahoo passou o GC=F para fev. (~US$ 29 acima do dez.); a Vantage segue o dez. (3.515 com dez. 3.516,8 → dez. − US$ 1,9). Regra automática em `b_precos`: se GC=F ≠ mês mais perto, ajuste = (GC=F − mês mais perto) + 1,9 (hoje ≈ US$ 31). Só 1 par: **reconferir com 2 pares ditados por ela**. Níveis da CME agora usam o preço do contrato que o GC=F é hoje no horário do ajuste (`b_0dte`). **Conferido em 26/11 (Code):** série contínua de 24 para 25/11 (sem salto), régua US$ 29,3, níveis GLD e CME coerentes com o preço. **Série diária ajustada por contrato (P2, 26/11, Code):** o Yahoo só trocou a série DIÁRIA do GC=F em 26/11 (var. do dia saía +1,63% falso); `b_precos` grava cada troca em `mi_rolagem.json` (branch `dados`: data, razão seguinte ÷ perto na véspera) e multiplica tudo antes da troca pela razão (26/11: 1,00815) → var. 1d/5d/20d/ano, ATR, 52s, correlações, valor justo, CTA e score sem salto (var. do dia 26/11: +0,81%). Trocas anteriores a 26/11 seguem com o salto (o Yahoo não guarda contratos vencidos).
- **GLD → ouro:** razão ouro ÷ GLD congelada no `last_trade_time` do GLD (ouro do GC 5 min × fator, naquele horário).
  - GLD fechado ou parado → usa o `close` oficial (a Cboe manda preço de pré-mercado com horário antigo).
  - Gamma (regime e flip) é recalculado com o ouro ao vivo na escala do GLD (`Sv = ouro / r`).
  - Bug antigo: esse cálculo deslocava ~US$ 38 à noite.
- **CME ouro → painel:** nível × (GC=F 5 min às 13h30 NY do pregão ÷ futuro pela paridade) × fator.
- **CME iene → USDJPY:** strike 1/K (call de iene = put de USDJPY); régua = JPY=X às 15h NY ÷ (1/F).
- **CME em equivalente GLD:** contratos × ouro ÷ GLD (~10,9 GLD por contrato de ouro).
- **Moedas, barra diária do Yahoo (P3, 26/11, Code):** abertura e fechamento de cada barra diária `=X` são o preço do INÍCIO dela (≈ 17h–19h NY da véspera); máx./mín. são do dia certo. `b_precos` usa como fechamento do dia D a abertura da barra seguinte (desde 2011; antes o Yahoo é misturado). EURUSD × DXY: +0,21/−0,08 → −0,93 (20 d) / −0,82 (250 d). Corrige var. 1d, correlações, sazonalidade, ATR e valor justo das moedas.
- **Testes de toque e de máx./mín.: só FUTUROS da CME (GC, 6J, 6E, 6S, 6B).** O Yahoo FX (`JPY=X` etc.) tem picos falsos nas máximas/mínimas e já inventou uma "defesa" de 70% que era só sujeira. Fechamentos do Yahoo FX servem.
- **Var. do dia do ouro (26/11):** `b_faixa` regrava `var_1d` do XAUUSD no `mi_ativos` como preço ÷ abertura da sessão (a barra diária do GC=F fecha no ajuste, 13h30 NY, e invertia o sinal).
- **Sessão do dia:** abre às **18h NY (20h BRT) para todos** (18/11: ela conferiu o candle de abertura da corretora, gráfico em horário de NY; antes as moedas abriam 17h NY). Semana das moedas: Yahoo FX só tem domingo a partir das 19h NY → abertura das 18h estimada pelo futuro da CME × razão à vista/futuro. O σ do mapa congela na 1ª coleta da sessão/semana (`mapa_fixo.json`). **27/11 (Code):** a sessão segue o relógio (18h NY, dia útil), não a última barra do Yahoo; sem barra da sessão nova (26/11: o Yahoo parou o 1 h de todos os futuros da CME em 25/11 23h NY), abertura = preço da 1ª coleta, congelado (`ab_est` no `mapa_fixo`) e `mapa.ab_estimada = true`. Chave da semana = `ativo|sem|segunda` (corrigido 16/11: na segunda o σ da semana saía igual ao do dia).

---

## 4. O que está no painel (aba Mercado, de cima para baixo)

> **27/11/2026 (decisão do Gabriel, vale sobre o que houver de antigo abaixo ou no §2/§3):** das opções, a tela, o `digest.txt` e a IA mostram **só call wall e put wall da CME** (ouro e iene) e o mapa de barras. Saíram: borboleta, GLD como nível próprio (voltou só como complemento, ver abaixo), flip, max pain, regime, gregas, pin, PCR, faixas por straddle e faixa da CME; a coleta continua gravando em arquivo. Faixa do dia única: GVZ a partir da abertura das 20h (±0,44σ metade; ±1σ 82%, 3.770 dias). Abertura estimada: avisa e não marca toque, máxima, mínima nem rompimento. Voltar exige 60 pregões e passar de 97,5% de níveis sorteados (`claude/quant-opcoes-fica-sai.md`).

0. **Cabeçalho "Dados de …"**: mostra também "CME: boletim de dd/mm (preliminar/final), chegou dd/mm hh:mm" (`cmeInfo()`, campo `recebido_em` gravado pelos leitores; 20/11).
1. **Panorama do dia:** leitura da IA; Fear & Greed, red folder, VIX, DXY.
2. **Macro, o que move o dólar:**
   - Radar institucional: liquidez, estresse, surpresa, regime EUA.
   - Dólar e juros: bps no cabeçalho, coluna "Leitura (fechamento)" só com Dólar/Iene e os pares (XAUUSD, EURUSD, USDJPY) com seta, verde = sobe, vermelho = cai (17/11). Resumo diz a data do fechamento dos juros dos EUA (não é "hoje"). Descreve o fechamento, não prevê.
   - Fed Funds usa o contrato fixo do mês (ex.: ZQZ26.CBT).
3. **Ativo, níveis e opções** (o seletor gruda no topo):
   - **"O que olhar hoje"** (20/11, pedido dela: painel confuso; `drawRS()`, `.op-card.rs`): σ do dia em pips/US$, dia normal (= grade) e stop (90%), níveis −1σ/normal/abertura/normal/+1σ com ✓, "Agora" (posição em σ + rompimento), resto do dia (Ásia+Londres), hora (ouro), "Direção: nenhum sinal comprovado". O mapa detalhado (tabelas, faixa, rompimento, precisão, conferência) fica em `details.mp-det` recolhido.
   - **"Quando o mercado fica lateral"** (24/11/2026, pedido dela; `drawLat()`, `.op-card.lat`, `docs/data/lateralidade.json`, igual nos 5 ativos): % de dias estreitos/normais/largos e de corpo pequeno, ontem → hoje, payroll (dia e semana), horas paradas/agitadas (Brasília), mês só onde passou (USDJPY). Dia da semana e semana do mês: **nenhuma diferença comprovada** (o "efeito segunda" das barras diárias do Yahoo era artefato do corte à meia-noite; na sessão real 18h→17h NY não existe). Scripts `testes/lateralidade.py` (15 anos diário, 75 testes, Bonferroni, metades) e `testes/lateralidade2.py` (sessão real 2 anos, persistência, GVZ). Registro diário para medir notícias: `mi_lateral_diario.json` (amplitude em σ, corpo, red folders do dia; 16h–18h NY).
   - **Padronização (24/11/2026, pedido dela): mesmo cálculo, mesmo roteiro e mesmos números em todos os ativos.** `docs/data/padrao.json` é a fonte única (dia normal, cortes Ásia+Londres, horas do ouro): a tela (`qNormal/cCedo/hOuro`) e o resumo da IA leem dali. A leitura da IA segue o mesmo roteiro para os 5 ativos ([σ], [DIA fixo], [SEMANA fixa], [AGORA], [LATERALIDADE], [RESTO DO DIA], [OPÇÕES]); só a linha de opções muda (ouro e iene = paredes da CME, euro/franco/libra = σ pelas opções de balcão DTCC, sem 0DTE próprio). **Qual σ olhar:** o do DIA fixo na abertura (card "O que olhar hoje", mesmo número do mapa e da IA; testado: ±1σ 78–83%, ±2σ 96–99%); o da SEMANA para posição de vários dias (73–83% / 97%); 0DTE = complemento ainda sem teste (fim de dez.).
   - **Mapa "até onde o preço deve ir":**
     - tabelas Hoje e Semana, níveis ±0,5/1/1,5/2σ a partir da abertura;
     - "chance agora": z = distância log ÷ (σ × √fração restante), com a curva real medida em 2 anos de 1 h (`toque_tabela.json`);
     - leitura em palavras: alvo provável ≥ 50%, possível 20–49%, difícil 8–19%, raro < 8%;
     - "Teste um preço" aceita vírgula e ponto.
   - **Rompimento do σ do dia** (`.mp-romp`, `rompimento.json`): preço de cada gatilho (±1σ/±1,25σ/±1,5σ), o que costuma acontecer depois e a linha "Hoje: em cima Xσ → …".
   - **Faixa esperada:**
     - ouro = GVZ (faixa única);
     - moedas = **vol. implícita das opções de balcão (DTCC)**: `dtcc.py` → `mi_otc.pares[].vol_impl` (negócios das últimas 24 h, prazo 1–30 d, strike ≤ 1% do preço na hora, prêmio → Black; mediana; ≥ 5 negócios); `b_faixa` usa se o mi_otc tiver < 3 h; reserva: vol. realizada 21 d × 1,09. 17/11: USDJPY DTCC 6,76% × CME 6,82%;
     - etiqueta da vol. contra a média de 1/3/5 anos (pesos 50/30/20);
     - tabela **Precisão medida** visível (`faixa_backtest.json`).
   - **Conferência diária** (`mi_validacao.json`): toque real × chance prevista, faixa e 0DTE (GLD e CME separados).
   - **Call wall e put wall (CME)** (`.op-card.pw`, `b_paredes` → `mi_paredes.json`; histórico `mi_paredes_hist.json`; rótulo "referência, sem teste"): fixas na chegada do boletim; soma o contrato em aberto dos vencimentos coletados ainda vivos (ouro: semanais + próximo mensal, desde 27/11 11h28; mudança registrada em `mudancas`); só strikes a até 1σ semanal do ajuste; call = mais calls acima, put = mais puts abaixo; ouro nível = strike − régua; iene = USDJPY às 15h NY × F ÷ strike (call do USDJPY vem das puts de iene); preço passou = "rompida" + 2ª parede. Mapa (`drawMapaOp`): puts à esquerda, calls à direita, paredes, 2ª tracejada, preço com horário. Conferente independente `confere_opcoes.py` (roda em toda coleta). 25/11: ouro 3573 / 2ª 3673 / put 3473.
   - **Faixa do ouro** (27/11 12:34; vale no lugar do ±0,44σ/±1σ como teto): 80% e 95% em destaque, 50% dia normal, "não sai por nenhum dos dois lados". k de 250 sessões do GC (`mi_faixa_k.json`, aprovado contra 1,00/1,55/2,44); registro e acerto em `mi_faixa_ouro.json`; `confere_faixa.py`. **HAR+GVZ em sombra (27/11 13h):** `b_har` com a semente `dados_fixos/semente_rv.csv` (500 sessões da Vantage) + variância do MT5 ou do GC 5 min ajustado; grava `mi_har_rv.json` e `mi_har_sombra.json`; troca só com 60+ sessões, erro menor e intervalo de 95% sem cruzar zero. Nada na tela.
   - **Grandes fora da faixa** (27/11 12:22): strikes entre 1σ e 2σ semanal do ajuste com mais contratos que a parede do mesmo lado (`fora_call`/`fora_put`); aparecem na tabela, no mapa (eixo até 2σ no máximo), no digest e na IA; não são parede. Boletim 25/11: calls 3723, 3773, 3873; puts nenhuma.
   - **GLD complementar** (27/11): foto única do dia (`mi_gld_oi.json`) na 1ª coleta com pregão aberto (10h–16h NY), contratos em aberto > 0 e GLD não parado, vencimentos até o mensal; vale no máximo até o dia útil seguinte; mesma regra de parede sobre o ajuste da CME; tamanho em contratos equivalentes (n ÷ razão); a até US$ 6 da parede CME = "coincide com o GLD" (nunca "confirmada": não é teste); mais longe = linha roxa própria; sem foto válida = "GLD sem dado". Não soma nem move a CME. Uso: referência no gráfico, não serve para entrada, saída nem proteção.
   - **Vencimento mensal da CME** (`ouro_mensal.json`, só para teste futuro; leitor e `confere_cme.py`).
   - **Balcão (DTCC):** não aparece na tela, só grava.
   - **"Mais sobre o ativo e o mercado"** (`details.mais`, recolhido): Regime, CTA (só ouro), preço/ATR, sazonalidade, COT, correlações, Goldbach, tabela macro.
4. **Agenda e notícias:** Forex Factory com "Atual" ao vivo (biquote/BLS/FRED); notícias com filtro. **Histórico recolhido (25/11, pedido dela):** Agenda da semana e "Eventos de hoje em diante" (aba Alto impacto) mostram só de HOJE em diante; dias anteriores ficam atrás do botão "▸ Ver N eventos de dias anteriores" (`barraAnt()`, barra ACIMA da tabela). Calendários (Alto impacto e Goldbach): mês atual e seguinte abertos; o anterior em `details.gb-ant` recolhido (Goldbach só mostra o anterior se houver dados dele).
- **Aba Dias de alto impacto:** calendário EUA + Goldbach/Hopiplaka (`goldbach_gen.py`).
- **Cores dos níveis:** teto vermelho, piso verde, flip âmbar, max pain roxo, faixa azul, ±1σ verde-água, ±2σ marrom.

**Convenções do front (`app.js`):**
- Mapa de opções: linhas finas por baixo; barras das paredes e das calls grandes por cima e mais grossas. Faixas escritas com "a" (sem travessão).
- `toqueMapa()` (27/11): mouse ou toque no mapa de opções mostra preço, strike, contratos e distância. `semCedo()` explica por que a leitura das 11h não apareceu.
- `drawMapaOp(el, w, cs)` desenha o mapa das opções a partir de uma linha do `mi_paredes`.
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
| **Dia típico em σ** (`testes/dia_tipico.py`, futuros diários 15 anos, ~3.750 dias cada) | Metade dos dias fecha a ≤ 0,55σ da abertura (moedas; ouro 0,45σ); 68% ≤ 0,85σ; 90% ≤ 1,5σ. Amplitude máx−mín mediana 1,2σ. Ouro com σ GVZ: 0,44σ / 90% ≤ 1,35σ / amplitude 1,05σ. Estável. **Na tela: bloco "Dia normal" do mapa** (`.mp-normal`, constantes `Q` no `app.js`). |
| **Ásia + Londres → tamanho do resto do dia** (`testes/range_cedo.py`, futuros 1 h, 2 anos, ~555 dias) | Amplitude 18h→9h NY em σ × amplitude 9h→17h: r 0,30–0,50 (t 7–14), metades estáveis. Cedo no terço alto → resto grande 61–73%; terço baixo → 30–42% (acaso 50%). Ouro (σ GVZ) o mais fraco: r 0,30 (metades 0,36/0,22). Na tela a partir das 11h BRT (`mapa.amp_cedo`, medido no futuro da CME; constantes `C` no `app.js`). Diz o TAMANHO, não o formato nem a direção. |
| **Horário em que o ouro anda menos** (`testes/horas_lateral.py`, GC 1 h 2 anos, metades estáveis) | Amplitude por hora em σ do dia: mais parado 17h–01h BRT (0,19–0,24σ/h ≈ US$ 12–15) e 14h–16h (0,24–0,27σ); mais agitado 10h–12h (0,48σ/h ≈ US$ 30) e 09h/22h (~0,38σ). Só TAMANHO: a proporção de horas "vai e volta" (5 min, 60 dias) é ~45–55% em todas as horas, sem horário mais ping-pong. Horas BRT misturam horário de verão americano (±1 h). Ainda não está na tela. |
| **Vol. das opções de balcão (DTCC) nas moedas** (`testes/vol_dtcc.py`, 2 anos, 380–480 dias/par) | Prevê a amplitude do dia melhor que a vol. realizada nos 4 pares: r 0,35–0,55 × 0,18–0,45, metades estáveis. ±1σ dia 78–83%, ±2σ 96–99%; semana 73–83% / 97–98%. Dia normal com σ DTCC: 50% ≤ 0,43–0,57σ, 90% ≤ 1,20–1,50σ, amplitude 0,97–1,16σ (constantes `Q`; cortes `C` reescalados pela razão realizada/DTCC). Precisão na tela via `faixa_backtest.json[par].dtcc`. Só opções ≤ 2 dias (`TENOR=2`): σ ~50% maior (USDJPY 15,6% × 10,7%), ±1σ contém 89–93% e prevê um pouco pior (r 0,31–0,51) → mantido 1–30 d. **Métricas do mapa das moedas refeitas com o σ DTCC** (`testes/metricas_dtcc.py`, série `testes/vol_dtcc_serie.json`): `toque_tabela.json` e `rompimento.json` das moedas (campo `sigma: "DTCC"`, 378–483 dias). Ex. USDJPY: toca +1σ 14% (antes 22%), fecha dentro ±1σ 83%; tocou 1σ → fecha fora 45–54%; passou 1,25σ → 64–76%; passou 1,5σ → 73–85%. Iene: toca 1σ metades 41%/30% (instável, 2025 teve choques). CME iene só desde 11/2026 → sem histórico para medir. |
| **Lateralidade** (`testes/lateralidade.py` e `lateralidade2.py`; estreito = amplitude ≤ 0,70 × média dos 20 dias anteriores; 75 testes, corte p 0,0007, estável nas metades) | % de dias estreitos: ouro 31, iene 30, libra 27, euro 24, franco 24; largos 15–19. **Payroll (1ª sexta): estreito só 7–13% (normal 24–32%), largo 25–42%** (5 ativos). **Ontem estreito → hoje estreito 28–41%; ontem largo → 16–22%** (p < 1e-5, 15 anos). Semana do payroll: mais larga em iene/euro/franco/libra/ouro. Horas (Brasília): mais paradas 17h–20h e 01h; mais agitadas 10h–12h e 22h. Dia da semana, semana do mês: nada (sessão real, 2 anos). Mês: só iene (abr/out/dez mais laterais, nov mais volátil). Ouro: GVZ bem abaixo do normal → 35% dias estreitos (normal 29%), efeito pequeno. |
| **Faixa do NAS100 pelo VXN** (`testes/faixa_vxn.py`, 2001+, NQ=F e ^NDX, ~6.500 dias) | Dia ±1σ 77–78% (metades 77/79, últimos 5 anos 74%), ±2σ 97,5%; semana 77–78% / 98%; mês 75–76% / 98–99%. Igual ao GVZ do ouro. No `mi_faixa` desde 26/11 (P11, Code): `FONTE["NAS100"] = ^VXN`, faixa a partir do preço de agora; **sem mapa** (sessão 18h NY, toque e rompimento não feitos para o índice à vista). Na tela ("O que olhar hoje" e faixa) e na IA (linha [FAIXA]) desde 26/11. |
| Regime forte | Mantém a direção por 13 semanas: DXY 91–100%, juros 57–90%. |

### Não passou (não usar como sinal)
| Teste | Resultado |
|---|---|
| **σ das opções × formato do dia** (hipótese dela: σ curto = lateral) | Formato igual em qualquer σ: ~1/3 ping-pong, ~1/3 tendência (t = −1,3). O σ diz **quanto** o preço anda, não **como**. |
| Ping-pong × tendência (eficiência = \|fech − abert\| ÷ caminho percorrido; ping-pong ≤ 0,12, tendência ≥ 0,30) | Nada antecipa com dado grátis: eficiência da véspera, GVZ (nível, variação, prêmio), gap, dia da semana, Ásia + Londres até 10h BRT → todos ~33%. |
| σ como ponto de reversão | 40–53% em todos os níveis; o 1σ não é especial. |
| "Defesa" (passou e voltou) | Nos futuros: 44–52% (acaso = 50%). Os 70% eram sujeira do Yahoo FX. |
| Momentum do fim do dia no ouro, sem gamma (Baltussen; `testes/momentum_fim.py`, GC 1 h 2 anos + 5 min 60 dias) | Retorno 18h→13h/15h/16h25 NY não prevê o trecho final (melhor t −2,3, metades instáveis; 4 testes). Com gamma: esperar o diário. |
| Regras de trader (`testes/regras_trader.py`, futuros 1 h 2 anos + diário 15 anos, 35 testes, corte \|t\| ≥ 3) | 1ª hora NY, noite → NY, Londres rompe Ásia, varrida da máx./mín. de ontem, dia estreito → tendência, fechou na máxima → amanhã, gap de domingo: nada útil. Só "fechou perto da máxima → ouro cai amanhã" (t −3,9), mas acerta só 54% e enfraquece na metade recente. Gap de domingo (`testes/gap_domingo.py`, 15 anos): euro t 4,0 instável (metades 0,26/0,01), resto nada. |
| **Fluxo das opções DTCC → direção** (`testes/fluxo_dtcc.py`, 2 anos, 4 pares, 32 testes) | Calls − puts (tamanho e prêmio), skew das fora do dinheiro, variação da vol.; madrugada → resto do dia e dia → dia seguinte: nada passou (melhor t 2,0, metades instáveis, acerto 42–54%). A DTCC não diz quem comprou, então não dá fluxo comprador × vendedor. |
| **Scalp pelo fluxo DTCC** (`testes/scalp_dtcc.py`; 5 min 60 dias + 1 h 2 anos; negócio grande ≥ US$ 50/200 mi e sequência ≥ US$ 100/300 mi em 15 min do mesmo lado; a partir do negócio e da publicação) | Preço nos 5–120 min seguintes: acaso (acerto 40–58%, melhor t 2,9 em ~100 testes). EURUSD "sequência ≥ 300 mi → reverte em 60 min" (t −2,9 em 60 dias) NÃO se confirmou em 2 anos (t +0,6). Obs.: tamanho com "+" (teto da DTCC) era descartado; corrigido. Só ≤ 2 dias (`TENOR=2`, 60 dias): GBPUSD ≥ US$ 50 mi → +0,7 pip em 5 min (t 3,6) e +1,6 em 15 min (t 3,2), metades estáveis, acerto 63%; a partir da publicação t 3,0/2,8; EURUSD t 2,2; demais acaso. Borderline (~128 testes), efeito ~ spread → `minutos.py` passou a gravar 6B (libra) para reteste com 1 min em fev/2027. 1 min (8 dias): efeitos < 0,3 pip (menor que o spread), acaso. O painel só vê o negócio na coleta seguinte (5 em 5 min). Tempo real de agressão só com fluxo dos futuros (Databento ou DOM da corretora). |
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

- **Níveis em sombra** (27/11, Estratégias): `mi_niveis_sombra.json`, 1 foto na 1ª coleta de cada hora com o ouro negociando (1σ GLD, 1σ CME, flip CME), só acrescenta; nada na tela, digest ou IA. Critério de medição: `claude/quant-niveis-sombra.md` (leitura semanal, conclusão com 40 sessões). A 1ª foto (27/11 14h47) tem `original` errado nas 2 linhas do GLD (o nível está certo; valor certo = nível ÷ razão).

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

1. Acompanhar a automação dos PDFs nos primeiros dias (log: `~/.local/state/painel-cme.log` no PC dela).
2. Recalibrar a régua da Vantage na troca do GC (fim de nov.).
3. Euro e franco na CME: achar as seções no boletim; seguir o molde do iene.
4. Rodar os testes da §6 nas datas. Ideias anotadas: rompimento por horário (Ásia/Londres/NY), rompimento com × sem red folder, gamma × rompimento, rompimento no σ da semana, grade do robô medida em σ.
5. Pergunta sem resposta: suavizar o gamma flip do GLD (média de 15 min)?
6. Conferir os leitores em 01/01/2027. Databento quando ela assinar.

- **Régua automática (27/11 12:22):** fonte xaus.com reprovada e removida. Vale a régua datada. **Régua pelo MT5 (27/11, aprovado):** `mt5/ReguaPainel.mq5` (só leitura, não compilado) manda o XAUUSD de 1 min ao repositório SEPARADO `gabrid15-creator/painel-regua` (`ultimo.csv`; a chave só desse repositório, nunca com acesso à main). `b_regua_mt5` casa com o GC fev no mesmo minuto e grava `mi_regua_mt5.json` (mediana do pregão; válido com 60+ minutos, dispersão até US$ 1, mudança até US$ 3); `confere_regua.py`. SÓ GRAVA: trocar a régua datada exige 3 pregões válidos e nova decisão. A abertura do ouro usa a barra 18h00 do MT5 quando a régua do último pregão é válida (`mapa.ab_fonte`). Falta: criar o repositório (público, só o Gabriel), a chave e instalar no servidor previsto para 29/11.
- Auditoria de 26/11: resta ver o P1 ao vivo em 30/11. Opções do ouro (27/11) corrigidas, falta a reconferência de Estratégias. Régua: remedir até 02/12.

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
