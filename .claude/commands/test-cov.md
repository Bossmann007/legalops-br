---
description: "Roda testes com cobertura e aponta gaps críticos"
---

Execute e analise cobertura:

```bash
cd /home/bossmann/Projects/legalops-br && uv run pytest --cov=src --cov-report=term-missing -q
```

Após resultado:
1. Cobertura geral ≥ 95%? → OK ou ATENÇÃO
2. Listar módulos abaixo de 95%
3. Para cada módulo abaixo: identificar as linhas não cobertas e sugerir teste
4. Priorizar: código de prazo e PII redaction são críticos (exigem 95%+)
