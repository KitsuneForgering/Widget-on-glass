# Widget on Glass

Protótipo de containers Quickshell com refração em shader GPU. A primeira versão
deforma um **fundo QML explícito**, com Snell, bordas arredondadas, iluminação
direcional e adaptação local à luminância. Por padrão, o centro fica sem blur,
tint, brilho ou deformação, preservando o texto atrás do vidro. O conteúdo do
widget é desenhado depois; os labels do preview usam uma proteção local.

Veja a [tese, evidências e critérios de decisão](docs/tese.md).
O preview inclui fundo claro/escuro, expansão de forma, feedback de hover/pressão
e dois containers sobre uma textura compartilhada. O efeito é inspirado no
lensing descrito pela Apple; a
[comparação técnica](docs/tese.md#comparação-com-o-liquid-glass-da-apple)
mostra por que ainda há apenas semelhança parcial.

## Executar

Requer Quickshell, Qt Quick Controls e `qsb` do Qt Shader Tools. Nesta máquina
eles já estão disponíveis; o Makefile usa `/usr/lib/qt6/bin/qsb`.

```sh
make check         # compila o shader, verifica matemática, manifesto e QML
make demo          # abre o painel; Fechar ou Escape o dispensa
make render-check  # janela breve na sessão Wayland + comparação de imagens
```

`render-check` também usa o ImageMagick já instalado no Omarchy. O teste altera
a espessura de 0 para 80 px: as bordas devem mudar, o centro plano deve continuar
igual. Com `ior=1`, os mesmos ajustes devem produzir imagens idênticas. Fonte
ausente e efeito desligado devem produzir o mesmo fallback opaco. O teste
também compara 200×80 pixels de texto ao fundo com a referência sem vidro,
em fontes local/compartilhada e fundos claro/escuro. Verifica feedback de
pressão, interpolação de geometria e movimento reduzido. As capturas ficam
em `/tmp/widget-on-glass-render-<fase>.png`.

O backend `software` do Qt usa o container opaco de fallback. O shader requer
um backend gráfico; o teste recusa `software`. Compilação para outros backends
não significa que eles foram testados.

## Usar o container

Coloque o fundo e `LiquidGlass` como **irmãos sem rotação ou escala própria**.
O fundo deve cobrir a área do container e a margem de amostragem. Nunca use
como fonte um ancestral que também contenha o efeito: isso cria recursão.

```qml
Item {
    width: 640; height: 400
    Image {
        id: backdrop
        anchors.fill: parent
        source: "wallpaper.jpg"
        fillMode: Image.PreserveAspectCrop
    }
    LiquidGlass {
        x: 140; y: 90; width: 360; height: 220
        sourceItem: backdrop
        thickness: 36
        contentRefraction: 0.25
        ior: 1.5
        Rectangle {
            anchors.centerIn: parent
            width: label.implicitWidth + 24; height: label.implicitHeight + 12
            radius: 6; color: parent.contentPlateColor
            Text { id: label; anchors.centerIn: parent; text: "Meu widget"; color: parent.parent.contentColor }
        }
    }
}
```

`radius`, `bevel` e `thickness` usam pixels lógicos. `ior` é adimensional.
`contentRefraction` varia de 0 a 1, com padrão 0; valores pequenos aplicam
paralaxe radial sutil no fundo sem blur. O preview usa 0,45. O centro exato
permanece alinhado e os labels opacos preservam contraste.
`glassEnabled: false` seleciona o container opaco. A textura acompanha mudanças
do fundo; as animações só ocorrem nas mudanças de estado. Esta versão assume fonte e container
no mesmo sistema de coordenadas e limita a espessura a 128 px.
`reducedTransparency: true` também seleciona o modo opaco; `highContrast: true`
usa fundo preto e borda branca. São opções explícitas do componente, sem
sincronização automática com preferências de acessibilidade do sistema.
O autor do widget continua responsável pela cor e legibilidade do conteúdo.
`preserveBackground` é `true` por padrão: posicione os itens que precisam ser
lidos no interior, afastados pelo menos `bevel` pixels das bordas arredondadas.
Defina `backdropColor` com uma cor representativa dessa área; `contentColor`
escolhe texto claro ou escuro pela luminância relativa WCAG. Para áreas com
fundo misto, use `contentPlateColor` atrás de cada label para manter contraste
local. O preview atualiza essas cores ao alternar entre fundos claros e escuros.
QML não consegue obter a cor média amostrada pelo shader sem ler pixels de volta
da GPU, então a cor representativa é responsabilidade do widget.
`contentColor` e `contentPlateColor` devem ser usados juntos atrás de cada
label: as placas opacas fornecidas formam pares com contraste acima de 7:1
(WCAG 2.2 AAA, critério 1.4.6). Sem a placa, o conteúdo do vidro não pode
garantir contraste sobre uma imagem ou fundo variável. Nos fallbacks, as cores
consideram a superfície realmente exibida. Outros fundos e componentes ainda
precisam de avaliação de contraste no contexto.
O preview dá aos textos do fundo um relevo sutil com `Text.Sunken`; a cor do
texto permanece opaca e de alto contraste.
`reducedMotion: true` desativa interpolação de tamanho/raio e transição de luz.
`pressed` deve ser ligado ao estado do controle, por exemplo `pressed: button.down`.
O hover usa `HoverHandler` sem bloquear os controles. `activeSurface: false`
reduz a iluminação; é uma opção explícita, sem detecção automática de foco.

Para compartilhar o fundo, crie um `ShaderEffectSource` separado com
`sourceItem: backdrop`, `visible: false` e um `sourceRect` que cubra todos os
containers e suas margens. Em cada `LiquidGlass`, use `sourceItem: backdrop`
e `sharedSource: essaTextura`. Fonte e containers devem continuar irmãos
sem transformações próprias. O compartilhamento não une as formas entre si.
Sem `sharedSource`, o componente usa um recorte local com margem fixa de
130 px; os dois modos são testados. Não há captura do desktop real.

## Integração com Omarchy

O manifesto declara um plugin `panel`, aberto sob demanda dentro da shell
existente. O preview independente usa outro processo apenas para desenvolvimento.
Os arquivos do sistema em `/usr/share/omarchy/` servem de referência.

Para testar a integração depois de compilar, copie `manifest.json`, `Panel.qml`,
`Preview.qml`, `LiquidGlass.qml` e `shaders/glass.frag.qsb`, preservando a pasta
`shaders`, para `~/.config/omarchy/plugins/kitsuneforgering.widget-on-glass/`.
Então execute:

```sh
omarchy-shell shell rescanPlugins
omarchy plugin enable kitsuneforgering.widget-on-glass
omarchy-shell shell summon kitsuneforgering.widget-on-glass '{}'
```

Para desativar: `omarchy plugin disable kitsuneforgering.widget-on-glass`.
A instalação na shell hospedeira não foi executada nesta entrega. O manifesto
foi validado e o painel foi carregado no Quickshell independente.

**Limite atual:** o preview não captura as janelas atrás da shell nem transforma
automaticamente widgets de outros plugins. O próximo teste para esse requisito
é avaliar a integração de compositor descrita na tese.
