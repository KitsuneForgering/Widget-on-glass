# Integração Omarchy: estado verificável

## Demonstração independente

```sh
bash build.sh run
```

Esse comando compila os shaders, analisa o QML e abre a pequena shell de demonstração em `src/`. Ela usa fundos QML próprios e não substitui a shell Omarchy. Para verificar o shader refrativo desse fundo sintético, rode `bash build.sh render-check`; o teste não prova refração do desktop real.

O protótipo `src/GlassWidget.qml` ainda demonstra refração de uma **textura QML fornecida pelo host**. Seu teste gráfico verifica somente esse caso. Ele não refrata o desktop e não é usado pelo adaptador Omarchy.

O adaptador em `integrations/omarchy/apply.py` integra `GlassOverlay.qml` à barra padrão, a `KeyboardPanel`, aos cartões de menu, clipboard, emojis, notificações popup, `PopupCard` e OSD. Ele deixa os fundos desses hosts transparentes, compila um shader para a borda e usa `BackgroundEffect.blurRegion` do Quickshell para pedir blur somente atrás da região do host. Nesse caminho, **Hyprland amostra o desktop real** e executa o blur. A base usa a cor própria de cada superfície do tema com 75% de opacidade na barra e 80% nos painéis; o adaptador reforça a opacidade do texto auxiliar em menu e clipboard para preservar o contraste. Uma segunda instância do shader pinta um reflexo e um brilho estreito no topo das bordas, sem aceitar eventos de entrada.

Menu, clipboard e emojis desenham um véu de tela inteira. O pedido de blur agora usa `Region { item: card; radius: card.radius }`, sem mudar a opacidade do véu. A região de notificações é a coluna de cartões, portanto os espaços entre cartões também podem ficar desfocados.

Os containers internos seguem o mesmo material. O adaptador insere em `BorderSurface` um `Loader` que, quando a superfície tem preenchimento, carrega uma borda refletiva com lente; isso cobre linhas selecionadas, chips de dispositivo, botões e outros estados dos painéis sem alterar cada plugin. As linhas de clipboard e emojis e os destaques de `Dropdown`, `SearchableDropdown` e `MultiSelect` são `Rectangle`s e recebem a mesma borda diretamente. Os popups desses dropdowns e o cartão de `ConfirmDialog`, antes opacos, usam base e reflexo de vidro. O véu de tela inteira de menu, clipboard e emojis passou a ser `GlassScrim`, um `Shape` com um furo arredondado sob o cartão; antes o véu escurecia também o vidro. Itens recortados por uma lista com `clip` só enviam à lente a parte visível.

`PopupCard` também usa o material compartilhado, cobrindo popups como media, tray e previews de plugins. O preview do plugin local `tornikegomareli.spaces` tinha um preenchimento próprio quase opaco; o reload o torna transparente e guarda um backup. Feader RSS usa `KeyboardPanel` e recebe o material sem mudar seu código.

