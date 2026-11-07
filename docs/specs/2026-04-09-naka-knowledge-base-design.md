# Naka Knowledge Base Design

## Visao Geral

Criar uma base de conhecimento em `seven_tools_api/knowledge/naka` otimizada para consumo por IA, a partir dos PDFs em `../docs/naka`.

O objetivo nao e arquivar cada PDF individualmente. O objetivo e transformar o corpus do Dennis Nakamura em poucos arquivos Markdown tematicos, densos, coerentes e com o maximo possivel de conhecimento util para prompts longos.

Essa decisao foi guiada pela implementacao atual em [knowledge.py](../../app/modules/ai/knowledge.py), que concatena todos os `.md` de uma pasta em ordem alfabetica. Nesse modelo, a qualidade da curadoria vale mais do que a rastreabilidade por documento.

## Objetivos

- Maximizar a retencao de conhecimento util do Naka para consumo da IA.
- Preservar a logica de raciocinio, a voz e os frameworks do autor.
- Reduzir redundancia entre materiais que repetem a mesma metodologia.
- Separar o nucleo do metodo dos materiais complementares ou perifericos.
- Produzir uma base que funcione bem com o loader linear atual, sem exigir busca vetorial.

## Nao Objetivos

- Criar uma biblioteca documental "um Markdown por PDF".
- Preservar ruido de slide, paginacao, creditos visuais ou layout de apresentacao.
- Fazer OCR perfeito de materiais escaneados.
- Tratar materiais perifericos como se fossem o centro da metodologia.

## Inventario do Corpus

Foram analisados 22 PDFs em `docs/naka`, com os seguintes grupos principais:

- Comercial e metodologia: `6`, `7`, `8`, `9`, `11`, `12`, `17`, `21`, `22`
- Gestao, escala e previsibilidade: `24`, `25`, `26`, `27`
- Voz, autoridade e posicionamento: `14`, `16`, `23`
- Materiais adjacentes: `13`, `15`, `18`
- Proposta de CRM: `19`, `20`

Notas de curadoria importantes:

- `19` e `20` sao arquivos duplicados, byte a byte identicos. Devem entrar uma unica vez.
- `21` e `22` sao variantes do mesmo material de funis. Devem ser unificados, preservando apenas diferencas uteis.
- `12` e um mapa mental. Ele deve servir como estrutura de metodo, nao como texto literal.
- `14` e `23` ajudam a calibrar autoridade, repertorio e contexto publico, mas nao devem virar biografia longa.

## Decisao de Estrutura

A base deve ser organizada como poucos arquivos tematicos consolidados, numerados para manter a ordem de concatenacao:

- `00_escopo_e_prioridades.md`
- `01_persona_e_voz.md`
- `02_crescimento_e_escala.md`
- `03_maquina_de_vendas_infinitas.md`
- `04_funis_e_geracao_de_demanda.md`
- `05_oferta_negociacao_e_decisao.md`
- `06_gestao_financeira_e_planejamento.md`
- `07_lideranca_cultura_e_governanca.md`
- `08_anexos_e_contextos_especificos.md`

Essa estrutura foi escolhida porque:

- preserva blocos conceituais grandes o bastante para a IA manter coerencia;
- evita uma base unica grande demais e dificil de manter;
- reduz a fragmentacao excessiva de um arquivo por PDF;
- encaixa no loader atual sem exigir mudancas no backend.

## Descricao dos Arquivos

### `00_escopo_e_prioridades.md`

Funcao:

- apresentar o papel da base;
- distinguir temas centrais de temas complementares;
- orientar a IA sobre o que deve ter mais peso no raciocinio.

Conteudo esperado:

- definicao do corpus principal;
- definicao de materiais perifericos;
- prioridade metodologica de vendas, escala, gestao e governanca;
- notas de uso para evitar que holdings ou CRM dominem respostas genericas.

### `01_persona_e_voz.md`

Funcao:

