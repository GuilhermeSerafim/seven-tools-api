# Caloni Knowledge Base Design

## Visao Geral

Criar uma nova base de conhecimento em `knowledge/caloni` otimizada para consumo por IA, a partir dos PDFs em `docs/caloni`, com foco nas ferramentas comerciais atuais da SEVEN e nas futuras.

O objetivo nao e transcrever aulas, arquivar PDFs ou reunir frases soltas. O objetivo e transformar o corpus do Caloni em uma base canonicamente organizada para:

- preservar o pensamento comercial do autor;
- ensinar a IA a ler contexto, diagnosticar e decidir;
- sustentar ferramentas operacionais, especialmente um copilot de call em tempo real;
- permitir consumo seletivo por ferramenta no futuro, sem perder coerencia metodologica.

Essa decisao parte do cenario atual em [knowledge.py](../../app/modules/ai/knowledge.py), que concatena todos os `.md` de `knowledge/caloni` em ordem alfabetica e injeta o corpus inteiro no prompt. O design novo precisa funcionar razoavelmente nesse loader linear agora, mas ja nascer preparado para um modelo posterior de composicao por perfil de ferramenta.

## Objetivos

- Maximizar reutilizacao futura sem sacrificar utilidade nas ferramentas comerciais atuais.
- Reorganizar `knowledge/caloni` do zero com uma taxonomia clara, estavel e editorialmente consistente.
- Separar identidade, leitura estrategica e acao operacional em camadas distintas.
- Ensinar a IA a interpretar reunioes de vendas, riscos, objecoes, lacunas do vendedor e proximos movimentos.
- Preparar o corpus para um copilot de call que atue como coach em tempo real.
- Reduzir duplicacao, conflito de instrucoes e ruido herdado das aulas.

## Nao Objetivos

- Manter a estrutura atual de arquivos por compatibilidade historica.
- Criar um Markdown por PDF ou preservar a ordem das aulas.
- Fazer transcricao literal do material fonte.
- Transformar a base em um repositorio de scripts de fala sem inteligencia contextual.
- Otimizar o corpus apenas para a implementacao atual de loader linear.

## Contexto Atual

O repositorio hoje possui uma pasta `knowledge/caloni` com arquivos heterogeneos que misturam:

- persona e voz;
- filosofia de vendas;
- fluxo de reuniao;
- tecnicas avancadas;
- customer success;
- arquivos curtos e longos com granularidade inconsistente.

O backend atual:

- le todos os `.md` de `knowledge/caloni`;
- concatena os arquivos em uma unica string;
- usa o corpus inteiro como parte do `system_prompt` para ferramentas como diagnostico comercial e analise de proposta.

Esse modelo cria tres limitacoes importantes:

- cada ferramenta recebe conhecimento demais e contexto de menos;
- conceitos e instrucoes competem entre si no mesmo prompt;
- um futuro copilot de call ficaria sobrecarregado com texto irrelevante para leitura em tempo real.

## Corpus Fonte

Foram analisados os materiais em `docs/caloni`, com blocos principais de conhecimento:

- desbloqueio mental de vendas;
- fluxo de reuniao de vendas;
- refinamentos avancados de conducao comercial;
- objecoes e negociacao;
- sucesso do cliente;
- padroes de linguagem, frases recorrentes e vocabulario caracteristico.

O corpus deve ser tratado como materia-prima para extracao. A organizacao final nao deve seguir o formato das aulas, e sim a logica de decisao comercial da IA.

## Decisao de Estrutura

A nova base deve usar uma taxonomia hibrida em camadas, com poucos arquivos densos, numerados para manter ordem de concatenacao previsivel:

- `00_identidade_e_principios.md`
- `01_voz_linguagem_e_conducao.md`
- `10_modelo_comercial_caloni.md`
- `11_fluxo_decisao_comercial.md`
- `12_estagios_da_reuniao.md`
- `13_sinais_riscos_e_lacunas.md`
- `20_playbook_reuniao_de_vendas.md`
- `21_playbook_objecoes.md`
- `22_playbook_proposta_e_fechamento.md`
- `23_playbook_customer_success.md`
- `30_biblioteca_objecoes.md`
- `31_biblioteca_perguntas.md`
- `32_biblioteca_intervencoes.md`
- `33_biblioteca_antipadroes.md`
- `40_casos_e_exemplos.md`
- `41_snippets_e_formulacoes.md`
- `99_indice_de_uso.md`

