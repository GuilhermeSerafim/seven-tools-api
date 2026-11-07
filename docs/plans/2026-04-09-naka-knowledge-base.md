# Naka Knowledge Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-ready Markdown knowledge base for Dennis Nakamura in `knowledge/naka`, extracted and consolidated from the PDFs in `../docs/naka`.

**Architecture:** Create nine numbered Markdown files under `knowledge/naka`, each one responsible for a single conceptual slice of the corpus. Favor dense, curated prose with explicit hierarchy between core method and peripheral material, so the current linear loader can concatenate the files without overwhelming the model with duplication or slide noise.

**Tech Stack:** Markdown, PowerShell, Python 3.12 verification snippets, existing FastAPI repo structure.

**Spec:** `docs/specs/2026-04-09-naka-knowledge-base-design.md`

---

## File Structure

```
seven_tools_api/
├── docs/
│   ├── specs/
│   │   └── 2026-04-09-naka-knowledge-base-design.md   # Approved design/spec
│   └── plans/
│       └── 2026-04-09-naka-knowledge-base.md          # This implementation plan
└── knowledge/
    └── naka/
        ├── 00_escopo_e_prioridades.md                 # Corpus role, weighting, usage rules
        ├── 01_persona_e_voz.md                        # Voice, posture, authority, decision style
        ├── 02_crescimento_e_escala.md                 # Growth logic, pillars, stages, scale
        ├── 03_maquina_de_vendas_infinitas.md          # ICP, offer packaging, sales machine
        ├── 04_funis_e_geracao_de_demanda.md           # Funnels, channels, lead generation
        ├── 05_oferta_negociacao_e_decisao.md          # Dream vs pain, value, negotiation
        ├── 06_gestao_financeira_e_planejamento.md     # DRE, indicators, ROI, planning
        ├── 07_lideranca_cultura_e_governanca.md       # Leadership, culture, governance, succession
        └── 08_anexos_e_contextos_especificos.md       # Holdings, CRM proposal, peripheral contexts
```

### Source Mapping

- `00_escopo_e_prioridades.md`: curation across the full corpus, guided by the approved spec
- `01_persona_e_voz.md`: PDFs `14`, `16`, `23`
- `02_crescimento_e_escala.md`: PDFs `11`, `24`, `26`, `27`
- `03_maquina_de_vendas_infinitas.md`: PDFs `9`, `12`, `17`, `26` with support from `24`, `27`
- `04_funis_e_geracao_de_demanda.md`: PDFs `7`, `12`, `21`, `22`
- `05_oferta_negociacao_e_decisao.md`: PDFs `6`, `8`, with support from `9`, `17`
- `06_gestao_financeira_e_planejamento.md`: PDFs `24`, `25`, with support from `26`
- `07_lideranca_cultura_e_governanca.md`: PDFs `18`, `26`, `27`
- `08_anexos_e_contextos_especificos.md`: PDFs `13`, `15`, `19`/`20` (deduplicated)

---

## Task 1: Scaffold `knowledge/naka` and write the corpus control files

**Files:**
- Create: `knowledge/naka/00_escopo_e_prioridades.md`
- Create: `knowledge/naka/01_persona_e_voz.md`

- [ ] **Step 1: Ensure the target directory exists**

Run:

```powershell
New-Item -ItemType Directory -Force -Path 'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka'
```

Expected: directory exists and no error is raised.

- [ ] **Step 2: Create `00_escopo_e_prioridades.md` with the agreed control structure**

Write:

```md
# Escopo e Prioridades

## Papel no corpus
- Explicar que a base existe para alimentar IA, nao para arquivar PDFs.
- Dizer que o objetivo e maximizar densidade util e reduzir ruido.

## Hierarquia de peso
- Nucleo principal: vendas, funis, crescimento, escala, financas, planejamento, lideranca, governanca, voz.
- Contextos complementares: holdings, patrimonial, proposta de CRM.

## Regras de leitura para a IA
- Privilegiar o metodo principal antes dos anexos.
- Nao tratar materiais complementares como centro do pensamento do Naka.
- Usar a voz e os criterios do autor em conjunto com o metodo.

## Notas de curadoria
- PDFs 19 e 20 sao duplicados.
- PDFs 21 e 22 devem ser tratados como variantes do mesmo material.
- PDF 12 e estrutural, nao textual.
```

