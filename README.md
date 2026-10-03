# Widget on Glass

Widget on Glass adiciona uma superfície translúcida aos widgets da shell Omarchy. O fundo recebe blur do Hyprland; um shader desenha a cor correspondente a cada superfície do tema com 75% de opacidade na barra e 80% nos painéis, além de um reflexo nas bordas. O conteúdo mantém suas cores. O projeto é para quem usa a barra e os painéis padrão do Omarchy e quer testar esse visual sem clonar cada plugin.

**Estado atual:** é um piloto inspirado no Liquid Glass da Apple. Todas as superfícies de vidro da shell (módulos da barra, painéis, menu, clipboard, emojis, popups, notificações e OSD) usam o `screen_shader` do Hyprland para refratar uma faixa estreita da borda com pixels reais do desktop. O fundo sob o centro de cada superfície continua apenas com blur, sem refração. Não reproduz o material proprietário da Apple. A integração de refração está direcionada a Omarchy `4.0.4`, Hyprland `0.56.2` e Quickshell `0.3.1`; outras versões podem precisar de ajustes no adaptador.

## Instalar

Na sessão Omarchy, com `git`, `python3` e Qt Shader Tools (`/usr/lib/qt6/bin/qsb`) disponíveis:

```sh
git clone https://github.com/KitsuneForgering/Widget-on-glass.git
cd Widget-on-glass
./install.sh
```

O instalador lê a versão do pacote Omarchy, baixa o tag correspondente do código-fonte oficial para `~/.local/share/widget-on-glass/`, aplica a integração, executa `omarchy dev link --no-reboot` e recarrega a shell na sessão Hyprland atual. O comando `dev link` usa `sudo` para apontar o sistema ao checkout. O reload sincroniza `OMARCHY_PATH` no Hyprland e no gerenciador de serviços do usuário antes de executar `omarchy restart shell`, preservando os atalhos da sessão. A barra padrão, seus painéis de teclado, menu, clipboard, emojis, notificações popup e OSD recebem o material após o reload. Reinicie depois para alinhar os demais serviços do sistema ao checkout.

Para preparar e revisar o checkout sem alterar a instalação ativa:

```sh
./install.sh --prepare-only
```

Quando estiver pronto para ativar o checkout preparado, execute novamente em um terminal para informar a senha do `sudo` quando solicitada:

```sh
./install.sh
```

O instalador reutiliza o checkout preparado sem baixar tudo novamente. Se já executou a versão anterior do instalador e quer apenas ativar a shell nesta sessão, sem repetir o `sudo`:

```sh
./install.sh --reload-only
```

Ao ativar a shell, o instalador também torna transparente o fundo do preview do plugin local `tornikegomareli.spaces`, quando ele está instalado, para que o `PopupCard` compartilhado apareça. O arquivo original fica em `Spaces.qml.widget-on-glass.bak` ao lado do plugin. Painéis de terceiros que usam `KeyboardPanel` ou `PopupCard` recebem o material pelo componente compartilhado; fundos opacos desenhados dentro de outros plugins ainda precisam de adaptação própria.

O reload também atualiza o caminho usado por `omarchy restart shell` e pelos keybinds do Hyprland. Um reboot posterior inicia toda a sessão diretamente no checkout.

O instalador recusa sobrescrever um diretório existente que não seja um checkout preparado. Ele também falha se o código-fonte do Omarchy tiver mudado nos pontos que o adaptador modifica. Nesse caso, não ative um checkout parcialmente preparado.

## Voltar à shell do pacote

```sh
omarchy dev unlink --no-reboot
```

Reinicie depois. O checkout criado pelo instalador permanece em `~/.local/share/widget-on-glass/` para inspeção; esse comando não o remove.

## O que está incluído

- Blur do desktop real delimitado por `BackgroundEffect.blurRegion` nos hosts integrados.
- Lente de borda via `screen_shader` em todas as superfícies de vidro, acompanhando posição e tamanho de cada uma. Ela fica suspensa quando outro shader já está configurado, quando há mais de uma tela ativa e sobre janelas em tela cheia.
- Containers internos também em vidro: itens selecionados, linhas, chips e botões preenchidos ganham borda refletiva e lente pelo `BorderSurface` compartilhado; popups de dropdown e o diálogo de confirmação usam o material completo. O véu de menu, clipboard e emojis tem um recorte sob o cartão, para o vidro mostrar o desktop desfocado em vez de ficar escurecido.
- `bar.glassLens: false` no `~/.config/omarchy/shell.json` desliga só a lente. Ela também se desliga com `bar.glassEnabled: false`, `bar.glassReducedTransparency: true` ou `bar.glassHighContrast: true`.
- Superfície e reflexo de borda renderizados na GPU pelo Quickshell; o reflexo fica acima dos widgets sem receber cliques.
- Fallback opaco para o backend de renderização por software.

Barras alternativas e plugins que criam janelas próprias não recebem o efeito automaticamente. Fundos opacos desenhados dentro de um widget também podem esconder a superfície. Image picker e tela de bloqueio mantêm o visual original.

A [implementação e validação](Docs/implementation.md) descreve a cobertura atual. A [pesquisa sobre refração do desktop](Docs/compositor-refraction.md) explica por que a etapa óptica restante depende do renderizador do Hyprland. Para executar apenas a demonstração Quickshell deste repositório, veja [Docs/implementation.md](Docs/implementation.md).
