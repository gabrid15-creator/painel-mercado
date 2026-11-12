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

- A CME bloqueia servidores do GitHub, então a leitura é feita por uma **tarefa agendada do Claude**: **"Opções euro e ouro (noite) → Drive → painel-mercado"**, Sonnet 5.5, **ter–sáb 03:37**.
- Ela grava `opcoes_<data>_<hora>.json` na pasta pública do Drive **painel-mercado-opcoes** (conta gabridemes15@gmail.com, id `1GTHAZCrqQe_LYxf8OuR3zwqncQmHUunx`).
- Vencimentos: **semanais dos próximos 10 dias + mensal mais próxima**.
- Status: **euro funcionando** (pregão 05/11 carregado). **Ouro pendente** (não achou a série mensal OG; dados de 30/10).

---

## 5. Pendências / próximos passos

1. **Ouro nas opções:** ajustar a tarefa para achar a seção certa da CME (semanais OG1–OG5 + mensal OG).
2. **Conferir o Fed Funds implícito** (+28 bps em um dia — possível troca de contrato).
3. **Backtest** do score e do CTA contra o retorno de 5–20 dias (10 anos) — hoje só Goldbach, sazonalidade e correlações têm medição estatística.
4. Previsão do CPI (Cleveland Fed nowcast) se houver fonte de dados confiável.
5. Domínio próprio do site (adiado).

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
