# Painel de mercado — resumo do projeto

**Site:** https://gabrid15-creator.github.io/painel-mercado/
**Repositório:** `gabrid15-creator/painel-mercado` (commit e push direto na `main`)
**Horário de referência:** sempre Brasília.

---

## 1. Como funciona (arquitetura)

| Peça | O que faz | Onde |
|---|---|---|
| **Coleta** | Roda a cada 5 min, busca todos os dados e grava JSON | `coletor.py` + `.github/workflows/coleta.yml` |
| **Disparo** | cron-job.org chama o workflow a cada 5 min (o cron do GitHub não disparava) | cron-job.org (token GitHub "cron painel", só Actions) |
| **Dados** | JSON ficam na branch `dados`; o site lê via `raw.githubusercontent.com` | branch `dados` |
| **Site** | HTML/JS estático, publicado no GitHub Pages **só em push** (código) | `docs/index.html`, `docs/app.js` |
| **Leitura da IA** | Haiku 5.5 escreve o texto geral e de cada ativo (sem viés: faixas, regime, eventos) | `ia.py`, segredo `ANTHROPIC_API_KEY` |
| **Opções da CME (ouro e iene)** | A usuária manda os PDFs do boletim na conversa; o Claude lê (`cme_pdf.py`, `cme_pdf_iene.py`), grava em `cme/` e faz push; a coleta carrega (`cme_local.py`) | ver seção 4 |

**Frequência da IA:** 6h–18h de hora em hora · à noite só 20h e 0h · sempre após red folder · parada sex 18h → dom 18h. Custo real ≈ US$ 0,003/leitura (~R$ 5–6/mês).

---

## 2. O que já está no ar

### Aba Mercado
- **Topo:** Fear & Greed, Red folder do dia (lista), VIX, DXY — com selo, régua e lista.
- **Leitura do dia (IA)**, sem viés de direção.
- **Radar institucional:** liquidez líquida do Fed (balanço − TGA − RRP), estresse (VIX ÷ VIX 3m, MOVE, NFCI), surpresa econômica por moeda (90 dias) e regime dos EUA.
- **Dólar e juros:** EUA 13 sem / 5a / 10a (intraday), Fed Funds implícito (futuro) vs. efetivo, JGB 10a, diferencial EUA−Japão, Bund 10a, diferencial EUA−Alemanha, GDPNow.
- **CTA (estimativa):** posição dos fundos de tendência por ativo (−100% a +100%) e gatilho de virada mais próximo.
- **Seletor de ativo** (gruda ao rolar) → mapa de probabilidades (níveis e chance de toque), leitura da IA do ativo, preço, valor justo, sazonalidade (padrão 10 anos), ATR.
- **Sazonalidade, caminho do mês, COT, correlações, Goldbach x extremos e sweeps (10 anos).**
- **Tabela macro** (juros, dólar, liquidez, risco, energia) + gráfico.
- **Agenda da semana** (Forex Factory) com **Atual em tempo real**:
  - biquote.io (navegador, 15 s perto das divulgações);
  - **BLS direto no navegador** (payroll, desemprego, salário-hora, CPI, PPI) — segundos;
  - FRED via coleta (seguro-desemprego, varejo, PCE, JOLTS, PIB) — minutos;
  - caixa verde/vermelha acima/abaixo da previsão, "Acabou de sair", dia de hoje em âmbar, cabeçalho fixo.
- **Notícias** (RSS, filtro por ativo).

### Aba Dias de alto impacto
Junta, um embaixo do outro: **Alto impacto EUA** (calendário de 3 meses só com dados americanos de alto impacto, dias Goldbach marcados, lista com previsão/anterior/atual) e **Dias Goldbach e Hopiplaka** (calendário, próximos dias, tabela).
A aba **Paredes de opções** foi removida em 12/11/2026 (o painel já mostra 0DTE, faixa e paredes por ativo; código do TradingView descontinuado).

### Visual
Ícone, manifest (app no celular), modo claro/escuro, cards com sombra, abas em pílula, "Como ler" em todo indicador.

---

## 3. Arquivos

| Arquivo | Função |
|---|---|
| `coletor.py` | Coleta tudo (Yahoo, Tesouro EUA, Fed NY, Bundesbank, FRED, Fed Chicago, MOF Japão, CFTC, CNN, Forex Factory, BLS, RSS) e calcula score, sazonalidade, correlações, COT, sweeps, CTA |
| `ia.py` | Leitura da IA (Anthropic, Haiku 5.5) |
| `opcoes_drive.py` | Importa o arquivo de opções mais recente da pasta do Drive (fluxo antigo) |
| `cme_pdf.py` / `cme_local.py` | Lê o PDF do boletim da CME enviado pela usuária → `cme/opcoes_<pregão>.json` → carregado pela coleta |
| `goldbach_gen.py` | Gera `docs/data/goldbach_dias.json` |
| `docs/index.html` / `app.js` | Site (abas Mercado e Dias de alto impacto) |
| `docs/data/*.json` | Cópia de reserva dos dados (o site prefere a branch `dados`) |
| `.github/workflows/coleta.yml` | Coleta → branch `dados`; site → Pages só em push |

---

## 4. Opções de ouro da CME (fluxo especial)

