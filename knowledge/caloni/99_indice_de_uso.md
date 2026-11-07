# Indice de Uso

## Papel no corpus
Este arquivo e o mapa editorial do corpus. Ele explica para que cada documento existe, em que combinacoes eles costumam ser mais uteis e quais limites de manutencao preservam a base coerente. Quando surgir duvida sobre onde colocar um conceito, uma frase ou um exemplo, este arquivo deve decidir antes do impulso de duplicar.

## Mapa dos arquivos
- `00_identidade_e_principios.md`: canon filosofico. Define o que e venda, o que e ajuda, quais eixos importam e o que jamais deve acontecer.
- `01_voz_linguagem_e_conducao.md`: tom, vocabulario e postura. Explica como o metodo soa e como conduz sem transformar voz em script.
- `10_modelo_comercial_caloni.md`: mecanica do metodo. Guarda a sequencia diagnostico -> prioridade -> valor -> objecao -> decisao.
- `11_fluxo_decisao_comercial.md`: logica de leitura em tempo real. Ensina a IA a escolher o proximo movimento antes de formular fala.
- `12_estagios_da_reuniao.md`: mapa dos estagios da call. Serve para detectar onde a conversa esta e o que falta para avancar.
- `13_sinais_riscos_e_lacunas.md`: leitura de sinais do lead, riscos da call e erros do vendedor. E a lente rapida de diagnostico.
- `20_playbook_reuniao_de_vendas.md`: execucao da reuniao comercial ponta a ponta. Usa os principios anteriores sem reensina-los.
- `21_playbook_objecoes.md`: processo operacional para antecipar, acolher, reenquadrar, isolar e neutralizar objecoes.
- `22_playbook_proposta_e_fechamento.md`: momento da proposta, ancoragem, condicoes e saida com decisao.
- `23_playbook_customer_success.md`: onboarding, acompanhamento, touch points, progresso e ROI cedo no pos-venda.
- `30_biblioteca_objecoes.md`: familias de objecao por leitura, causa provavel, objetivo e intervencao.
- `31_biblioteca_perguntas.md`: perguntas por objetivo conversacional. E uma biblioteca de efeitos, nao o banco canonico de frases.
- `32_biblioteca_intervencoes.md`: reenquadramentos, microcorrecoes e movimentos curtos de recuperacao de call.
- `33_biblioteca_antipadroes.md`: taxonomia de erros recorrentes e direcoes curtas de correcao.
- `40_casos_e_exemplos.md`: cenas concretas de reuniao, objecao, recuperacao e pos-venda com explicacao do por que funcionam.
- `41_snippets_e_formulacoes.md`: casa canonica das falas curtas e formulacoes recorrentes. Sempre preferir este arquivo para ownership de frase.
- `99_indice_de_uso.md`: este mapa editorial.

Ordem de leitura humana recomendada:
1. `00`, `01`
2. `10`, `11`, `12`, `13`
3. `20`, `21`, `22`, `23`
4. `30`, `31`, `32`, `33`
5. `40`, `41`
6. `99` para manutencao ou onboard de quem vai editar o corpus

## Sugestoes de consumo por ferramenta
- Copilot de call em tempo real:
  Prioridade alta para `00`, `01`, `11`, `12`, `13`, `20`, `21`, `31`, `32`, `33`, `41`.
  Uso tipico: ler contexto da call, diagnosticar gargalo, sugerir proximo movimento e so depois oferecer fala curta.

- Diagnostico comercial pos-call:
  Prioridade alta para `00`, `10`, `11`, `12`, `13`, `20`, `21`, `33`, `40`.
  Uso tipico: resumir estagio da conversa, riscos, lacunas do vendedor, qualidade da conducao e oportunidades perdidas.

- Analise de proposta e fechamento:
  Prioridade alta para `00`, `10`, `11`, `21`, `22`, `30`, `32`, `33`, `41`.
  Uso tipico: revisar se houve valor suficiente antes do preco, se a oferta entrou cedo demais e qual formulacao pode mover a decisao.

- Ferramenta de tratamento de objecoes:
  Prioridade alta para `00`, `10`, `11`, `21`, `30`, `32`, `33`, `40`, `41`.
  Uso tipico: classificar objecao, distinguir fumaca de causa e sugerir intervencao proporcional.

- Customer success e acompanhamento:
  Prioridade alta para `00`, `10`, `11`, `13`, `23`, `40`.
  Uso tipico: definir onboarding, touch points, plano de acao, sinais de risco e oportunidades de ROI cedo.

- Assistentes generalistas ou loaders lineares:
  Consumir o corpus inteiro na ordem alfabetica atual, mas respeitando a hierarquia editorial implicita: identidade e leitura mandam mais do que snippets.

## Regras de manutencao
- Regra de ownership:
  Principios canonicos moram em `00` e `10`.
  Logica de leitura e decisao mora em `11`, `12` e `13`.
  Procedimento operacional mora em `20` a `23`.
  Bibliotecas taticas moram em `30` a `33`.
  Casos moram em `40`.
  Frases recorrentes e snippets moram em `41`.

- Regra contra duplicacao:
  Se a ideia ja existe em outro arquivo, so repetir quando o novo arquivo precisar ficar autonomo ou quando houver um angulo tatico realmente diferente.
  Nao copiar blocos inteiros de principios entre `00`, `10` e `20`.
  Nao espalhar a mesma frase em `31`, `32` e `41`; em caso de duvida, `41` vence.
  Nao transformar `21` e `33` no mesmo arquivo com nomes diferentes; `21` explica processo, `33` nomeia erros.

- Regra de escrita:
  Escrever para LLM, com prosa densa e curada.
  Evitar aula, transcricao, teatralidade e listas de bordoes sem funcao.
  Priorizar leitura -> decisao -> formulacao, nessa ordem.

- Regra de extensao:
  Antes de criar arquivo novo, tentar encaixar o conteudo numa camada existente.
  Se surgir um novo consumidor do corpus, atualizar primeiro este indice com a composicao recomendada antes de espalhar instrucoes pelos outros arquivos.
