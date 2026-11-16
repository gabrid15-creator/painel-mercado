# Painel de mercado

Leia o resumo completo do projeto abaixo antes de qualquer tarefa; ele é a memória entre conversas.

@PROJETO.md

## Regras de trabalho
- Português do Brasil, respostas curtas e diretas, para leigo; horário de Brasília.
- Commit e push direto na `main` (o site publica em push). Mantenha o `PROJETO.md` atualizado a cada mudança relevante.
- Só entra no painel o que passar em teste estatístico de previsão (t ≥ 2, estável no tempo, corrigido pelo número de testes). Retrato do momento não serve.
- Opções: sempre incluir a CME junto com o GLD. IAU descartado.
- Todo card novo tem "Como ler" direto ao ponto: o que é, como usar, como impacta o preço.
- Economia de cota: tarefas agendadas no Sonnet quando possível; não ampliar a tarefa noturna além do que o painel usa.
- A CME bloqueia robôs; dados dela só pelos PDFs que a usuária manda. **Sempre** rodar `confere_cme.py` depois dos leitores: só publica com 0 erro, extremo rigor (pedido dela). Nunca confiar no "FUTURES SETT." do cabeçalho: futuro sempre pela paridade.