- **Rotina atual (desde 13/11/2026):** seg–sex ~8h a usuária manda 3 PDFs na conversa: ouro (Section64), iene calls (Section33) e iene puts (Section34). O Claude roda `python3 cme_pdf.py <pdf ouro>` e `python3 cme_pdf_iene.py <calls> <puts>`, depois **obrigatoriamente** `python3 confere_cme.py --ouro <pdf> cme/opcoes_<pregão>.json --iene <calls> <puts> cme/iene_<pregão>.json` (só publica com 0 erro; avisos são explicados à usuária), faz commit dos arquivos em `cme/` e push na main. Lembrete .ics na agenda dela (8h, com os 3 links).
- A tarefa agendada antiga ("Opções de ouro CME (noite)") está DESLIGADA: a CME bloqueia robôs.
- **13/11/2026: a CME passou a bloquear robôs (detecção de bot) desde ~06/11** — vale para GitHub, Claude e outros servidores. Tarefa noturna DESLIGADA (gastava cota sem trazer nada). Burlar o bloqueio: descartado. Fonte paga (Databento): recusada. **Horário da CME (página do boletim, 13/11):** preliminar sai ~00h CT = ~03h BRT do dia seguinte ao pregão; final ~10h CT = ~13h BRT. Lembrete da usuária: seg–sex 8h BRT. **Fluxo novo (grátis):** a usuária baixa de manhã o PDF "Metals Option Products" do boletim diário (https://www.cmegroup.com/daily_bulletin/current/Section64_Metals_Option_Products.pdf) e manda na conversa com o Claude; o Claude roda `python3 cme_pdf.py <pdf>` (séries de sexta OG/OG1–OG5 que vencem em até 2 dias úteis + a 1ª com ≥ 3 dias; futuro por paridade call−put) → grava `cme/opcoes_<pregão>.json` → commit e push na main; `cme_local.py` (passo do workflow) carrega em `ouro_cadeia`/`ouro_boletim`. Semanais de seg–qui: só a série curta, separada pelo preço (ver 5.6). 1º pregão carregado: 12/11/2026.
- **Automação pelo PC da usuária (16/11/2026):** `pc/baixar_cme.sh` + `pc/painel-cme.timer` (systemd de usuário, seg–sáb 3h30 → 8h de 30 em 30 min): baixa os 3 PDFs com curl da internet de casa (sem driblar bloqueio: se a CME recusar, só registra em `~/.local/state/painel-cme.log`), só envia se mudou (hash), e empurra **um único commit só com os PDFs** para a branch `pdfs` (force; o repo não cresce). O workflow `.github/workflows/cme_pdfs.yml` (push em `pdfs`) roda `cme_pdf.py`, `cme_pdf_iene.py` e `confere_cme.py`; **só grava na main com 0 erro** (erro → job falha e o GitHub avisa). Falta: instalar no PC (passo a passo enviado), token do GitHub com permissão só neste repositório.
- **Automação planejada (adiada, 13/11/2026):** celular Android da usuária, ~03h30: MacroDroid baixa os PDFs da CME (internet de casa/4G não é bloqueada) → Autosync for Google Drive envia para a pasta "painel-mercado-opcoes" → GitHub Actions lê o PDF do Drive (pdfplumber) e atualiza sozinho. Alternativa: computador Ubuntu com timer que acorda o PC. Falta: confirmar Android, montar a leitura do PDF no Actions, passo a passo dos apps.
- **Iene na CME (13/11/2026):** PDFs separados: `Section33_Japanese_Yen_Call_Options.pdf` (PG 33) e, pelo padrão, `Section34_Japanese_Yen_Put_Options.pdf` (PG 34), em https://www.cmegroup.com/daily_bulletin/current/. Opções de iene contra dólar → converter strike 1/K para USDJPY e call de iene = put de USDJPY.
- Fluxo antigo pelo Drive (pasta **painel-mercado-opcoes**, id `1GTHAZCrqQe_LYxf8OuR3zwqncQmHUunx`, `opcoes_drive.py`) segue no workflow, sem uso; será reaproveitado na automação pelo celular.

---

## 5. Foco atual (atualizado 13/11/2026)

**Prioridade: dólar e juros.** É o que move os pares operados: **XAU/USD, USD/JPY, USD/CHF, EUR/USD**. O euro fica em segundo plano (opções do euro só mantidas, sem evolução).

### 5.1 Testes estatísticos (nada fica no painel sem medição)
1. **CTA × DBMF/KMLM:** retorno implícito do modelo (posição × variação) vs. retorno diário do DBMF (réplica do SG CTA Index) e KMLM, desde 2019. Também vs. COT Managed Money semanal (desde 2016). Se a correlação for fraca → tirar o CTA do painel.
2. ~~Backtest do score~~ feito (ver resultado abaixo).
3. **Juros → pares:** medir quanto variação do 2a/10a EUA, diferencial EUA−Japão, EUA−Suíça, EUA−Alemanha, juro real (TIPS) e DXY explicam o retorno de cada par (correlação móvel, beta, defasagem).

**Resultado 12/11/2026 (dados Yahoo/FRED/CFTC, 2016+):**
- CTA × DBMF: corr 0,19 diária / 0,33 semanal → fraca.
- CTA × COT (nível / variação semanal): ouro 0,59 / 0,51 · iene 0,56 / 0,06 · euro 0,45 / 0,14 · franco 0,27 / −0,23.
- CTA prevendo 20 dias: ouro 54,5% de acerto (t = 2,1, fraco mas significativo); iene 55,5% (t = 1,5, não significativo); franco e euro abaixo de 50%.
- **Feito:** CTA só no ouro; retirado de franco, euro e iene.
- **Score:** backtest dos fatores tendência, movimento, dólar, COT e risco → não prevê 5 nem 20 dias em nenhum par (só a tendência do ouro, t ≈ 2,2). Marcado no site como "resumo do momento, não sinal". A refazer.
- Juros → pares (semanal, mesma semana): DXY é o que mais explica (franco 0,69, euro −0,78). Juro real × ouro −0,39 (mas +0,31 em 2025: regime quebrou). EUA 10a × iene 0,42 (−0,04 em 2025).
- Beta 12m: +10 bps no juro real → ouro −1,6%, iene +0,35%, franco +0,32%, euro −0,27%.
- Juros **explicam** o movimento da semana, mas **não antecipam** a semana seguinte de forma confiável (o sinal aparente vem de desalinhamento de horário no câmbio do Yahoo).
- **Feito:** card "Regime" (correlação 26/52 semanas + reação a +10 bps/+1% DXY, alerta de quebra) → `mi_regime.json`.

### 5.6 Posição dos institucionais — teste 12/11/2026
- **Faixa das opções (vol. implícita):** ouro (GVZ) semana ±1σ = 74%, ±2σ = 96% → **precisa, no painel** (`mi_faixa.json`). Moedas via opções de FXY/FXF/FXE (Cboe): no painel, validação pendente (`mi_faixa_hist.json` grava o histórico).
- **Estoque do GLD (toneladas, diário desde 2004):** acompanha o preço na mesma semana (0,39), mas **não antecipa** (t < 2). Não entrou.
- **Put/call dos ETFs de moeda:** pouquíssimos contratos, não representa institucional. Não entrou.
- **0DTE ouro (GLD, vence todo dia):** faixa do dia (straddle), call/put wall, gamma flip, max pain → no painel (`mi_0dte.json`); validação após ~30 pregões (`mi_0dte_hist.json`). Moedas: sem 0DTE gratuito (ETFs ilíquidos; CME só pela tarefa noturna).
- **0DTE CME:** card mostra GLD (ao vivo) ao lado da CME (ajuste do pregão anterior, do PDF). Desde 13/11/2026 a coluna CME tem teto, piso, max pain, **gamma flip** (vol. de cada opção pelo ajuste, Black-76; exposição com contratos em aberto, recalculada com o tempo restante), **faixa do dia** (straddle no dinheiro) e **±1σ**, todos **convertidos para o ouro à vista** (futuro de dez. ÷ (1 + juro 13 sem × prazo até o venc. do futuro), ~US$ 20). Vencimentos de todos os dias desde 16/11/2026.
- Tarefa noturna renomeada "Opções ouro e euro (noite)": ouro primeiro, inclui séries que vencem em 0–2 dias úteis. Falhou em 12/11 por limite de uso da conta.
- **0DTE gráfico do dia:** caminho de cada nível (teto, piso, flip, max pain, ±1σ) a cada 5 min + perfil de volume por strike; zera no vencimento seguinte (`mi_0dte_dia.json`).
- **Faixa do ouro com duas fontes:** GVZ (Cboe/GLD) e CME (straddle no dinheiro do pregão anterior; tarefa noturna agora grava `settle`).
- **Faixa das moedas:** trocada para vol. realizada 21d × 1,09 (testada); opções dos ETFs de moeda descartadas (pouco negociadas). Etiqueta da vol. vs. média 1/3/5 anos (peso 50/30/20).
- **0DTE gráfico:** valores ao passar o mouse, etiqueta de preço por linha, linhas liga/desliga (escala se ajusta).
- **Termômetro do dólar:** testado (concordância de 5 ativos em 2 h não prevê a hora seguinte: 55%/49%, t < 2) → descartado. Regra: só entra o que prevê com teste.
- **Score e viés removidos (12/11/2026):** 52 testes macro de prazo maior (carry, diferencial de juros, valor justo, juro real, prêmio de vol. do ouro, momento) + 40 diários + intradiário → nenhum prevê direção com segurança. No lugar: **mapa de probabilidades** por ativo (níveis ±0,5/1/1,5/2σ a partir da abertura do dia 17h NY e da semana, chance real de toque em ~2 anos de 1 h, `docs/data/toque_tabela.json`; ✓ quando já tocado; campo para testar um preço). IA sem viés: descreve faixas, regime e eventos.
- **Mapa:** duas tabelas (Hoje e Semana), cada uma com "projetado na abertura de … · vale até …", leitura em palavras (alvo provável ≥ 50%, possível 20–49%, difícil 8–19%, raro < 8%) e resumo em uma frase. σ congelado na 1ª coleta da sessão (19h BRT) e da semana (`mapa_fixo.json` na branch dados): níveis projetados antes do movimento.
- **Dólar e juros:** + Bund 10a e diferencial 10a EUA − Alemanha (Bundesbank). GDPNow: atualiza 6–7×/mês após dados-chave (ISM, varejo, PIB…), em geral ~10–11h ET (12–13h BRT); confira a aba "Release Dates" do Fed de Atlanta.
- GLD é o ETF de ouro mais negociado. IAU avaliado e descartado: < 1% da exposição em ouro das opções do GLD e só vence às sextas.
- **Put/call ratio e sinais de opções → direção (13/11/2026):** 210 testes (PCR total/ações/índices da Cboe 2006–2019 em nível, z-score 20d e média 5d; GVZ nível e variação; GVZ − vol. realizada; SKEW; VIX/VIX3M) × ouro, DXY, iene, franco, euro × 1/5/20 dias, sem sobreposição. Melhor t = 3,0 (PCR z20 → euro 20d), abaixo do corte corrigido (t ≈ 3,7) e instável entre metades. **Nenhum prevê direção. Não entrou.** PCR do GLD e da CME: sem histórico gratuito.
- **Padrões de calendário/sessão (13/11/2026):** 67 testes (retorno por sessão Ásia/Londres/NY em 2 anos de 1 h; dia da semana, virada do mês e continuação/reversão após dia > 2σ e > 3σ em 20 anos) × ouro, DXY, iene, franco, euro. Só passou dólar/franco subindo na Ásia (t = 4,0), mas some no futuro da CME (6S) → falha do câmbio do Yahoo. **Nada entrou.**
- **SMT (13/11/2026):** ouro × prata, ouro × DXY e pares (futuros 6E/6J/6S) × DXY; rompimento de máx./mín. de 24/72 h sem confirmação do par → retorno 4/12/24 h (2 anos de 1 h, 41 testes) e de 5/20 dias → 1/5 dias (20 anos diário, 46 testes). Como reversão: **não funciona** em nenhum. No 1 h o ouro *continuou* após topo com SMT (t ≈ 4), mas só nos topos e só no ciclo de alta de 2025–26; em 20 anos some (melhor t = 2,6). **Não entrou.**
- **SMT intradiário (13/11/2026):** swings (pivô de 3 barras) em 1m (29 dias), 5m e 15m (59 dias), futuros CME: ouro×prata, prata×ouro, ouro×DXY, 6E/6J/6S×DXY. Mede reversão em 5/15/30 barras após confirmar o pivô e se o extremo segura; compara SMT × swing confirmado. 315 testes, corte t ≈ 3,8. Único acima: franco 15m topo (t = 4,1), mas vs. swing confirmado só t = 2,4 → topo do franco reverte com ou sem SMT. Ouro×prata: SMT não reverte (fundos da prata até continuam). **Não entrou.** Amostra curta (limite do Yahoo); refazer com Databento se assinar.
- **SMT intradiário v2 (13/11/2026):** entrada no 1º candle que rompe o último swing (um ativo rompe, o outro não acompanha em até 3 candles); alvo = stop = 0,5 ou 1 ATR, o que bate primeiro em 30 candles; separado em captura de liquidez (fecha de volta) e rompimento. 354 testes, corte t ≈ 3,8 → nada passou. Candidatos (t ≈ 2–2,6, estáveis nas metades): euro×DXY 1m/5m, SMT reverte 57–62% (vs. 50% quando o DXY acompanha); prata×ouro 15m topo 64–65%. Capturas de liquidez no iene *continuam* (só 28–30% revertem). Retestar com amostra maior.
- **Gravando desde 13/11/2026:** put/call diário do GLD (volume e contratos em aberto: total, 0DTE, até 7 e até 30 dias) e da CME (séries curtas da tarefa noturna) + skew 25Δ (GLD ~30 dias; CME 1ª semanal, vol. pelo settle) → `mi_pcr_hist.json` (só branch `dados`, fora do painel). Teste automático: tarefa agendada "Testar put/call, contratos em aberto e skew (CME + GLD) → direção do ouro" (Sonnet, 17/05/2027 10:13); se passar, só propõe o card.
- **Laboratório do ouro removido (13/11/2026):** página `docs/lab`, pasta `lab/`, capturas automáticas (lab, lab-intra, lab-gld), branches `lab-dados`, `lab-gld`, `lab-duka-2020` e tarefa antiga "Inteligência de mercado (madrugada)" apagados.
- **Backtest diário (13/11/2026):** a coleta guarda cada dia/semana do mapa (`mi_mapa_hist.json`) e confere, a cada 5 min, o toque real dos níveis ±0,5/1/1,5/2σ vs. a chance da tabela, a faixa das opções (fechamento dentro de ±1σ/±2σ) e o 0DTE (dentro da faixa e entre as paredes) → `mi_validacao.json`; aparece como "Conferência diária" no fim do card do mapa.
- **Repositório `Jireh-dados` (privado):** mantido para uso futuro; tem a cadeia diária do GLD (Cboe) desde 31/10/2026 em `dados/AAAA-MM-DD/cboe_gld.json`. Captura automática desligada em 13/11/2026 (dados até 12/11 mantidos). Não é usado pelo painel hoje.
- **Dólar e juros (13/11/2026):** resumo do dia (juros EUA subindo/caindo → dólar), coluna "Leitura" por série (dólar/ouro, USDJPY, EURUSD; < 2 bps = neutro) e "Como ler" com EUA − Alemanha → EURUSD. Descreve o dia, não prevê.
- **Faixa das opções (13/11/2026):** colunas Prazo | ±1σ normal | ±2σ extremo (cabeçalho com a cor de cada faixa); linha da fonte diz "vol. hoje X% contra a média Y% → [etiqueta] significado"; Como ler em tópicos com a legenda colorida das etiquetas (bem acima / acima / normal / abaixo).
- **Mapa com "Chance agora" (13/11/2026):** a chance de toque é recalculada pelo preço atual e pelo tempo que falta (z = distância log ÷ (σ × √fração restante)), com curva real medida em 2 anos de 1 h por ativo (estável nas metades; serve para dia e semana; `toque_tabela.json` → `agora_z`/`agora_p`). A fórmula teórica das opções superestimava no meio (45% previsto → 33–40% real), por isso usa a curva medida. Chance da abertura fica em cinza embaixo. Resumo e "Teste um preço" também usam a chance de agora.
- **Gravando surpresas dos EUA desde 13/11/2026:** previsão, anterior e resultado oficial (BLS/FRED) de cada dado de alto impacto → `mi_surpresa_hist.json`; nowcast de inflação do Fed de Cleveland 1×/dia → `cleveland_nowcast.json` (bruto, formato a definir). Testar em ~6 meses se nowcast e surpresa anterior preveem o lado da surpresa; só entra se passar.
- **Gravando candles de 1 min desde 13/11/2026** (ouro GC, prata SI, DXY, euro 6E, iene 6J, franco 6S; Yahoo, grátis) → branch `minutos`, um `AAAA-MM-DD.csv.gz` por dia (~70 KB), `minutos.py` 1×/dia ~01h UTC. **Teste pré-registrado em ~3 meses (fev/2027), só estas 4 hipóteses** (corte t ≈ 2,5): (1) SMT de USDJPY×DXY e USDCHF×DXY (pares diretos, sem inverter; escolha da usuária em 13/11) no 1m/5m reverte (alvo = stop 0,5/1 ATR); (2) topo de prata×ouro 15m reverte; (3) SMT de USDJPY (e pares) × DXY na hora antes de red folder antecipa a direção; (4) SMT de EURUSD × DXY com a relação invertida (euro invertido vs. DXY) no 1m/5m reverte.
- **Validação 0DTE GLD × CME (13/11/2026):** `mi_0dte_hist.json` grava também o retrato da CME do mesmo vencimento (faixa, paredes, flip); a Conferência diária mostra o acerto de cada fonte separado. Hoje as fontes ficam lado a lado (não são unidas); o gráfico do dia usa só o GLD. Range do dia testado = mapa (GVZ + curva medida); faixa do 0DTE ainda sem teste.
- **0DTE: concordância GLD × CME (13/11/2026):** tolerância = 1 strike do GLD em preço de ouro (ouro ÷ GLD, ~US$ 11; escolha da usuária). Tabela: linha dourada + "✓ concordam" ou "dif. US$ X". Gráfico: níveis da CME pontilhados (fixos do dia, liga/desliga) e faixa colorida onde GLD e CME concordam.
- **0DTE barras (13/11/2026):** dois botões "Barras: ○ Volume do dia / ● Contratos em aberto" (o aceso é o mostrado) alternam volume do dia (GLD) e contratos em aberto (GLD + CME somados no mesmo degrau; CME em equivalente GLD = contratos × ouro ÷ GLD, ~10,9). Cores (desde 13/11, pedido da usuária): verde = calls, vermelho = puts. Strike sem barra = sem contrato listado (ex.: 13/11 o GLD só listou 351 e 355). Hipótese "ímã" (pinning no strike de maior OI) sem teste.
- **0DTE gráfico do dia (bug corrigido 13/11/2026):** pontos passam a ter data (`d`) e só são gravados no próprio dia do vencimento; antes, das 16h às 16h15 de NY o vencimento seguinte recebia pontos da tarde anterior e o gráfico fazia loop/degrau. Tela filtra pelo dia e ordena por horário; preço do ouro em linha contínua. Faixa ±1σ: opção sem compra/venda usa o último negócio; straddle procura o strike mais próximo com call e put com preço; faixa fora de 0,1–5% não é gravada (nem no retrato de validação); sombra em degraus.
- **0DTE dólar/iene (13/11/2026):** `cme_pdf_iene.py <calls> <puts>` lê os PDFs Section33/34 (parte "ADDITIONAL", séries separadas: 1JY–5JY sexta da semana N, MJ seg, TJ ter, WJ qua, SJ qui, JPU mensal) → `cme/iene_<pregão>.json` → `cme_local.py` → `iene_cadeia`. Coleta (`b_0dte_iene`) pega o vencimento mais próximo (FX vence 9h CT = 12h BRT), converte para USDJPY (1/K; call de iene = put de USDJPY), futuro → à vista pela razão fechamento do Yahoo ÷ (1/F); teto, piso, max pain, gamma flip (Black-76), faixa = straddle ÷ F → `mi_0dte_iene.json` e `mi_0dte_iene_hist.json` (validação). Faixa CME do USDJPY no card de faixa (1º vencimento ≥ 3 dias). Card "0DTE dólar/iene" só com CME + barras de contratos em aberto por strike. Usa o vencimento mais próximo com ≥ 10 strikes e par call/put perto do futuro; os pulados aparecem num aviso no card (ex.: após o venc. de sexta, seg–qui têm 1–9 strikes → usa a sexta seguinte). 1º pregão: 12/11 (teto 160,13 · piso 158,23 · flip 159,63 · faixa ±0,32%).
- **0DTE iene, gráfico refeito (13/11/2026):** barras em borboleta (puts à esquerda, calls à direita, número de contratos na ponta), faixa até o vencimento em sombra azul, preço + teto, piso, gamma flip e max pain com etiqueta à direita (linhas atrás das barras, números com fundo). Conferido no PC e no celular sem sobreposição.
- **Gráfico padrão de opções por strike (13/11/2026):** `drawBorb()` em `app.js` é o mesmo gráfico em borboleta para todos os ativos com opções. Ouro: GLD + CME na grade de strikes do GLD (±1,3% do preço; CME em equivalente GLD), botão Em aberto (GLD + CME) / Volume do dia (GLD); as barrinhas laterais do gráfico do dia do ouro saíram. Iene: só CME. Euro, franco, libra e Nasdaq: sem cadeia de opções atual (euro parado em 05/11 desde que a tarefa noturna foi desligada) → precisam dos PDFs da CME para entrar.
- **PCR no gráfico em borboleta (13/11/2026, pedido da usuária):** número grande abaixo do gráfico (puts ÷ calls; > 1,05 = +Puts vermelho, < 0,95 = +Calls verde). Ouro: segue o botão (em aberto GLD + CME em equivalente GLD, ou volume do dia GLD; strikes até ±3%). Iene: em aberto CME (±2%). Retrato: o PCR já foi testado e não prevê direção (aviso no Como ler).
- **Card 0DTE padronizado (13/11/2026, pedido da usuária):** todo ativo com opções usa o mesmo card, na mesma ordem: título "0DTE <ativo> · opções do vencimento mais próximo" → selo (vence DD/MM + hora de Brasília calculada com o horário de verão americano · fontes) → Como ler (mesma legenda) → tabela (Teto, preço, Gamma flip, Max pain, Piso por valor; Faixa até o vencimento; ±1σ; Regime) → Contratos por strike (borboleta) → PCR. Só o ouro difere: coluna GLD ao vivo, botões Em aberto/Volume, soma GLD + CME e o Gráfico do dia no fim. Novo ativo (euro, franco) entra no mesmo molde quando tiver PDF da CME.
- **Ouro só com a borboleta (13/11/2026, pedido da usuária):** o "Gráfico do dia" (linhas no tempo) saiu do site; `mi_0dte_dia.json` segue sendo gravado, sem uso na tela. A borboleta do ouro junta tudo: barra clara = em aberto (GLD + CME em equivalente GLD), barra escura = volume do dia do GLD (perfil, ao vivo); níveis do GLD tracejados + ±1σ; níveis da CME pontilhados; faixa dourada ✓ onde GLD e CME concordam (≤ 1 strike do GLD); níveis fora da grade listados em "Fora do gráfico"; dois PCR (em aberto GLD + CME e volume do dia GLD). Sem botões. Grade: ±max(1,3%, 1,15σ). No celular o número mostra só o em aberto (volume no toque).
- **Reação nos níveis de σ do dia (16/11/2026):** ao tocar ±0,25…2σ (σ do GVZ no ouro; vol. realizada 21d × 1,09 nas moedas; abertura 18h NY), mede se volta 0,25σ/0,5σ antes de andar mais 0,25σ/0,5σ. 2 anos de 1 h (GC, 6J, 6E, 6S) e 60 dias de 5 min (GC, 6J). Resultado: **40–53% em todos os níveis, nenhum acima de 50% com t ≥ 2**; o 1σ não é especial frente aos vizinhos. O σ serve para **até onde costuma ir** (mapa de toque, já testado), **não** como ponto de reversão sozinho. Próximo: testar paredes de opções (OI alto, GLD + CME, concordância ✓) e gamma flip como ponto de reação — precisa de histórico da cadeia (grava desde 31/10–13/11; ou Databento histórico).
- **Painel enxuto (16/11/2026, pedido da usuária):** todo "Como ler", explicação de card (`.mi-exp`, listas) e texto fixo longo vira `.ajuda`, escondido; botão **?** logo depois do título de cada card abre só aquele; **? Explicações** no topo abre todos (lembra a escolha). Divisórias de seção: Panorama do dia · Macro: o que move o dólar · Ativo: níveis e opções · Agenda e notícias. "Faixa esperada pelas opções" virou bloco dentro do card do mapa ("de onde vem o σ"). Regime, CTA, quadros de preço/ATR, sazonalidade, COT, correlações, Goldbach e tabela macro ficam em **"Mais sobre o ativo e o mercado"** (recolhido; gráficos desenham ao abrir). Diagramação: `text-wrap: pretty/balance`, sem hífen nem palavra cortada, listas sem bolinha. Varredura de sobreposição (texto linha a linha, PC 1200 px e celular 390 px, com e sem ajuda): 0.
- **0DTE ouro à noite (bug corrigido 16/11/2026):** fora do pregão do GLD a conversão GLD → ouro usava o ouro de agora e deslocava todos os níveis (dom 16/11: ~US$ 38; teto 3.855 → 3.888, flip 3.838 → 3.870, regime positivo → negativo). Agora a razão é a do ouro (GC=F, 5 min) no `last_trade_time` do GLD; gamma (regime e flip) recalculado com o ouro ao vivo na escala do GLD; selo mostra "GLD parado desde …". Contratos em aberto só mudam 1×/dia (OCC/CME), então paredes valem a noite toda.
- **CME 0DTE do ouro todos os dias (16/11/2026):** `cme_pdf.py` passou a ler as semanais de seg–qui (GMW seg, GWT ter, GWW qua, GWR qui), que no PDF vêm misturadas (calls, puts e 2+ vencimentos no mesmo bloco). Só a série que vence em ≤ 2 dias úteis: tipo pelo delta (ITM > 0,5), vencimento pela vol. implícita calculada para esse prazo (grupo 0,8–1,5× a menor vol. ATM; as longas dão vol. absurda). Travas: vol. ATM entre 0,5× e 1,6× a da sexta e paridade call − put com erro ≤ US$ 3 (13/11: erro US$ 0,10 em seg e ter). Duplicado mesmo strike/tipo → menor prêmio. 1º uso: pregão 13/11 → venc. 16/11 (CME flip 3.874 × GLD 3.871, concordam).
- **Correções 16/11/2026 (print da usuária no celular):** selo do 0DTE vazava do card (texto longo do "GLD parado") → selo curto ("GLD fechado (13/11)"), explicação no ?, e todo `.tl-chip` quebra linha em vez de vazar; cabeçalho "GLD (último pregão)" com o GLD fechado. Faixa esperada (CME) passou a pegar a série de seg 16/11 (vol. 16,6%, faixa estreita demais) → agora 1ª série com **≥ 3 dias úteis** (também no skew do `mi_pcr_hist`). Tabelas (Regime, CTA) vazavam no celular → toda `table.op-table` fica em `.tbl-x` (rola dentro do card) e mais compacta < 600 px. "?" fica dentro do título (quebra junto).
- **Diagramação 2 (16/11/2026, prints da usuária):** título do mapa partia em duas colunas (h2 flex + ? dentro) → texto do h2 num `span.h2-t`; `.sc-nome` na mesma fonte do título. "Dólar e juros": unidade bps no cabeçalho (número não quebra), "vs. efetivo" em linha menor. Parágrafos: 15 px, entrelinha 1,65, máx. 72–80 caracteres; células alinhadas ao meio, 1ª coluna à esquerda. Grade Hoje/Semana do mapa encolhe em tela estreita. Varredura agora também em **340 px** (celular com letra grande): 36/36 limpos.
- **Conferência rigorosa da CME (16/11/2026, pedido da usuária: "extremo rigor, sempre"):** novo `confere_cme.py` roda SEMPRE depois dos leitores e antes do commit; refaz a leitura por conta própria e para (código 1) se: alguma linha do JSON não existir no PDF no bloco/vencimento certo (strike, ajuste, contratos em aberto), a paridade call − put não fechar entre os strikes no dinheiro (vencimentos ≤ 35 dias), algum ajuste ficar abaixo do intrínseco; compara o futuro com GC=F (13h30 NY) e 6J=F/JPY=X (15h NY). 1ª rodada (pregão 13/11): ouro 227/227 e iene 479/479 linhas conferidas, 0 erro. **Erros achados e corrigidos na conferência:** (1) **ouro CME US$ 20 baixo**: o preço do painel é o GC=F (futuro de dez.), mas os níveis da CME eram convertidos para o à vista → agora pela razão GC=F às 13h30 NY do pregão ÷ futuro (flip CME 3.876 → 3.896; a "concordância" com o GLD em 16/11 era efeito do erro); (2) **GLD no pré-mercado**: Cboe manda preço de pré-mercado em `current_price` com `last_trade_time` antigo → fora do pregão usa o `close` oficial; (3) **iene com futuro errado**: o "FUTURES SETT." do cabeçalho NOV26 (,006259) é o mês-calendário; as opções usam o trimestral seguinte (nov → dez ,006273; 11/12, jan, fev → mar ,006322) → futuro pela paridade (mediana de 3 strikes), séries finas herdam do vencimento mais próximo do mesmo cabeçalho; régua futuro → à vista pelo USDJPY às 15h NY (não o fechamento diário). Níveis do iene estavam ~0,36 iene deslocados; com o futuro certo, o vencimento de 18/11 passou a ser usado. Arquivo de 12/11 também corrigido.
- **Backtest longo da faixa (16/11/2026):** `faixa_backtest.py` (histórico diário completo do Yahoo, mesmo método do painel, janelas sem sobreposição) → `docs/data/faixa_backtest.json` → tabela **visível** "Precisão medida" no bloco da faixa (fechou dentro ±1σ/±2σ, nem tocou ±1σ, pior–melhor ano). Ouro (GVZ, 2008+, 4.640 dias): dia 78%/96%, semana 77%/97%, mês 72%/96%; moedas (vol. 21d × 1,09, 1996–2003+, 6–7,7 mil dias): dia 73–74%/95%, semana 71–74%/94–96%. Estável por ano (dia 68–82%). "Conferência diária" voltou a aparecer (o "Como ler" dela fica no ?). **Qual σ (ouro, 2008+):** GVZ puro ±1σ 77,8% / ±2σ 96,2% (largo no 1σ, certo no 2σ); GVZ × 0,87 72,7%/94,1% dia e 67,3%/94,5% semana (ajuste dentro da amostra, não aplicado); vol. realizada 21d × 1,09 75,3%/94,4%. Caudas grossas: nenhuma escala acerta 68% e 95% ao mesmo tempo. Straddle 0DTE (GLD/CME): sem histórico, validação em curso.
- **DTCC (opções de câmbio de balcão, 16/11/2026):** testado e funciona, grátis. Host `pddata.dtcc.com` liberado no ambiente "painel-mercado". Lista intradiária: `GET /ppd/api/slice/CFTC/FX` (JSON, mais novo primeiro; um pacote a cada ~10–30 s, segundos após o negócio); pacote: `/ppd/api/report/intraday/cftc/<fileName>` (zip/CSV); dia fechado: `/ppd/api/report/cumulative/cftc/CFTC_CUMULATIVE_FOREX_AAAA_MM_DD.zip` (~2 MB). Opções: `UPI FISN` começa com `NA/O` (Van = vanilla, Bar = barreira); campos úteis: Execution Timestamp, Action type (NEWT novo, TERM encerrado, CORR/MODI/EROR), Expiration Date, Strike Price, Strike price currency/currency pair (ex.: USD/JPY), Call/Put amount e currency, Notional amount-Leg 1 ("+" = teto de tamanho), Option Premium Amount. 13/11: 4.892 opções de câmbio no dia, 808 de USD/JPY (US$ 15–100 mi cada, comum). Limites: são **negócios**, não posições em aberto (paredes = soma de NEWT − TERM por strike/vencimento numa janela); só negócios com parte americana (CFTC); notional com teto. Próximo: montar no coletor (pacotes novos a cada 5 min + arquivos diários dos últimos ~30 dias) → borboleta "OTC" para iene, euro, franco e libra.
- **Card "Balcão (DTCC)" no ar (16/11/2026):** `dtcc.py` (passo próprio do workflow, ≤ 150 s, estado `dtcc_estado.json` na branch dados) → `mi_otc.json` (+ `mi_otc_hist.json`, retrato diário para o teste) → card abaixo do 0DTE em USDJPY, EURUSD, USDCHF e GBPUSD: botões de vencimento (mais curtos primeiro, corte de NY 10h = 12h BRT), teto (mais calls acima) / piso (mais puts abaixo), borboleta em US$ mi (degrau 0,25 iene / 0,0025), PCR em US$. **Regras de rigor (todas validadas):** só vanilla; strike normalizado pela faixa plausível do par (rótulo e strike às vezes em convenções opostas: 12 descartados); tamanho pela conta das duas pontas (cotada = base × strike), nunca pelo rótulo de moeda; > US$ 3 bi descartado; **tipo só quando o nome do produto (UPI FISN) e o "Call currency" concordam** (discordam/vazio ≈ 23% → descartados). **Auditoria pelo prêmio** (`confere_dtcc.py`, opções ≤ 60 dias, Black-Scholes com preço da hora do negócio): tipo confirmado iene 97,2%, euro 98,9%, franco 100%, libra 98,3%; nos casos bem decisivos 99,8–99,9%; prêmio real ÷ teórico 0,92–1,19 (tamanho certo). Limites: negócios dos últimos 60 dias (opções longas abertas antes ficam de fora), só negócios com parte americana, "+" = acima do teto de divulgação. Hipótese "vencimento grande segura o preço até o corte": sem teste (grava todo dia).
- **Backtest das paredes de balcão (DTCC) e do σ, 2 anos (16/11/2026):** `testes/backtest_otc.py` + `_analise.py` (arquivos diários da DTCC desde 14/11/2024, só opções simples dos 4 pares; estoque reconstruído **na véspera** de cada vencimento, sem olhar o futuro; preços em candles de 1 h do Yahoo; acaso = mesma régua aplicada aos outros dias do mesmo par; corte |t| ≥ 2,5). 1.192 vencimentos (298 dias × 4 pares). **Nada passou:** atração 7h→corte 46,0% × 46,0% (≥ US$ 1 bi: 42,4% × 46,3%); range do dia dentro de piso–teto 47,6% × 47,2%; extremo parou a ≤ 1 degrau do teto 29,7% × 29,9%, do piso 27,5% × 27,9%; extremo parou a ≤ 0,1σ do ±1σ 7,4% × 7,0%; da parede 7,0% × 7,2%; confluência parede + ±1σ 6,6% × 7,2%. Estável nos 4 pares e nas duas metades. σ: range do dia dentro de ±1σ 51,6%, tocou +1σ 24,2% / −1σ 24,8% (confirma o mapa). **Conclusão:** paredes de balcão são retrato, não suporte/resistência; aviso visível no card. 0DTE GLD/CME: sem histórico grátis para o mesmo teste (validação em curso).
- **DTCC só gravando (16/11/2026, decisão da usuária):** retestado só com opções de balcão de vencimento curtíssimo (abertas a ≤ 2 dias do vencimento, incl. madrugada do próprio dia até 7h NY; `CURTO=2 testes/backtest_otc.py`), 921 vencimentos: atração 42,3% × 46,3% (t = −2,3, não passa o corte; se algo, afasta), range dentro de piso–teto 26,2% × 26,3%, parou no teto 42,9% × 40,5%, no piso 37,3% × 37,5%. **Card escondido** (`MOSTRA_OTC = false` em app.js); `dtcc.py` segue rodando na coleta (estado + `mi_otc_hist.json`). A DTCC guarda ≥ 2 anos de arquivos diários: retestar quando quiser. Foco: 0DTE da CME (+ GLD no ouro).
- **Ouro: régua da Vantage = GC − US$ 6,5 (2ª calibração 16/11/2026, preços simultâneos ditados pela usuária: GC 3.882 × Vantage 3.875; 3.880 × 3.874).** `VANTAGE_USD` em `b_precos()`; fator = 1 − 6,5 ÷ GC aplicado a todo o ouro (série, mapa, GLD, CME). Título do mapa mostra "régua da Vantage · futuro − US$ 6,5". Recalibrar na troca de contrato do GC=F (fim de nov.) pedindo 2 pares de preços simultâneos. 1ª calibração (pelos extremos do print, menos precisa): Print da usuária: XAUUSD Vantage máx. 3.905,84 / mín. 3.832,45 / pico 3.888,9 × GCZ26 3.904,3 / 3.835,2 / 3.892,6 → a Vantage anda colada no futuro ativo (US$ 0–4), não no à vista teórico (−US$ 20). **Conversão para o à vista DESFEITA** (fator 1); `spot_ouro()` só informa `teorico_base_usd`. Recalibrar quando o GC=F trocar de contrato (dez → fev, fim de nov.): ver se a Vantage acompanha o novo contrato. Histórico da tentativa: **Ouro no à vista (16/11/2026, a usuária opera XAUUSD na Vantage):** o Yahoo só tem o futuro (GC=F; XAUUSD=X não existe mais). `spot_ouro()` no coletor descobre qual contrato é o GC=F (GCZ26, GCG27…) e o seguinte, mede o carrego r = ln(F2/F1) ÷ prazo e aplica fator = e^(−r × dias até a entrega ÷ 365) em **toda** a série do ouro (P["XAUUSD"]), nas barras de 1 h do mapa, na razão GLD → ouro e na régua da CME. Trava: 0 < r < 12% e 0,97 < fator ≤ 1, senão reserva pelo juro de 13 semanas (aviso no status). 16/11: GC 3.882,9 → à vista 3.862,9 (fator 0,99485, carrego 4,71%/ano). Exposto em `mi_geral.ouro_spot` e no título do mapa ("à vista · futuro − US$ X"). Falta calibrar com um preço da Vantage (horário + valor). Históricos de validação gravados antes de 16/11 estão na régua do futuro.
- **"Passou e fechou de volta dentro" (defesa) — 16/11/2026:** com o câmbio à vista do Yahoo parecia haver defesa (passou do ±2σ → fechou de volta em 69–77%), mas **com os futuros da CME (dados limpos) some**: 44–52% (acaso = 50%, princípio da reflexão), nos 4 pares e no ouro. Era sujeira de máxima/mínima do Yahoo FX (picos falsos). **Não usar máx./mín. do câmbio do Yahoo para testes de toque**; usar futuros (6J, 6E, 6S, 6B, GC). Fechamento dentro de ±1σ nos futuros: 73–75% / ±2σ ~95% (confirma a "Precisão medida").
- **"Sambou e fechou dentro" (16/11/2026, futuros, 18–25 anos; `testes/samba*.py`):** depois de passar do ±1σ, só "sambou" (máx. ≤ 0,25σ além) em 31–34% dos casos e **seguiu** (> 0,25σ além) em 66–69%. Quando só sambou, fechou dentro em 82–90% (≤ 0,1σ além: 89–98%); quando seguiu, só 28–33%; no total ~50%. Igual em 0,8σ e 1,2σ → é geometria (máx. perto do nível ⇒ fecha perto/dentro), não defesa especial do 1σ. Na hora do toque não dá para saber qual dos dois casos vai ser.
- **Rompimento do σ do dia no mapa (16/11/2026, pedido da usuária):** `testes/rompimento.py` (futuros GC/6J/6E/6S/6B, mesma régua do mapa: a partir da abertura, σ do GVZ no ouro e vol. 21d × 1,09 nas moedas; 18–26 anos) → `docs/data/rompimento.json` → bloco "Rompimento do σ do dia" no card do mapa: preço de cada gatilho (±1σ, ±1,25σ, ±1,5σ), o que costuma acontecer depois e linha dourada na situação de hoje ("Hoje: em cima Xσ → …"). Números: tocou ±1σ → fecha fora 49–51% (cara ou coroa); passou de ±1,25σ → fecha fora 68–71%, chega a 1,5σ 62–67% (desde 2016: 68–73%); passou de ±1,5σ → fecha fora 80–84%, chega a 2σ 37–45%. Fecha dentro do ±1σ a partir da abertura: ouro 82,8%, moedas 73–75%.
- **Pesquisa (16/11/2026):** Golez & Jackwerth (S&P 500 futuros 1992–2009): futuro puxado para o strike no dinheiro nos dias de vencimento das opções sobre o futuro (≈ 0DTE da CME); estudo 2016–2025 não acha mais pinning no S&P → testar por mercado. SpotGamma: S&P fecha dentro do movimento esperado de 1 dia em 76% (bate com 73–78% nosso). Baltussen, Da, Lammers & Martens (JFE 2021, 60+ futuros desde 1974): "intraday momentum" na última meia hora, forte em dias de gamma NEGATIVO, ausente em gamma positivo → hipótese a testar com o histórico de gamma (GLD/CME) que estamos gravando. Câmbio: há estudos de reversão após movimentos muito grandes nos futuros de moeda (Rentzler et al. 2006), sem consenso. Pinning em câmbio: sem estudo sólido encontrado.
- **Textos revistos (16/11/2026, pedido da usuária):** "Como ler" de Radar, Dólar e juros, mapa, 0DTE ouro (+ contratos por strike), 0DTE iene (+ contratos), Regime e CTA reescritos em `div.op-note.ajuda.guia`: introdução curta + um item por linha (sem bolinha), frases completas, menos "=" e "→"; 0DTE do ouro agora diz "régua da Vantage" (não "à vista"). Largura: tirado o limite de 72–80 caracteres (no PC o texto parecia cortado) → texto vai de borda a borda.
- Databento: adiado (pago; CME ao vivo a partir de US$ 199/mês).
- **Visual:** cards por ativo (Regime, Faixa das opções, 0DTE, CTA) ficam abaixo do seletor e só aparecem para o ativo escolhido; níveis com cores (teto vermelho, piso verde, flip âmbar, max pain roxo, faixa azul, ±1σ verde-água, ±2σ marrom).
- **Precisão:** Regime forte mantém a direção 13 semanas em 91–100% (DXY) e 57–90% (juros); faixa ±1σ semana 72–74% / ±2σ 93–96%; 0DTE sem teste ainda.
- Pendente: contratos em aberto da CME (via tarefa noturna), e Databento (precisa de conta).

### 5.2 Fluxo dos grandes (substituir/complementar o COT)
- **Databento (CME, MBO em tempo real):** delta agressor, lotes grandes e absorção em **GC (ouro), 6J (iene), 6S (franco), 6E (euro)**. Cobrança por uso. Licença CME: não exibir tempo real em site público → só indicadores derivados ou página privada.
- **CLS FX Flow:** fluxo por tipo de participante (fundos, empresas, bancos), horário. Institucional, preço sob consulta — só se houver orçamento.

### 5.3 Dólar e juros — a expandir
- Curva EUA 2a/5a/10a/30a e inclinação 2s10s; juro real 10a (TIPS) e breakeven (inflação implícita) — chave para o ouro.
- Diferenciais por par: EUA−Japão (USD/JPY), EUA−Suíça (USD/CHF), EUA−Alemanha (EUR/USD), juro real EUA (ouro).
- ~~Salto do Fed Funds~~ resolvido 13/11/2026: era troca de contrato do ZQ=F no Yahoo; agora usa o contrato fixo do próximo mês (ex.: ZQZ26.CBT).
- Probabilidade implícita de BoJ e SNB, se houver fonte confiável.

### 5.4 Outras pendências
2. Previsão do CPI (Cleveland Fed nowcast): gravação iniciada 13/11/2026 (ver 5.6).
3. Domínio próprio (adiado).

### 5.5 Ambiente do Claude
- Ambiente "painel-mercado" (rede liberada: Yahoo, FRED, CFTC) para rodar testes.

---

## 6. Contas e serviços

| Serviço | Uso |
|---|---|
| GitHub | repositório, Actions, Pages |
| cron-job.org | dispara a coleta a cada 5 min |
| Anthropic Console | chave da API (leitura da IA) — limite de gasto recomendado |
| Google Drive (gabridemes15@gmail.com) | ponte das opções (fluxo antigo / futura automação) |
| Claude (tarefas agendadas) | teste put/call+skew (17/05/2027); CME noturna desligada |

## 6.1 Próximos passos (13/11/2026)
1. **Automação dos PDFs da CME pelo celular** (Android: MacroDroid 03h30 → Autosync Drive → Actions lê o PDF). Montar a leitura do PDF no Actions + passo a passo dos apps.
2. **Euro e franco na CME** (mesmo esquema do iene; achar as seções no boletim).
3. Validações que rodam sozinhas: 0DTE GLD × CME e iene (~30 vencimentos, fim de dez.), mapa/faixa (Conferência diária), SMT (fev/2027), surpresas EUA e put/call+skew (mai/2027).
4. Pedido em aberto: suavizar o gamma flip do GLD (média 15 min)? A usuária não respondeu.
5. CME reorganiza o boletim em 01/01/2027: conferir nomes/formatos das seções.

## 7. Preferências
Português · respostas curtas e econômicas · capricho visual: nada sobreposto nem vazando do card (rodar varredura de sobreposição **e de vazamento** no PC (1200), celular (390) e celular estreito/letra grande (340), claro e escuro, ouro/iene/euro, com e sem ajuda, **usando cópia dos dados atuais da branch `dados`** — o teste local sem rede usa a reserva `docs/data` antiga e esconde problemas) antes de publicar · "Como ler" em todo indicador novo · horário de Brasília · **opções: sempre incluir a CME (mercado muito maior) junto com o GLD, em qualquer análise ou teste**; só entra no painel o que passar em teste estatístico (previsão; retrato não serve).


## 16/11/2026 — σ das opções × ping-pong/tendência (`testes/pingpong_sigma.py`)
Hipótese da usuária: σ curto = lateral, σ longo = tendência. GC=F 1 h, sessão 18h NY, 559 dias (07/2024–11/2026), σ = GVZ da véspera.
Terços por σ em US$: curto σ 29,7 → deslocamento 21,1, range 41,3, eficiência 0,240, ping-pong 31,6%, tendência 33,2%; médio 50,1 → 37,5 / 75,1 / 0,232 / 36,0% / 31,7%; longo 82,9 → 62,5 / 126,5 / 0,228 / 31,7% / 30,6%.
Correlação σ × deslocamento r 0,44 (t 11,6), σ × range r 0,70 (t 23,4), σ × eficiência r −0,06 (t −1,3); σ relativo à média de 60 dias × eficiência r 0,007. Estável nas duas metades.
Conclusão: o σ prevê QUANTO o ouro anda (forte), não o FORMATO (ping-pong × tendência). Deslocamento líquido médio ≈ 0,75σ em qualquer regime. Uso prático: grade e stop medidos em σ do dia.


## 16/11/2026 — bug do σ da semana no mapa
- Na segunda, `hoje_s == seg` → chaves do dia e da semana iguais no `mapa_fixo` → σ da semana = σ do dia (√5 menor). Chave da semana agora `ativo|sem|data`.
- Rótulo "dia_ini" na segunda mostrava "sex 20h"; agora "dom".
- Limpeza do `mapa_fixo` era por ordem alfabética (últimos 200) e podia apagar o EURUSD do dia; agora guarda 21 dias por data.

## 16/11/2026 — pesquisa 0DTE, gregas D+0 no diário, teste de momentum do fim do dia
- Pesquisa (resumo dado a ela): gamma + → reversão / − → momentum (Dim-Eraker-Vilkov, Adams et al., Barbon-Buraschi, Baltussen 2021); efeito vem do estoque que vence D+0. PCR 0DTE na abertura prevê 1ª hora, mas sem lucro fora da amostra (Maurer-Müller 2026). Pan-Poteshman não vale para índice. Pinning em ações (Ni-Pearson-Poteshman); no S&P sumiu. Charm/vanna/call wall: só regra de fornecedor.
- Diário do ouro ganhou gregas D+0 (GLD/CME), pin, PCR CME e preços por horário. Ela pediu: nada na tela; contar com 30 dias.
- `testes/momentum_fim.py`: 1ª versão deu t 7,2 por erro (o preço das 17h pegava a abertura das 18h). Corrigido: n 583, t −2,29 (13h→14h), 1,42 (15h→17h); 5 min 60 dias t −0,4/−1,4. Não passou.

## 16/11/2026 — dia típico em σ (moedas "longas")
- Ela acha o σ das moedas largo demais. `testes/dia_tipico.py` (futuros 6J/6E/6S/6B/GC, 15 anos): mediana |fech−abert| 0,54–0,57σ moedas, 0,45σ ouro; 68% ≤ 0,83–0,86σ; ±1σ contém 75–76% (80% ouro); amplitude mediana 1,18–1,30σ. O σ está certo; o dia "normal" é ~metade dele.

## 16/11/2026 — "Dia normal" no mapa + Ásia/Londres prevê tamanho do resto do dia
- Bloco "Dia normal" (todos os 5 ativos): metade dos dias ±q50·σ, 9 em 10 ±q90·σ, amplitude típica, amplitude de hoje até agora.
- `testes/range_cedo.py`: amplitude 18h→9h NY prevê a de 9h→17h. Ouro GVZ r 0,30 t 7,3; 6J r 0,50 t 13,7; 6E 0,31; 6S 0,40; 6B 0,31. Cortes (σ): terço baixo <~0,8, alto ≥~1,2; resto mediano baixo/médio/alto: ouro 0,75/0,79/0,95, 6J 0,48/0,62/0,85, 6E 0,72/0,82/1,01, 6S 0,70/0,75/0,91, 6B 0,71/0,81/0,99.
- `amp_cedo` no `mi_faixa.mapa`, calculado com futuros (6E/6B/6J/6S/GC) entre 9h e 17h NY.

## 16/11/2026 — regras de trader (H1–H7) e gap de domingo
- 35 testes; nenhum útil. Ouro CLV t −3,9 (metades −0,09/−0,04, acerto 54%) = fraco. Gap domingo: euro t 4,0 só na 1ª metade; "gap fecha 62–86%" é porque o gap é pequeno, não sinal.

## 17/11/2026 — "current" da CME devolveu boletim velho
- Ela colou o link "current" e abriu o de sexta (cópia guardada). Solução manual: acrescentar `?x=<qualquer número>` ao link. `pc/baixar_cme.sh` agora pede sem cache (`?t=<hora>` + Cache-Control).

## 17/11/2026 — Dólar e juros
- Resumo dizia "Hoje:" mas os juros são do fechamento anterior (16/11) → agora "Juros dos EUA, fechamento de seg 16/11". Leitura só com pares e Dólar/Iene, seta + cor. Tabela dentro de .tbl-x.

## 17/11/2026 — mega revisão do painel (pedido dela)
- Dólar e juros: "hoje (ao vivo)" quando o dado é do dia; "fechamento de <dia>" antes de os juros dos EUA abrirem (Yahoo ^IRX/^FVX/^TNX diário).
- Textos corrigidos: "mais de 90 sinais" → centenas; Faixa esperada (moedas não usam opções; precisão 71–78% conforme tabela; moedas 71–74%/94–95%); Valor justo sem "tende a subir"; ATR ≠ dia normal; COT sem "score" e sem promessas; VIX sem "ouro ganha" (correlação negativa); Radar = contexto, não sinal; PCR volume do GLD diz "último pregão" com GLD fechado.
- Conferido e certo: max pain = teto hoje (curva achatada 357–360 no GLD, recalculado direto da Cboe); diferenciais e spreads batem; liquidez = balanço − TGA − RRP; Fed Funds +18 bps; máx./mín. Yahoo FX × futuros sem pico hoje.
- Varredura: página inteira, 60 combinações, nada vazando.

## 17/11/2026 — robô da CME no PC dela
- curl no PC dela: 000 (HTTP/2) e 403 (HTTP/1.1, JSON da CME). Ela pediu para usar navegador. `baixar_cme.sh` agora abre o Brave em perfil separado, baixa os 3 PDFs (prefs: always_open_pdf_externally, pasta temp), fecha com pkill do perfil. Headless não baixa; precisa tela (DISPLAY/XAUTHORITY/Wayland achados sozinhos). Teste local com Chromium + Xvfb: 3 PDFs baixados.

## 17/11/2026 — horários de lateralidade no ouro
- Ver `testes/horas_lateral_resultado_2026-11-17.txt`. Amplitude/hora varia 2,5× (01h 0,19σ × 10h 0,48σ); eficiência por hora não difere (0,21–0,38, n≈50, ruído). Blocos: eficiência depende do nº de barras, não comparável entre blocos.

## 17/11/2026 — σ das moedas pela DTCC
- Ela pediu "algo que meça as opções melhores" no Forex. DTCC tem o prêmio de cada opção → vol. implícita. Teste 2 anos (`testes/vol_dtcc_resultado_2026-11-17.txt`): USDJPY r 0,52 × 0,34; EURUSD 0,55 × 0,45; USDCHF 0,35 × 0,32; GBPUSD 0,37 × 0,18. Ligado em produção com reserva na realizada. Cortes da Ásia+Londres reescalados (×0,925 iene, ×0,96 euro, ×0,99 franco, ×1,01 libra).

## 17/11/2026 — métricas das moedas com σ DTCC
- Pedido dela: medir todas as métricas das moedas com CME/DTCC. CME iene sem histórico (só desde 11/2026). Refeito com DTCC (2 anos): toque dia/semana, fecha dentro, curva agora, rompimento. Antigos (vol. realizada, 1996+/2001+) substituídos; resultados em `testes/metricas_dtcc_resultado_2026-11-17.txt`.
- Também: título "Mapa de opções"; linha da hora no ouro.

## 17/11/2026 — fluxo DTCC × direção
- 32 testes, nada (ver resultado). 1ª rodada tinha erro (lia só "Call" no FISN e descartava "Put"); corrigido antes de concluir. Obs.: `vol_dtcc.py` também só lia "Call" no FISN (metade dos negócios, tipos certos) — o teste de σ continua válido; o `dtcc.py` de produção lê os dois.

## 17/11/2026 — scalp pelo fluxo DTCC
- Ela quer viés de minutos (agressão do MM), não do dia. Testado negócio grande isolado e sequências de 15 min, 5 min (60 d) e 1 h (2 anos): nada. Resultados em `testes/scalp_dtcc_resultado_2026-11-17.txt` e `_1h_`.

## 18/11/2026 — abertura do dia e da semana
- Ela mandou o candle de abertura do USDJPY (TradingView em horário de NY, 18:00): O 159,445 H 159,488 L 159,421 C 159,486. Yahoo 20h BRT: O 159,41 H 159,488 L 159,396 C 159,486 (máx. e fech. iguais). Painel abria moedas às 17h NY (19h BRT, 159,354) → agora 18h NY para todos (`sess` +6 h, `hab` 18, `b_valid` idem). Semana: Yahoo FX começa domingo 19h NY → estimada pelo futuro (USDJPY 159,818 × antes 159,78).

## 18/11/2026 — robô da CME pegou boletim velho
- 3h: veio o boletim de 16/11 (já processado), hash diferente → enviou e marcou PRELIM → não tentou mais até 10h. Corrigido: compara a data do boletim com o dia útil anterior; auto-atualização do script.

## 18/11/2026 — leitor do ouro: call/put trocadas no strike colado ao preço
- Boletim de 17/11 (robô, 08:38): conferência barrou GWR 19/11 (K+C−P 3865,8 × 3864,2). Strike 3865 tinha deltas 0,5002 e 0,4999 → classificação por delta trocou call e put. `cme_pdf.py`: quando o delta está a ≤ 0,02 de 0,5, decide pela paridade (mediana dos outros strikes). 17/11 e 16/11 com 0 erro.

## 19/11/2026 — leitor do ouro: vencimento mensal (OG, 24/11) entrou na janela
- O bloco OG traz vários meses (DEC26, JAN27…, com o cabeçalho repetido a cada página) → o leitor misturava → paridade quebrada. Agora só o 1º mês do bloco (`fechado`). A referência (futuro/vol.) usava strikes de 2 vencimentos misturados → GWR descartada (vol. 3%); agora só o vencimento mais próximo. Boletim 18/11 (enviado por ela, só ouro) com 0 erro; 16/11 e 17/11 seguem com 0 erro. Robô não disparou nada desde 18/11 08:38 → pedir o log.

## 20/11/2026 — card "O que olhar hoje"
- Ela achou o painel confuso ("qual sigma olhar"). Novo card no topo do ativo com só o comprovado; detalhes do mapa recolhidos. Varredura 60 combinações ok.

## 23/11/2026 — leitor do ouro: semanal que não existe no dia do vencimento mensal
- Boletim de 20/11 (robô, 03:00 de segunda): barrado — GWT "24/11" não existe (24/11 é o vencimento mensal OG; o bloco GWT só traz dezembro) e o leitor misturava dezembro com 24/11. Regra: dia = VENC["OG"] → pula a semanal. 17/11 e 18/11 inalterados; 20/11 com 0 erro. (Fim de semana: nada puxado de sáb 21/11 porque o boletim de sexta só sai em seg de madrugada? — confirmar no log do PC.)

## 23/11/2026 — painel sem atualizar (0DTE e conferência)
- **0DTE do GLD parado desde sex 20/11 17:20 NY:** a Cboe (cdn.cboe.com → cdn-api.cboe.com) passou a devolver 403 do Cloudflare ("you have been blocked") para o servidor da coleta. Não vamos driblar o bloqueio. Reserva legítima: opções do GLD pela API pública do Yahoo (`gld_yahoo()`, crumb do próprio site; formato igual ao da Cboe; sem delta → só afeta o skew do mi_pcr_hist). Aviso no card 0DTE quando a fonte falha. Não testável no ambiente do Claude (Yahoo options bloqueado lá): conferir na coleta seguinte.
- **"Backtest diário: 2 is not in list" desde 17/11:** minha refação do `toque_tabela.json` das moedas (σ DTCC) tinha só k até 1,5; o código e o mapa precisam de 2 e 2,5 → ±2σ das moedas ficava vazio e a conferência diária não rodava. `testes/metricas_dtcc.py` agora gera k até 2,5.
