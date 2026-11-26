# COMECE AQUI — instruções para o Claude (conta nova do Gabriel)

Você está assumindo o projeto **Painel de mercado** (repo `gabrid15-creator/painel-mercado`, site https://gabrid15-creator.github.io/painel-mercado/). Este arquivo tem tudo: as regras da usuária, o guia de transferência e o estado atual completo. **Leia-o inteiro antes de responder.**

Faça, nesta ordem:
1. Se o repositório `gabrid15-creator/painel-mercado` não estiver na sessão, anexe-o (add_repo, com push) e clone-o. O `HISTORICO.md` (diário completo) fica lá; só abra se precisar de um detalhe antigo.
2. Siga as regras da parte 1 (CLAUDE.md) **sempre**: respostas curtas, só resumo, português do Brasil, para leigo, horário de Brasília; commit e push direto na `main`; só entra no painel o que passar em teste estatístico; CME sempre com `confere_cme.py` e só publica com 0 erro.
3. Responda SOMENTE isto, em 3 linhas: o estado atual do painel e o próximo passo.
4. Pendências de partida: recalibrar a régua da Vantage com 2 pares de preço (troca do contrato do GC); mandar o iene de 24/11 (PDFs 33 e 34) e ver por que o robô do PC não mandou o boletim; recriar a tarefa agendada de 17/05/2027 (put/call + skew).
5. Na conta nova, ainda faltam (peça ao Gabriel só se bloquear): conectar o GitHub ao Claude, criar o ambiente "painel-mercado" com a rede liberada (ver parte 2) e conferir a chave `ANTHROPIC_API_KEY` do repositório.

Quem fala com você é o Gabriel (dono do GitHub); a usuária do painel, que opera e dita os preços da Vantage, é a esposa dele. Ambos querem respostas diretas, sem rodeio.

---

# PARTE 1 — CLAUDE.md (regras do projeto)

# Painel de mercado

Leia o resumo do projeto abaixo antes de qualquer tarefa; ele é a memória entre conversas. Só abra o `HISTORICO.md` se precisar de um detalhe antigo.

@PROJETO.md

Transferência para outra conta (acessos, segredos, pendências): `TRANSFERENCIA.md`.

## Economia de tokens (prioridade)
- **Formato das respostas (pedido dela, sempre):** só o resumo final. Um item por ponto: funciona ou não + o motivo em 1 linha. Sem tabelas longas, sem detalhe técnico, sem explicar o processo.
- Objetivo fixo: **gastar o mínimo de tokens**. Respostas curtas, diretas, objetivas; sem rodeio, sem repetir o que ela disse, sem listar opções que não vai seguir.
- Não reler arquivos que já estão no resumo; ler só o trecho necessário (grep/sed com linhas), não o arquivo inteiro.
- Não refazer testes ou conferências já registrados no resumo, a não ser que ela peça ou os dados tenham mudado.
- Agir direto quando a tarefa é clara; perguntar só se a decisão for dela.
- Explicar em poucas linhas, para leigo, com o número que importa.

## Regras de trabalho
- Português do Brasil, para leigo; horário de Brasília.
- Commit e push direto na `main` (o site publica em push). A cada mudança relevante: atualizar o `PROJETO.md` (estado atual) e anexar o detalhe no `HISTORICO.md`.
- Só entra no painel o que passar em teste estatístico de previsão (t ≥ 2, estável no tempo, corrigido pelo número de testes). Retrato do momento não serve.
- Opções: sempre incluir a CME junto com o GLD. IAU descartado.
- Todo card novo tem "Como ler" direto ao ponto: o que é, como usar, como impacta o preço.
- Economia de cota: tarefas agendadas no Sonnet quando possível; não ampliar a tarefa noturna além do que o painel usa.
- A CME bloqueia robôs; dados dela só pelos PDFs que a usuária manda. **Sempre** rodar `confere_cme.py` depois dos leitores: só publica com 0 erro, extremo rigor (pedido dela). Nunca confiar no "FUTURES SETT." do cabeçalho: futuro sempre pela paridade.


---

# PARTE 2 — TRANSFERENCIA.md

# Transferência do painel para outra conta — guia completo

> **ATUALIZAÇÃO (26/11): só a conta do Claude muda.** O GitHub (repo, Actions, Pages, cron-job.org, token do robô) já é do Gabriel e **não precisa transferir nada**. Na conta nova do Claude, só refazer: (1) conectar o GitHub (claude.ai/connect-github) e instalar o app Claude no repo; (2) criar o ambiente "painel-mercado" com a rede liberada (seção 3); (3) conferir de quem é a chave `ANTHROPIC_API_KEY` (se for do Console da esposa, criar uma nova no Console do Gabriel e trocar o segredo do repo); (4) recriar a tarefa agendada de 17/05/2027 (seção 6). O resto deste guia só vale se o GitHub também mudar.

> Escrito em 26/11/2026. Serve para o Gabriel (ou qualquer conta nova do Claude/GitHub) continuar exatamente de onde parou.
> **Nenhuma senha, chave ou token está neste arquivo** (eu nunca tive acesso a eles). A seção 3 lista cada um que precisa ser recriado.
> Memória do projeto no próprio repositório: `CLAUDE.md` (regras), `PROJETO.md` (estado atual, ~32 KB), `HISTORICO.md` (diário completo, ~58 KB). **Copiar o repositório inteiro já leva tudo isso.**

---

## 1. O que levar (e como)

| Item | Onde está | Como levar |
|---|---|---|
| Código, textos, memória (`CLAUDE.md`, `PROJETO.md`, `HISTORICO.md`), testes, PDFs lidos da CME | repo `gabrid15-creator/painel-mercado`, branch `main` | **Settings → Transfer ownership** do repo (mantém histórico, Actions e Pages) ou `git clone --mirror` + `git push --mirror` para um repo novo |
| Dados da coleta (JSON, 1 commit forçado a cada 5 min) | branch `dados` | vai junto com o espelho; recria sozinha na próxima coleta (histórico longo: `mi_*_hist.json`, `mi_diario_ouro.json`, `mi_lateral_diario.json`, `mi_0dte_hist.json`, `mi_pcr_hist.json`, `mi_otc_hist.json`, `mi_surpresa_hist.json`, `mapa_fixo.json`, `mi_0dte_fixo.json` — **esses acumulam dias e não dá para recalcular; não perder**) |
| Candles de 1 min (testes de fev/2027) | branch `minutos` (`AAAA-MM-DD.csv.gz`) | idem; não dá para recuperar o passado |
| PDFs que o robô do PC manda | branch `pdfs` | idem (descartável) |
| Repo privado `Jireh-dados` (cadeia do GLD de 31/10 a 12/11, sem uso) | outra conta/repo dela | opcional |
| Robô da CME no PC dela (Linux Mint) | `~/.config/painel-cme/` (token, estado, perfil do Brave) e timer `painel-cme.timer` (systemd de usuário) | ver seção 4 |
| Tarefa agendada no Claude | teste de put/call + skew em **17/05/2027** (Sonnet) | recriar na conta nova (seção 6) |

**Ordem recomendada:** (1) transferir/espelhar o repo → (2) recriar os segredos → (3) ativar Pages → (4) recriar o disparo no cron-job.org → (5) rodar a coleta uma vez à mão e conferir → (6) refazer o robô do PC → (7) recriar a tarefa agendada.

---

## 2. Como o painel funciona (resumo de 10 linhas)

1. `coletor.py` roda a cada 5 min no GitHub Actions (`.github/workflows/coleta.yml`), disparado por **cron-job.org → `workflow_dispatch`** (o `schedule` do GitHub é só reserva). Depois roda `dtcc.py` e `ia.py` e grava tudo como 1 commit forçado na branch `dados`.
2. O site (`docs/index.html` + `docs/app.js`, D3) é publicado pelo **GitHub Pages só em push** na `main` e lê os JSON de `raw.githubusercontent.com/<dono>/painel-mercado/dados/`. **Se o dono/nome do repo mudar, trocar essa URL no `app.js` (procurar `raw.githubusercontent.com`) e em qualquer `index.html`/script que cite `gabrid15-creator`.**
3. A IA (`ia.py`, modelo `claude-haiku-5-5`, variável `IA_MODELO`) usa o segredo `ANTHROPIC_API_KEY`.
4. A CME bloqueia robôs. Os PDFs entram por: (a) ela manda e eu leio (`cme_pdf.py`, `cme_pdf_iene.py`, **sempre** `confere_cme.py`, só publica com 0 erro); ou (b) o robô do PC dela baixa pelo Brave dela, manda para a branch `pdfs` e dispara `cme_pdfs.yml`.
5. Opções do GLD: Cboe (bloqueou o servidor com 403 Cloudflare em 20–23/11; **não driblar**) → reserva `gld_yahoo()` (Yahoo + crumb).
6. Detalhes de cada cálculo, régua de preço, testes estatísticos e decisões: `PROJETO.md` (estado) e `HISTORICO.md` (por quê).

---

## 3. Acessos, contas e segredos a recriar

| O quê | Para que serve | O que fazer na conta nova |
|---|---|---|
| **GitHub** (repo, Actions, Pages) | tudo | transferir o repo; em *Settings → Pages* escolher "Deploy from branch: `main` / pasta `/docs`" (confirmar como estava); em *Actions → General* permitir workflows e "Read and write permissions" |
| **Segredo `ANTHROPIC_API_KEY`** (Actions → Secrets) | leitura da IA no painel | criar chave nova no Anthropic Console da conta nova e salvar como segredo do repo. Sem ela a coleta continua, só a leitura da IA para |
| **cron-job.org** | dispara a coleta de 5 em 5 min | recriar o job: `POST https://api.github.com/repos/<dono>/painel-mercado/actions/workflows/coleta.yml/dispatches`, corpo `{"ref":"main"}`, cabeçalhos `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, de 5 em 5 min. Token: fine-grained do GitHub, só este repo, permissão **Actions: Read and write** |
| **Token do robô do PC** (`~/.config/painel-cme/token`) | enviar PDFs à branch `pdfs` e disparar `cme_pdfs.yml` | fine-grained, só este repo, **Contents RW + Actions RW**; gravar no arquivo acima |
| **Anthropic Console** | chave da IA | ver acima |
| **DTCC** (`pddata.dtcc.com`) | opções de balcão de câmbio | grátis, sem conta |
| **Yahoo, FRED, CFTC, Tesouro, Fed NY, Bundesbank, MOF Japão, Forex Factory/biquote** | dados | públicos; nenhuma chave |
| **Google Drive, pasta "painel-mercado-opcoes"** | fluxo antigo (`opcoes_drive.py`) | sem uso hoje |
| **Ambiente Claude "painel-mercado"** (Claude Code na web) | onde as sessões rodam | recriar na conta nova com rede liberada para: Yahoo, FRED, CFTC, Cboe, SPDR, CME, DTCC (e `raw.githubusercontent.com`, `api.github.com`); Playwright/Chromium já vêm instalados |
| **Databento** | CME histórico/ao vivo (~US$ 199/mês) | ela disse que ia assinar; ainda não |
| **Vantage Markets** | só referência de preço (ela dita os preços) | nada |

---

## 4. Robô da CME no PC dela (refazer se trocar de máquina/usuário)

Arquivos no repo: `pc/baixar_cme.sh`, `pc/painel-cme.service`, `pc/painel-cme.timer`, `pc/LEIAME.md` (passo a passo de instalação — seguir esse arquivo).

- Linux Mint. O `curl` toma 403 da CME até no PC dela, então o script abre o **Brave dela num perfil separado** (`~/.config/painel-cme/brave`; precisa estar logado no site da CME), baixa os 3 PDFs (Section64 ouro, Section33/34 iene) para pasta temporária, fecha o Brave, envia à branch `pdfs` (commit órfão) e dispara `cme_pdfs.yml` (lê, confere, só grava na `main` com 0 erro).
- Timer: seg–sáb, 3h–8h de 30 em 30 min + 10h e 12h (Brasília). Estado em `~/.config/painel-cme/estado`. Confere a DATA do boletim (pdftotext) e só marca o dia como feito se for o último pregão. Auto-atualiza o script pelo GitHub (raw) a cada execução — **se o repo mudar de dono, trocar a URL dentro de `baixar_cme.sh` e do `.service`**.
- Log: `~/.local/state/painel-cme.log`.
- **Situação em 25/11/2026: o robô NÃO mandou o boletim do pregão 24/11** (último automático: 24/11 03:30 BRT, pregão 23/11). Causa não investigada (PC desligado? Brave sem sessão? boletim ainda não publicado?). Primeiro passo na conta nova: ver esse log.
- Rotina manual (quando falha): ela manda os PDFs → `python3 cme_pdf.py <Section64>` → `python3 cme_pdf_iene.py <Section33> <Section34>` → `python3 confere_cme.py --ouro <Section64> cme/opcoes_<pregão>.json --iene <Section33> <Section34> cme/iene_<pregão>.json` → só commit/push com **0 erro**. Explicar cada aviso em 1 linha.
- Em 25/11 só o ouro de 24/11 foi publicado (0 erro, 1 aviso explicado). **Falta o iene de 24/11** (Section33 e 34).
- **01/01/2027:** a CME reorganiza o boletim → conferir os leitores.

---

## 5. Estado em 26/11/2026 e pendências

**Publicado hoje (commits na `main`):**
- `240b53c` agenda: coluna "Atual"/"aguarda" não corta em tela estreita; palavra do evento não quebra.
- `8ac4fe7` CME ouro, pregão 24/11, conferido 0 erro.
- `cb76974` + remoção de `saida/`: **troca do contrato do GC=F (dez → fev)**. O Yahoo passou o GC=F para fev. (~US$ 29 acima do dez.); a Vantage segue o dez. Regra automática em `b_precos`: se GC=F ≠ mês mais perto, `VANTAGE_USD = (GC=F − mês mais perto) + 1,9` (≈ US$ 31). Níveis da CME no `b_0dte` usam o preço do contrato que o GC=F é hoje no horário do ajuste.
- Ela ditou **Vantage 3.515** quando o Yahoo mostrava dez. 3.516,8 e fev./GC=F 3.546. **Só 1 par; o Yahoo tem ~10 min de atraso.**

**Pendências (em ordem):**
1. **Recalibrar a régua da Vantage com 2 pares simultâneos** (GC × Vantage no mesmo instante, ditados por ela). Reconferir também quando o dez. vencer (fim de dezembro) — o prêmio de 1,9 muda.
2. **Verificar a coleta depois da troca de contrato**: ouro no painel ≈ Vantage; níveis da CME (teto/piso/flip/max pain) coerentes com o preço; `mi_status.json` sem erro novo (blocos "Ouro: contrato da Vantage" e "0DTE CME contrato do GC").
3. **Iene de 24/11** (PDFs 33 e 34) e investigar o robô do PC.
4. Aviso do `confere_cme.py` ("futuro pela paridade × GC=F às 13h30") é esperado enquanto o GC=F estiver em outro mês que as opções; a razão normaliza. Se quiser, ensinar o `confere_cme.py` a comparar contra o contrato certo.
5. Gamma flip da CME veio vazio (sem cruzamento perto do preço no boletim de 23/11) — ver com boletim novo.
6. Google News dá 429 ocasional (notícias); falha isolada do GitHub ("Internal Server Error" ao gravar na `dados`, run 5784 de 25/11) já passou, sem ação.
7. 0DTE do GLD depende da reserva do Yahoo (frágil); se as duas fontes falharem, o card mostra "⚠ sem atualizar".
8. Euro e franco na CME: achar as seções no boletim e seguir o molde do iene.
9. Pergunta aberta: suavizar o gamma flip do GLD (média de 15 min)?

**Testes marcados (só rodar nas datas):**
- ~fim de dez/2026: 0DTE GLD × CME e iene (`mi_0dte_hist`, `mi_0dte_iene_hist`), 1ª contagem de ~30 vencimentos; faixa do dia ±1σ do 0DTE; gregas D+0 gravadas no diário.
- ~meados de fev/2027: diário do ouro (`mi_diario_ouro.json`, ~60 dias): gamma, distância ao flip, faixa 0DTE e PCR preveem (1) ping-pong × tendência e (2) o lado do dia? Corte |t| ≥ 2,5, pré-registrado. Também: 4 hipóteses de SMT nos candles de 1 min (`minutos`); reteste do scalp GBPUSD pelo fluxo DTCC (com 6B de 1 min).
- ~mai/2027: surpresas EUA + nowcast de Cleveland; **17/05/2027** put/call + skew 25Δ (`mi_pcr_hist`).
- Notícias × lateralidade: `mi_lateral_diario.json` (acumular alguns meses).

---

## 6. Como usar o Claude na conta nova

1. Abrir o repo no Claude Code (web ou terminal). O `CLAUDE.md` é lido sozinho e puxa o `PROJETO.md`; **não é preciso colar nada**.
2. Primeira mensagem sugerida: *"Leia o resumo e me diga em 3 linhas o estado atual do painel e o próximo passo."* (foi como a usuária sempre começou).
3. Modelos: tarefas agendadas e rotina no **Sonnet** (economia de cota); a IA do painel é `claude-haiku-5-5`.
4. Recriar a **tarefa agendada de 17/05/2027** (teste put/call + skew 25Δ GLD e CME, usando `mi_pcr_hist`; corte |t| ≥ 2,5, janelas sem sobreposição, metades estáveis, reportar curto).
5. Commits: direto na `main` (o site publica em push); atualizar `PROJETO.md` (estado) e anexar o detalhe no `HISTORICO.md` a cada mudança relevante. Terminar commits com as linhas de atribuição pedidas pelo ambiente; **sem identificador de modelo** nos arquivos.
6. Não subir pastas de teste (`saida/`, `__pycache__`); usar o scratchpad da sessão para temporários.

---

## 7. Regras que a usuária impôs (valem sempre)

**Formato das respostas:** só o resumo final, em português do Brasil, para leigo, horário de Brasília. Um item por ponto: *funciona ou não + motivo em 1 linha*. Sem tabelas longas, sem detalhe técnico, sem explicar o processo, sem repetir o que ela disse, sem listar opções que não vai seguir. Ela se irrita com rodeio e erro bobo. Perguntar só quando a decisão for dela.

**Economia de tokens:** não reler arquivos já resumidos; ler só trechos (grep/sed); não refazer testes já registrados; tarefas agendadas no Sonnet; não ampliar a tarefa noturna além do que o painel usa.

**Rigor:** só entra no painel o que passar em teste estatístico de previsão (**t ≥ 2, estável nas metades, corrigido pelo número de testes**; corte |t| ≥ 2,5 quando há muitos testes). Retrato do momento não serve como sinal. Baseline/placebo, janelas sem sobreposição, sem olhar o futuro, script reproduzível em `testes/`. Dizer "retrato" quando é retrato e "não sei" quando não sabe.

**Opções:** sempre CME junto com GLD. IAU descartado.

**CME:** bloqueia robôs, **não driblar** (nem Cboe/Cloudflare). Dados da CME só pelos PDFs. **Sempre** rodar `confere_cme.py`; publicar só com **0 erro**. **Nunca** usar o "FUTURES SETT." do cabeçalho: futuro sempre pela paridade (mediana de K + C − P nos 3 strikes mais no dinheiro).

**Cards novos:** todo card tem "Como ler" no "?" direto ao ponto: o que é, como usar, como impacta o preço. Itens em frases naturais, sem bolinha, pouco "=" e "→"; texto de borda a borda no PC.

**Padronização:** mesmo cálculo, mesmo roteiro e mesmos números em todos os ativos (XAUUSD, EURUSD, USDJPY, USDCHF, GBPUSD); fonte única `docs/data/padrao.json`; leitura da IA = a mesma do mapa (um só σ, um só nível). Só a linha de opções muda por ativo.

**Visual (obrigatório antes de publicar):** varredura Playwright com os dados atuais da branch `dados`: nada sobreposto nem vazando; larguras 1200, 390, 360/340 (e 320) px; tema claro e escuro; 5 ativos, com e sem ajuda aberta; medir os retângulos dos textos. Playwright e Chromium já vêm instalados (não reinstalar).

**Ela dita os preços da Vantage** para calibrar a régua do ouro (pares simultâneos).

---

## 8. Perfil da usuária e objetivo

Opera **XAUUSD na Vantage Markets**, USDJPY, USDCHF, EURUSD (e olha GBPUSD/Nasdaq). Tem **robô de grade/DCA** (compra e vende lado a lado): ganha em dia de **ping-pong**, sofre em dia de **tendência**. Quer descobrir com estatística: (1) ping-pong × tendência (ligar ou não o robô); (2) o lado do dia (para alongar compras/vendas e ajustar o stop). Foco em opções diárias (0DTE). Pensa como trader: importa onde o dia **fecha** (pode "sambar" além do nível e voltar).

**Conclusões já fechadas (detalhe e números em `PROJETO.md` §5):**
- Comprovado e no painel: σ do dia/semana (GVZ no ouro, opções de balcão DTCC nas moedas) acerta o fechamento (±1σ 78–83%, ±2σ 96–99%); chance de tocar níveis (curva real); rompimento do σ; dia normal em σ; Ásia+Londres prevê o TAMANHO do resto do dia; horas paradas/agitadas do ouro; lateralidade (payroll quase nunca estreito; ontem estreito → hoje estreito 28–41%); regime forte do DXY/juros.
- **Não passou (não usar como sinal):** σ como ponto de reversão; "defesa"/"sambou e voltou"; formato do dia (ping-pong × tendência) por qualquer dado grátis testado; momentum do fim do dia; regras de trader; fluxo DTCC → direção e scalp; paredes do balcão; PCR/GVZ/SKEW → direção; macro de prazo maior; calendário/sessão; SMT; dia da semana e semana do mês (o "efeito segunda" era artefato do corte à meia-noite).
- **O σ diz QUANTO o preço anda, não COMO nem PARA ONDE.** Direção: "nenhum sinal comprovado".

---

## 9. Mapa dos arquivos do repositório

- `coletor.py` (coleta; funções `b_precos`, `b_faixa`, `b_0dte`, `b_0dte_iene`, `b_valid`, `b_agenda`, etc.), `ia.py`, `dtcc.py`, `minutos.py`, `cme_local.py`, `cme_pdf.py`, `cme_pdf_iene.py`, `confere_cme.py`, `confere_dtcc.py`, `faixa_backtest.py`, `goldbach_gen.py`, `opcoes_drive.py` (antigo).
- `docs/` (site): `index.html`, `app.js`, `data/` (`padrao.json`, `lateralidade.json`, `faixa_backtest.json`, `rompimento.json`, `toque_tabela.json`, `goldbach_dias.json`; reserva antiga dos demais JSON).
- `cme/` (`opcoes_<pregão>.json`, `iene_<pregão>.json`), `pc/` (robô do PC), `testes/` (todos os testes estatísticos reproduzíveis e seus resultados), `.github/workflows/` (`coleta.yml`, `cme_pdfs.yml`).
- Convenções do front (`drawBorb`, `drawZ0b`, `drawZ0j`, `drawRS`, `drawLat`, `prepAjuda`, `IDS`, `.tbl-x`, `.sec-t`): `PROJETO.md` §4.

---

## 10. Checklist de verificação depois de transferir

- [ ] Repo na conta nova, branches `main`, `dados`, `minutos`, `pdfs` presentes.
- [ ] Pages ativo e o site abre; os dados carregam (URL `raw…/dados/` correta).
- [ ] Segredo `ANTHROPIC_API_KEY` criado; cron-job.org disparando; 1 execução de `coleta.yml` com sucesso e novo commit na `dados`.
- [ ] `mi_status.json` sem erros novos; ouro do painel ≈ preço da Vantage dela.
- [ ] Token do robô do PC refeito; 1 execução manual do `baixar_cme.sh` com sucesso; `cme_pdfs.yml` verde.
- [ ] Tarefa agendada de 17/05/2027 recriada.
- [ ] Primeira sessão: "Leia o resumo e me diga em 3 linhas o estado atual do painel e o próximo passo."


---

# PARTE 3 — PROJETO.md (estado atual completo)

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
| CME pelo PC | `pc/` (`baixar_cme.sh`, `painel-cme.service/.timer`, `LEIAME.md`): Ubuntu, seg–sáb 3h30–8h de 30 em 30 min, curl dá 403 até no PC dela (17/11) → baixa abrindo o **Brave dela num perfil separado** (`~/.config/painel-cme/brave`, PDF direto para pasta temporária, fecha depois; precisa sessão logada; testado com Chromium + Xvfb), envia à branch `pdfs` (commit órfão) e dispara `.github/workflows/cme_pdfs.yml` (lê, confere, só grava na main com 0 erro). Token fine-grained em `~/.config/painel-cme/token` (Contents + Actions RW, só este repo). **Instalado no PC dela em 17/11 (Linux Mint): 1º teste ok, leitura automática conferida e publicada.** Roda 3h–8h de 30 em 30 min + 10h e 12h, abre o Brave só até pegar o boletim (estado em `~/.config/painel-cme/estado`). 18/11: confere a DATA do boletim (pdftotext) e só marca o dia como feito se for o último pregão (às 3h a CME ainda servia o de 16/11); o script se auto-atualiza pelo GitHub (raw) a cada execução. |
| GLD (0DTE) | Cboe `cdn.cboe.com/.../GLD.json` (bloqueou o servidor com 403 Cloudflare em 20–23/11/2026, não driblar) → reserva `gld_yahoo()` (Yahoo options + crumb). Se as duas falharem, o card 0DTE mostra "⚠ sem atualizar". |
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
  - **Troca de contrato feita em 25/11/2026:** o Yahoo passou o GC=F para fev. (~US$ 29 acima do dez.); a Vantage segue o dez. (3.515 com dez. 3.516,8 → dez. − US$ 1,9). Regra automática em `b_precos`: se GC=F ≠ mês mais perto, ajuste = (GC=F − mês mais perto) + 1,9 (hoje ≈ US$ 31). Só 1 par: **reconferir com 2 pares ditados por ela**. Níveis da CME agora usam o preço do contrato que o GC=F é hoje no horário do ajuste (`b_0dte`).
- **GLD → ouro:** razão ouro ÷ GLD congelada no `last_trade_time` do GLD (ouro do GC 5 min × fator, naquele horário).
  - GLD fechado ou parado → usa o `close` oficial (a Cboe manda preço de pré-mercado com horário antigo).
  - Gamma (regime e flip) é recalculado com o ouro ao vivo na escala do GLD (`Sv = ouro / r`).
  - Bug antigo: esse cálculo deslocava ~US$ 38 à noite.
- **CME ouro → painel:** nível × (GC=F 5 min às 13h30 NY do pregão ÷ futuro pela paridade) × fator.
- **CME iene → USDJPY:** strike 1/K (call de iene = put de USDJPY); régua = JPY=X às 15h NY ÷ (1/F).
- **CME em equivalente GLD:** contratos × ouro ÷ GLD (~10,9 GLD por contrato de ouro).
- **Testes de toque e de máx./mín.: só FUTUROS da CME (GC, 6J, 6E, 6S, 6B).** O Yahoo FX (`JPY=X` etc.) tem picos falsos nas máximas/mínimas e já inventou uma "defesa" de 70% que era só sujeira. Fechamentos do Yahoo FX servem.
- **Sessão do dia:** abre às **18h NY (20h BRT) para todos** (18/11: ela conferiu o candle de abertura da corretora, gráfico em horário de NY; antes as moedas abriam 17h NY). Semana das moedas: Yahoo FX só tem domingo a partir das 19h NY → abertura das 18h estimada pelo futuro da CME × razão à vista/futuro. O σ do mapa congela na 1ª coleta da sessão/semana (`mapa_fixo.json`). Chave da semana = `ativo|sem|segunda` (corrigido 16/11: na segunda o σ da semana saía igual ao do dia).

---

## 4. O que está no painel (aba Mercado, de cima para baixo)

0. **Cabeçalho "Dados de …"**: mostra também "CME: boletim de dd/mm (preliminar/final), chegou dd/mm hh:mm" (`cmeInfo()`, campo `recebido_em` gravado pelos leitores; 20/11).
1. **Panorama do dia:** leitura da IA; Fear & Greed, red folder, VIX, DXY.
2. **Macro, o que move o dólar:**
   - Radar institucional: liquidez, estresse, surpresa, regime EUA.
   - Dólar e juros: bps no cabeçalho, coluna "Leitura (fechamento)" só com Dólar/Iene e os pares (XAUUSD, EURUSD, USDJPY) com seta, verde = sobe, vermelho = cai (17/11). Resumo diz a data do fechamento dos juros dos EUA (não é "hoje"). Descreve o fechamento, não prevê.
   - Fed Funds usa o contrato fixo do mês (ex.: ZQZ26.CBT).
3. **Ativo, níveis e opções** (o seletor gruda no topo):
   - **"O que olhar hoje"** (20/11, pedido dela: painel confuso; `drawRS()`, `.op-card.rs`): σ do dia em pips/US$, dia normal (= grade) e stop (90%), níveis −1σ/normal/abertura/normal/+1σ com ✓, "Agora" (posição em σ + rompimento), resto do dia (Ásia+Londres), hora (ouro), "Direção: nenhum sinal comprovado". O mapa detalhado (tabelas, faixa, rompimento, precisão, conferência) fica em `details.mp-det` recolhido.
   - **"Quando o mercado fica lateral"** (24/11/2026, pedido dela; `drawLat()`, `.op-card.lat`, `docs/data/lateralidade.json`, igual nos 5 ativos): % de dias estreitos/normais/largos e de corpo pequeno, ontem → hoje, payroll (dia e semana), horas paradas/agitadas (Brasília), mês só onde passou (USDJPY). Dia da semana e semana do mês: **nenhuma diferença comprovada** (o "efeito segunda" das barras diárias do Yahoo era artefato do corte à meia-noite; na sessão real 18h→17h NY não existe). Scripts `testes/lateralidade.py` (15 anos diário, 75 testes, Bonferroni, metades) e `testes/lateralidade2.py` (sessão real 2 anos, persistência, GVZ). Registro diário para medir notícias: `mi_lateral_diario.json` (amplitude em σ, corpo, red folders do dia; 16h–18h NY).
   - **Padronização (24/11/2026, pedido dela): mesmo cálculo, mesmo roteiro e mesmos números em todos os ativos.** `docs/data/padrao.json` é a fonte única (dia normal, cortes Ásia+Londres, horas do ouro): a tela (`qNormal/cCedo/hOuro`) e o resumo da IA leem dali. A leitura da IA segue o mesmo roteiro para os 5 ativos ([σ], [DIA fixo], [SEMANA fixa], [AGORA], [LATERALIDADE], [RESTO DO DIA], [OPÇÕES]); só a linha de opções muda (ouro = 0DTE GLD+CME, iene = 0DTE CME, euro/franco/libra = σ pelas opções de balcão DTCC, sem 0DTE próprio). **Qual σ olhar:** o do DIA fixo na abertura (card "O que olhar hoje", mesmo número do mapa e da IA; testado: ±1σ 78–83%, ±2σ 96–99%); o da SEMANA para posição de vários dias (73–83% / 97%); 0DTE = complemento ainda sem teste (fim de dez.).
   - **Mapa "até onde o preço deve ir":**
     - tabelas Hoje e Semana, níveis ±0,5/1/1,5/2σ a partir da abertura;
     - "chance agora": z = distância log ÷ (σ × √fração restante), com a curva real medida em 2 anos de 1 h (`toque_tabela.json`);
     - leitura em palavras: alvo provável ≥ 50%, possível 20–49%, difícil 8–19%, raro < 8%;
     - "Teste um preço" aceita vírgula e ponto.
   - **Rompimento do σ do dia** (`.mp-romp`, `rompimento.json`): preço de cada gatilho (±1σ/±1,25σ/±1,5σ), o que costuma acontecer depois e a linha "Hoje: em cima Xσ → …".
   - **Faixa esperada:**
     - ouro = GVZ, mais a CME (straddle no dinheiro da 1ª série com ≥ 3 dias úteis);
     - moedas = **vol. implícita das opções de balcão (DTCC)**: `dtcc.py` → `mi_otc.pares[].vol_impl` (negócios das últimas 24 h, prazo 1–30 d, strike ≤ 1% do preço na hora, prêmio → Black; mediana; ≥ 5 negócios); `b_faixa` usa se o mi_otc tiver < 3 h; reserva: vol. realizada 21 d × 1,09. 17/11: USDJPY DTCC 6,76% × CME 6,82%;
     - etiqueta da vol. contra a média de 1/3/5 anos (pesos 50/30/20);
     - tabela **Precisão medida** visível (`faixa_backtest.json`).
   - **Conferência diária** (`mi_validacao.json`): toque real × chance prevista, faixa e 0DTE (GLD e CME separados).
   - **0DTE ouro:** só a **borboleta** (`drawBorb`).
     - **Níveis fixos do dia (24/11/2026, pedido dela: teto/piso/flip mudavam a cada coleta):** teto, piso, max pain, gamma flip (GLD e CME) e faixa são calculados **só com contratos em aberto** (sem o volume do dia); 9h30–10h NY = calibra (mediana das coletas), **10h NY = fixa até o vencimento** (`mi_0dte_fixo.json`; campo `fixacao` no `mi_0dte`; valores ao vivo ficam em `vivo`, `cwv/pwv/gfv` no `mi_0dte_dia`). Ao vivo: preço, regime de gamma agora, barras/volume. O retrato de validação (`mi_0dte_hist`) e a foto da manhã do diário passam a ser os níveis fixos das 10h NY (antes: 1ª coleta, com OI + volume; dias 12–23/11 têm outra definição).
     - **Faixas do card 0DTE (25/11/2026, ela não entendia a "faixa até o vencimento" do GLD):** (1) **Faixa do dia ±1σ** = σ fixo da abertura (a do mapa; coluna CME = straddle de 1 dia do ajuste de ontem, mesmo tamanho: 23–24/11 ±70–72); (2) **"O que falta andar"** = straddle do GLD que vence hoje às 16h NY, centrado no preço de agora, ao vivo: encolhe com o tempo (implícita ~38% a.a., coerente) e NÃO é faixa do dia. O ±1σ tracejado do gráfico agora é o do dia; a sombra azul é o que falta andar. O `faixa`/`s1` congelado às 10h NY segue só para a validação (`mi_0dte_hist`: preço de fechamento × faixa de 10h NY→16h).
     - **Quando cada nível fica fixo:** CME (teto, piso, max pain, faixa) = desde que o boletim chega (~3h BRT); flip da CME = na 1ª conta depois do boletim (`cme|venc|pregão` no `mi_0dte_fixo.json`); GLD = provisório até as 10h NY (12h BRT no inverno, 11h no verão americano), depois fixo. σ do mapa = fixo desde a abertura das 20h BRT.
     - **Uma só leitura:** `faixas` dia/semana do `mi_faixa` (e da CME) agora saem do preço de ABERTURA com σ congelado = igual ao mapa e à leitura da IA (antes saíam do preço de agora). A IA recebe os mesmos níveis e é instruída a não calcular outra faixa.
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
4. **Agenda e notícias:** Forex Factory com "Atual" ao vivo (biquote/BLS/FRED); notícias com filtro. **Histórico recolhido (25/11, pedido dela):** Agenda da semana e "Eventos de hoje em diante" (aba Alto impacto) mostram só de HOJE em diante; dias anteriores ficam atrás do botão "▸ Ver N eventos de dias anteriores" (`barraAnt()`, barra ACIMA da tabela). Calendários (Alto impacto e Goldbach): mês atual e seguinte abertos; o anterior em `details.gb-ant` recolhido (Goldbach só mostra o anterior se houver dados dele).
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
| **Dia típico em σ** (`testes/dia_tipico.py`, futuros diários 15 anos, ~3.750 dias cada) | Metade dos dias fecha a ≤ 0,55σ da abertura (moedas; ouro 0,45σ); 68% ≤ 0,85σ; 90% ≤ 1,5σ. Amplitude máx−mín mediana 1,2σ. Ouro com σ GVZ: 0,44σ / 90% ≤ 1,35σ / amplitude 1,05σ. Estável. **Na tela: bloco "Dia normal" do mapa** (`.mp-normal`, constantes `Q` no `app.js`). |
| **Ásia + Londres → tamanho do resto do dia** (`testes/range_cedo.py`, futuros 1 h, 2 anos, ~555 dias) | Amplitude 18h→9h NY em σ × amplitude 9h→17h: r 0,30–0,50 (t 7–14), metades estáveis. Cedo no terço alto → resto grande 61–73%; terço baixo → 30–42% (acaso 50%). Ouro (σ GVZ) o mais fraco: r 0,30 (metades 0,36/0,22). Na tela a partir das 11h BRT (`mapa.amp_cedo`, medido no futuro da CME; constantes `C` no `app.js`). Diz o TAMANHO, não o formato nem a direção. |
| **Horário em que o ouro anda menos** (`testes/horas_lateral.py`, GC 1 h 2 anos, metades estáveis) | Amplitude por hora em σ do dia: mais parado 17h–01h BRT (0,19–0,24σ/h ≈ US$ 12–15) e 14h–16h (0,24–0,27σ); mais agitado 10h–12h (0,48σ/h ≈ US$ 30) e 09h/22h (~0,38σ). Só TAMANHO: a proporção de horas "vai e volta" (5 min, 60 dias) é ~45–55% em todas as horas, sem horário mais ping-pong. Horas BRT misturam horário de verão americano (±1 h). Ainda não está na tela. |
| **Vol. das opções de balcão (DTCC) nas moedas** (`testes/vol_dtcc.py`, 2 anos, 380–480 dias/par) | Prevê a amplitude do dia melhor que a vol. realizada nos 4 pares: r 0,35–0,55 × 0,18–0,45, metades estáveis. ±1σ dia 78–83%, ±2σ 96–99%; semana 73–83% / 97–98%. Dia normal com σ DTCC: 50% ≤ 0,43–0,57σ, 90% ≤ 1,20–1,50σ, amplitude 0,97–1,16σ (constantes `Q`; cortes `C` reescalados pela razão realizada/DTCC). Precisão na tela via `faixa_backtest.json[par].dtcc`. Só opções ≤ 2 dias (`TENOR=2`): σ ~50% maior (USDJPY 15,6% × 10,7%), ±1σ contém 89–93% e prevê um pouco pior (r 0,31–0,51) → mantido 1–30 d. **Métricas do mapa das moedas refeitas com o σ DTCC** (`testes/metricas_dtcc.py`, série `testes/vol_dtcc_serie.json`): `toque_tabela.json` e `rompimento.json` das moedas (campo `sigma: "DTCC"`, 378–483 dias). Ex. USDJPY: toca +1σ 14% (antes 22%), fecha dentro ±1σ 83%; tocou 1σ → fecha fora 45–54%; passou 1,25σ → 64–76%; passou 1,5σ → 73–85%. Iene: toca 1σ metades 41%/30% (instável, 2025 teve choques). CME iene só desde 11/2026 → sem histórico para medir. |
| **Lateralidade** (`testes/lateralidade.py` e `lateralidade2.py`; estreito = amplitude ≤ 0,70 × média dos 20 dias anteriores; 75 testes, corte p 0,0007, estável nas metades) | % de dias estreitos: ouro 31, iene 30, libra 27, euro 24, franco 24; largos 15–19. **Payroll (1ª sexta): estreito só 7–13% (normal 24–32%), largo 25–42%** (5 ativos). **Ontem estreito → hoje estreito 28–41%; ontem largo → 16–22%** (p < 1e-5, 15 anos). Semana do payroll: mais larga em iene/euro/franco/libra/ouro. Horas (Brasília): mais paradas 17h–20h e 01h; mais agitadas 10h–12h e 22h. Dia da semana, semana do mês: nada (sessão real, 2 anos). Mês: só iene (abr/out/dez mais laterais, nov mais volátil). Ouro: GVZ bem abaixo do normal → 35% dias estreitos (normal 29%), efeito pequeno. |
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
