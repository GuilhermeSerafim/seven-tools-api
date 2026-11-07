# Caloni Knowledge Base Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `knowledge/caloni` into a layered, AI-ready Markdown corpus sourced from `docs/caloni`, while keeping the current linear loader working.

**Architecture:** Replace the legacy mixed taxonomy in `knowledge/caloni` with 17 numbered Markdown files grouped into identity, strategic reading, operational playbooks, tactical libraries, and supporting examples. Keep [knowledge.py](../app/modules/ai/knowledge.py) unchanged in this implementation; the plan only restructures and rewrites the knowledge corpus so the existing concatenation model still works and a later selective-loading change has a clean foundation.

**Tech Stack:** Markdown, PowerShell, Python 3.12, existing FastAPI repo structure, `pdfplumber` for extraction support, git.

**Spec:** `docs/specs/2026-04-10-caloni-knowledge-base-design.md`

---

## Scope Notes

This plan covers one subsystem: the Caloni knowledge corpus in `knowledge/caloni`.

It does **not** include backend changes for per-tool selective loading yet. The current implementation in `app/modules/ai/knowledge.py` should remain intact; the only requirement is that it can continue concatenating the new files successfully after the corpus rewrite.

## File Structure

### Final `knowledge/caloni` structure

```text
seven_tools_api/
|-- docs/
|   |-- specs/
|   |   `-- 2026-04-10-caloni-knowledge-base-design.md
|   `-- plans/
|       `-- 2026-04-10-caloni-knowledge-base.md
|-- app/
|   `-- modules/
|       `-- ai/
|           `-- knowledge.py
`-- knowledge/
    `-- caloni/
        |-- 00_identidade_e_principios.md
        |-- 01_voz_linguagem_e_conducao.md
        |-- 10_modelo_comercial_caloni.md
        |-- 11_fluxo_decisao_comercial.md
        |-- 12_estagios_da_reuniao.md
        |-- 13_sinais_riscos_e_lacunas.md
        |-- 20_playbook_reuniao_de_vendas.md
        |-- 21_playbook_objecoes.md
        |-- 22_playbook_proposta_e_fechamento.md
        |-- 23_playbook_customer_success.md
        |-- 30_biblioteca_objecoes.md
        |-- 31_biblioteca_perguntas.md
        |-- 32_biblioteca_intervencoes.md
        |-- 33_biblioteca_antipadroes.md
        |-- 40_casos_e_exemplos.md
        |-- 41_snippets_e_formulacoes.md
        `-- 99_indice_de_uso.md
