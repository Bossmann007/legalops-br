# Aviso, Riscos e Limitação de Responsabilidade

**Leia antes de usar.** Este documento descreve o que o **LegalOps BR** é, o que **não** é, os riscos de cada componente, e de quem é a responsabilidade por cada um. Ao instalar, configurar ou usar qualquer parte deste projeto — engine, skills, hooks, agents ou dashboard — você declara ter lido e aceito integralmente os termos abaixo.

---

## 1. Natureza do software

LegalOps BR é um conjunto de ferramentas de **apoio a fluxo de trabalho jurídico** ("O Sócio Invisível") que roda sobre o Claude Code / Claude API. Ele **não é**, e não pretende ser:

- um escritório de advocacia, nem advogado(a);
- uma fonte oficial de prazos, publicações ou andamentos processuais;
- um substituto do controle de prazos, do sistema oficial do tribunal (PJe, e-SAJ, Projudi, Domicílio Judicial Eletrônico) ou do julgamento de um(a) advogado(a) inscrito(a) na OAB;
- um serviço com garantia de disponibilidade, exatidão, atualidade ou adequação a qualquer finalidade.

**Toda saída é rascunho (`DRAFT`) para revisão de advogado(a) habilitado(a) antes de embasar qualquer decisão, petição, prazo ou aconselhamento.** A responsabilidade final por qualquer ato jurídico é, sempre e exclusivamente, do(a) profissional que o pratica.

---

## 2. Fornecido "COMO ESTÁ" — sem garantia

O software é fornecido **"como está" e "conforme disponível"**, sem garantia de qualquer natureza, expressa ou implícita, incluindo — sem limitação — garantias de comerciabilidade, adequação a um fim específico, exatidão jurídica, atualidade da legislação, ou não violação.

O(s) autor(es) e contribuidor(es) **não garantem** que:

- as citações legais, súmulas, artigos, prazos ou cálculos (inclusive de prazo CPC) estejam corretos ou vigentes;
- os parsers de tribunal (TJPR/TJSP/TJMG/TJSC/TJRJ/TJDFT) retornem dados completos, atuais ou livres de erro;
- o software esteja livre de defeitos, interrupções ou falhas de segurança.

---

## 3. Limitação de responsabilidade

Na máxima extensão permitida pela lei aplicável, **o(s) autor(es) e contribuidor(es) não serão responsáveis** por qualquer dano — direto, indireto, incidental, especial, consequencial, moral, ou lucros cessantes — decorrente de ou relacionado ao uso, à impossibilidade de uso, ou aos resultados do software, incluindo, sem limitação:

- **perda de prazo** processual ou material;
- **citação legal incorreta, desatualizada ou fabricada** utilizada em peça, parecer ou decisão;
- **cálculo de prazo CPC incorreto** (feriado municipal ausente, suspensão forense não registrada, contagem em dobro);
- **vazamento, exposição ou tratamento indevido de dados pessoais** de clientes ou terceiros;
- **decisão profissional** tomada com base em qualquer saída do software;
- **indisponibilidade, lentidão, bloqueio ou erro** de qualquer serviço de terceiros (portais dos tribunais, Evolution API/WhatsApp, ou outros).

O uso é feito **por conta e risco exclusivo do(a) usuário(a)**. A responsabilidade por verificar, validar e assumir qualquer saída é integralmente do(a) advogado(a) ou profissional que a utiliza.

---

## 4. Responsabilidades do(a) usuário(a)

Ao usar este software, você assume a responsabilidade por:

- **Verificar toda citação legal e todo prazo** contra a fonte primária (Planalto, DJe do tribunal, PJe/Projudi) antes de confiar. Uma saída do software descreve **o que o modelo produziu**, **não** que está correta.
- **Manter o controle oficial de prazos** no sistema do tribunal. Este software é rede de segurança adicional, **nunca** a fonte da verdade.
- **Proteger os dados pessoais** que trafegam ou ficam armazenados na sua máquina (ver §5.3), em conformidade com a LGPD (Lei 13.709/2018) — você é o **controlador** desses dados.
- **Confirmar a base legal** e o segredo de justiça antes de colar ou processar qualquer dado sensível ou sigiloso.
- **Manter chaves e credenciais** próprias seguras e fora de versionamento (`LEGALOPS_PII_SALT`, tokens da Evolution API, etc.).

