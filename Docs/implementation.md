# Integração Omarchy: estado verificável

## Demonstração independente

```sh
bash build.sh run
```

Esse comando compila os shaders, analisa o QML e abre a pequena shell de demonstração em `src/`. Ela usa fundos QML próprios e não substitui a shell Omarchy. Para verificar o shader refrativo desse fundo sintético, rode `bash build.sh render-check`; o teste não prova refração do desktop real.

O protótipo `src/GlassWidget.qml` ainda demonstra refração de uma **textura QML fornecida pelo host**. Seu teste gráfico verifica somente esse caso. Ele não refrata o desktop e não é usado pelo adaptador Omarchy.

O adaptador em `integrations/omarchy/apply.py` integra `GlassOverlay.qml` à barra padrão, a `KeyboardPanel`, aos cartões de menu, clipboard, emojis, notificações popup e OSD. Ele deixa os fundos desses hosts transparentes, compila um shader para a borda e usa `BackgroundEffect.blurRegion` do Quickshell para pedir blur somente atrás da região do host. Nesse caminho, **Hyprland amostra o desktop real** e executa o blur. A base translúcida é desenhada atrás dos ícones e texto; uma segunda instância do shader pinta apenas o reflexo da borda acima deles, sem aceitar eventos de entrada. O gradiente artificial usado na versão anterior foi removido.

Menu, clipboard e emojis desenham um véu de tela inteira. O pedido de blur agora usa `Region { item: card; radius: card.radius }`, sem mudar a opacidade do véu. A região de notificações é a coluna de cartões, portanto os espaços entre cartões também podem ficar desfocados.

Isso é uma aproximação funcional, não uma reprodução fiel do Liquid Glass da Apple. Falta refração geométrica dos pixels reais, adaptação por luminância do fundo, fusão/morfismo entre superfícies e avaliação de legibilidade e desempenho. O [material descrito pela Apple](https://developer.apple.com/videos/play/wwdc2025/219/) combina essas propriedades. O `ShaderEffectSource` do Qt não entrega os pixels do desktop antes da composição. A regra `no_screen_share` do Hyprland oculta a camada com preto na captura; por isso não resolve a realimentação de `ScreencopyView`.

## Instalar ou aplicar a um checkout de código-fonte

`./install.sh` detecta a versão do pacote Omarchy, clona o tag `v<versão>` oficial, aplica o adaptador, chama `omarchy dev link --no-reboot` e recarrega a shell na sessão Hyprland atual. `./install.sh --prepare-only` cria o checkout sem alterar o vínculo do sistema. `./install.sh --reload-only` recarrega um checkout já vinculado, sem repetir o `sudo`. O reload para a shell antiga com `quickshell kill` e inicia `omarchy-launch-shell` com `OMARCHY_PATH` e `PATH` do checkout, esperando o ping de IPC; se a nova shell não ficar pronta, tenta restaurar a anterior. Não recarrega uma sessão bloqueada. Até o reboot, `omarchy restart shell` ainda lê o caminho antigo da sessão.

Em 2026-10-03, `./install.sh --reload-only` iniciou `quickshell -n -p ~/.local/share/widget-on-glass/omarchy-v4.0.4/shell` na sessão atual e `omarchy-shell shell ping` respondeu `ok`. Isso confirma a ativação da shell, mas ainda não constitui inspeção visual ou medição de desempenho.

```sh
python3 integrations/omarchy/apply.py /caminho/para/checkout-do-omarchy
```

O script espera a estrutura Omarchy observada em 2026-10-03 e falha quando âncoras de código divergem. Ele altera os hosts da barra, painel de teclado, menu, clipboard, emojis e notificações, além de `shell/Ui/qmldir`, e copia o componente e o shader compilado para `shell/Ui/`. Ele recusa `/usr/share/omarchy` e não altera a sessão em execução. Revise o diff do checkout antes de ativá-lo pelo fluxo de desenvolvimento do Omarchy.

`bar.glassEnabled: false` no `shell.json` desliga o material e o pedido de blur na barra e em `KeyboardPanel`; os outros hosts ainda não expõem essa opção. `bar.glassReducedTransparency` e `bar.glassHighContrast` são opções manuais só para esses dois hosts. Elas não se conectam automaticamente às preferências de acessibilidade do sistema.

## Cobertura e próximos critérios

A barra padrão, `KeyboardPanel`, menu, clipboard, emojis, notificações popup e OSD são os pontos integrados. Image picker, lock screen, outros `PanelWindow` e barras alternativas ainda não usam o material. Widgets que desenham fundos opacos também encobrem o material do host. Por isso, ainda não se pode chamar a integração de global.

O Hyprland 0.56.2 local implementa `ext-background-effect-v1` e tem blur habilitado, mas não expõe `decoration:blur:variant`; a variante `acrylic` da documentação mais nova não está disponível nesta instalação. Para chegar ao requisito de refração real, é necessário alterar o estágio de composição do Hyprland ou usar uma futura API que aplique refração à imagem atrás de cada camada, com geometria, escala e sincronização corretas. Até existir essa prova, o efeito no desktop real é blur com iluminação de borda.

Validação feita: shader compilado com `qsb`, QML analisado por `qmllint`, adaptador aplicado a uma cópia temporária da shell instalada e uma janela Quickshell mínima com `BackgroundEffect.blurRegion` carregada na sessão Wayland. Isso prova carregamento, não confirma visualmente o blur nem mede desempenho. Ainda faltam inspeção visual da sessão Omarchy alterada, medições de tempo de quadro/energia e testes de acessibilidade.