```

### Legacy files to remove

```text
knowledge/caloni/00_persona.md
knowledge/caloni/00_persona_e_voz.md
knowledge/caloni/01_desbloqueio_vendas.md
knowledge/caloni/01_objecoes.md
knowledge/caloni/02_reuniao_vendas.md
knowledge/caloni/03_proposta_forte.md
knowledge/caloni/03_reuniao_vendas_avancado.md
knowledge/caloni/04_sucesso_cliente.md
knowledge/caloni/05_desbloqueio.md
```

### Source mapping

- `docs/caloni/document_pdf (1).pdf`: desbloqueio mental de vendas, crencas, dinheiro, rejeicao, filosofia comercial
- `docs/caloni/document_pdf (2).pdf`: fluxo completo de reuniao de vendas, 3 sims, ponto A e ponto B, agitacao, valor
- `docs/caloni/document_pdf (3).pdf`: refinamentos avancados de reuniao, conexao, varinha magica, agitacao continua, conducoes reais
- `docs/caloni/document_pdf (4).pdf`: objecoes, significado, antecipacao, leitura de insegurancas, neutralizacao
- `docs/caloni/document_pdf (5).pdf`: extracao de padroes, vocabulario, frases recorrentes, formulacoes e conceitos-chave
- `docs/caloni/document_pdf.pdf`: customer success, primeiros 30 dias, touch points, diagnostico, ROI cedo

---

## Task 1: Reset the corpus directory and scaffold the new taxonomy

**Files:**
- Delete: `knowledge/caloni/00_persona.md`
- Delete: `knowledge/caloni/00_persona_e_voz.md`
- Delete: `knowledge/caloni/01_desbloqueio_vendas.md`
- Delete: `knowledge/caloni/01_objecoes.md`
- Delete: `knowledge/caloni/02_reuniao_vendas.md`
- Delete: `knowledge/caloni/03_proposta_forte.md`
- Delete: `knowledge/caloni/03_reuniao_vendas_avancado.md`
- Delete: `knowledge/caloni/04_sucesso_cliente.md`
- Delete: `knowledge/caloni/05_desbloqueio.md`
- Create: `knowledge/caloni/00_identidade_e_principios.md`
- Create: `knowledge/caloni/01_voz_linguagem_e_conducao.md`
- Create: `knowledge/caloni/10_modelo_comercial_caloni.md`
- Create: `knowledge/caloni/11_fluxo_decisao_comercial.md`
- Create: `knowledge/caloni/12_estagios_da_reuniao.md`
- Create: `knowledge/caloni/13_sinais_riscos_e_lacunas.md`
- Create: `knowledge/caloni/20_playbook_reuniao_de_vendas.md`
- Create: `knowledge/caloni/21_playbook_objecoes.md`
- Create: `knowledge/caloni/22_playbook_proposta_e_fechamento.md`
- Create: `knowledge/caloni/23_playbook_customer_success.md`
- Create: `knowledge/caloni/30_biblioteca_objecoes.md`
- Create: `knowledge/caloni/31_biblioteca_perguntas.md`
- Create: `knowledge/caloni/32_biblioteca_intervencoes.md`
- Create: `knowledge/caloni/33_biblioteca_antipadroes.md`
- Create: `knowledge/caloni/40_casos_e_exemplos.md`
- Create: `knowledge/caloni/41_snippets_e_formulacoes.md`
- Create: `knowledge/caloni/99_indice_de_uso.md`
- Reference: `app/modules/ai/knowledge.py`

- [ ] **Step 1: Verify the current directory and loader assumptions**

Run:

```powershell
@'
from pathlib import Path

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\knowledge\caloni')
files = sorted(p.name for p in base.glob('*.md'))
print('knowledge_files=', files)

