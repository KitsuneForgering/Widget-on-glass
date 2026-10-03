# Pesquisa: Liquid Glass para widgets Quickshell

> Atualização de 2026-10-03: a integração Omarchy passou a pedir blur por região com `BackgroundEffect` e a pintar uma borda translúcida no Quickshell. O texto abaixo registra a pesquisa e o plano originais; a decisão de usar `ShaderEffectSource` com gradiente como material dos hosts foi substituída. Veja [implementation.md](implementation.md) para o estado atual e [compositor-refraction.md](compositor-refraction.md) para a investigação da refração do desktop real.

**Data da revisão:** 2026-10-03
**Decisão:** desenvolver um material reutilizável na shell Quickshell e validá-lo primeiro na barra e em um painel real. Refração das janelas do desktop atrás da shell permanece uma capacidade separada, que exige uma fonte de pixels anterior à composição da própria shell.
**Estado da evidência:** análise documental e de código; sem benchmark novo ou integração executada nesta revisão.

## Pergunta e escopo

Como aplicar uma superfície inspirada no Liquid Glass da Apple aos widgets da **shell inteira**, com shader executado na GPU, sem clonar cada plugin? Aqui, “acima dos widgets” significa uma linguagem visual comum ao conjunto de widgets. Na composição de cada controle, o material deve ficar **atrás do texto, ícones e área interativa**. Desenhar uma captura dos widgets por cima deles distorceria o conteúdo e poderia prejudicar a leitura.

O projeto é um protótipo QML/GLSL para Quickshell no Omarchy. A referência inspecionada é o commit `d255288`. No momento da revisão, `LiquidGlass.qml`, `shaders/glass.frag`, `Panel.qml`, `Preview.qml`, testes e a documentação do commit estavam **removidos do diretório de trabalho**; foram lidos com `git show HEAD:<arquivo>`. Esta pesquisa não restaura esses arquivos nem altera a shell instalada. A instalação local oferece Quickshell 0.3.1 e `qsb` 6.11.2. O comando `hyprctl version` não conseguiu acessar o socket nesta revisão, portanto não há confirmação atual do compositor em execução.

Critérios da decisão, definidos antes de qualquer piloto: (1) material comum sem cópia do código de cada widget; (2) conteúdo e interação preservados; (3) fonte de fundo definida sem realimentação; (4) custo mensurado contra o visual atual; (5) fallback opaco e manutenção proporcionais ao ganho visual. O custo de errar inclui texto ilegível, latência perceptível, uso contínuo da GPU e uma arquitetura impossível de manter entre atualizações.

## Hipóteses e evidência que as distinguiria

| Hipótese | Estado atual | Resultado que a enfraqueceria |
|---|---|---|
| H1: `ShaderEffect` e `ShaderEffectSource` bastam para refratar uma fonte QML conhecida | Sustentada pela API do Qt e pelo protótipo do commit; integração geral pendente | Falha visual ou custo excessivo num painel real com fundo animado |
| H2: uma única camada QML pode refratar automaticamente tudo atrás de todas as janelas da shell | Não sustentada: as entradas documentadas não fornecem a cena do compositor anterior a cada superfície | Um protocolo/API comprovado que entregue esse buffer, exclua a própria shell e preserve sincronização |
| H3: integrar nos pontos hospedeiros evita clonar plugins | Sustentada para widgets que passam pelo host da barra; cobertura de painéis com `PanelWindow` próprio ainda exige trabalho | Um widget hospedado que não possa usar o material sem modificar sua implementação |
| H4: a GPU integrada mantém custo aceitável em vários containers | Aberta; há apenas contagem analítica de pixels e texturas | Medição representativa acima do orçamento de quadro ou aumento de energia considerado inaceitável |
| H5: a semelhança visual com a Apple melhora a experiência | Aberta; a Apple descreve propriedades e usos, sem publicar seu shader nem medir preferência destes usuários | Teste comparativo em que blur simples seja preferido ou torne os controles mais legíveis |

## Fundamentos e limites da plataforma

