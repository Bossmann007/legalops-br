# Instalação — LegalOps (passo a passo)

Guia para **instalar** o LegalOps na máquina do escritório. Feito para ser seguido por
quem monta o computador (pode ser você ou alguém de confiança). Depois de instalado, o
uso do dia a dia está no [QUICKSTART-TIA.md](QUICKSTART-TIA.md) — sem tecnês.

> ⚠️ **Regra de ouro da instalação:** o LegalOps guarda dados de cliente nesta pasta. **NUNCA**
> instale dentro de OneDrive, Google Drive, Dropbox ou iCloud — isso vazaria dado de cliente pra
> nuvem (LGPD). Use uma pasta **local**, ex.: `~/legalops`. O instalador recusa pasta sincronizada
> automaticamente.

## 0. O que precisa ter antes (uma vez só)
- **Python 3.11 ou mais novo.** Teste: `python3 --version`.
- **uv** (gerenciador Python, recomendado). Instale: `curl -LsSf https://astral.sh/uv/install.sh | sh`.
  (Se não tiver uv, o instalador usa `pip` — funciona igual.)
- **Claude Code** instalado e logado na conta Claude dela (Pro).

## 1. Colocar o projeto numa pasta LOCAL
```bash
# pasta local, FORA de qualquer nuvem sincronizada
mkdir -p ~/legalops && cd ~/legalops
git clone https://github.com/Bossmann007/legalops-br.git .
```
(Se não usa git: copie a pasta do projeto para `~/legalops`.)

## 2. Rodar o instalador
```bash
cd ~/legalops
bash setup.sh
```
O que ele faz sozinho:
- **Recusa** se a pasta estiver numa nuvem sincronizada (proteção LGPD).
- Instala o engine Python (`uv sync` ou `pip`).
- Gera um **salt de PII** e grava em `.env` (esse arquivo é local e nunca sobe pro git/nuvem).

Deu certo quando aparecer: `✅ LegalOps instalado.`

## 3. Ativar como plugin do Claude Code
O harness (comandos `/`) roda como plugin do Claude Code. Dentro da pasta do projeto:
```bash
cd ~/legalops
claude plugin install .
```
Isso registra os comandos (`/painel`, `/prazo`, `/intimacao`, `/varrer`, …) e os hooks
(carrega o estado do escritório e mostra o guia de comandos no início de cada sessão).

> Se `claude plugin install .` não existir na versão dela, aponte o Claude Code para a pasta
> do projeto como plugin local conforme a documentação da versão instalada. O essencial: o
> Claude precisa enxergar `.claude-plugin/plugin.json` desta pasta.

## 4. Conectar a caixa de email (para o `/varrer`) — opcional
O `/varrer` checa a caixa dela (Outlook/M365) por intimações novas. Para isso, o **conector
Outlook/Microsoft 365** precisa estar ligado na conta Claude dela.

1. Em claude.ai → Configurações → Conectores → conectar **Outlook / Microsoft 365** (login OAuth dela).
2. Autorize acesso de **leitura** ao email.

**Se o plano dela não tiver esse conector:** sem problema — ela usa o `/intimacao` (colar a
intimação na mão), que funciona do mesmo jeito. O `/varrer` é conveniência, não obrigatório.

> ⚠️ Confirme antes: nem todo plano tem o conector M365. Se não tiver, o `/varrer` avisa que
> não conseguiu olhar a caixa (nunca finge que "não há prazo") e manda usar o `/intimacao`.

## 5. Primeiro uso
Abra o Claude Code dentro de `~/legalops` e rode, nesta ordem:
1. `/onboarding` — configura o escritório (nome, OAB, áreas, aliases de cliente). Os dados reais
   ficam em `memory.local/` (local, nunca versionado).
2. `/painel` — visão geral.
3. `/varrer` (se conectou o email) ou `/intimacao` (colar) — processar intimações.

## 6. Atualizar depois
```bash
cd ~/legalops
git pull
bash setup.sh   # re-sincroniza dependências; o .env e os dados locais ficam intactos
```

## Segurança / LGPD (não pular)
- Pasta **local**, nunca sincronizada. Dados de cliente por **apelido** (`CLI-021`), nunca nome real.
- `.env`, `data/`, `logs/`, `memory.local/` são locais e gitignored — não copie para nuvem.
- Leia uma vez: [AVISO-E-RISCOS.md](AVISO-E-RISCOS.md).
