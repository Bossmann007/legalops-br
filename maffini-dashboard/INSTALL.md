# Guia de Instalação — Maffini Dashboard

Centro de comando da Maffini & Rangel. Roda no seu computador e abre no navegador.

---

## O que você vai precisar

- **Node.js 20 ou superior** — baixe em [nodejs.org](https://nodejs.org) (botão "LTS")
- **Python 3.10+** com o LegalOps instalado (já feito pelo Enzo)
- Acesso ao terminal (Prompt de Comando / PowerShell no Windows, Terminal no Mac/Linux)

Para checar se já tem o Node instalado, abra o terminal e digite:

```
node --version
```

Se aparecer algo como `v20.x.x` ou maior, está pronto.

---

## Instalação passo a passo

### 1. Baixar os arquivos

```bash
git clone https://github.com/bossmann007/legalops-br.git
cd legalops-br/maffini-dashboard
```

> Se o Enzo já te mandou a pasta, pule este passo e entre direto na pasta `maffini-dashboard`.

### 2. Instalar as dependências

Dentro da pasta `maffini-dashboard`, execute:

```bash
npm install
```

### 3. Configurar o arquivo `.env`

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Abra o arquivo `.env` em qualquer editor de texto e preencha **apenas** estas linhas obrigatórias:

```
LEGALOPS_PII_SALT=  ← gere um valor secreto (veja abaixo)
LEGALOPS_BIN=       ← caminho do legalops (o Enzo vai te passar)
```

**Para gerar o `LEGALOPS_PII_SALT`** (chave secreta de proteção de dados — Art. 13 LGPD):

```bash
node -e "const c=require('crypto');console.log(c.randomBytes(24).toString('hex'))"
```

Copie o resultado e cole depois do `=` na linha `LEGALOPS_PII_SALT=`.

> **Guarde esse valor com segurança.** Ele protege os dados do escritório. Se perder, precisará regerar e reprocessar documentos anteriores.

### 4. Iniciar o dashboard

```bash
npm start
```

Você verá no terminal:

```
Maffini Dashboard listening on http://127.0.0.1:4318
auth: disabled (loopback-only)
```

Abra o navegador e acesse: **http://localhost:4318**

---

## Como usar o dashboard

### Tela inicial (Home)
Visão geral do escritório: prazos próximos, DSARs pendentes e saúde do sistema.

### Prazos
- **Novo prazo**: clique em "Adicionar", preencha processo, descrição e data
- **Editar/remover**: clique no prazo da lista e use os botões da linha
- Prazos com vencimento nos próximos 7 dias aparecem em destaque

### Intimações
- Cole o texto da intimação no campo de entrada
- Clique **Processar** — o sistema redige dados pessoais, extrai prazo, calcula dias úteis e registra no audit
- Resultado: texto redigido · prazo calculado · hash de integridade

### Contratos
- Cole ou faça upload do texto do contrato
- Clique **Analisar risco** — retorna cláusulas de risco com nível (alto / médio / baixo)
- Requer `ANTHROPIC_API_KEY` no `.env` para usar o Claude for Legal

### DSAR — Pedidos LGPD (Art. 18/19)
- Registre pedidos de acesso/exclusão de dados de titulares
- Acompanhe status (pendente / em análise / respondido)
- Prazo legal de 15 dias é calculado automaticamente

### Clientes
- Mini cadastro de aliases para clientes
- Útil para referenciar processos sem expor nome completo nos logs

### Auditoria
- Histórico de todas as operações com hash chain de integridade
- **Verificar integridade**: checa se algum registro foi adulterado

### Configurações
- Informações do ambiente e versão do LegalOps conectado

---

## Segurança — o que você precisa saber

- O dashboard **só abre no seu computador** (endereço `127.0.0.1`). Ninguém externo acessa.
- Todo comando pede **confirmação explícita** — o botão "Autorizo" deve ser clicado antes de qualquer ação rodar no sistema.
- Dados pessoais são **pseudonimizados** antes de qualquer envio externo (apenas quando Claude for Legal está ativo).

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| Não abre no navegador | Verifique se o terminal ainda está rodando `npm start` |
| "LEGALOPS_BIN not found" | O caminho do LegalOps no `.env` está errado — peça ao Enzo |
| "LEGALOPS_PII_SALT is required" | `.env` não foi configurado — volte ao passo 3 |
| "Port 4318 already in use" | Outra instância rodando; feche o outro terminal ou mude `MAFFINI_PORT` no `.env` |
| Dados somem após reiniciar | Os dados ficam em `data/store.json` — faça backup dessa pasta |

---

## Instalação permanente no Linux (systemd)

Para que o dashboard inicie automaticamente com o sistema:

```bash
sudo bash deploy/setup.sh
```

O script pergunta o caminho de instalação (padrão: `/opt/maffini-dashboard`) e configura tudo.

Após instalar:

```bash
systemctl status maffini-dashboard    # verificar status
sudo systemctl stop maffini-dashboard  # parar
sudo systemctl start maffini-dashboard # iniciar
journalctl -u maffini-dashboard -f    # ver logs em tempo real
```

---

## Atualizar para nova versão

```bash
git pull
npm install
npm run build
sudo systemctl restart maffini-dashboard   # se rodando via systemd
```

---

## Suporte

Qualquer dúvida: **Enzo Bossmann** — enzombromanus@gmail.com