- [ ] **Step 3: Populate `00_escopo_e_prioridades.md` with final prose**

Use the approved spec plus the full PDF reading notes to turn the scaffold into dense prose. Make sure the file explicitly states:

- why this corpus is organized thematically instead of one-file-per-PDF;
- which topics should dominate generic answers;
- why annexes exist but carry less interpretive weight.

- [ ] **Step 4: Create `01_persona_e_voz.md` with the required sections**

Write:

```md
# Persona e Voz

## Identidade intelectual
## Como o Naka pensa
## Como o Naka orienta
## Como o Naka corrige e decide
## Linguagem, tom e postura
## Sinais de autoridade e repertorio
## Limites do estilo
```

- [ ] **Step 5: Populate `01_persona_e_voz.md` from PDFs 14, 16, and 23**

The final file must capture:

- directness, clarity, and strategic posture;
- diagnostic style over motivational rhetoric;
- business authority, execution background, and public credibility;
- what he avoids in language and reasoning.

- [ ] **Step 6: Verify the two files exist and contain the required headings**

Run:

```powershell
@'
from pathlib import Path

checks = {
    Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka\00_escopo_e_prioridades.md'): [
        '## Papel no corpus',
        '## Hierarquia de peso',
        '## Regras de leitura para a IA',
    ],
    Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka\01_persona_e_voz.md'): [
        '## Identidade intelectual',
        '## Como o Naka pensa',
        '## Linguagem, tom e postura',
    ],
}

for path, headings in checks.items():
    text = path.read_text(encoding='utf-8')
    assert text.startswith('# '), path
    for heading in headings:
        assert heading in text, (path, heading)

print('task-1-ok')
'@ | python -
```

Expected: `task-1-ok`

- [ ] **Step 7: Commit**

```powershell
git add knowledge/naka/00_escopo_e_prioridades.md knowledge/naka/01_persona_e_voz.md
git commit -m "docs(naka): add scope and voice files"
```

---

## Task 2: Write the growth and sales-machine core

**Files:**
- Create: `knowledge/naka/02_crescimento_e_escala.md`
- Create: `knowledge/naka/03_maquina_de_vendas_infinitas.md`

- [ ] **Step 1: Create the outline for `02_crescimento_e_escala.md`**

Write:

```md
# Crescimento e Escala

## Principios centrais de crescimento
## Tres formas de crescer
## Cinco pilares da escala
## Estagios de maturidade da empresa
## Crescimento com previsibilidade
## Erros de empresas que confundem movimento com progresso
```

- [ ] **Step 2: Populate `02_crescimento_e_escala.md` from PDFs 11, 24, 26, and 27**

The final file must preserve:

- the three growth levers;
- the five strategic pillars;
- the link between sales, management, culture, governance, and ecosystem;
- scale as an organizational upgrade, not just revenue growth.

- [ ] **Step 3: Create the outline for `03_maquina_de_vendas_infinitas.md`**

Write:

```md
# Maquina de Vendas Infinitas

## Papel da maquina comercial
## ICP e escolha de publico
## Produto perfeito e embalagem da oferta
## Apresentacao de vendas
## Estrutura minima da operacao comercial
## Papeis da equipe e fases de maturidade
## CRM, inteligencia comercial e acompanhamento
## Customer success como extensao da receita
```

- [ ] **Step 4: Populate `03_maquina_de_vendas_infinitas.md` from PDFs 9, 12, 17, and 26**

The final file must capture:

- ICP as the first strategic filter;
- the idea of packaging the same offer for different profiles;
- the minimum viable sales operation;
- role clarity across SDR, closer, CS, and management;
- CRM and commercial intelligence as control layers, not admin overhead.

- [ ] **Step 5: Verify both files**

Run:

```powershell
@'
from pathlib import Path

checks = {
    Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka\02_crescimento_e_escala.md'): [
        '## Tres formas de crescer',
        '## Cinco pilares da escala',
        '## Estagios de maturidade da empresa',
    ],
    Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka\03_maquina_de_vendas_infinitas.md'): [
        '## ICP e escolha de publico',
        '## Produto perfeito e embalagem da oferta',
        '## Estrutura minima da operacao comercial',
    ],
}

for path, headings in checks.items():
    text = path.read_text(encoding='utf-8')
    for heading in headings:
        assert heading in text, (path, heading)
    assert len(text.split()) >= 500, path

print('task-2-ok')
'@ | python -
```

Expected: `task-2-ok`

- [ ] **Step 6: Commit**

```powershell
git add knowledge/naka/02_crescimento_e_escala.md knowledge/naka/03_maquina_de_vendas_infinitas.md
git commit -m "docs(naka): add growth and sales machine core"
```

---

## Task 3: Write demand generation and decision-making files

**Files:**
- Create: `knowledge/naka/04_funis_e_geracao_de_demanda.md`
- Create: `knowledge/naka/05_oferta_negociacao_e_decisao.md`

- [ ] **Step 1: Create `04_funis_e_geracao_de_demanda.md`**

Write:

```md
# Funis e Geracao de Demanda

## Papel dos funis na maquina de crescimento
## Principios de geracao continua de leads
## Funis e canais prioritarios
## Prospeccao ativa e passiva
## Como escolher os primeiros funis
## Como combinar funis sem dispersao
## Erros comuns de quem tenta gerar demanda
```

- [ ] **Step 2: Populate `04_funis_e_geracao_de_demanda.md` from PDFs 7, 12, 21, and 22**

The final file must preserve:

- lead generation as a system, not a magic channel;
- the idea that 3 or 4 active funnels can sustain the machine;
- selection criteria for first funnels;
- overlap between owned audience, outbound, partnerships, events, and social channels.

- [ ] **Step 3: Create `05_oferta_negociacao_e_decisao.md`**

Write:

```md
# Oferta, Negociacao e Decisao

## Sonho versus dor
## Como a dor acelera decisao
## Construcao de valor
## Negociacao sem guerra de preco
## Diferenciacao quando o mercado parece igual
## Elementos de uma proposta forte
## Erros de abordagem e de argumentacao
```

- [ ] **Step 4: Populate `05_oferta_negociacao_e_decisao.md` from PDFs 6 and 8**

The final file must preserve:

- how dream and pain shape messaging;
- why pain tends to mobilize action faster;
- how value construction changes negotiation;
- why undifferentiated offers get pushed into discounting.

- [ ] **Step 5: Verify both files**

Run:

```powershell
@'
from pathlib import Path

checks = {
    Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka\04_funis_e_geracao_de_demanda.md'): [
        '## Principios de geracao continua de leads',
        '## Funis e canais prioritarios',
        '## Como escolher os primeiros funis',
    ],
    Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka\05_oferta_negociacao_e_decisao.md'): [
        '## Sonho versus dor',
        '## Construcao de valor',
        '## Negociacao sem guerra de preco',
    ],
}

for path, headings in checks.items():
    text = path.read_text(encoding='utf-8')
    for heading in headings:
        assert heading in text, (path, heading)
    assert len(text.split()) >= 350, path

print('task-3-ok')
'@ | python -
```

Expected: `task-3-ok`

- [ ] **Step 6: Commit**

```powershell
git add knowledge/naka/04_funis_e_geracao_de_demanda.md knowledge/naka/05_oferta_negociacao_e_decisao.md
git commit -m "docs(naka): add demand generation and decision files"
```

---

## Task 4: Write finance, planning, leadership, and governance files