loader = Path(r'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\app\modules\ai\knowledge.py')
text = loader.read_text(encoding='utf-8')
assert 'knowledge" / "caloni"' in text
assert 'glob("*.md")' in text
print('loader_ok')
'@ | python -
```

Expected: prints the current Markdown file list and `loader_ok`.

- [ ] **Step 2: Remove the legacy Markdown files from `knowledge/caloni`**

Run:

```powershell
$base = 'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\knowledge\caloni'
$legacy = @(
  '00_persona.md',
  '00_persona_e_voz.md',
  '01_desbloqueio_vendas.md',
  '01_objecoes.md',
  '02_reuniao_vendas.md',
  '03_proposta_forte.md',
  '03_reuniao_vendas_avancado.md',
  '04_sucesso_cliente.md',
  '05_desbloqueio.md'
)
foreach ($name in $legacy) {
  $path = Join-Path $base $name
  if (Test-Path $path) { Remove-Item -LiteralPath $path }
}
Get-ChildItem -LiteralPath $base -Filter *.md | Select-Object -ExpandProperty Name
```

Expected: no legacy files remain in the output.

- [ ] **Step 3: Scaffold the new file set with canonical headings**

Run:

```powershell
@'
from pathlib import Path

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\knowledge\caloni')
scaffolds = {
    '00_identidade_e_principios.md': '''# Identidade e Principios

## Papel no corpus
## Quem e o Caloni
## Como ele pensa comercialmente
## Crencas centrais
## Valores e guardrails
## O que jamais deve acontecer
''',
    '01_voz_linguagem_e_conducao.md': '''# Voz, Linguagem e Conducao

## Papel no corpus
## Tom de voz
## Vocabulario caracteristico
## Estrutura de conducao
## Frases recorrentes
## O que evitar na linguagem
''',
    '10_modelo_comercial_caloni.md': '''# Modelo Comercial Caloni

## Papel no corpus
## Vender como diagnostico
## Solucao como ponte
## Valor, urgencia e compromisso
## Objecao como inseguranca
## Processo acima de improviso
''',
    '11_fluxo_decisao_comercial.md': '''# Fluxo de Decisao Comercial

## Papel no corpus
## Sequencia de leitura e decisao
## Como decidir o proximo movimento
## O que trava a decisao
## Como recuperar a conducao
''',
    '12_estagios_da_reuniao.md': '''# Estagios da Reuniao

## Papel no corpus
## Conexao e abertura
## Diagnostico do presente
## Priorizacao
## Futuro desejado
## Agitacao
## Compromisso
## Solucao e valor
## Objecoes
## Fechamento e combinado
''',
    '13_sinais_riscos_e_lacunas.md': '''# Sinais, Riscos e Lacunas

## Papel no corpus
## Sinais do lead
## Riscos da call
## Lacunas do vendedor
## Leitura estrategica
## Proximo movimento recomendado
''',
    '20_playbook_reuniao_de_vendas.md': '''# Playbook Reuniao de Vendas

## Contexto de uso
## Objetivo
## Entradas esperadas
## Sequencia da reuniao
## Intervencoes recomendadas
## O que evitar
## Criterios de boa execucao
''',
    '21_playbook_objecoes.md': '''# Playbook Objecoes

## Contexto de uso
## Objetivo
## Tipos de objecao
## Sequencia de tratamento
## Intervencoes recomendadas
## O que evitar
## Criterios de boa execucao
''',
    '22_playbook_proposta_e_fechamento.md': '''# Playbook Proposta e Fechamento

## Contexto de uso
## Objetivo
## Quando entrar em proposta
## Como sustentar valor
## Como conduzir a decisao
## O que evitar
## Criterios de boa execucao
''',
    '23_playbook_customer_success.md': '''# Playbook Customer Success

## Contexto de uso
## Objetivo
## Primeiros 30 dias
## Touch points e diagnostico
## Plano de acao e ROI
## O que evitar
## Criterios de boa execucao
''',
    '30_biblioteca_objecoes.md': '''# Biblioteca de Objecoes

## Papel no corpus
## Preco
## Tempo
## Preciso pensar
## Preciso falar com outra pessoa
## Inseguranca sobre entrega
## Comparacao com alternativas
''',
    '31_biblioteca_perguntas.md': '''# Biblioteca de Perguntas

## Papel no corpus
## Perguntas de abertura
## Perguntas de diagnostico
## Perguntas de prioridade
## Perguntas de agitacao
## Perguntas de compromisso
## Perguntas de fechamento
''',
    '32_biblioteca_intervencoes.md': '''# Biblioteca de Intervencoes

## Papel no corpus
## Reenquadramentos
## Microcorrecoes de rota
## Recuperacao de conducao
## Intervencoes para urgencia
## Intervencoes para compromisso
''',
    '33_biblioteca_antipadroes.md': '''# Biblioteca de Antipadroes

## Papel no corpus
## Explicar cedo demais
## Defender preco cedo demais
## Virar professor
## Aceitar objecao superficial
## Sair sem combinado
''',
    '40_casos_e_exemplos.md': '''# Casos e Exemplos

## Papel no corpus
## Casos de reuniao
## Casos de objecao
## Casos de recuperacao de call
## Casos de pos-venda
''',
    '41_snippets_e_formulacoes.md': '''# Snippets e Formulacoes

## Papel no corpus
## Formulacoes de abertura
## Formulacoes de diagnostico
## Formulacoes de agitacao
## Formulacoes de compromisso
## Formulacoes de fechamento
''',
    '99_indice_de_uso.md': '''# Indice de Uso

## Papel no corpus
## Mapa dos arquivos
## Sugestoes de consumo por ferramenta
## Regras de manutencao
'''
}

for name, content in scaffolds.items():
    (base / name).write_text(content + '\n', encoding='utf-8')
