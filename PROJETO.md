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
| **Opções de ouro (CME)** | Tarefa agendada do Claude lê a CME e grava no Google Drive; a coleta importa (0DTE e vol. CME) | ver seção 4 |

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
| `opcoes_drive.py` | Importa o arquivo de opções mais recente da pasta do Drive |
| `goldbach_gen.py` | Gera `docs/data/goldbach_dias.json` |
| `docs/index.html` / `app.js` | Site (abas Mercado e Dias de alto impacto) |
| `docs/data/*.json` | Cópia de reserva dos dados (o site prefere a branch `dados`) |
| `.github/workflows/coleta.yml` | Coleta → branch `dados`; site → Pages só em push |

---

## 4. Opções de ouro da CME (fluxo especial)

- A CME bloqueia servidores do GitHub; a leitura é feita pela **tarefa agendada do Claude "Opções de ouro CME (noite) → Drive → painel-mercado"** (Sonnet 5.5, ter–sáb 03:37).
- Só ouro: séries que vencem em 0–2 dias úteis (0DTE) + primeira semanal a partir de 3 dias (vol. implícita). Euro e ETFs removidos em 12/11/2026 para economizar a cota.
- Grava `opcoes_<data>_<hora>.json` (ouro_cadeia com settle, ouro_boletim) na pasta do Drive **painel-mercado-opcoes** (id `1GTHAZCrqQe_LYxf8OuR3zwqncQmHUunx`); `opcoes_drive.py` importa.

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
- **Gravando desde 13/11/2026:** put/call diário do GLD (volume e contratos em aberto: total, 0DTE, até 7 e até 30 dias) e da CME (séries curtas da tarefa noturna) → `mi_pcr_hist.json`. Testar após ~6 meses (nível e variação dos contratos em aberto → ouro 1/5/20 dias, com correção pelo nº de testes).
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
Português · respostas curtas e econômicas · "Como ler" em todo indicador novo · horário de Brasília · **opções: sempre incluir a CME (mercado muito maior) junto com o GLD, em qualquer análise ou teste**; só entra no painel o que passar em teste estatístico (previsão; retrato não serve).
