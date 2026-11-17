# PDFs da CME pelo seu PC (Ubuntu)

O PC baixa os 3 PDFs da CME de madrugada (seg a sáb, de 30 em 30 min das 3h às 8h, e de novo às 10h e 12h para pegar a versão final), envia ao GitHub
e dispara a leitura. O GitHub lê, confere com rigor e só publica no painel com **0 erro**.
Se der erro, nada é publicado e o GitHub te avisa por e-mail.

**Como baixa:** a CME recusa programas simples (curl → 403), mas aceita navegador. O robô abre o **Brave** num perfil separado (não mexe no seu Brave), baixa os 3 PDFs e fecha. Precisa: Brave instalado e **você logada no Ubuntu** (tela bloqueada serve; desligado ou deslogado não).

## 1. Criar o token do GitHub (uma vez)

1. GitHub → foto → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. Nome: `painel-cme` · Expiração: 1 ano.
3. **Repository access** → *Only select repositories* → `painel-mercado`.
4. **Permissions** → *Repository permissions*:
   - **Contents**: Read and write
   - **Actions**: Read and write
5. **Generate token** e copie (começa com `github_pat_`).

## 2. Instalar no PC (copie e cole no Terminal, um bloco por vez)

```bash
sudo apt install -y git curl poppler-utils
```

```bash
mkdir -p ~/painel-cme ~/.config/painel-cme ~/.config/systemd/user ~/painel-mercado-pdfs
R=https://raw.githubusercontent.com/gabrid15-creator/painel-mercado/main/pc
curl -sSL $R/baixar_cme.sh -o ~/painel-cme/baixar_cme.sh && chmod +x ~/painel-cme/baixar_cme.sh
curl -sSL $R/painel-cme.service -o ~/.config/systemd/user/painel-cme.service
curl -sSL $R/painel-cme.timer -o ~/.config/systemd/user/painel-cme.timer
cd ~/painel-mercado-pdfs && git init -q
```

Guardar o token (cole quando pedir; não aparece na tela):

```bash
read -rsp "Cole o token: " T && echo "$T" > ~/.config/painel-cme/token && chmod 600 ~/.config/painel-cme/token && echo " ok"
```

Ligar o agendamento (roda mesmo sem você estar usando o PC):

```bash
systemctl --user daemon-reload && systemctl --user enable --now painel-cme.timer && loginctl enable-linger "$USER"
```

## 3. Testar agora

```bash
~/painel-cme/baixar_cme.sh; tail -3 ~/.local/state/painel-cme.log
```

- `enviado e leitura disparada` → funcionou.
- `sem boletim novo` → funcionou (o boletim de hoje já tinha ido).
- `falhou ... (HTTP 403)` → a CME bloqueou também o seu PC. Me avise; voltamos ao envio manual.

Ver os próximos horários: `systemctl --user list-timers painel-cme.timer`