'@ | python -
```

Expected: command exits successfully and creates the 17 files.

- [ ] **Step 4: Verify the exact file set and required headings**

Run:

```powershell
@'
from pathlib import Path

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\knowledge\caloni')
expected = [
    '00_identidade_e_principios.md',
    '01_voz_linguagem_e_conducao.md',
    '10_modelo_comercial_caloni.md',
    '11_fluxo_decisao_comercial.md',
    '12_estagios_da_reuniao.md',
    '13_sinais_riscos_e_lacunas.md',
    '20_playbook_reuniao_de_vendas.md',
    '21_playbook_objecoes.md',
    '22_playbook_proposta_e_fechamento.md',
    '23_playbook_customer_success.md',
    '30_biblioteca_objecoes.md',
    '31_biblioteca_perguntas.md',
    '32_biblioteca_intervencoes.md',
    '33_biblioteca_antipadroes.md',
    '40_casos_e_exemplos.md',
    '41_snippets_e_formulacoes.md',
    '99_indice_de_uso.md',
]
actual = sorted(p.name for p in base.glob('*.md'))
assert actual == expected, actual
for path in sorted(base.glob('*.md')):
    text = path.read_text(encoding='utf-8')
    assert text.startswith('# '), path.name
    assert '## Papel no corpus' in text or '## Contexto de uso' in text or '## Papel no corpus' in text, path.name
print('task-1-ok', len(actual))
'@ | python -
```

Expected: `task-1-ok 17`

- [ ] **Step 5: Commit the scaffold reset**

```powershell
git add knowledge/caloni
git commit -m "docs(caloni): reset knowledge corpus taxonomy"
```

---

## Task 2: Write the canonical identity and decision-reading layer

**Files:**
- Modify: `knowledge/caloni/00_identidade_e_principios.md`
- Modify: `knowledge/caloni/01_voz_linguagem_e_conducao.md`
- Modify: `knowledge/caloni/10_modelo_comercial_caloni.md`
- Modify: `knowledge/caloni/11_fluxo_decisao_comercial.md`
- Modify: `knowledge/caloni/12_estagios_da_reuniao.md`
- Modify: `knowledge/caloni/13_sinais_riscos_e_lacunas.md`
- Reference: `docs/caloni/document_pdf (1).pdf`
- Reference: `docs/caloni/document_pdf (2).pdf`
- Reference: `docs/caloni/document_pdf (3).pdf`
- Reference: `docs/caloni/document_pdf (4).pdf`
- Reference: `docs/caloni/document_pdf (5).pdf`

- [ ] **Step 1: Populate `00_identidade_e_principios.md` with the canon**

The final file must capture:

- vendas como ajuda, diagnostico e conducao;
- dinheiro como troca legitima de valor;
- prioridade, compromisso, urgencia e valor como eixos do metodo;
- objecao como inseguranca, nao rejeicao;
- processo acima de improviso;
- a proibicao de vender cedo, explicar cedo ou sair sem combinado.

Use this file shape:

```md
# Identidade e Principios

## Papel no corpus
## Quem e o Caloni
## Como ele pensa comercialmente
## Crencas centrais
## Valores e guardrails
## O que jamais deve acontecer
```

- [ ] **Step 2: Populate `01_voz_linguagem_e_conducao.md` from the pattern-extraction material**

The final file must capture:

- tom direto, firme, proximo e adulto;
- acolhimento sem moleza e provocacao sem humilhacao;
- vocabulario de diagnostico, prioridade, compromisso, urgencia, resultado e combinado;
- frases recorrentes como ferramentas de conducao, nao como bordoes decorativos;
- como o Caloni abre, aquece, pergunta, reenquadra e fecha.

Use this file shape:

```md
# Voz, Linguagem e Conducao