**Files:**
- Create: `knowledge/naka/06_gestao_financeira_e_planejamento.md`
- Create: `knowledge/naka/07_lideranca_cultura_e_governanca.md`

- [ ] **Step 1: Create `06_gestao_financeira_e_planejamento.md`**

Write:

```md
# Gestao Financeira e Planejamento

## Papel da gestao financeira no crescimento
## DRE e leitura da realidade
## Indicadores financeiros e tomada de decisao
## ROI, lucratividade e previsibilidade
## Planejamento estrategico como instrumento de direcao
## Ligacao entre financas, marketing, vendas e operacao
```

- [ ] **Step 2: Populate `06_gestao_financeira_e_planejamento.md` from PDFs 24, 25, and 26**

The final file must preserve:

- DRE as a management tool, not just an accounting report;
- financial reading tied to decision quality;
- ROI and profitability as operating questions;
- planning as a live management discipline.

- [ ] **Step 3: Create `07_lideranca_cultura_e_governanca.md`**

Write:

```md
# Lideranca, Cultura e Governanca

## Lideranca como formacao de pessoas
## Cultura e valores que sustentam a escala
## Governanca e clareza de papeis
## Sucessao e formacao de lideres
## Maturidade organizacional
## Crescimento sem caos
```

- [ ] **Step 4: Populate `07_lideranca_cultura_e_governanca.md` from PDFs 18, 26, and 27**

The final file must preserve:

- servant-style leadership lessons only where they strengthen the business lens;
- culture and values as execution infrastructure;
- governance as a scale requirement;
- leader formation and succession as bottleneck removal.

- [ ] **Step 5: Verify both files**

Run:

```powershell
@'
from pathlib import Path

checks = {
    Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka\06_gestao_financeira_e_planejamento.md'): [
        '## DRE e leitura da realidade',
        '## ROI, lucratividade e previsibilidade',
        '## Planejamento estrategico como instrumento de direcao',
    ],
    Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka\07_lideranca_cultura_e_governanca.md'): [
        '## Cultura e valores que sustentam a escala',
        '## Governanca e clareza de papeis',
        '## Sucessao e formacao de lideres',
    ],
}

for path, headings in checks.items():
    text = path.read_text(encoding='utf-8')
    for heading in headings:
        assert heading in text, (path, heading)
    assert len(text.split()) >= 300, path

print('task-4-ok')
'@ | python -
```

Expected: `task-4-ok`

- [ ] **Step 6: Commit**

```powershell
git add knowledge/naka/06_gestao_financeira_e_planejamento.md knowledge/naka/07_lideranca_cultura_e_governanca.md
git commit -m "docs(naka): add finance and governance files"
```

---

## Task 5: Add annexes and run final corpus review

**Files:**
- Create: `knowledge/naka/08_anexos_e_contextos_especificos.md`
- Modify: `knowledge/naka/00_escopo_e_prioridades.md`
- Modify: `knowledge/naka/01_persona_e_voz.md`
- Modify: `knowledge/naka/02_crescimento_e_escala.md`
- Modify: `knowledge/naka/03_maquina_de_vendas_infinitas.md`
- Modify: `knowledge/naka/04_funis_e_geracao_de_demanda.md`
- Modify: `knowledge/naka/05_oferta_negociacao_e_decisao.md`
- Modify: `knowledge/naka/06_gestao_financeira_e_planejamento.md`
- Modify: `knowledge/naka/07_lideranca_cultura_e_governanca.md`

- [ ] **Step 1: Create `08_anexos_e_contextos_especificos.md`**

Write:

```md
# Anexos e Contextos Especificos

## Papel dos anexos no corpus
## Holdings e planejamento patrimonial
## Proposta de CRM como contexto operacional
## Como usar esses materiais sem distorcer o metodo principal
```

- [ ] **Step 2: Populate `08_anexos_e_contextos_especificos.md` from PDFs 13, 15, and 19/20**