---

## 5. Riscos por componente

Ranqueados por dano potencial real.

### 5.1 🔴 Parsers de tribunal — falso-negativo → prazo perdido

Os parsers (`tjpr_parser`, `tjsp_parser`, etc.) consultam portais públicos dos tribunais. **A publicação atrasa e o scraping pode falhar** (mudança de layout, indisponibilidade, captcha). Se uma intimação ou movimentação ainda não foi publicada ou não foi capturada, o `/briefing` pode exibir "nada novo" — sem que isso signifique que nada ocorreu.

> **Ausência de resultado não é prova de ausência de prazo.** Missar uma intimação por confiar apenas neste software pode configurar perda de prazo. O controle oficial (PJe / Domicílio Judicial Eletrônico) é a única fonte da verdade. A responsabilidade por essa verificação é integralmente do(a) usuário(a).

### 5.2 🟠 Segredo de justiça — filtro não é parede

Processos em segredo de justiça geralmente **não aparecem** em portais públicos; não confunda a ausência deles com inexistência. Não há garantia de que nenhum dado sigiloso jamais seja retornado por falha do portal de origem. Ao processar qualquer conteúdo sigiloso, o guardrail `oab_sigilo` é uma proteção adicional — **não uma garantia**.

### 5.3 🟠 LGPD — dados pessoais na sua máquina

O software processa **nomes, CPF, número de OAB e texto de intimações/contratos** — dado pessoal, por vezes sensível (LGPD art. 5, II). O `pii_redactor` redige PII antes de logar e clientes são referenciados por alias (`CLI-021`), mas:

- **não sincronize** bancos locais, logs ou `data/clientes-aliases.json` para nuvem compartilhada nem os versione (já estão no `.gitignore`);
- você é o **controlador** desses dados e responde por seu tratamento;
- para dev/teste, use dados anonimizados (`faker` + CPF sintético) — **nunca** dados reais de processo.

### 5.4 🟡 WhatsApp / Evolution API

O `whatsapp_notifier` envia briefings e alertas via Evolution API. Entrega **não é garantida** (número inválido, instância caída, bloqueio do WhatsApp). Não assuma que um alerta enviado foi lido. Mensagens a clientes passam por revisão manual antes do envio (preferência da usuária) — mantenha esse gate.

### 5.5 🟡 Dado é metadado, não mérito

Um movimento processual é metadado; **não conclua procedência, resultado ou estratégia** a partir dele. A análise de contrato aponta red flags como **hipóteses para revisão**, não como parecer.

### 5.6 🟡 Conteúdo de terceiros / prompt-injection

O texto de intimações, movimentos e contratos é escrito por terceiros (inclusive a parte adversária). Documentos colados podem conter instruções maliciosas embutidas. O plugin `anti-injection` trata esse texto como **dado, não instrução** e sinaliza padrões suspeitos. Essa é uma **camada de detecção**, não uma parede — não confie cegamente em nenhum texto colado ou capturado.

### 5.7 🟡 Exatidão e vigência das citações

As bases legais evoluem. Uma citação correta na data de escrita pode estar revogada, modulada ou superada por jurisprudência depois. O software **não versiona a legislação**. **Confirme a vigência antes de protocolar.**

---

## 6. Serviços de terceiros

O software acessa portais públicos dos tribunais e a Evolution API (WhatsApp). O(s) autor(es) deste projeto **não controlam, não operam e não respondem** por esses serviços — sua disponibilidade, exatidão, termos de uso, políticas de dados ou mudanças. O uso sujeita-se aos termos dos respectivos provedores, cuja observância é responsabilidade do(a) usuário(a).

---

## 7. Sem relação advogado-cliente

O uso deste software **não estabelece** qualquer relação advogado-cliente entre o(a) usuário(a) e o(s) autor(es), nem entre o(a) usuário(a) e a Anthropic. O(s) autor(es) não prestam serviço jurídico.

---

## 8. Aceitação

Se você não concorda com qualquer termo acima, **não use** este software. O uso continuado constitui aceitação integral destes termos e a assunção de todos os riscos aqui descritos.

---

*Este documento é um aviso de risco e limitação de responsabilidade do software, não um parecer jurídico. Última revisão: 2026-07-09.*