## Papel no corpus
## Tom de voz
## Vocabulario caracteristico
## Estrutura de conducao
## Frases recorrentes
## O que evitar na linguagem
```

- [ ] **Step 3: Populate `10_modelo_comercial_caloni.md` and `11_fluxo_decisao_comercial.md`**

`10_modelo_comercial_caloni.md` must capture:

- diagnostico antes de solucao;
- solucao como ponte entre ponto A e ponto B;
- valor antes de preco;
- compromisso antes de oferta;
- consciencia do problema mais urgencia em resolver como motor do desejo.

`11_fluxo_decisao_comercial.md` must capture:

- como a IA deve ler contexto primeiro, decidir direcao depois e formular fala por ultimo;
- como identificar travas de valor, compromisso, urgencia, prioridade e inseguranca;
- como escolher entre aprofundar, agitar, validar, propor, tratar objecao ou fechar;
- como recuperar a conducao quando a conversa sai da rota.

Use these file shapes:

```md
# Modelo Comercial Caloni

## Papel no corpus
## Vender como diagnostico
## Solucao como ponte
## Valor, urgencia e compromisso
## Objecao como inseguranca
## Processo acima de improviso
```

```md
# Fluxo de Decisao Comercial

## Papel no corpus
## Sequencia de leitura e decisao
## Como decidir o proximo movimento
## O que trava a decisao
## Como recuperar a conducao
```

- [ ] **Step 4: Populate `12_estagios_da_reuniao.md` and `13_sinais_riscos_e_lacunas.md`**

`12_estagios_da_reuniao.md` must define, for each stage:

- objetivo do estagio;
- sinais de entrada;
- sinais de saida;
- erros comuns;
- risco de pular essa etapa;
- proximo movimento ideal.

Stages to cover:

- conexao e abertura;
- diagnostico do presente;
- priorizacao;
- futuro desejado;
- agitacao;
- compromisso;
- solucao e valor;
- objecoes;
- fechamento e combinado.

`13_sinais_riscos_e_lacunas.md` must define:

- sinais do lead;
- riscos de call;
- lacunas do vendedor;
- leitura estrategica Caloni;
- objetivo do proximo movimento.

- [ ] **Step 5: Verify headings and minimum density for the identity and reading layer**

Run:

```powershell
@'
from pathlib import Path

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\knowledge\caloni')
checks = {
    '00_identidade_e_principios.md': ['## Crencas centrais', '## Valores e guardrails'],
    '01_voz_linguagem_e_conducao.md': ['## Tom de voz', '## Frases recorrentes'],
    '10_modelo_comercial_caloni.md': ['## Solucao como ponte', '## Processo acima de improviso'],
    '11_fluxo_decisao_comercial.md': ['## Sequencia de leitura e decisao', '## Como decidir o proximo movimento'],
    '12_estagios_da_reuniao.md': ['## Conexao e abertura', '## Fechamento e combinado'],
    '13_sinais_riscos_e_lacunas.md': ['## Sinais do lead', '## Lacunas do vendedor'],
}
for filename, headings in checks.items():
    text = (base / filename).read_text(encoding='utf-8')
    for heading in headings:
        assert heading in text, (filename, heading)
    assert len(text.split()) >= 220, filename
print('task-2-ok')
'@ | python -
```

Expected: `task-2-ok`

- [ ] **Step 6: Commit the identity and reading layer**

```powershell
git add knowledge/caloni/00_identidade_e_principios.md knowledge/caloni/01_voz_linguagem_e_conducao.md knowledge/caloni/10_modelo_comercial_caloni.md knowledge/caloni/11_fluxo_decisao_comercial.md knowledge/caloni/12_estagios_da_reuniao.md knowledge/caloni/13_sinais_riscos_e_lacunas.md
git commit -m "docs(caloni): add identity and decision layers"
```

---

## Task 3: Write the operational playbooks for sales, objections, proposal, and customer success

**Files:**
- Modify: `knowledge/caloni/20_playbook_reuniao_de_vendas.md`
- Modify: `knowledge/caloni/21_playbook_objecoes.md`
- Modify: `knowledge/caloni/22_playbook_proposta_e_fechamento.md`
- Modify: `knowledge/caloni/23_playbook_customer_success.md`
- Reference: `docs/caloni/document_pdf (2).pdf`
- Reference: `docs/caloni/document_pdf (3).pdf`
- Reference: `docs/caloni/document_pdf (4).pdf`
- Reference: `docs/caloni/document_pdf.pdf`

- [ ] **Step 1: Populate `20_playbook_reuniao_de_vendas.md`**

The final file must answer:

- qual e o objetivo da reuniao;
- como usar APA e a abertura sem virar script engessado;
- como diagnosticar ponto A, ponto B e prioridade;
- como buscar os 3 sims na ordem certa;
- como usar agitacao e geracao de valor sem matar a fome do lead;
- como encerrar com decisao ou combinado claro.

Required structure:

```md
# Playbook Reuniao de Vendas