Essa estrutura foi escolhida porque:

- separa doutrina de operacao;
- separa leitura de contexto de formulacao de fala;
- funciona para ferramentas atuais e futuras;
- sustenta um copilot de call sem aprisionar o corpus a um unico caso de uso;
- reduz o risco de duplicar conceitos centrais em varios lugares.

## Papel de Cada Camada

### `00` a `01`: Identidade canonica

Esses arquivos definem:

- quem e o Caloni como referencia comercial;
- como pensa, decide, valoriza e conduz;
- tom de voz, linguagem, vocabulario e limites do estilo;
- frases caracteristicas e o que jamais deve ser feito.

### `10` a `13`: Leitura estrategica

Esses arquivos ensinam:

- como o Caloni enxerga o processo comercial;
- como diagnosticar estagio, prioridade, risco, objecao e lacuna;
- como decidir o proximo movimento sem depender de script pronto.

### `20` a `23`: Playbooks operacionais

Esses arquivos definem:

- o que fazer em contextos comerciais principais;
- como conduzir reunioes, tratar objecoes, fortalecer proposta e operar customer success;
- quais entradas, sequencias e criterios importam em cada caso.

### `30` a `33`: Biblioteca tatica

Esses arquivos organizam:

- objecoes por tipo;
- perguntas por objetivo;
- intervencoes e reenquadramentos;
- erros recorrentes e anti-padroes.

### `40` a `41`: Casos e formulacoes

Esses arquivos preservam:

- exemplos ilustrativos;
- falas curtas;
- formulacoes uteis;
- casos de referencia.

Eles devem servir de apoio, nunca de nucleo interpretativo.

### `99`: Indice de uso

Esse arquivo mapeia:

- o papel de cada documento no corpus;
- orientacoes de manutencao;
- futuros perfis de consumo por ferramenta.

## Contrato Editorial

Cada arquivo deve ser escrito para LLM, nao como material de aula. O contrato editorial por camada e o seguinte.

### Arquivos `00` e `01`

Devem responder:

- quem e o Caloni;
- como ele pensa;
- como conduz;
- que tipo de linguagem usa;
- o que evita;
- que guardrails de estilo devem valer para toda a base.

Formato recomendado:

- principios;
- crencas;
- vocabulario;
- tom e postura;
- frases caracteristicas;
- limites e proibicoes.

### Arquivos `10` a `13`

Devem ensinar a IA a interpretar.

Formato recomendado:

- o que e esse mecanismo;
- por que importa;
- sinais de deteccao;
- leitura estrategica Caloni;
- erro mais comum;
- risco se ignorar;
- decisao recomendada.

### Arquivos `20` a `23`

Devem responder o que fazer agora.

Formato recomendado:

- contexto de uso;
- objetivo;
- entradas esperadas;
- diagnostico do momento;
- sequencia de acao;
- intervencoes recomendadas;
- perguntas ou falas sugeridas;
- o que evitar;
- criterios de boa execucao.

### Arquivos `30` a `33`

Devem funcionar como biblioteca operacional consultavel.

Exemplos:

- objecoes por tipo, sinais, leitura, lacuna do vendedor, intervencao, fala sugerida e fala a evitar;
- perguntas por objetivo de conversa, nao apenas por etapa;
- microintervencoes para corrigir rota em tempo real;
- anti-padroes que enfraquecem a conducao comercial.

### Arquivos `40` e `41`

Devem ilustrar e acelerar resposta, sem dominar a interpretacao.

Regra central:

- primeiro entender;
- depois orientar;
- por ultimo formular.

## Estrategia de Transformacao do Conteudo Fonte

Os PDFs devem ser tratados como fonte, nao como estrutura final.

O processo de curadoria deve:

- extrair principios;
- consolidar frameworks;
- mapear sinais observaveis;
- identificar heuristicas de decisao;
- isolar anti-padroes;
- preservar exemplos com alto valor explicativo;
- reduzir oralidade desnecessaria, repeticao de palco e ruido visual.

Quando o mesmo conceito aparecer em varios materiais:

- ele entra uma vez na camada canonica adequada;
- variantes entram como nuance, exemplo ou aplicacao;
- nao se replica o mesmo bloco em varios arquivos sem necessidade.

Exemplos de conceitos centrais que devem ser consolidados:

- diagnostico antes de solucao;
- a solucao e uma ponte;
- objecao e pedido de ajuda;
- nao sair de reuniao sem combinado;
- desejo como consciencia do problema mais urgencia em resolver.

## Modelo de Saida Prioritaria para o Copilot de Call

O copilot de call deve seguir a prioridade:

1. leitura de contexto;
2. recomendacao estrategica;
3. sugestao curta de fala.

Isso significa que o corpus precisa ensinar a IA a produzir:

- estagio atual da call;
- risco em curso;
- objecao ou sinal detectado;
- lacuna do vendedor;
- objetivo do proximo movimento;
- intervencao recomendada;
- pergunta, frase ou enquadramento curto.

O corpus nao deve ser escrito como repositorio de respostas prontas. A fala e uma camada derivada da leitura e da decisao.

## Modelo de Consumo pelas Ferramentas

A base deve ser unica, canonica e modular. O consumo deve evoluir para perfis especificos por ferramenta.

Exemplos de composicao futura:

- diagnostico comercial: identidade, modelo comercial, fluxo de decisao, sinais, riscos, lacunas e anti-padroes;
- analise de proposta: identidade, modelo comercial, proposta e fechamento, intervencoes e anti-padroes;
- copilot de call: identidade, voz, fluxo de decisao, estagios da reuniao, sinais, riscos, lacunas, playbook de reuniao, playbook de objecoes, biblioteca de perguntas, intervencoes e anti-padroes;
- customer success: identidade, modelo comercial, playbook de CS e sinais relevantes de acompanhamento e ROI.

Enquanto o backend ainda usa `load_caloni_knowledge()` para concatenar tudo, os arquivos devem ser autonomos e bem delimitados. Mas a base precisa nascer pronta para um passo seguinte de carregamento seletivo por perfil.

## Criterios de Qualidade

A base sera considerada bem desenhada se:

- a identidade do Caloni estiver coerente ao longo do corpus;
- a separacao entre doutrina, leitura e acao estiver clara;
- a IA conseguir diagnosticar estagio, risco, objecao e lacuna sem depender apenas de frases prontas;
- os playbooks estiverem orientados a decisao, nao a transcricao;
- a biblioteca tatica acelerar uso operacional sem conflitar com os principios;
- o loader linear atual puder consumir a base sem quebrar;
- a futura composicao por perfis de ferramenta ficar obvia a partir da estrutura.

## Riscos e Mitigacoes

### Risco: virar um repositorio de scripts

Mitigacao:

- priorizar mecanismos de leitura e decisao;
- deixar frases prontas como camada secundaria.

### Risco: manter redundancia herdada das aulas

Mitigacao:

- consolidar conceitos centrais em uma unica camada canonica;
- usar exemplos apenas quando adicionarem nuance real.

### Risco: escrever para a call e empobrecer o resto do sistema

Mitigacao:

- desenhar a base para o universo comercial Caloni;
- tratar o copilot de call como primeiro consumidor prioritario, nao como unico caso de uso.

### Risco: o loader atual incentivar arquivos genericos demais

Mitigacao:

- manter delimitacao editorial forte entre arquivos;
- planejar evolucao futura para composicao seletiva por ferramenta.

## Proxima Etapa

Depois da aprovacao deste design no arquivo escrito, a proxima etapa e criar um plano de implementacao para:

- apagar a taxonomia atual de `knowledge/caloni`;
- criar a nova grade de arquivos;
- curar o conteudo dos PDFs para os novos documentos;
- preparar o backend para, futuramente, carregar recortes por perfil de ferramenta.
