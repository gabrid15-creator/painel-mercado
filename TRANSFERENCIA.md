# Transferência do painel para outra conta — guia completo

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