## Contexto de uso
## Objetivo
## Entradas esperadas
## Sequencia da reuniao
## Intervencoes recomendadas
## O que evitar
## Criterios de boa execucao
```

- [ ] **Step 2: Populate `21_playbook_objecoes.md`**

The final file must answer:

- como interpretar objecao como pedido de ajuda;
- como antecipar objecoes durante a reuniao;
- como separar objecao real de objecao superficial;
- como acolher, reenquadrar, isolar e neutralizar;
- como evitar desconto precoce e defesa reativa.

Required structure:

```md
# Playbook Objecoes

## Contexto de uso
## Objetivo
## Tipos de objecao
## Sequencia de tratamento
## Intervencoes recomendadas
## O que evitar
## Criterios de boa execucao
```

- [ ] **Step 3: Populate `22_playbook_proposta_e_fechamento.md` and `23_playbook_customer_success.md`**

`22_playbook_proposta_e_fechamento.md` must capture:

- quando a proposta faz sentido e quando ela e prematura;
- como reconectar proposta a dor, prioridade, urgencia e ROI;
- como sustentar decisao sem virar professor ou negociador defensivo;
- como sair com decisao ou combinado.

`23_playbook_customer_success.md` must capture:

- regra dos primeiros 30 dias;
- touch points de 7 a 10 dias;
- diagnostico antes de plano de acao;
- progresso, resultado e ROI cedo;
- CS proativo, nao reativo.

- [ ] **Step 4: Verify the playbooks**

Run:

```powershell
@'
from pathlib import Path

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\knowledge\caloni')
checks = {
    '20_playbook_reuniao_de_vendas.md': ['## Sequencia da reuniao', '## Criterios de boa execucao'],
    '21_playbook_objecoes.md': ['## Sequencia de tratamento', '## O que evitar'],
    '22_playbook_proposta_e_fechamento.md': ['## Quando entrar em proposta', '## Como conduzir a decisao'],
    '23_playbook_customer_success.md': ['## Primeiros 30 dias', '## Plano de acao e ROI'],
}
for filename, headings in checks.items():
    text = (base / filename).read_text(encoding='utf-8')
    for heading in headings:
        assert heading in text, (filename, heading)
    assert len(text.split()) >= 220, filename
