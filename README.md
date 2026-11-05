# Painel de mercado

Site: https://gabrid15-creator.github.io/painel-mercado/

- `coletor.py` coleta os dados (Yahoo, Tesouro dos EUA, Fed de NY, Bundesbank, CFTC, CNN, Forex Factory, notícias) e calcula score, sazonalidade, correlações e COT.
- `.github/workflows/coleta.yml` roda a cada 5 minutos e publica o site (GitHub Pages).
- `docs/data/mi_ia.json` é a leitura da IA, escrita pelo Claude duas vezes por dia.
- `goldbach_gen.py` gera `docs/data/goldbach_dias.json`.