O [`ShaderEffectSource` do Qt](https://doc.qt.io/qt-6/qml-qtquick-shadereffectsource.html) rasteriza um `sourceItem` QML em textura; `live` a atualiza quando a fonte muda. A documentação avisa que isso acrescenta uso de memória de vídeo e normalmente reduz desempenho. Dependência recursiva exige outra textura e, com `live`, pode manter renderização contínua. O [`ShaderEffect`](https://doc.qt.io/qt-6/qml-qtquick-shadereffect.html) aplica o shader à geometria do item; no Qt 6 usa arquivo `.qsb`, e o backend software não executa o efeito. Essas são propriedades da cena Qt, não uma API para ler o framebuffer do compositor.

O [`ScreencopyView` do Quickshell 0.3.1](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/ScreencopyView/) aceita monitor ou janela como `captureSource`, condicionados aos protocolos disponíveis. Sua API não documenta uma captura “todos os pixels atrás desta superfície, excluindo esta superfície”. **Inferência:** uma captura ao vivo de monitor aplicada sobre o próprio monitor pode produzir realimentação ou atraso; seria necessário um experimento específico para saber o comportamento local. Uma captura de uma única janela também não representa todas as superfícies atrás de um painel.

O [`QsWindow` do Quickshell](https://quickshell.org/docs/v0.3.1/types/Quickshell/QsWindow/) oferece `contentItem`, máscara de entrada e escala por janela. Isso ajuda a compor o material **dentro** de cada janela, sem criar uma janela de overlay que cubra toda a tela. A máscara resolve regiões clicáveis; não fornece pixels de fundo. Como a shell Omarchy instalada cria a barra em `/usr/share/omarchy/shell/plugins/bar/Bar.qml:1234` e carrega painéis em `/usr/share/omarchy/shell/shell.qml:1293`, não existe uma árvore visual única que possa ser envolvida por um `ShaderEffectSource`. O slot de cada módulo da barra está em `Bar.qml:1773`; painéis podem criar suas próprias superfícies.

A função GLSL [`refract` da Khronos](https://registry.khronos.org/OpenGL/specs/gl/GLSLangSpec.4.60.html) fundamenta a direção do raio em uma interface idealizada. O shader do commit usa uma normal sintética na borda, `eta = 1/ior` e deslocamento em pixels proporcionado por `thickness × ray.xy / -ray.z` (`shaders/glass.frag:23-42`). `ior`, espessura efetiva, normal e luz são parâmetros artísticos, não medidas do material da Apple. A [apresentação da Apple sobre Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/) sustenta a inspiração em lensing, adaptação, highlights, interação e prioridade de legibilidade; não permite alegar equivalência de implementação.

## Revisão da implementação existente

Fluxo do commit: fundo QML explícito → `ShaderEffectSource` local ou compartilhado → amostragem no shader → superfície arredondada → conteúdo do widget desenhado em primeiro plano. `LiquidGlass.qml:41-56` escolhe a fonte e o recorte; `:72-105` instancia o efeito e a captura; `:108` mantém o conteúdo em um item posterior. `shaders/glass.frag:22-59` calcula máscara, normal, refração, uma amostra de textura, cor e alfa. `Panel.qml:17-32` apresenta apenas o preview em um `PanelWindow`. O manifesto do commit registra esse painel, não uma extensão global da shell.

**Escolhas que fazem sentido:** conteúdo separado do shader; textura compartilhável por vários containers dentro da mesma cena; fallback opaco; limites dos parâmetros; nenhuma dependência gráfica adicional além de Qt/Quickshell. O preview e `tests/render.qml` do commit registram controles ópticos e comparações de imagens, mas os testes não foram repetidos nesta revisão porque os arquivos estão ausentes do diretório de trabalho. Os relatos em `docs/tese.md` são histórico do projeto, não uma nova medição independente.

**Limites confirmados:** `sourcePosition` subtrai `x/y` de irmãos sem transformações (`LiquidGlass.qml:50-56`); não é um mapeamento geral entre itens ou janelas. A fonte local usa margem fixa de 130 px em torno de cada container (`:49-56`), independentemente do deslocamento efetivo. O shader restringe UV a `[0,1]` (`glass.frag:42`), o que pode esticar pixels na borda quando o recorte não cobre uma amostra. `sharedSource` elimina texturas locais duplicadas para uma região QML comum, mas não une as formas nem atravessa janelas Wayland. Estas são limitações de correção ou escala sob certos layouts, não gargalos medidos.

## Modelo algorítmico e de recursos

Sejam `N` containers, `Aᵢ = WᵢHᵢ` suas áreas em pixels lógicos, `D` a escala física por eixo, `F` quadros por segundo, `P` a margem lógica da textura local e `S` amostras de textura por fragmento coberto. O shader atual tem `S = 1` e trabalho aproximado `Θ(D² ΣAᵢ)` por quadro, mais o passe de geração das texturas e a composição. A carga de leituras do passe é aproximadamente `F S D² ΣAᵢ` por segundo. Uma fonte local por container retém pelo menos `4D² Σ(Wᵢ+2P)(Hᵢ+2P)` bytes em RGBA8, sem MSAA, buffers temporários, alinhamento ou cópias. Uma fonte QML compartilhada de área `B` troca essa parcela por aproximadamente `4D²B` bytes, além dos passes separados de cada container. Compartilhar só compensa se a área comum e sua taxa de atualização justificarem o recorte; sua invalidação também pode redesenhar regiões que não mudaram.

Conta local reproduzida nesta revisão com aritmética Python: seis containers de `360×180`, `D=2`, `F=60` geram **93.312.000 fragmentos/s** no passe de efeito. Com `P=130`, seis fontes locais somam **24,98 MiB** em RGBA8; uma região compartilhada de `640×480` usa **4,69 MiB**. São cenários sintéticos do tamanho do preview, não estimativas de milissegundos, consumo elétrico ou memória total. O custo de captura pode dominar: a [orientação de desempenho do Qt](https://doc.qt.io/qt-6/qtquick-performance.html) recomenda medir o pré-render de `ShaderEffectSource` e o shader por pixel.

Prioridades algorítmicas: (1) evitar capturar a mesma região várias vezes; (2) renderizar apenas superfícies visíveis e atualizar fundos estáticos sob demanda; (3) limitar a área capturada com margem derivada do maior deslocamento permitido e uma guarda de filtragem; (4) só então ajustar instruções do shader ou resolução. Uma margem menor sem prova de cobertura troca memória por artefatos. Nenhuma dessas mudanças possui ganho medido neste projeto.

## Arquitetura candidata para a shell inteira

1. Manter **um único material** QML + `.qsb`, com contrato para fonte, geometria, estado de interação, acessibilidade e fallback.
2. Na barra, integrar a camada visual no host da superfície e nos `ModuleSlot` existentes, preservando seus `Loader`, IPC, foco e ordem de desenho. Vários slots da mesma janela podem ler uma textura compartilhada da fonte QML disponível; não devem capturar um ancestral que inclua o próprio vidro.
3. Para painéis, usar um componente hospedeiro comum ao criar novos `PanelWindow` e adaptar os painéis existentes que criam janelas próprias. Alterar só o `Loader` de `shell.qml:1335` não envolve automaticamente o conteúdo visual das janelas criadas pelos plugins. A cobertura da shell deve ser inventariada por **superfície**, incluindo popups e overlays, antes de afirmar que é global.
4. Em cada janela, compor na ordem: fundo conhecido → material refrativo → ícones/texto/controles. Preservar entradas e regiões clicáveis. Se o fundo real não estiver disponível, usar superfície opaca ou visual estilizado explicitamente rotulado como tal.
5. Se a exigência for refratar aplicativos do desktop, investigar uma integração que forneça à shell o buffer pré-composição, junto com coordenadas, escala, sincronização e exclusão da própria superfície. Sem essa prova, não fundar a arquitetura em screencopy. A alternativa nativa de blur do compositor continua o comparador mais simples para esse requisito visual.

Essa arquitetura requer mudanças nos pontos de hospedagem da shell; **não** propõe clonar plugins. Ela também não promete aplicar o material a janelas Quickshell independentes que não adotem o contrato comum. Uma janela de overlay em tela cheia tampouco transforma, por si, seus pixels em uma fonte pré-composição.

## Comparação e plano de validação

| Opção | Fundo do desktop real | Reuso na shell | Custo/risco principal | Decisão |
|---|---|---|---|---|
| Transparência e blur do compositor | Sim, segundo a configuração do compositor | Por superfície/layer | Sem refração geométrica do shader | Baseline |
| Shader QML com fonte conhecida | Apenas fonte fornecida | Alto nos hosts integrados | Captura extra, recorte e cobertura das janelas | **Piloto recomendado** |
| Screencopy de monitor + shader | Captura do monitor | Possível, ainda não demonstrado | Feedback, atraso, exclusão e escala | Não adotar sem experimento discriminante |
| Fonte pré-composição do compositor | Potencialmente sim | Depende da interface com a shell | Desenvolvimento e manutenção do compositor | Pesquisa separada se desktop real for requisito |

**Piloto proposto, ainda não executado:** integrar uma barra e um painel com fundo QML animado; comparar em ordem alternada (A) visual atual/blur, (B) material com captura local e (C) material com captura compartilhada, mantendo geometria, conteúdo, escala e hardware iguais. Medir tempo de quadro p50/p95, uso de memória GPU quando disponível, quadros perdidos, taxa de atualização em repouso, comportamento com 1 e 6 containers e escalas 1 e 2. Registrar GPU, versões, resolução, backend Qt e carga. Critério inicial **escolhido para o piloto**, sujeito a revisão antes dos resultados: acréscimo p95 ≤2 ms a 60 Hz, ausência de feedback/artefatos e texto tão legível quanto no baseline. Testar hover, clique, painéis ocultos, fundos claros/escuros e fallback; verificação de contraste deve incluir os pixels realmente apresentados, conforme [WCAG 2.2, 1.4.6](https://www.w3.org/TR/WCAG22/#contrast-enhanced). Uma captura de screenshot e o teste óptico do shader não substituem essas medições.

Para a hipótese de desktop real, fazer antes uma prova mínima com uma superfície Quickshell e uma janela em movimento atrás dela: verificar se a fonte recebida exclui a própria superfície em todos os quadros, mantém alinhamento sob escala/movimento e não adiciona atraso perceptível. Se qualquer condição falhar, manter essa capacidade fora do escopo QML. Nenhum experimento desse tipo foi executado aqui.

## Decisão de engenharia

| Prioridade | Ação | Evidência e benefício esperado | Verificação |
|---|---|---|---|
| Alta | Restaurar ou localizar a implementação antes de desenvolver; integrar o material no host da barra e em um painel | O commit tem o componente, mas o diretório de trabalho não; o preview não cobre widgets reais | Ambos usam o mesmo componente, sem cópia por plugin |
| Alta | Definir a fonte por janela e impedir dependência recursiva | A API Qt captura apenas `sourceItem`; recursão pode forçar render contínuo | Fundo animado sem feedback; repouso sem atualização desnecessária |
| Média | Substituir a posição por mapeamento correto e limitar o recorte com prova | O cálculo atual pressupõe irmãos sem transformações; margem local custa memória | Testes com deslocamento, escala e bordas sem clamp visível |
| Experimental | Obter fundo pré-composição do compositor | Único caminho identificado para refração confiável do desktop real | Prova mínima com exclusão, sincronização e custo medidos |

**Conclusão condicional:** aplicar o material na shell para fundos QML conhecidos, com piloto e fallback. Não descrever o resultado como refração do desktop real nem como implementação equivalente à Apple. O fator mais capaz de mudar a arquitetura é a existência comprovada de uma fonte pré-composição adequada. A pesquisa examinou o commit, caminhos relevantes da shell instalada e documentação primária de Qt, Quickshell, Khronos e Apple; parou quando a escolha do piloto ficou sustentada. Compatibilidade em outras versões, desempenho e preferência dos usuários continuam abertos.

## Fontes e rastreabilidade

Fontes acessadas em **2026-10-03**. As páginas de Qt abertas nesta revisão descrevem Qt **6.12**, enquanto o `qsb` instalado é **6.11.2**; a correspondência exata do comportamento local exige teste. Datas de atualização das páginas, quando não indicadas, são desconhecidas.

| Origem | Trecho utilizado | Papel e limite |
|---|---|---|
| [Qt, ShaderEffectSource](https://doc.qt.io/qt-6/qml-qtquick-shadereffectsource.html) | Detailed Description; `sourceItem`, `live`, `recursive`, `sourceRect` | Contrato da captura QML e alertas de custo; não mede esta shell |
| [Qt, ShaderEffect](https://doc.qt.io/qt-6/qml-qtquick-shadereffect.html) | Shaders; suporte do backend | Contrato do shader Qt 6; não confirma esta GPU |
| [Qt, Performance](https://doc.qt.io/qt-6/qtquick-performance.html) | Shader Effects | Orientação para medir captura e fragmentos |
| [Quickshell 0.3.1, ScreencopyView](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/ScreencopyView/) | `captureSource`, `live` | Entradas documentadas; ausência de garantia de exclusão é limite documental |
| [Quickshell 0.3.1, QsWindow](https://quickshell.org/docs/v0.3.1/types/Quickshell/QsWindow/) | `contentItem`, `mask`, `devicePixelRatio` | Superfície, entrada e escala por janela |
| [Khronos, GLSL 4.60](https://registry.khronos.org/OpenGL/specs/gl/GLSLangSpec.4.60.html) | função `refract` | Fundamento matemático de uma interface, não do material Apple |
| [Apple, Meet Liquid Glass, WWDC25](https://developer.apple.com/videos/play/wwdc2025/219/) | Dynamics, Adaptivity, Principles | Referência de comportamento visual e legibilidade; não divulga shader interno |
| Omarchy instalado | `shell.qml:1293-1365`; `plugins/bar/Bar.qml:1234-1284,1773-1872` | Evidência local dos pontos de hospedagem; pode mudar com atualização |
| Commit `d255288` | `LiquidGlass.qml`, `shaders/glass.frag`, `Panel.qml`, `tests/render.qml`, `docs/tese.md` | Implementação e testes históricos; arquivos ausentes da árvore de trabalho atual |
