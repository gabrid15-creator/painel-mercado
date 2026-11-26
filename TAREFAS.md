# Quadro de tarefas: chat do Projeto × Claude Code (desde 26/11/2026)

Duas conversas trabalham neste repositório. Este arquivo evita trabalho em dobro, sobrescrita e tarefa esquecida.

## Quem faz o quê
**Padrão: tudo é do CHAT** (Projeto Gabriel no claude.ai).
**O CODE faz só o que o chat não consegue:** o que precisa buscar dados ao vivo nas fontes (Yahoo, FRED, CFTC, Cboe, DTCC, Tesouro). Testado no chat em 26/11: essas fontes são bloqueadas.
Exemplos do CODE: rodar o `coletor.py`/`dtcc.py` de verdade, incluir ou consertar fonte de dados, teste estatístico que baixa dados.
O chat faz o resto: PDFs da CME e `confere_cme.py`, robô do PC, textos e visual (Playwright funciona nele, dados pela branch `dados`), documentação e status.

## Regras (valem para os dois)
1. Começo: `git pull --ff-only` e ler este arquivo.
2. Só pegar tarefa da própria coluna "Dono". Antes de mexer, marcar `fazendo` com os arquivos, commit e push.
3. Arquivo listado numa tarefa `fazendo` do outro: não tocar.
4. Fim: `git pull --rebase`, commit, push; marcar `feito` com o commit e como desfazer; atualizar `PROJETO.md` e `HISTORICO.md`.
5. Nunca `push --force` na `main`. Conflito: parar e avisar o Gabriel.
6. Precisa do outro: criar linha `aberto` com o dono certo. Não fazer por conta própria.
7. O CODE não edita os docs do Projeto no claude.ai. O chat copia o resumo daqui para `claude/painel/STATUS-painel.md`.

## Tarefas
| Estado | Dono | Tarefa | Arquivos / observação |
|---|---|---|---|
| aberto | CHAT | Confirmar o robô da CME no log de 27/11 depois das 03:00 | 26/11 19:25 ok pelo systemd; suspeita: chaveiro, aplicado `--password-store=basic` (desfazer: `git revert` do commit "Robô CME: sem chaveiro"); desfazer o envio do log: `git revert 61b44a5` |
| feito | CHAT | CME 25/11 (ouro e iene) | 26/11 19:20, automático, 0 erro, commit 0bfd6c5. Desfazer: `git revert 0bfd6c5` |
| aberto | CHAT | CME iene de 24/11 | aguarda PDFs do Gabriel |
| aberto | CHAT | Recalibrar a régua da Vantage com 2 pares | aguarda preços simultâneos; `coletor.py` (`b_precos`) |
| feito | CODE | Conferir a coleta depois da troca de contrato do GC (ouro e níveis da CME coerentes) | 26/11: coerente (sem salto de ~US$ 29 entre 24 e 25/11; régua dez. + 1,9 = US$ 29,3; níveis GLD e CME em volta do preço). Só corrigido o texto `como` do `mi_geral` (dizia 6,5 fixo). Desfazer: `git revert` deste commit |
| aberto | CODE | Euro e franco na CME só se precisar de dado ao vivo; a leitura dos PDFs é do chat | combinar antes (não iniciado). Obs. 26/11: o Code voltou ao ambiente "painel-mercado" (Yahoo, FRED, DTCC etc. liberados; incluído `cdn-api.cboe.com`, para onde a Cboe agora redireciona o GLD.json) |
| feito | CHAT | Recados P1, P4, P5, P8, P9, P10, P11 (texto da IA), P12 e `mi_quant_diario.json` | 26/11, commit ef5f8c5, conferido na coleta 16:51. Desfazer: `git revert ef5f8c5`. Arquivos liberados |
| feito | CODE | P2 (prioridade): série do ouro ajustada por contrato (var 1d/5d/20d/ano, ATR, 52s, correlações, valor justo, CTA, score) | 26/11: `mi_rolagem.json` + razão da troca (var. do dia +1,63% → +0,81%). Desfazer: `git revert` deste commit |
| feito | CODE | P3: candle diário das moedas (correlação EURUSD x DXY errada), var 1d e sazonalidade por dia | 26/11: fechamento do dia = abertura da barra seguinte (Yahoo `=X`); EURUSD × DXY −0,93. Desfazer: `git revert` deste commit |
| feito | CODE | P6: put/call e skew do GLD pela reserva Yahoo (delta pela vol implícita, marcar fonte) | 26/11: delta Black-Scholes, todos os vencimentos, `fonte_gld`; skew 25Δ volta a gravar. Yahoo dá put/call 0,43 × Cboe 0,29 (diferença de fonte). Desfazer: `git revert` deste commit |
| feito | CODE | P7: `dtcc.py` só marcar dia coberto com arquivo fechado; ver 88 erros; avaliar mínimo > 5 negócios | 26/11: só arquivo fechado marca o dia; erros por rodada (os 88 eram acumulado de conexão derrubada); mínimo 10 negócios com janela 48/72 h. Desfazer: `git revert` deste commit |
| feito | CODE | P11 (resto): σ do NAS100 pelo VXN | 26/11: testado (dia ±1σ 77–78%, ±2σ 97,5%, 2001+), no `mi_faixa`, sem mapa. Desfazer: `git revert` deste commit |
| aberto | CHAT | Mostrar a faixa do NAS100 (VXN) na tela e liberar na IA (hoje o ia.py diz "NAS100 sem σ") | `mi_faixa` já tem NAS100 (sem `mapa`); `docs/app.js`, `ia.py`; precisão em `testes/faixa_vxn_resultado_2026-11-26.txt` |

Linhas `feito` com mais de 30 dias: apagar (o detalhe fica no `HISTORICO.md`).

## Detalhe dos números (auditoria de 26/11)
- P2: 26/11 16:25 o painel dava +1,64% no dia; abertura 3588,7 e preço 3564,3 (-0,68%); fechamento 25/11 no diário 3577,8. Causa provável: fator Vantage de hoje aplicado à série inteira após a troca do GC.
- P3: EURUSD x DXY +0,21 (20d) e -0,08 (250d); na semanal -0,83.
- P6: desde 23/11 delta 0, `gld_skew25` não grava; `gld_total` só até 40 dias (0,44 contra 0,29).
- P7: USDCHF com 7 a 8 negócios, GBPUSD com 10.