print('task-3-ok')
'@ | python -
```

Expected: `task-3-ok`

- [ ] **Step 5: Commit the operational playbooks**

```powershell
git add knowledge/caloni/20_playbook_reuniao_de_vendas.md knowledge/caloni/21_playbook_objecoes.md knowledge/caloni/22_playbook_proposta_e_fechamento.md knowledge/caloni/23_playbook_customer_success.md
git commit -m "docs(caloni): add operational playbooks"
```

---

## Task 4: Build the tactical libraries for objections, questions, interventions, and anti-patterns

**Files:**
- Modify: `knowledge/caloni/30_biblioteca_objecoes.md`
- Modify: `knowledge/caloni/31_biblioteca_perguntas.md`
- Modify: `knowledge/caloni/32_biblioteca_intervencoes.md`
- Modify: `knowledge/caloni/33_biblioteca_antipadroes.md`
- Reference: `docs/caloni/document_pdf (2).pdf`
- Reference: `docs/caloni/document_pdf (3).pdf`
- Reference: `docs/caloni/document_pdf (4).pdf`
- Reference: `docs/caloni/document_pdf (5).pdf`

- [ ] **Step 1: Populate `30_biblioteca_objecoes.md`**

For each objection family, include:

- sinais de deteccao;
- leitura estrategica;
- lacuna do vendedor;
- objetivo do proximo movimento;
- intervencao recomendada;
- exemplos de fala;
- o que evitar.

Mandatory objection families:

- preco;
- tempo;
- preciso pensar;
- preciso falar com outra pessoa;
- inseguranca sobre entrega;
- comparacao com alternativas.

- [ ] **Step 2: Populate `31_biblioteca_perguntas.md`**

Group questions by objective, not by PDF or by vague category:

- abertura;
- diagnostico;
- prioridade;
- futuro desejado;
- agitacao;
- compromisso;
- validacao de solucao;
- fechamento e combinado.

Each group must explain:

- para que serve;
- quando usar;
- como nao soar mecanico;
- exemplos curtos de pergunta.

- [ ] **Step 3: Populate `32_biblioteca_intervencoes.md` and `33_biblioteca_antipadroes.md`**

`32_biblioteca_intervencoes.md` must organize:

- reenquadramentos;
- recuperacao de conducao;
- microcomandos para o vendedor;
- intervencoes para valor, urgencia, prioridade e compromisso.

`33_biblioteca_antipadroes.md` must organize:

- explicar cedo demais;
- defender preco cedo demais;
- virar professor;
- aceitar objecao superficial;
- empilhar informacao sem prioridade;
- sair sem combinado.

Each anti-pattern must include:

- como aparece;
- por que enfraquece a venda;
- como corrigir;
- formula curta de substituicao.

- [ ] **Step 4: Verify the tactical libraries**

Run:

```powershell
@'
from pathlib import Path

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\knowledge\caloni')
checks = {
    '30_biblioteca_objecoes.md': ['## Preco', '## Comparacao com alternativas'],
    '31_biblioteca_perguntas.md': ['## Perguntas de diagnostico', '## Perguntas de fechamento'],
    '32_biblioteca_intervencoes.md': ['## Reenquadramentos', '## Intervencoes para compromisso'],
    '33_biblioteca_antipadroes.md': ['## Explicar cedo demais', '## Sair sem combinado'],
}
for filename, headings in checks.items():
    text = (base / filename).read_text(encoding='utf-8')
    for heading in headings:
        assert heading in text, (filename, heading)
    assert len(text.split()) >= 220, filename
print('task-4-ok')
'@ | python -
```

Expected: `task-4-ok`

- [ ] **Step 5: Commit the tactical libraries**

```powershell
git add knowledge/caloni/30_biblioteca_objecoes.md knowledge/caloni/31_biblioteca_perguntas.md knowledge/caloni/32_biblioteca_intervencoes.md knowledge/caloni/33_biblioteca_antipadroes.md
git commit -m "docs(caloni): add tactical libraries"
```

---

## Task 5: Add supporting examples, usage index, and run final corpus verification

**Files:**
- Modify: `knowledge/caloni/40_casos_e_exemplos.md`
- Modify: `knowledge/caloni/41_snippets_e_formulacoes.md`
- Modify: `knowledge/caloni/99_indice_de_uso.md`
- Modify: `knowledge/caloni/00_identidade_e_principios.md`
- Modify: `knowledge/caloni/01_voz_linguagem_e_conducao.md`
- Modify: `knowledge/caloni/10_modelo_comercial_caloni.md`
- Modify: `knowledge/caloni/11_fluxo_decisao_comercial.md`
- Modify: `knowledge/caloni/12_estagios_da_reuniao.md`
- Modify: `knowledge/caloni/13_sinais_riscos_e_lacunas.md`
- Modify: `knowledge/caloni/20_playbook_reuniao_de_vendas.md`
- Modify: `knowledge/caloni/21_playbook_objecoes.md`
- Modify: `knowledge/caloni/22_playbook_proposta_e_fechamento.md`
- Modify: `knowledge/caloni/23_playbook_customer_success.md`
- Modify: `knowledge/caloni/30_biblioteca_objecoes.md`
- Modify: `knowledge/caloni/31_biblioteca_perguntas.md`
- Modify: `knowledge/caloni/32_biblioteca_intervencoes.md`
- Modify: `knowledge/caloni/33_biblioteca_antipadroes.md`
- Reference: `app/modules/ai/knowledge.py`

- [ ] **Step 1: Populate `40_casos_e_exemplos.md`**

The final file must preserve:

- exemplos reais de reuniao e objecao com valor didatico;
- casos de recuperacao de conducao;
- casos de abertura, agitacao e fechamento;
- exemplos de CS com diagnostico, plano de acao e ROI cedo.

The file must explain why each case matters, not just narrate what happened.

- [ ] **Step 2: Populate `41_snippets_e_formulacoes.md` and `99_indice_de_uso.md`**

`41_snippets_e_formulacoes.md` must preserve:

- exemplos curtos de fala para abertura, diagnostico, prioridade, agitacao, compromisso, proposta e fechamento;
- avisos de uso para evitar literalismo;
- relacao entre snippet e objetivo da fala.

`99_indice_de_uso.md` must map:

- o papel de cada arquivo;
- em quais ferramentas cada grupo de arquivos e mais util;
- ordem de leitura humana;
- regras de manutencao para evitar duplicacao e conflito.

- [ ] **Step 3: Run an overlap review across all 17 files**

Read every file in `knowledge/caloni` and trim duplication. Keep a concept in multiple files only when:

- it is required for the file to stand on its own; or
- the same idea appears with a genuinely different tactical angle.

Specifically trim:

- repeticao literal de principios entre `00`, `10` e `20`;
- repeticao literal de falas entre `31`, `32` e `41`;
- repeticao de anti-padroes entre `21` e `33`.

- [ ] **Step 4: Verify the full corpus shape, total density, and loader compatibility**

Run:

```powershell
@'
from pathlib import Path
from app.modules.ai.knowledge import load_caloni_knowledge

