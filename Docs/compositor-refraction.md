# Refração do desktop real: investigação e decisão

**Revisão:** 2026-10-03. **Sistema examinado:** Hyprland 0.56.2 (`efb5099`), Quickshell 0.3.1 e Omarchy instalado em `/usr/share/omarchy`. **Decisão:** aplicar agora blur delimitado pelo compositor; manter a refração geométrica como trabalho do renderizador do Hyprland. O material do adaptador continua uma aproximação, não o Liquid Glass da Apple.

## Pergunta, hipóteses e critério

O efeito desejado deve deslocar **pixels reais de janelas e wallpaper atrás** de cada widget, sem incluir o próprio widget na fonte, preservar texto/ícones nítidos e custar pouco quando nada muda. Uma prova mínima exige: padrão de referência atrás de uma barra, deslocamento mensurável desse padrão apenas na borda do cartão, centro estável, ausência de cópias recursivas e alinhamento correto com escala 1 e fracionária. Aceitar apenas um gradiente QML ou uma captura com atraso não atende ao critério.

| Hipótese | Predição discriminante | Resultado documental/local |
|---|---|---|
| `ShaderEffectSource` lê o desktop | Uma fonte QML incluiria janelas externas atrás da shell | Falsa pelo contrato: a fonte é um `sourceItem` da cena Qt. [Qt](https://doc.qt.io/qt-6/qml-qtquick-shadereffectsource.html) |
| `ScreencopyView` fornece o buffer anterior à própria shell | A API garantiria captura sem a shell ou ofereceria um modo pré-composição | Não documentado; aceita monitor ou toplevel. Capturar o monitor ao vivo pode realimentar o efeito. [Quickshell](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/ScreencopyView/) |
| `no_screen_share` remove a shell da captura e revela o fundo | A área da shell seria transparente na captura | Contrariada pela especificação: a camada ocultada é substituída por preto. [Hyprland, layer rules](https://wiki.hypr.land/configuring/core/rules/layer-rules/) |
| `ext-background-effect-v1` permite refração | O protocolo devolveria pixels ou aceitaria shader/deslocamento | Falsa: expõe somente uma região de **blur** cuja técnica é política do compositor. [Protocolo](https://wayland.app/protocols/ext-background-effect-v1) |
| Um plugin Hyprland pode mudar o estágio de renderização | Haveria uma extensão de shader estável para uma layer | Não encontrada na API 0.56.2; a API documenta hooks de função sem estabilidade garantida. [Hyprland 0.56, desenvolvimento](https://wiki.hypr.land/0.56.0/Plugins/Development/Advanced/), [API](https://github.com/hyprwm/Hyprland/blob/v0.56.2/src/plugins/PluginAPI.hpp) |

O modelo de composição explica o limite: um fragment shader QML recebe a textura de um item Qt; a imagem composta atrás de uma layer está no renderizador do compositor. Para aplicar `uv' = uv + d(normal, espessura, IOR)` aos pixels corretos, o shader precisa executar **antes de compor a layer**, amostrando uma cópia válida do framebuffer anterior. A região, o raio e a opacidade da layer devem mascarar o resultado; conteúdo do widget é então desenhado por cima. Esse é um desenho de arquitetura inferido das APIs, não uma implementação comprovada.

## Alternativas comparadas

| Caminho | Desktop real | Refração geométrica | Custo e limite |
|---|---|---|---|
| `BackgroundEffect.blurRegion` + shader QML de borda | Sim, atrás da região | Não | API existente, custo restrito à região; escolhido como etapa aplicável |
| Screencopy de monitor + shader QML | Captura final | Possível, mas com realimentação/latência | Não oferece o buffer pré-layer exigido; rejeitado para integração geral |
| Plugin com hook privado no Hyprland 0.56.2 | Sim | Potencial | ABI e símbolos internos instáveis; um erro pode derrubar a sessão. Só justificável em sessão Hyprland aninhada e após protótipo medido |
| Patch do renderizador Hyprland ou API upstream | Sim | Sim, em princípio | Maior trabalho e manutenção; caminho correto para a propriedade óptica requerida |
| Variantes `acrylic` de documentação mais nova | Sim | Documentação descreve refração | `hyprctl getoption decoration:blur:variant` respondeu `no such option` em 0.56.2; indisponível aqui. [Configuração atual](https://wiki.hypr.land/configuring/core/config-options/) |

## O que foi aplicado e testado localmente

O adaptador Omarchy passou a usar [`BackgroundEffect.blurRegion`](https://quickshell.org/docs/v0.3.1/types/Quickshell.Wayland/BackgroundEffect/) em cada janela integrada. Barra usa sua área de janela; `KeyboardPanel`, menu, clipboard, emojis e OSD usam a geometria do cartão; notificações usam a coluna. Isso remove as regras globais de blur e o ajuste artificial da opacidade do véu dos menus. O shader `GlassOverlay` desenha a base atrás do conteúdo e um reflexo de borda acima.

**Execução local:** `bash build.sh` passou; `apply.py` foi aplicado sem erro a uma cópia temporária de `/usr/share/omarchy/shell`; uma janela Quickshell mínima com `BackgroundEffect.blurRegion` e `GlassOverlay` carregou por dois segundos na sessão Wayland. `hyprctl version` confirmou 0.56.2, `hyprctl getoption decoration:blur:enabled` retornou `true`, e `hyprctl getoption decoration:blur:variant` retornou `no such option`. Os headers locais incluem `BackgroundEffect.hpp`. Esses resultados confirmam API e carregamento, **não** a aparência final ou a refração geométrica.

**Próxima prova para refração real:** em um Hyprland aninhado da mesma versão, instrumentar um estágio de renderização pré-layer; usar padrão quadriculado em janela móvel, comparar imagem sem efeito/com efeito, medir deslocamento da borda, preservação de centro, latência e p95 de quadro. Só depois integrar à sessão Omarchy. Não carregar um hook experimental no compositor da sessão principal para descobrir se o desenho funciona.

O trabalho parou no limite verificável da API de aplicação. A observação que mudaria a decisão seria uma API estável do compositor que forneça refração por região ou um protótipo de renderizador aninhado que satisfaça o critério acima. A Apple descreve lensing, adaptação e fusão, mas não publica o shader interno; mesmo uma refração correta do desktop não provaria equivalência ao material proprietário. [Apple, Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/)
