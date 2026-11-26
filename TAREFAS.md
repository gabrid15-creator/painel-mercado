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
| aberto | CHAT | Ver o log do robô da CME depois de 27/11 03:00 | branch `log`; desfazer o envio: `git revert 61b44a5` |
| aberto | CHAT | CME 25/11 (ouro e iene) e iene de 24/11 | aguarda PDFs do Gabriel |
| aberto | CHAT | Recalibrar a régua da Vantage com 2 pares | aguarda preços simultâneos; `coletor.py` (`b_precos`) |
| feito | CODE | Conferir a coleta depois da troca de contrato do GC (ouro e níveis da CME coerentes) | 26/11: coerente (sem salto de ~US$ 29 entre 24 e 25/11; régua dez. + 1,9 = US$ 29,3; níveis GLD e CME em volta do preço). Só corrigido o texto `como` do `mi_geral` (dizia 6,5 fixo). Desfazer: `git revert` deste commit |
| aberto | CODE | Euro e franco na CME só se precisar de dado ao vivo; a leitura dos PDFs é do chat | combinar antes (não iniciado). Obs. 26/11: a sessão do Code está no ambiente "Default", que bloqueia Yahoo/FRED/Cboe/DTCC; o ambiente "painel-mercado" não existe mais |

Linhas `feito` com mais de 30 dias: apagar (o detalhe fica no `HISTORICO.md`).