base = Path(r'C:\Users\Guiler\Desktop\wks\seven\seven_tools\seven_tools_api\knowledge\caloni')
expected = [
    '00_identidade_e_principios.md',
    '01_voz_linguagem_e_conducao.md',
    '10_modelo_comercial_caloni.md',
    '11_fluxo_decisao_comercial.md',
    '12_estagios_da_reuniao.md',
    '13_sinais_riscos_e_lacunas.md',
    '20_playbook_reuniao_de_vendas.md',
    '21_playbook_objecoes.md',
    '22_playbook_proposta_e_fechamento.md',
    '23_playbook_customer_success.md',
    '30_biblioteca_objecoes.md',
    '31_biblioteca_perguntas.md',
    '32_biblioteca_intervencoes.md',
    '33_biblioteca_antipadroes.md',
    '40_casos_e_exemplos.md',
    '41_snippets_e_formulacoes.md',
    '99_indice_de_uso.md',
]
actual = sorted(p.name for p in base.glob('*.md'))
assert actual == expected, actual

total_words = 0
for filename in expected:
    text = (base / filename).read_text(encoding='utf-8')
    assert text.startswith('# '), filename
    total_words += len(text.split())

full = load_caloni_knowledge()
assert len(full) > 10000, len(full)
assert total_words >= 5000, total_words
print('task-5-ok', len(actual), total_words, len(full))
'@ | python -
```

Expected: `task-5-ok 17 <word-count> <char-count>`

- [ ] **Step 5: Commit the completed corpus**

```powershell
git add knowledge/caloni
git commit -m "docs(caloni): add curated knowledge corpus"
```

---

## Self-Review Checklist

- Spec coverage:
  - Does the plan create the exact 17-file taxonomy from the approved spec?
  - Does it separate identity, reading, action, tactical libraries, and support files?
  - Does it keep backend loader changes out of this implementation scope?
  - Does it preserve the copilot priority of context reading first, strategic recommendation second, and phrasing third?

- Placeholder scan:
  - No `TODO`, `TBD`, `implement later`, or vague "handle appropriately" instructions.
  - Every task has exact file paths.
  - Every verification step has an exact command and expected outcome.

- Consistency:
  - File names in the tasks match the final structure exactly.
  - Section names used in verification scripts exist in the scaffold and prose requirements.
  - The final verification imports `load_caloni_knowledge` without requiring backend code edits.

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-04-10-caloni-knowledge-base.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
