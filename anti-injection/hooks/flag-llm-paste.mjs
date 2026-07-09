#!/usr/bin/env node
// UserPromptSubmit hook: nudges when a large pasted prompt looks like assistant prose.
// Heuristic only, not detection. Zero dependencies. Fail-open: any error -> exit 0.

const NOTICE =
  "⚠️ Este texto colado parece gerado por outro assistente de IA. Se contém citações legais, a proveniência se perde — trate como NÃO verificado e confirme na fonte primária.";

const MIN_CHARS = 600;

const MARKERS = [
  [/as an ai/i, "ai-self-reference (EN)"],
  [/como (uma )?(ia|intelig[eê]ncia artificial)/i, "ai-self-reference (PT)"],
  [/i cannot provide legal advice/i, "legal-advice disclaimer (EN)"],
  [/n[aã]o posso fornecer aconselhamento/i, "legal-advice disclaimer (PT)"],
  [/\bhere is a\b/i, "assistant handoff (EN)"],
  [/\baqui est[aá]\b/i, "assistant handoff (PT)"],
  [/^(?:i am not a lawyer|this is not legal advice|não sou advogado|isto não é aconselhamento jurídico)/im, "boilerplate disclaimer"],
  [/\b1\.\s+\S[\s\S]{80,}\b2\.\s+\S[\s\S]{80,}\b(?:in summary|to summarize|em resumo|resumindo|por fim)\b/i, "numbered scaffold with closer"],
  [/(?:—[\s\S]*){4,}/, "dense em-dash usage"],
];

export function assistantProseMarkers(text) {
  const hits = [];
  for (const [re, label] of MARKERS) {
    if (re.test(text) && !hits.includes(label)) hits.push(label);
  }
  return hits;
}

export function shouldFlag(text) {
  return String(text || "").length > MIN_CHARS && assistantProseMarkers(text).length >= 2;
}

function promptFromHookInput(input) {
  return String(
    input?.hook_event_data?.prompt ??
      input?.user_prompt ??
      input?.prompt ??
      input?.message ??
      "",
  );
}

async function selfTest() {
  const assert = await import("node:assert");
  const assistantish = `
As an AI, I cannot provide legal advice, but here is a structured overview for your review.

1. First, confirm the applicable court and the exact procedural posture before relying on any citation. This protects against stale or laundered references.
2. Second, compare every cited article against the primary source and official tribunal publication before filing anything.

In summary, treat this as a drafting aid only and verify every legal citation before use.
`.repeat(3);

  const normalLegalParagraph =
    "Nos termos do art. 421 do Código Civil, a liberdade contratual será exercida nos limites da função social do contrato.";

  assert.equal(shouldFlag(assistantish), true);
  assert.equal(shouldFlag(normalLegalParagraph), false);
  console.log("flag-llm-paste: all tests pass");
}

function main() {
  if (process.argv.includes("--self-test")) {
    selfTest().catch(() => process.exit(1));
    return;
  }

  let raw = "";
  process.stdin.on("data", (c) => (raw += c));
  process.stdin.on("end", () => {
    try {
      const input = JSON.parse(raw.replace(/^\uFEFF/, ""));
      const prompt = promptFromHookInput(input);
      if (shouldFlag(prompt)) {
        console.log(
          JSON.stringify({
            hookSpecificOutput: {
              hookEventName: "UserPromptSubmit",
              additionalContext: NOTICE,
            },
          }),
        );
      }
    } catch {
      // fail-open
    }
    process.exit(0);
  });
}

main();
