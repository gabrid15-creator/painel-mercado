#!/usr/bin/env bash
# Baixa os PDFs do boletim diário da CME (ouro e iene) e envia para a branch "pdfs" do painel.
# Roda no PC da usuária (internet de casa), pelo timer do systemd, de 30 em 30 min das 3h30 às 8h.
# Não tenta driblar bloqueio: se a CME recusar, registra no log e para.
set -u
REPO="$HOME/painel-mercado-pdfs"          # clone só para os PDFs (criado no passo a passo)
LOG="$HOME/.local/state/painel-cme.log"; mkdir -p "$(dirname "$LOG")"
URL=https://www.cmegroup.com/daily_bulletin/current
ARQS="Section64_Metals_Option_Products.pdf Section33_Japanese_Yen_Call_Options.pdf Section34_Japanese_Yen_Put_Options.pdf"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
log() { echo "$(date '+%d/%m %H:%M') $*" >> "$LOG"; }
for a in $ARQS; do
  code=$(curl -sS -L -m 60 -o "$TMP/$a" -w '%{http_code}' -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36" "$URL/$a") || code=000
  if [ "$code" != 200 ] || [ "$(head -c 4 "$TMP/$a")" != "%PDF" ]; then log "falhou $a (HTTP $code)"; exit 1; fi
done
cd "$REPO" || { log "pasta $REPO não existe"; exit 1; }
# só envia se mudou (o mesmo boletim fica no ar até sair o próximo)
novo=$(cat "$TMP"/*.pdf | sha256sum | cut -c1-16)
[ -f .ultimo ] && [ "$(cat .ultimo)" = "$novo" ] && { log "sem boletim novo"; exit 0; }
git rm -rq --cached . 2>/dev/null; rm -f ./*.pdf
cp "$TMP"/*.pdf .; git add -f ./*.pdf
c=$(git -c user.name="PC" -c user.email="pc@painel.local" commit-tree "$(git write-tree)" -m "PDFs CME $(date '+%d/%m %H:%M')")
if git push -qf origin "$c":refs/heads/pdfs; then echo "$novo" > .ultimo; log "enviado ($novo)"; else log "falhou o envio ao GitHub"; exit 1; fi
git gc -q --prune=now 2>/dev/null; true