- capturar a identidade intelectual do Naka;
- calibrar tom, postura, linguagem, criterio e autoridade.

Fontes principais:

- `16`, `14`, `23`

Conteudo esperado:

- voz, mentalidade e estilo de conducao;
- forma de diagnosticar, orientar e corrigir;
- nivel de franqueza, objetividade e criterio;
- provas de autoridade e repertorio publico.

### `02_crescimento_e_escala.md`

Funcao:

- consolidar a visao de crescimento empresarial do Naka.

Fontes principais:

- `11`, `24`, `26`, `27`

Conteudo esperado:

- tres formas de crescer;
- cinco pilares da escala;
- estagios de evolucao da empresa;
- relacao entre vendas, gestao, cultura, governanca e ecossistema;
- principios de crescimento sustentavel e previsivel.

### `03_maquina_de_vendas_infinitas.md`

Funcao:

- registrar a espinha dorsal da metodologia comercial.

Fontes principais:

- `9`, `12`, `17`, `26`

Fontes de apoio:

- `24`, `27`

Conteudo esperado:

- ICP;
- produto perfeito;
- apresentacao de vendas;
- estrutura minima de operacao comercial;
- papeis e fases da equipe;
- CRM, inteligencia comercial e acompanhamento;
- customer success como extensao do sistema.

### `04_funis_e_geracao_de_demanda.md`

Funcao:

- consolidar a logica de abastecimento continuo de leads e oportunidades.

Fontes principais:

- `7`, `21`, `22`

Fonte de apoio:

- `12`

Conteudo esperado:

- canais e funis de aquisicao;
- geracao recorrente de leads;
- prospeccao ativa e passiva;
- criterio de escolha dos primeiros funis;
- combinacao de funis sem dispersao.

### `05_oferta_negociacao_e_decisao.md`

Funcao:

- transformar o conhecimento de abordagem comercial em criterios decisorios.

Fontes principais:

- `6`, `8`

Fontes de apoio:

- `9`, `17`

Conteudo esperado:

- vender pela dor e pelo sonho;
- construcao de valor;
- negociacao;
- diferenciacao;
- deslocamento da conversa de preco para valor;
- elementos de proposta forte e decisao mais provavel.

### `06_gestao_financeira_e_planejamento.md`

Funcao:

- ligar gestao financeira, planejamento e execucao.

Fontes principais:

- `24`, `25`

Fonte de apoio:

- `26`

Conteudo esperado:

- DRE;
- indicadores financeiros;
- ROI, lucratividade e previsibilidade;
- conexao entre financas, marketing, vendas e operacao;
- planejamento estrategico como instrumento de clareza e direcao.

### `07_lideranca_cultura_e_governanca.md`

Funcao:

- consolidar a camada organizacional que sustenta a escala.

Fontes principais:

- `18`, `26`, `27`

Conteudo esperado:

- formacao de lideres;
- cultura;
- valores;
- sucessao;
- governanca;
- maturidade de equipe e crescimento sem caos.

### `08_anexos_e_contextos_especificos.md`

Funcao:

- preservar conhecimento util que nao pertence ao nucleo principal do metodo.

Fontes principais:

- `13`, `15`, `19`/`20`

Conteudo esperado:

- holdings e planejamento patrimonial como repertorio complementar;
- proposta de CRM como contexto de visao operacional e comercial;
- aviso explicito de que esse arquivo tem peso inferior na hierarquia do corpus.

## Estrategia de Extracao

Cada arquivo nao deve apenas resumir aulas. Ele deve capturar o maximo possivel de conhecimento util em formato bom para IA.

O processo de extracao deve priorizar:

- principios;
- modelos mentais;
- frameworks;
- checklists;
- sequencias operacionais;
- criterios de decisao;
- erros recorrentes;
- exemplos e analogias com alto valor explicativo;
- conexoes entre temas do corpus.

O foco nao e copiar o texto original, e sim destilar o metodo.

## Regras de Curadoria

### 1. Preservar a logica do autor

