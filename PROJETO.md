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
| **Site** | HTML/JS estático, publicado no GitHub Pages **só em push** (código) | `docs/index.html`, `docs/app.js`, `docs/opcoes.js` |
| **Leitura da IA** | Haiku 5.5 escreve o texto geral e de cada ativo + viés (bullish/neutro/bearish) | `ia.py`, segredo `ANTHROPIC_API_KEY` |
| **Opções** | Tarefa agendada do Claude lê a CME e grava no Google Drive; a coleta importa | ver seção 4 |

**Frequência da IA:** 6h–18h de hora em hora · à noite só 20h e 0h · sempre após red folder · parada sex 18h → dom 18h. Custo real ≈ US$ 0,003/leitura (~R$ 5–6/mês).

---

## 2. O que já está no ar

### Aba Mercado
- **Topo:** Fear & Greed, Red folder do dia (lista), VIX, DXY — com selo, régua e lista.
- **Leitura do dia (IA)** com selo de viés.
- **Radar institucional:** liquidez líquida do Fed (balanço − TGA − RRP), estresse (VIX ÷ VIX 3m, MOVE, NFCI), surpresa econômica por moeda (90 dias) e regime dos EUA.
- **Dólar e juros:** EUA 13 sem / 5a / 10a (intraday), Fed Funds implícito (futuro) vs. efetivo, JGB 10a, diferencial EUA−Japão, GDPNow.
- **CTA (estimativa):** posição dos fundos de tendência por ativo (−100% a +100%) e gatilho de virada mais próximo.
- **Seletor de ativo** (gruda ao rolar) → score 0–100 com fatores, leitura da IA do ativo, preço, valor justo, sazonalidade (padrão 10 anos), ATR.
- **Sazonalidade, caminho do mês, COT, correlações, Goldbach x extremos e sweeps (10 anos).**
- **Tabela macro** (juros, dólar, liquidez, risco, energia) + gráfico.
- **Agenda da semana** (Forex Factory) com **Atual em tempo real**:
  - biquote.io (navegador, 15 s perto das divulgações);
  - **BLS direto no navegador** (payroll, desemprego, salário-hora, CPI, PPI) — segundos;
  - FRED via coleta (seguro-desemprego, varejo, PCE, JOLTS, PIB) — minutos;
  - caixa verde/vermelha acima/abaixo da previsão, "Acabou de sair", dia de hoje em âmbar, cabeçalho fixo.
- **Notícias** (RSS, filtro por ativo).

### Aba Paredes de opções (euro e ouro, mesmos cards)
Pregão lido, futuro, maior call/put wall, gamma flip, gamma +/− máximo, código do TradingView (gerado dos mesmos dados), mapa de contratos e curva de gamma. Só strikes em **futuro ± 6×ATR** (mín. 300 pips / US$ 300).

### Aba Dias Goldbach
Calendário de 2 meses (H = dia do mês Hopiplaka), próximos dias, tabela.

### Aba Alto impacto EUA
Calendário do mês anterior, atual e seguinte só com dados americanos de alto impacto, marcando dias Goldbach (★/G/H), e lista com previsão, anterior e atual.

### Visual
Ícone, manifest (app no celular), modo claro/escuro, cards com sombra, abas em pílula, "Como ler" em todo indicador.

---

## 3. Arquivos

| Arquivo | Função |
|---|---|
| `coletor.py` | Coleta tudo (Yahoo, Tesouro EUA, Fed NY, Bundesbank, FRED, Fed Chicago, MOF Japão, CFTC, CNN, Forex Factory, BLS, RSS) e calcula score, sazonalidade, correlações, COT, sweeps, CTA |
| `ia.py` | Leitura da IA (Anthropic, Haiku 5.5) |
| `opcoes_drive.py` | Importa o arquivo de opções mais recente da pasta do Drive |
| `goldbach_gen.py` | Gera `docs/data/goldbach_dias.json` |
| `docs/index.html` / `app.js` / `opcoes.js` | Site |
| `docs/data/*.json` | Cópia de reserva dos dados (o site prefere a branch `dados`) |
| `.github/workflows/coleta.yml` | Coleta → branch `dados`; site → Pages só em push |

---

## 4. Opções (fluxo especial)

- A CME bloqueia servidores do GitHub, então a leitura é feita por uma **tarefa agendada do Claude**: **"Opções ouro e euro (noite) → Drive → painel-mercado"**, Sonnet 5.5, **ter–sáb 03:37**.
- Ela grava `opcoes_<data>_<hora>.json` na pasta pública do Drive **painel-mercado-opcoes** (conta gabridemes15@gmail.com, id `1GTHAZCrqQe_LYxf8OuR3zwqncQmHUunx`).
- Vencimentos: **semanais dos próximos 10 dias + mensal mais próxima**.
- Status: **euro funcionando** (pregão 05/11 carregado). **Ouro pendente** (não achou a série mensal OG; dados de 30/10).

---

## 5. Foco atual (atualizado 12/11/2026)

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
- **0DTE CME:** card mostra GLD (ao vivo) ao lado da CME (pregão anterior, vencimento do dia) quando a tarefa noturna traz `ouro_cadeia` com venc = data.
- Tarefa noturna renomeada "Opções ouro e euro (noite)": ouro primeiro, inclui séries que vencem em 0–2 dias úteis. Falhou em 12/11 por limite de uso da conta.
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
- Precificação do Fed (Fed Funds futuro) → **conferir o salto de +28 bps** (possível troca de contrato).
- Probabilidade implícita de BoJ e SNB, se houver fonte confiável.

### 5.4 Outras pendências
1. Ouro nas opções: ajustar a tarefa para a seção certa da CME (OG1–OG5 + OG mensal).
2. Previsão do CPI (Cleveland Fed nowcast), se houver fonte confiável.
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
| Google Drive (gabridemes15@gmail.com) | ponte das opções |
| Claude (tarefa agendada) | leitura noturna da CME |

## 7. Preferências
Português · respostas curtas e econômicas · "Como ler" em todo indicador novo · horário de Brasília · códigos do TradingView sempre gerados dos mesmos dados do painel.
