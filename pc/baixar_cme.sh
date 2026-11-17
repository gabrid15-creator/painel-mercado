#!/usr/bin/env bash
# Baixa os PDFs do boletim diário da CME (ouro e iene) e envia para a branch "pdfs" do painel.
# Roda no PC da usuária (internet de casa), pelo timer do systemd, de 30 em 30 min das 3h30 às 8h.
set -u
REPO="$HOME/painel-mercado-pdfs"          # pasta só para os PDFs (criada no passo a passo)
TOKEN=$(cat "$HOME/.config/painel-cme/token" 2>/dev/null)   # token do GitHub só deste repositório (Contents e Actions: leitura e escrita)
GH=gabrid15-creator/painel-mercado
LOG="$HOME/.local/state/painel-cme.log"; mkdir -p "$(dirname "$LOG")"
URL=${CME_URL:-https://www.cmegroup.com/daily_bulletin/current}
ARQS="Section64_Metals_Option_Products.pdf Section33_Japanese_Yen_Call_Options.pdf Section34_Japanese_Yen_Put_Options.pdf"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
log() { echo "$(date '+%d/%m %H:%M') $*" >> "$LOG"; }
# A CME recusa programas simples de download (curl → 403) e aceita navegador de verdade.
# Por isso abre o Brave da própria usuária num PERFIL SEPARADO (não mexe no Brave normal), só para baixar os 3 PDFs, e fecha.
# PC fraco (i3, HD) rodando o copy: abre o navegador o MÍNIMO de vezes.
# Já pegou o preliminar hoje → só volta às 10h/12h para o final; já pegou o final → não abre mais hoje.
EST="$HOME/.config/painel-cme/estado"; HOJE=$(date +%F); H=$(date +%H)
if [ -f "$EST" ] && [ "$(cut -d' ' -f1 "$EST")" = "$HOJE" ]; then
  case "$(cut -d' ' -f2 "$EST")" in FINAL) exit 0;; PRELIM) [ "$H" -lt 10 ] && exit 0;; esac
fi
BRAVE=${BRAVE_BIN:-}; [ -n "$BRAVE" ] || BRAVE=$(command -v brave-browser || command -v brave || command -v brave-browser-stable)
[ -n "$BRAVE" ] || { log "Brave não encontrado"; exit 1; }
PERFIL="$HOME/.config/painel-cme/brave"; mkdir -p "$PERFIL/Default"
# preferências do perfil: baixar PDF direto (sem abrir o leitor), na pasta temporária, sem perguntar
cat > "$PERFIL/Default/Preferences" <<P
{"plugins":{"always_open_pdf_externally":true},"download":{"default_directory":"$TMP","prompt_for_download":false,"directory_upgrade":true},"savefile":{"default_directory":"$TMP"},"profile":{"exit_type":"Normal","exited_cleanly":true}}
P
# precisa da tela da sessão aberta (sem janela o navegador não baixa): acha a tela do Ubuntu sozinho (X11 ou Wayland)
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}" DISPLAY="${DISPLAY:-:0}"
[ -z "${XAUTHORITY:-}" ] && XA=$(ls "$XDG_RUNTIME_DIR"/.mutter-Xwaylandauth.* "$XDG_RUNTIME_DIR"/gdm/Xauthority "$HOME/.Xauthority" 2>/dev/null | head -1) && [ -n "$XA" ] && export XAUTHORITY="$XA"
[ -z "${WAYLAND_DISPLAY:-}" ] && [ -S "$XDG_RUNTIME_DIR/wayland-0" ] && export WAYLAND_DISPLAY=wayland-0
URLS=""; for a in $ARQS; do URLS="$URLS $URL/$a?x=$(date +%s%N)"; done
nice -n 19 ionice -c3 "$BRAVE" --user-data-dir="$PERFIL" --no-first-run --no-default-browser-check --disable-session-crashed-bubble \
  --disable-extensions --disable-gpu --disable-background-networking --disable-component-update --disable-sync --mute-audio \
  --disk-cache-size=1 --window-size=800,600 $URLS >/dev/null 2>&1 &   # prioridade mínima: o copy/MetaTrader vem primeiro
for i in $(seq 1 120); do   # espera até 4 min os 3 PDFs completos (PC lento)
  n=0; for a in $ARQS; do [ -s "$TMP/$a" ] && [ "$(head -c 4 "$TMP/$a")" = "%PDF" ] && n=$((n+1)); done
  [ $n -eq 3 ] && ! ls "$TMP"/*.crdownload >/dev/null 2>&1 && break; sleep 2
done
pkill -f -- "--user-data-dir=$PERFIL" 2>/dev/null; sleep 1
for a in $ARQS; do
  if [ ! -s "$TMP/$a" ] || [ "$(head -c 4 "$TMP/$a")" != "%PDF" ]; then log "falhou $a (o Brave não baixou)"; exit 1; fi
done
rm -f "$TMP"/*.crdownload
cd "$REPO" || { log "pasta $REPO não existe"; exit 1; }
# só envia se mudou (o mesmo boletim fica no ar até sair o próximo)
novo=$(cat "$TMP"/*.pdf | sha256sum | cut -c1-16)
[ -f .ultimo ] && [ "$(cat .ultimo)" = "$novo" ] && { log "sem boletim novo"; [ "$H" -ge 10 ] && echo "$HOJE FINAL" > "$EST"; exit 0; }
git rm -rq --cached . 2>/dev/null; rm -f ./*.pdf
cp "$TMP"/*.pdf .; git add -f ./*.pdf
c=$(git -c user.name="PC" -c user.email="pc@painel.local" commit-tree "$(git write-tree)" -m "PDFs CME $(date '+%d/%m %H:%M')")
[ -n "$TOKEN" ] || { log "sem token em ~/.config/painel-cme/token"; exit 1; }
if ! git push -qf "https://x-access-token:$TOKEN@github.com/$GH.git" "$c":refs/heads/pdfs; then log "falhou o envio ao GitHub"; exit 1; fi
# dispara a leitura + conferência no GitHub
code=$(curl -sS -o /dev/null -w '%{http_code}' -X POST -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GH/actions/workflows/cme_pdfs.yml/dispatches" -d '{"ref":"main"}')
TIPO=PRELIM; command -v pdftotext >/dev/null && pdftotext -l 1 "$TMP/Section64_Metals_Option_Products.pdf" - 2>/dev/null | grep -q FINAL && TIPO=FINAL
[ "$code" = 204 ] && { echo "$HOJE $TIPO" > "$EST"; echo "$novo" > .ultimo; log "enviado e leitura disparada ($novo)"; } || { log "PDFs enviados, mas o disparo falhou (HTTP $code)"; exit 1; }
git gc -q --prune=now 2>/dev/null; true
