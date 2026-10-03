# Tese: containers refrativos para widgets no Omarchy

**Conclusão:** vale um piloto aberto para autores de shells Quickshell e usuários
que personalizam o Omarchy. A matemática e a renderização do componente com
fonte explícita foram verificadas. Refração do desktop real e interesse de uso
continuado permanecem hipóteses. A proposta é permitir que widgets existentes
ganhem uma superfície refrativa opcional, com adoção simples e custo aceitável
na GPU integrada. Não há objetivo comercial declarado.

Pesquisa em 2026-10-03: três frentes — APIs/texturas, alternativa no compositor,
e projetos comparáveis — com aprofundamentos nas fontes decisivas. Paramos
quando a escolha do protótipo ficou sustentada; mais buscas não substituem
medições de hardware ou usuários. Não foi uma revisão exaustiva.

## Hipóteses e mecanismos

**H1 — Shader QML basta para uma fonte conhecida.** Qt Quick fornece shader
customizado e renderização de itens em textura. Qt 6 usa shaders pré-compilados
por `qsb`; o backend software não renderiza `ShaderEffect`. Essa é a fundação
da implementação, sem biblioteca gráfica adicional.
[Qt: ShaderEffect](https://doc.qt.io/qt-6/qml-qtquick-shadereffect.html),
[Qt: ShaderEffectSource](https://doc.qt.io/qt-6/qml-qtquick-shadereffectsource.html).

**H2 — O mesmo shader consegue obter sozinho o fundo do desktop.** Não foi
sustentada. `ShaderEffectSource` recebe um item QML; não é acesso ao framebuffer
do compositor. `ScreencopyView` aceita monitor ou janela, condicionado aos
protocolos disponíveis, mas não documenta uma fonte “tudo atrás deste painel,
excluindo o próprio painel”. Inferência: captura de monitor apresentada sobre
ele pode realimentar a própria imagem. Não executamos esse experimento.
[Quickshell: ScreencopyView, captureSource](https://quickshell.org/docs/v0.2.0/types/Quickshell.Wayland/ScreencopyView/).

**H3 — Há interesse no material entre usuários de shells Linux.** Há sinais
indiretos: configurações Quickshell para Omarchy com efeitos GLSL e outro
projeto com opções de vidro no overview. Isso evidencia oferta e experimentação;
não mede preferência, retenção ou procura pelo nosso componente. Vidro com
tint/blur também não prova procura por refração.
[bjarneo/quickshell](https://github.com/bjarneo/quickshell),
[quickshell-overview: efeitos](https://github.com/Shanu-Kumawat/quickshell-overview#readme).

**H4 — GPU integrada comporta vários containers.** Ainda depende de benchmark.
GPU executa o shader, mas captura, resolução, quantidade de passes e área
afetada podem dominar o custo. “Acelerado por GPU” não implica baixo consumo.

## Fundamento óptico e modelo implementado

A fundação é a função vetorial `refract` especificada pela Khronos, equivalente
a Snell para uma interface. Entradas: vetor incidente `I` e normal `N`
normalizados; `eta = n_entrada / n_saida`, adimensional. O teste compara a
fórmula vetorial com `n₁ sin(θ₁) = n₂ sin(θ₂)`. Para incidência de 30°,
`n₁=1` e `n₂=1,5`, o cálculo local resulta em 19,47°.
[Khronos: refract, Description](https://raw.githubusercontent.com/KhronosGroup/OpenGL-Refpages/main/gl4/refract.xml).

No shader, a distância a um retângulo arredondado define uma normal inclinada
nas bordas. A direção refratada `R` produz o deslocamento
`Δuv = t × R.xy / (-R.z) / tamanho_da_textura`, com `t` em pixels lógicos.
Um pixel do interior plano tem normal `(0,0,1)` e deslocamento zero. O padding
preserva amostras além da borda; o componente limita os parâmetros utilizados.

**Premissas assumidas:** câmera ortográfica, uma interface sintética, inclinação
artística e distância efetiva ajustável. `ior=1,5` é um parâmetro escolhido,
não uma medição de material. Fresnel usa a aproximação de Schlick. Tint é
misturado diretamente na cor amostrada, sem transporte espectral. Isso não
simula um volume de vidro com duas interfaces, absorção e cáusticas. Não há
alegação de equivalência ao material proprietário da Apple.

## Comparação com o Liquid Glass da Apple

**Resultado da revisão:** a aplicação é parcialmente similar no lensing e na
separação entre fundo e controles. O protótipo agora tem textura compartilhada,
iluminação direcional, adaptação local e interpolação de tamanho/raio. Ainda
não demonstra equivalência ao material completo ou às transições da Apple. A aplicação
recomendada é um grupo de controles flutuantes, com o conteúdo abaixo intacto;
não transformar toda informação de cada widget em vidro.

A descrição oficial diferencia um material Regular adaptativo de um Clear
mais transparente, com dimming e requisitos de legibilidade. A Apple descreve
highlights, sombras adaptativas, resposta à interação e ajustes de acessibilidade.
[Apple, Meet Liquid Glass: 1:29, 6:00 e 10:31](https://developer.apple.com/videos/play/wwdc2025/219/).

| Critério observado na Apple | Este protótipo | Avaliação |
|---|---|---|
| Lensing que define a forma | Snell sobre normal sintética de borda | Similaridade de mecanismo visual, sem equivalência do shader |
| Controles acima do conteúdo | Conteúdo do widget desenhado após o efeito | Separação compatível no preview |
| Fundo amostrado além da forma | Recorte QML com margem | Compatível para fonte explícita; desktop real pendente |
| Amostragem compartilhada entre elementos agrupados | `sharedSource` usado pelos dois containers do preview | Região única; sem união de formas |
| Material Regular adaptativo | Luminância modula tint e sombreamento de borda | Adaptação local simples; sem troca automática de glyphs |
| Highlights e sombras dependentes do contexto | Luz direcional e bordas escuras/claras conforme o fundo | Sem sombra projetada ou luz ambiente da cena |
| Feedback e morphing | Hover/pressão iluminam bordas; Qt interpola tamanho/raio | Transição de uma forma; sem fusão entre containers |
| Acessibilidade do material | Modo opaco, contraste/transparência e movimento reduzido explícitos | Sem integração automática com o sistema |

O `GlassEffectContainer` documentado pela Apple compartilha a região de
amostragem e permite transições entre formas. Nosso `sharedSource` cobre a
primeira função; a segunda ainda não foi implementada entre elementos distintos.
[Apple, Build a SwiftUI app with the new design: 17:57–21:31](https://developer.apple.com/videos/play/wwdc2025/323/).

Nas fontes examinadas, a Apple apresenta comportamento e APIs, sem fornecer
o shader ou parâmetros ópticos internos. Portanto, usar Snell não prova que
estamos usando os cálculos da Apple. Acesso à transcrição das duas sessões foi
completo; a página de API exigiu JavaScript e sua versão Markdown não pôde ser
obtida. Não tratamos essa página como documentação lida.

**Aplicação proposta para a próxima prova:** comparar um grupo de controles
sobre imagem e conteúdo em movimento, com fonte explícita, usando três
condições: blur nativo, protótipo refrativo e referência visual Apple. Avaliar
reconhecimento de controles, leitura de labels e preferência após uso. A
referência visual pode orientar aparência, mas não validar o algoritmo interno.
Esse estudo ainda não foi executado; nenhuma pontuação de “fidelidade Apple”
foi atribuída.

## Revisão anti-ai-mediocrity: falhas materiais

1. **Escopo ainda incompleto para o desktop real:** `LiquidGlass.sourceItem`
   recebe um irmão QML. `Panel.qml` apenas hospeda o preview; não converte os
   widgets da shell existente. Mantemos essa limitação explícita, e a prova de
   compositor continua necessária antes de apresentar o projeto como pronto.
2. **O teste anterior aceitava uma causa alternativa:** `padding` variava junto
   de `thickness`; uma mudança de rasterização poderia passar na comparação
   de pixels. Corrigimos para margem fixa e acrescentamos o controle `ior=1`:
   mudar a espessura deve resultar em imagens idênticas quando não há diferença
   entre índices de refração. O teste passou na sessão Wayland/OpenGL.
3. **Conteúdo podia ultrapassar o vidro:** a altura fixa de 220 px no primeiro preview
   não acompanhava a soma das alturas dos controles e espaçamentos. Agora o
   revisão derivou a altura de `controls.implicitHeight + 48`. O preview atual
   separa os ajustes externos e os botões nos cantos para deixar o item ao fundo
   visível no centro do vidro.
4. **Fallback tinha pouca evidência:** agora fonte ausente e efeito desligado
   são comparados graficamente e produzem o mesmo container opaco. As novas
   flags de acessibilidade são explícitas; não são apresentadas como detecção
   das configurações do sistema.
5. **Demanda e custo continuam sem observação real:** os números do piloto
   são escolhas e cenários, não mercado medido. A contagem de fragmentos
   exclui o passe de textura; agora também mostramos o custo da margem fixa.
   Esses limites impedem concluir que há demanda ou ganho energético.

## Alternativas sob os mesmos critérios

| Caminho | Fundo real | Integração/manutenção | Decisão |
|---|---|---|---|
| Transparência + blur nativos | Compositor mistura o fundo | Recursos já disponíveis | Baseline para comparar preferência e custo; não oferece esta refração |
| Shader QML com fonte explícita | Só a textura fornecida | QML + `qsb`; container por widget | Protótipo atual; útil para cenas e widgets com fundo conhecido |
| Captura de monitor + shader | Imagem capturada do monitor | Protocolos, latência, alinhamento e possível feedback | Não adotar sem demonstrar exclusão da própria superfície |
| Plugin de compositor existente | Segundo o projeto, amostra o framebuffer anterior à superfície | Acesso correto ao fundo; depende da ABI do Hyprland | Candidato para testar o desktop real |

O projeto `hyprland-liquid-glass` descreve suporte a layers por namespace e
avisa que precisa ser recompilado quando o Hyprland muda. Também pula overlays
fullscreen. São alegações documentais, sem teste local ou auditoria do C++.
Um layer retangular não identifica automaticamente cada container dentro dele;
containers independentes e overlays precisam de prova específica. Portanto,
reusar esse plugin pode resolver painéis inteiros, mas não está demonstrado
que resolve qualquer grupo de widgets.
[Hyprland Liquid Glass: Requirements e Layer Shell Surfaces](https://github.com/0xdilo/hyprland-liquid-glass#readme).

**Observações locais:** Omarchy 4.0.4-1, Quickshell 0.3.1, Qt 6.11.2 e Hyprland
0.56.2. A configuração pessoal já habilita blur com `size=4`, `passes=2`; o
comentário nela cita Intel Iris Xe, sem inventário de GPU independente.
A barra usa `omarchy-bar`, não o namespace padrão `quickshell` do candidato.
O registry instalado já suporta plugins, hot reload e painéis sob demanda.
Essas observações vieram do código/configuração local, não de uma promessa
de compatibilidade para outras versões. Nenhuma configuração do desktop foi alterada.

## Escala e custo: contas, não benchmark

Para `N` containers, área lógica `W×H`, escala `D`, frequência `F` e `S`
amostras por fragmento, a carga aproximada do passe de efeito é
`N × W × H × D² × F × S`. Ela exclui o passe de geração da textura, padding,
composição, blur e caches; não deve ser convertida diretamente em milissegundos.

| Cenário sintético escolhido | Fragmentos/s | Leituras/s com 1 amostra | Com 3 amostras |
|---|---:|---:|---:|
| 6 containers 360×180, 60 Hz, escala 1 | 23 milhões | 23 milhões | 70 milhões |
| Mesmo cenário, escala 2 | 93 milhões | 93 milhões | 280 milhões |

O protótipo usa **uma** amostra de textura por fragmento coberto. Três amostras
são um cenário futuro de dispersão cromática, não o código atual. RGBA8 ocupa
7,91 MiB por textura 1920×1080 e 31,64 MiB em 3840×2160, sem buffers extras.
São contas locais reproduzíveis em `python3 tests/check.py`.

O preview atualizado usa uma textura compartilhada de todo o fundo: na área
lógica 640×480, RGBA8 ocupa 1,17 MiB na escala 1 e 4,69 MiB na escala 2,
independentemente do número de containers que leem essa fonte. Os passes de
efeito continuam individuais e a área compartilhada inteira participa do passe
de captura. Isso reduz duplicação, sem provar economia de tempo ou energia.

Após a revisão, o recorte tem 130 px de margem fixa por lado. Um container
360×180 gera uma fonte 620×440: 272.800 pixels, cerca de 4,2 vezes a área do
efeito, e 1,04 MiB por textura RGBA8 na escala 1. Seis fontes na escala 2
ocupam aproximadamente 25 MiB, excluindo outros buffers. O cálculo é
`(W+2P) × (H+2P) × D² × 4 bytes`, com `P=130 px`. Esse é o custo de manter o
recorte estável para o intervalo inteiro de espessuras. Não há benchmark de
alocação ou banda de memória; uma margem menor exigiria derivar e testar o
deslocamento máximo suportado antes de adotá-la.

## Público e prova de desejabilidade

Beneficiários iniciais: autores de plugins Quickshell que querem reaproveitar
o material e usuários Omarchy que aceitam experimentar aparência. Não sabemos
quantos são alcançáveis. Stars, screenshots e projetos semelhantes não são uma
estimativa de usuários ativos. O resultado desejado é uso voluntário mantido,
com legibilidade e desempenho preservados.

Proponho **20 participantes por 14 dias**, como escolha para uma primeira
decisão, não previsão de demanda. Cenários ilustrativos:

| Cenário | Pessoas que experimentam | Fração hipotética que mantém após 14 dias | Pessoas retidas |
|---|---:|---:|---:|
| Conservador | 10 | 30% | 3 |
| Base | 20 | 50% | 10 |
| Ambicioso para o piloto | 30 | 70% | 21 |

Fórmula: retidos = participantes × fração que mantém. A retenção é o maior
desconhecido; entrevistar usuários após comparar blur simples e refração é
mais informativo que acumular downloads. A janela de 14 dias testa apenas
interesse inicial, sem demonstrar retenção longa. Não contatamos ninguém.

| Prova proposta | Evidência mínima / recurso escolhido | Regra de decisão |
|---|---|---|
| Desejabilidade | 20 voluntários; baseline e refração; feedback ao instalar e no dia 14; até 2 semanas de calendário | Expandir se ≥10/20 mantêm por preferência de uso; investigar motivos se <5/20 |
| Viabilidade gráfica | GPU integrada e dedicada, 3 configurações no total; 1 e 6 containers, escala 1 e 2; reserva estimada de 1–3 dias de medição | Mirar acréscimo p95 ≤2 ms a 60 Hz, sem falhas de alinhamento/feedback |
| Reuso | Dois autores externos integram em widgets diferentes; medir tempo e intervenções do mantenedor | Mirar integração em ≤30 min; revisar API se exigir patches específicos na shell |
| Sustentabilidade | Acompanhamento semanal manual por 4 semanas; envelope escolhido ≤2 h/semana de suporte | Reduzir matriz suportada ou redesenhar se manutenção exceder esse envelope repetidamente |

O mantenedor registra manualmente participantes, falhas, tempo de instalação
e uso no dia 14; usuários escolhem relatar esses dados. Nos testes técnicos,
registrar hardware, versões, resolução, carga, aquecimento e baseline; alternar
baseline/efeito, repetir três séries e medir frame time e energia por 10 min
por condição. O limite de energia inicial escolhido é ≤10% de aumento sobre
o baseline equivalente, com incerteza de medição registrada. Nada disso foi
executado como benchmark nesta entrega.

Guardrails: modo opaco acessível, texto sem deformação, widgets ocultos sem
captura contínua, preferência por movimento reduzido e legibilidade em fundos
claros/escuros. A recomendação de aplicar o material com parcimônia e responder
a configurações de acessibilidade vem também das diretrizes da Apple; é uma
referência de design, sem prova de qualidade deste protótipo.
[Apple: Materials, Liquid Glass](https://developer.apple.com/design/human-interface-guidelines/materials).

## Verificação realizada e pendências

**Implementação atual para legibilidade do fundo:** `preserveBackground=true`
remove tint, iluminação e refração do centro plano. O efeito de borda usa
luminância da amostra para ajustar tint e sombra, com highlight direcional e
feedback de hover/pressão. Não há blur ou amostras adicionais. `sharedSource`
permite dois containers lerem a mesma textura sem recortes duplicados.
As transições de largura/altura/raio usam `Behavior` do Qt, e `reducedMotion`
as desativa. A fonte continua explícita; essas mudanças não capturam o desktop.

Para texto de primeiro plano, `contentColor` deve acompanhar `contentPlateColor`:
os pares opacos atuais medem 14,75:1 e 15,83:1, acima dos 7:1 do critério
1.4.6 AAA da [WCAG 2.2](https://www.w3.org/TR/WCAG22/#contrast-enhanced).
Nos fallbacks, a seleção considera a cor efetivamente desenhada. Isso verifica
esses pares e o preview, não conformidade WCAG AAA do plugin ou da shell inteira;
texto sobre vidro sem placa ainda depende do fundo real e precisa ser avaliado.
No preview, `Text.Sunken` acrescenta uma sombra nativa e discreta aos itens sob o
vidro. `contentRefraction` aplica uma normal radial suave, com padrão zero e
valor demonstrativo 0,45; isso desloca a imagem de fundo sem rasterizar texto
novo nem aplicar blur. A captura compara o interior com a refração desativada.

**Testes atuais executados em Wayland/OpenGL:** 200×80 pixels com o texto ao
fundo foram idênticos à referência sem vidro, com fonte local e compartilhada,
em fundos branco e escuro. Feedback de pressão alterou as bordas e preservou
o mesmo recorte. O controle `ior=1` e os fallbacks passaram. Uma sonda durante
a transição confirmou largura intermediária; com movimento reduzido a largura
mudou imediatamente. Isso demonstra preservação de pixels nos cenários
sintéticos testados, sem provar uma melhoria de leitura em usuários reais.

Durante a implementação, a comparação com a referência revelou uma falha
de amostragem: um uniform chamado `textureSize` conflitava com o nome da
função GLSL e foi renomeado para `sourceExtent`. O teste passou após a correção.
O teste óptico também exige deslocamento exatamente zero para `ior=1`,
evitando resíduos de precisão de ponto flutuante. Esses controles permanecem
executáveis em `tests/render.qml` e `tests/check.py --render`.
O preview Quickshell atualizado carregou por 3 s sem erro de QML/shader,
mantendo o aviso de registro de portal previamente observado.

As verificações abaixo registram as etapas anteriores do protótipo.

**Executado localmente:** `make check` compilou com `qsb`, validou manifesto
via Omarchy, passou `qmllint` e verificou Snell vetorial/escalar, vetores
unitários e reflexão interna total. O teste numérico valida o modelo de
referência; não executa a instrução GLSL diretamente.

**Executado graficamente:** `tests/render.qml` na sessão Wayland com API
OpenGL comparou espessuras 0 e 80 px. As imagens diferiram nas bordas e o
recorte central 16×16 permaneceu igual. `tests/check.py --render` verificou
esses critérios com ImageMagick. A inspeção visual confirmou a máscara e o
fundo. A demo Quickshell carregou por 3 s e foi encerrada por timeout; houve
um aviso de registro de app no portal, sem erro de QML/shader.

**Revisão gráfica adicional:** seis imagens cobriram refração com espessuras
0/80, controle com `ior=1` e os fallbacks desligado/sem fonte. O centro com
texto permaneceu igual, a borda mudou com refração, o controle óptico produziu
imagens idênticas e os dois fallbacks também. Essa evidência é mais forte que
apenas detectar alguma diferença de pixels, mas não prova fidelidade Apple.

**Não executado:** instalação dentro da shell Omarchy, plugin externo de
compositor, benchmark de tempo/energia, pesquisa com usuários e matriz de GPUs.
O Qt offscreen desta máquina selecionou software; forçar OpenGL/Vulkan nesse
modo não produziu contexto funcional. A prova gráfica foi feita na sessão
Wayland e não deve ser relatada como teste headless bem-sucedido.

Próxima evidência decisiva: um painel real com fundo em movimento, sem feedback,
na GPU integrada, comparado ao blur atual. Se o requisito permanecer
“containers independentes dentro de qualquer widget”, verificar primeiro se
o compositor consegue receber a geometria de cada container; a documentação
do candidato só estabelece superfícies/layers. Se isso exigir manter um fork
amplo do compositor antes de haver preferência de usuários, reduzir o piloto
a painéis inteiros. Se os usuários preferirem o baseline, manter o componente
como experimento visual sem expandir para toda a shell.

## Registro das fontes

Todas acessadas em 2026-10-03. Datas de atualização/publicação não disponíveis
nos trechos consultados ficam **desconhecidas**. Fontes de terceiros descrevem
seus próprios projetos; não foram consideradas benchmarks independentes.

| Instituição/autor | Documento e localização lida | Versão/data conhecida | Limite |
|---|---|---|---|
| Qt | ShaderEffect: Shaders; ShaderEffectSource: Detailed Description, sourceItem | Documentação online 6.12; local 6.11.2; atualização desconhecida | Uso confirmado apenas na versão local |
| Quickshell | ScreencopyView: captureSource, live | Docs v0.2.0; local 0.3.1; atualização desconhecida | Não garante exclusão da própria superfície |
| Khronos | refract: Description, linhas 62–79 do XML | Copyright 2011–2014; revisão desconhecida | Matemática de uma interface |
| 0xdilo | README: Requirements, Layer Shell Surfaces, Performance Notes | Branch main; atualização desconhecida | Só documentação; shader/C++ não auditados |
| bjarneo | README: tabela de módulos GLSL/Omarchy | Branch main; atualização desconhecida | Oferta, sem métricas de adoção |
| Shanu-Kumawat | README: opções glassMode/glassTintStrength | Branch master/main conforme página; atualização desconhecida | Vidro estilizado, sem prova de demanda por refração |
| Apple | Materials: Liquid Glass e variantes/acessibilidade | Revisão desconhecida | Referência de design para plataformas Apple |
| Apple, equipes de design/SwiftUI | Transcrições WWDC25/219 e /323, capítulos Dynamics, Adaptivity, Principles e Liquid Glass effects | WWDC 2025; atualização desconhecida; acessadas em 2026-10-03 | Comportamentos/APIs, sem shader interno; API HTML/Markdown inacessível nesta revisão |
| Omarchy local | shell/README.md, PluginRegistry, Bar.qml; guia plugins.md | Pacote 4.0.4-1 | API e namespaces desta instalação |
