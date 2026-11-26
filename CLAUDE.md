# Painel de mercado

Leia o resumo do projeto abaixo antes de qualquer tarefa; ele é a memória entre conversas. Só abra o `HISTORICO.md` se precisar de um detalhe antigo.

@PROJETO.md

**Antes de qualquer mudança, siga o quadro abaixo** (divisão entre o chat do Projeto e o Claude Code):

@TAREFAS.md

Para colar numa conversa nova: `COMECE_AQUI.md` (regras + transferência + estado, tudo em um arquivo). Transferência: `TRANSFERENCIA.md`.

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
