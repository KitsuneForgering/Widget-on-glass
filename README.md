# Widget on Glass

Widget on Glass adiciona uma superfície translúcida aos widgets da shell Omarchy. O fundo recebe blur do Hyprland; um shader desenha a cor do vidro atrás do conteúdo e um reflexo discreto acima das bordas. Texto, ícones e cliques continuam nos widgets originais. O projeto é para quem usa a barra e os painéis padrão do Omarchy e quer testar esse visual sem clonar cada plugin.

**Estado atual:** é um piloto inspirado no Liquid Glass da Apple. Ele **não refrata geometricamente as janelas do desktop** e não reproduz o material proprietário da Apple. A instalação foi validada com Omarchy `4.0.4`, Hyprland `0.56.2` e Quickshell `0.3.1`; outras versões podem precisar de ajustes no adaptador.

## Instalar

Na sessão Omarchy, com `git`, `python3` e Qt Shader Tools (`/usr/lib/qt6/bin/qsb`) disponíveis:

```sh
git clone https://github.com/KitsuneForgering/Widget-on-glass.git
cd Widget-on-glass
./install.sh
```

O instalador lê a versão do pacote Omarchy, baixa o tag correspondente do código-fonte oficial para `~/.local/share/widget-on-glass/`, aplica a integração e executa `omarchy dev link --no-reboot`. O comando `dev link` usa `sudo` para apontar o sistema ao checkout; **reinicie o computador para ativar**. Depois do reboot, a barra padrão, seus painéis de teclado, menu, clipboard, emojis, notificações popup e OSD recebem o material.

Para preparar e revisar o checkout sem alterar a instalação ativa:

```sh
./install.sh --prepare-only
```

Quando estiver pronto para ativar o checkout preparado, execute novamente em um terminal para informar a senha do `sudo` quando solicitada:

```sh
./install.sh
```

O instalador reutiliza o checkout preparado sem baixar tudo novamente. Reinicie depois.

O instalador recusa sobrescrever um diretório existente que não seja um checkout preparado. Ele também falha se o código-fonte do Omarchy tiver mudado nos pontos que o adaptador modifica. Nesse caso, não ative um checkout parcialmente preparado.

## Voltar à shell do pacote

```sh
omarchy dev unlink --no-reboot
```

Reinicie depois. O checkout criado pelo instalador permanece em `~/.local/share/widget-on-glass/` para inspeção; esse comando não o remove.

## O que está incluído

- Blur do desktop real delimitado por `BackgroundEffect.blurRegion` nos hosts integrados.
- Superfície e reflexo de borda renderizados na GPU pelo Quickshell; o reflexo fica acima dos widgets sem receber cliques.
- Fallback opaco para o backend de renderização por software.

Barras alternativas e plugins que criam janelas próprias não recebem o efeito automaticamente. Fundos opacos desenhados dentro de um widget também podem esconder a superfície. Image picker e tela de bloqueio mantêm o visual original.

A [implementação e validação](Docs/implementation.md) descreve a cobertura atual. A [pesquisa sobre refração do desktop](Docs/compositor-refraction.md) explica por que a etapa óptica restante depende do renderizador do Hyprland. Para executar apenas a demonstração Quickshell deste repositório, veja [Docs/implementation.md](Docs/implementation.md).
