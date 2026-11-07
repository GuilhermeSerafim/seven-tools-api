# Escopo e Prioridades

## Papel no corpus
Este arquivo define como a base deve ser lida pela IA. O objetivo nao e arquivar PDFs nem reproduzir a ordem dos materiais originais; o objetivo e transformar o corpus do Dennis Nakamura em uma base tematica, compacta e pronta para consumo por modelos que vao concatenar os `.md` em sequencia alfabetica. Aqui o valor esta na curadoria: reduzir ruido, consolidar repeticoes e deixar explicita a hierarquia do que tem peso para raciocinio generico.

## Hierarquia de peso
Quando houver conflito, a leitura deve seguir esta ordem de importancia:

1. Nucleo mais forte: vendas, funis, crescimento, escala, gestao financeira, planejamento, lideranca, governanca e voz.
2. Camada de contexto: holdings, patrimonial, CRM e materiais que ampliam repertorio, mas nao definem o metodo.

Se houver conflito entre arquivos, a IA deve preferir o principio mais central e a formulacao mais coerente com o corpus inteiro, nao o trecho mais especifico, recente ou literal. Quando dois arquivos disserem coisas proximas, a leitura deve unificar o criterio sem diluir a hierarquia: metodo acima de contexto, voz acima de enfeite, consolidacao acima de repeticao.

## Regras de leitura para a IA
- Ler esta base como um sistema tematico, nao como uma colecao de PDFs isolados.
- Tratar os arquivos numerados como blocos de conhecimento que se complementam.
- Preferir a formulacao mais consolidada e util, mesmo quando ela tiver sido destilada de varias fontes.
- Usar materiais complementares apenas quando eles adicionarem contexto real ou nuance decisoria.
- Em duvida, favorecer o tema central mais recorrente no corpus em vez do exemplo periferico.
- Se dois trechos entrarem em tensao, a IA deve obedecer a hierarquia de peso deste arquivo antes de tentar conciliar tudo.

## Notas de curadoria
Os PDFs foram organizados tematicamente porque o loader atual consome os arquivos por concatenacao linear; nesse formato, a rastreabilidade por documento vale menos do que a densidade do conhecimento final. A divisao por tema evita repeticao mecanica, permite agrupar conceitos que se reforcam entre si e produz uma base mais util para prompts longos, nos quais a IA precisa manter coerencia de pensamento e nao apenas citar uma origem.

Os temas que devem dominar respostas genericas sao vendas, funis, crescimento, escala, gestao financeira, planejamento, lideranca, governanca e voz. A IA deve tratar esses temas como o centro do raciocinio e usar os anexos apenas quando eles esclarecem um contexto, corrigem uma leitura ou completam uma decisao.

Os anexos existem porque contem contexto util, sinais de autoridade e materias complementares que ajudam a interpretar a trajetoria e o ecossistema, mas eles carregam menos peso interpretativo porque servem ao metodo, nao substituem o metodo. Em caso de divergencia entre um anexo e o corpus principal, o anexo deve ceder salvo se houver motivo claro para entender a excecao como mais especifica e mais forte para aquela resposta.

Material de curadoria especifica:
- `19` e `20` sao duplicados e devem ser tratados como um unico insumo.
- `21` e `22` sao variantes do mesmo material e devem ser unificados por criterio.
- `12` e uma estrutura de metodo, nao uma transcricao literal.
- `14` e `23` ajudam a calibrar autoridade e contexto publico, mas nao devem virar biografia longa nem dominar o corpus.