A base deve refletir como o Naka pensa:

- crescimento como sistema;
- diagnostico antes de acao;
- clareza antes de escala;
- venda como engenharia, nao improviso;
- gestao como previsibilidade, nao correria;
- cultura e governanca como partes do crescimento.

### 2. Curar redundancia sem empobrecer

Quando dois ou mais PDFs repetirem o mesmo conceito:

- manter a melhor formulacao consolidada;
- usar os demais como reforco, nuance ou exemplo;
- evitar repeticao literal em arquivos diferentes.

### 3. Transformar material visual em texto acionavel

Mapas mentais, slides e materiais visuais devem ser convertidos para:

- estruturas de metodo;
- dimensoes de analise;
- criterios de avaliacao;
- sequencias de implementacao;
- repertorio estrategico.

Nao devem virar descricao de slide.

### 4. Separar nucleo de metodo e periferia

O corpus principal deve ter prioridade de peso sobre contextos especificos.

Nucleo:

- vendas;
- funis;
- crescimento;
- escala;
- financas;
- planejamento;
- lideranca;
- governanca;
- voz do autor.

Periferia:

- holdings;
- patrimonial;
- proposta de CRM.

### 5. Maximizar densidade util

Cada secao deve buscar alta densidade de conhecimento por paragrafo. O resultado ideal e:

- texto enxuto;
- sem gordura;
- sem perda de nuance relevante;
- sem lixo de PDF;
- sem repeticao mecanica.

## Formato Interno Recomendado para Cada `.md`

Os arquivos nao precisam ter uma estrutura identica, mas devem tender a este formato:

1. Papel do arquivo no corpus
2. Principios centrais
3. Frameworks e modelos
4. Aplicacao pratica e operacao
5. Sinais, erros e alertas
6. Exemplos, analogias e referencias recorrentes
7. Conexoes com outros arquivos da base

Essa forma ajuda a IA a:

- entender contexto;
- achar rapidamente criterios de decisao;
- navegar melhor entre diagnostico, estrategia e execucao.

## Regras de Escrita

- Escrever para LLM, nao para aula humana.
- Usar titulos curtos e previsiveis.
- Preferir blocos tematicos coesos.
- Usar listas quando melhorarem recuperacao de contexto.
- Evitar frases decorativas e discurso motivacional.
- Manter o vocabulario do autor quando ele carregar decisao ou postura.
- Limpar ruido de layout, credenciais, numeracao de slide e elementos visuais irrelevantes.
- Manter exemplos quando eles ajudarem a IA a raciocinar melhor.
- Explicitar o peso menor dos materiais complementares.

## Criterios de Qualidade

A base sera considerada bem desenhada se:

- a IA conseguir responder com voz coerente ao Naka;
- o metodo principal aparecer antes dos anexos;
- os temas centrais estiverem distribuidos sem sobreposicao caotica;
- nao houver duplicacao inutil de blocos entre arquivos;
- a densidade de conhecimento por arquivo for alta;
- o loader atual puder consumir tudo sem nenhuma mudanca de codigo.

## Riscos e Mitigacoes

### Risco: excesso de resumo

Mitigacao:

- extrair frameworks, criterios e exemplos, nao apenas topicos superficiais.

### Risco: excesso de transcricao

Mitigacao:

- reescrever com curadoria, removendo repeticao e ruido.

### Risco: materiais perifericos contaminarem o corpus central

Mitigacao:

- usar `00_escopo_e_prioridades.md` para deixar a hierarquia explicita;
- isolar anexos em `08_anexos_e_contextos_especificos.md`.

### Risco: duplicidade entre PDFs parecidos

Mitigacao:

- tratar `19` e `20` como um unico insumo;
- fundir `21` e `22` por criterio, nao por copia.

## Proxima Etapa

Depois da aprovacao deste design, a proxima etapa e escrever um plano de implementacao e, em seguida, produzir os arquivos Markdown em `knowledge/naka` com base nas regras acima.