The final file must:

- retain useful knowledge from holdings and patrimonial planning;
- retain the operational/commercial logic from the CRM proposal;
- state explicitly that this file has lower weight than the core corpus.

- [ ] **Step 3: Run an overlap review across all nine files**

Read all files and trim obvious duplication. Keep a concept in multiple files only when:

- it is necessary to understand that file on its own; or
- the concept appears with a different angle that matters for the model.

- [ ] **Step 4: Run final verification for file list, ordering, headings, and minimum size**

Run:

```powershell
@'
from pathlib import Path

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka')
expected = [
    '00_escopo_e_prioridades.md',
    '01_persona_e_voz.md',
    '02_crescimento_e_escala.md',
    '03_maquina_de_vendas_infinitas.md',
    '04_funis_e_geracao_de_demanda.md',
    '05_oferta_negociacao_e_decisao.md',
    '06_gestao_financeira_e_planejamento.md',
    '07_lideranca_cultura_e_governanca.md',
    '08_anexos_e_contextos_especificos.md',
]

actual = sorted(p.name for p in base.glob('*.md'))
assert actual == expected, actual

required = {
    '00_escopo_e_prioridades.md': ['## Papel no corpus', '## Hierarquia de peso'],
    '01_persona_e_voz.md': ['## Identidade intelectual', '## Como o Naka pensa'],
    '02_crescimento_e_escala.md': ['## Tres formas de crescer', '## Cinco pilares da escala'],
    '03_maquina_de_vendas_infinitas.md': ['## ICP e escolha de publico', '## Estrutura minima da operacao comercial'],
    '04_funis_e_geracao_de_demanda.md': ['## Funis e canais prioritarios', '## Como combinar funis sem dispersao'],
    '05_oferta_negociacao_e_decisao.md': ['## Sonho versus dor', '## Negociacao sem guerra de preco'],
    '06_gestao_financeira_e_planejamento.md': ['## DRE e leitura da realidade', '## Planejamento estrategico como instrumento de direcao'],
    '07_lideranca_cultura_e_governanca.md': ['## Cultura e valores que sustentam a escala', '## Governanca e clareza de papeis'],
    '08_anexos_e_contextos_especificos.md': ['## Papel dos anexos no corpus', '## Proposta de CRM como contexto operacional'],
}

total_words = 0
for filename in expected:
    path = base / filename
    text = path.read_text(encoding='utf-8')
    assert text.startswith('# '), filename
    for heading in required[filename]:
        assert heading in text, (filename, heading)
    total_words += len(text.split())

assert total_words >= 3500, total_words
print('task-5-ok', total_words)
'@ | python -
```

Expected: `task-5-ok <word-count>`

- [ ] **Step 5: Preview concatenated corpus size to confirm it is usable for prompt assembly**

Run:

```powershell
@'
from pathlib import Path

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\Seven_Tools\seven_tools_api\knowledge\naka')
parts = [p.read_text(encoding='utf-8') for p in sorted(base.glob('*.md'))]
full = '\n\n---\n\n'.join(parts)
print('files=', len(parts))
print('chars=', len(full))
print('words=', len(full.split()))
'@ | python -
```

Expected: exactly `files= 9` plus non-zero `chars` and `words`.

- [ ] **Step 6: Commit**

```powershell
git add knowledge/naka
git commit -m "docs(naka): add curated knowledge corpus"
```

---

## Self-Review Checklist

- Spec coverage:
  - Does the plan create all nine files defined in the spec?
  - Does it preserve the core/peripheral hierarchy?
  - Does it include deduplication for `19`/`20` and consolidation for `21`/`22`?

- Placeholder scan:
  - No `TODO`, `TBD`, or "implement later".
  - Every file has required headings and source mapping.
  - Every verification step has an exact command.

- Naming consistency:
  - File names match the approved spec exactly.
  - Repeated heading names are consistent across verification commands and task steps.

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-04-09-naka-knowledge-base.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
