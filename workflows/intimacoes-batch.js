export const meta = {
  name: 'intimacoes-batch',
  description: 'Processa um lote de intimações coladas pelo mesmo pipeline determinístico do /intimacao (dual-extract + oracle + cálculo fail-closed).',
  phases: [
    { title: 'Extract', detail: 'dual-model por intimação' },
    { title: 'Validar', detail: 'oracle determinístico' },
  ],
}

// args = lista de textos JÁ REDIGIDOS (uma intimação por item). Redação acontece
// antes do workflow — nenhum texto cru entra aqui. ponytail: cap fixo de 20/rodada
// para não estourar a quota de 5h; lotes maiores viram fila manual.
const MAX_POR_RODADA = 20
const itens = (Array.isArray(args) ? args : []).slice(0, MAX_POR_RODADA)
if (Array.isArray(args) && args.length > MAX_POR_RODADA) {
  log(`Lote tem ${args.length}; processando os primeiros ${MAX_POR_RODADA}. Cole o resto numa segunda rodada.`)
}

const EXTRACT_SCHEMA = {
  type: 'object',
  required: ['data_publicacao', 'prazo_dias', 'parte', 'tribunal', 'via_dje', 'cnj', 'confianca'],
  properties: {
    data_publicacao: { type: ['string', 'null'] },
    tipo_ato: { type: ['string', 'null'] },
    prazo_dias: { type: ['integer', 'null'] },
    parte: { type: ['string', 'null'] },
    tribunal: { type: ['string', 'null'] },
    via_dje: { type: 'boolean' },
    cnj: { type: ['string', 'null'] },
    confianca: { type: 'number' },
  },
}

const resultados = await pipeline(
  itens,
  // Stage 1: dual-extract (dois modelos diferentes, em paralelo por item)
  async (texto, _orig, i) => {
    const [a, b] = await parallel([
      () => agent(`Extraia os campos desta intimação redigida:\n\n${texto}`,
        { label: `extract-a:${i}`, phase: 'Extract', model: 'haiku', schema: EXTRACT_SCHEMA }),
      () => agent(`Segundo revisor independente — extraia os campos desta intimação redigida do zero:\n\n${texto}`,
        { label: `extract-b:${i}`, phase: 'Extract', model: 'sonnet', schema: EXTRACT_SCHEMA }),
    ])
    return { i, a, b }
  },
  // Stage 2: oracle determinístico via CLI (0 tokens). O agente aqui só é um
  // wrapper fino que escreve os JSON e roda `validar-extracao`, retornando o veredito.
  async ({ i, a, b }) => {
    if (!a || !b) return { i, status: 'revisao_manual_obrigatoria', reasons: ['extração falhou (modelo não respondeu)'] }
    const veredito = await agent(
      `Escreva estes dois JSON em data/tmp/batch-a-${i}.json e data/tmp/batch-b-${i}.json e rode:\n` +
      `uv run legalops validar-extracao --file-a data/tmp/batch-a-${i}.json --file-b data/tmp/batch-b-${i}.json\n` +
      `Retorne o JSON do veredito exatamente como o comando imprimiu.\n\n` +
      `A=${JSON.stringify(a)}\nB=${JSON.stringify(b)}`,
      { label: `oracle:${i}`, phase: 'Validar', model: 'haiku',
        schema: { type: 'object', required: ['status'], properties: {
          status: { type: 'string' }, reasons: { type: 'array' }, campos: { type: 'object' } } } },
    )
    return { i, ...(veredito || { status: 'revisao_manual_obrigatoria', reasons: ['oracle não retornou'] }) }
  },
)

const ok = resultados.filter(Boolean).filter(r => r.status === 'ok')
const revisao = resultados.filter(Boolean).filter(r => r.status !== 'ok')
log(`Lote: ${ok.length} prontos p/ cálculo · ${revisao.length} → revisão manual`)
return { total: itens.length, ok, revisao }
