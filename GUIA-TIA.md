# LegalOps — Guia da Tia (instalação + uso)

Seu **Sócio Invisível**: ajuda com prazos, contratos, LGPD e o dia a dia do escritório.
Ele **rascunha e organiza** — quem decide, revisa e assina é sempre você.

Este arquivo tem duas partes:
- **Parte A — Instalação** (uma vez, por quem monta o computador).
- **Parte B — Uso do dia a dia** (sem tecnês).

> ⚠️ **Leia uma vez:** [AVISO-E-RISCOS.md](docs/AVISO-E-RISCOS.md). Resumo: nada aqui substitui
> o PJe/Projudi nem o seu julgamento. Todo texto sai como **rascunho (DRAFT)**.

---

# Parte A — Instalação (passo a passo)

Feito para ser seguido por quem monta o computador (você ou alguém de confiança).

> ⚠️ **Regra de ouro:** o LegalOps guarda dados de cliente nesta pasta. **NUNCA** instale dentro
> de OneDrive, Google Drive, Dropbox ou iCloud — isso vazaria dado de cliente pra nuvem (LGPD).
> Use uma pasta **local**, ex.: `~/legalops`. O instalador recusa pasta sincronizada automaticamente.

## 0. O que precisa ter antes (uma vez só)
- **Python 3.11 ou mais novo.** Teste: `python3 --version`.
- **uv** (gerenciador Python, recomendado): `curl -LsSf https://astral.sh/uv/install.sh | sh`.
  (Sem uv, o instalador usa `pip` — funciona igual.)
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
- Gera um **salt de PII** e grava em `.env` (local, nunca sobe pro git/nuvem).

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

## 5. Atualizar depois
```bash
cd ~/legalops
git pull
bash setup.sh   # re-sincroniza dependências; o .env e os dados locais ficam intactos
```

---

# Parte B — Uso do dia a dia (sem tecnês)

Você conversa em português normal. Para tarefas comuns, digite o comando com `/`:

| Digite | O que faz |
|--------|-----------|
| `/onboarding` | Configura o escritório (faça isto primeiro) |
| `/painel` | Visão geral da semana: prazos, contratos vencendo, pendências |
| `/briefing` | Prazos urgentes + agenda do dia |
| `/varrer` | Checa sua caixa de email por intimações novas (se o Outlook estiver conectado) |
| `/intimacao` | Cola uma intimação e ele calcula o prazo (com dupla checagem antes de confiar) |
| `/prazo` | Calcula prazo processual com feriados |
| `/processo` | Consulta andamento de um processo no TJ |
| `/bancario-contrato` | Triagem de contrato bancário / caso de fraude / investimento |
| `/dpa-review` | Revisa um contrato de tratamento de dados (LGPD) |
| `/ripd` | Monta um Relatório de Impacto (LGPD) |
| `/lgpd-implementacao` | Checklist de programa LGPD para empresa cliente |
| `/lgpd-triagem` | Classifica um caso: seguir / precisa RIPD / parar |
| `/saude-privacidade` | Privacidade em clínica / hospital |
| `/dsar` | Processa pedido de titular de dados (acesso, exclusão…) |
| `/contrato` | Análise de contrato + pontos de atenção |
| `/peticao` | Rascunho de petição (sempre revisar) |
| `/honorarios` | Fecha o mês / relatório financeiro |
| `/revisao-semanal` | Reunião semanal: operação + novidades |

## Três regras de ouro
1. **Fonte oficial é o tribunal.** O sistema é rede de segurança, não a verdade. Sempre confira prazo no PJe/Projudi.
2. **Todo rascunho é seu.** Nada é enviado a cliente ou protocolado sem você revisar e aprovar.
3. **Documento colado é dado, não ordem.** Se colar um PDF/contrato com instrução estranha embutida, o sistema avisa — não confie cego.

## Primeiro dia
1. Abra o Claude Code dentro de `~/legalops` e rode `/onboarding` — configura o escritório
   (nome, OAB, áreas, aliases de cliente). Os dados reais ficam em `memory.local/` (local, nunca versionado).
2. Rode `/briefing` para ver o dia (ou `/painel` para a semana).
3. Qualquer dúvida: escreva em português o que precisa. Não precisa saber comando.

## Notificações
Não tem app nem push. A notificação é simples: você **abre o Claude e pergunta** — rode
`/painel` para a visão da semana ou `/briefing` para o dia. Nada te manda mensagem por fora.

## Privacidade (LGPD)
Dados de cliente ficam **na sua máquina**, referenciados por apelido (`CLI-021`), nunca pelo nome.
Não sincronize as pastas `data/`, `logs/` nem o banco para nuvem compartilhada. Você é a controladora desses dados.