Isso é uma aproximação funcional, não uma reprodução fiel do Liquid Glass da Apple. Cada `GlassOverlay` de base se registra no singleton `GlassLens`. A cada 300 ms, ou logo após uma mudança de visibilidade, o singleton reúne os retângulos visíveis em coordenadas de janela e chama o helper `bin/widget-on-glass-lens` só quando o conjunto muda. O helper localiza cada janela pela lista de layers do Hyprland (mesmo PID e tamanho) e gera um único `screen_shader` com a lente de borda de todas as superfícies. A faixa da borda escala com a superfície: 10 px nos cartões grandes, cerca de 3 px nos módulos da barra. A lente roda só numa tela ativa sem rotação e quando não há outro `screen_shader` configurado. Em tela cheia, as superfícies abaixo da layer de overlay saem da lente. Ela é reenviada depois de `hyprctl reload` e de mudanças em `shell.json`, e é limpa quando a shell fecha ou reinicia. A lente não recupera o fundo oculto no centro das superfícies; fusão/morfismo entre superfícies e avaliação completa de legibilidade também permanecem pendentes. O [material descrito pela Apple](https://developer.apple.com/videos/play/wwdc2025/219/) combina essas propriedades. O `ShaderEffectSource` do Qt não entrega os pixels do desktop antes da composição.

## Instalar ou aplicar a um checkout de código-fonte

`./install.sh` detecta a versão do pacote Omarchy, clona o tag `v<versão>` oficial, aplica o adaptador, chama `omarchy dev link --no-reboot` e recarrega a shell na sessão Hyprland atual. `./install.sh --prepare-only` cria o checkout sem alterar o vínculo do sistema. `./install.sh --reload-only` recarrega um checkout já vinculado, sem repetir o `sudo`. O reload atualiza `OMARCHY_PATH` tanto no Hyprland quanto no gerenciador de serviços do usuário, encerra a shell antiga e chama `omarchy restart shell`. Ele verifica o ping de IPC e restaura o caminho anterior em caso de falha. Não recarrega uma sessão bloqueada. O reboot posterior atualiza também os demais processos da sessão.

Em 2026-10-03, a primeira versão do reload iniciou `quickshell -n -p ~/.local/share/widget-on-glass/omarchy-v4.0.4/shell` e o ping de IPC respondeu `ok`, mas os keybinds do Hyprland ainda usavam o caminho anterior e falharam. A shell do pacote foi restaurada enquanto se corrigia o mecanismo de ativação.

```sh
python3 integrations/omarchy/apply.py /caminho/para/checkout-do-omarchy
```

O script espera a estrutura Omarchy observada em 2026-10-03 e falha quando âncoras de código divergem. Ele altera os hosts da barra, painel de teclado, menu, clipboard, emojis e notificações, além de `shell/Ui/qmldir`, e copia o componente, o singleton `GlassLens`, os shaders e o helper da lente para o checkout. Ele recusa `/usr/share/omarchy`. Em checkouts de versões anteriores, o `--refresh` remove a lente específica do menu e os arquivos `GlassAppearance.qml`/`GlassBackdrop.qml`, que não eram mais usados.

`bar.glassEnabled: false` no `shell.json` desliga o material e o pedido de blur na barra e em `KeyboardPanel`; os outros hosts ainda não expõem essa opção. `bar.glassReducedTransparency` e `bar.glassHighContrast` são opções manuais só para esses dois hosts. Elas não se conectam automaticamente às preferências de acessibilidade do sistema. A lente de borda é global: qualquer uma dessas três opções, ou `bar.glassLens: false`, desliga a lente em todas as superfícies.

## Cobertura e próximos critérios

A barra padrão, `KeyboardPanel`, menu, clipboard, emojis, notificações popup e OSD são os pontos integrados. Image picker, lock screen, outros `PanelWindow` e barras alternativas ainda não usam o material. Widgets que desenham fundos opacos também encobrem o material do host. Por isso, ainda não se pode chamar a integração de global.

O Hyprland 0.56.2 local implementa `ext-background-effect-v1` e tem blur habilitado, mas não expõe `decoration:blur:variant`; a variante `acrylic` da documentação mais nova não está disponível nesta instalação. Para chegar ao requisito de refração real, é necessário alterar o estágio de composição do Hyprland ou usar uma futura API que aplique refração à imagem atrás de cada camada, com geometria, escala e sincronização corretas. Até existir essa prova, o efeito no desktop real é blur com iluminação de borda.

Validação feita: shader compilado com `qsb`, QML analisado por `qmllint`, atualização aplicada a uma cópia temporária do checkout preparado, shell reiniciada com ping de IPC e captura da barra na sessão Wayland. O teste de contraste cobre texto primário em paletas claras e escuras representativas sobre fundos cinza; não cobre todos os temas nem todos os estados dos widgets. `checks/lens.py` verifica o posicionamento dos retângulos pelo helper, incluindo janelas ambíguas, layers de outros processos e tela cheia. A medição de custo da lente está em [compositor-refraction.md](compositor-refraction.md). Ainda faltam inspeção visual de todos os painéis, medição de energia e testes completos de acessibilidade.
