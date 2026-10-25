# golden-frames

**Edição de vídeo guiada por spec, feita pelo Claude.** Você aponta uma pasta de filmagens e uma música, e o Claude segue as specs deste repositório para entregar um vídeo cinematográfico, quente e afetivo. Ele varre os clipes, corta nas frases da música, enquadra, faz o color grade cena a cena, cria os títulos, renderiza em 1080 e em 4K e revisa o resultado.

> Nada aqui gera imagem, vídeo, voz ou música com IA. É só edição da filmagem real: corte, enquadramento, velocidade, cor e tipografia.

## Como usar

No [Claude Code](https://claude.com/claude-code), dentro deste repositório:

```
/golden-frames vídeo de 5 anos de namoro, 45 s, quadrado, vídeos em D:/osmo, música em D:/musica/tema.mp3
```

O Claude cria a spec do projeto (`specs/project.template.md`) e pergunta só o que faltar. Depois executa as etapas da skill (`.claude/skills/golden-frames/SKILL.md`), mostrando pranchas e prévias nos pontos de decisão.

### Pré-requisitos
- `ffmpeg` / `ffprobe` no PATH. Recomendado o build "full", com `libx265`.
- Python 3.10+ e `pip install -r requirements.txt` (librosa, numpy, Pillow).
- Fontes da tipografia padrão: Bodoni MT, Gill Sans MT e Garamond. Elas vêm com o Windows/Office; se faltarem, o estilo usa Georgia ou Times.

## Pipeline

| Etapa | Ferramenta | O que faz |
|---|---|---|
| Inventário | `tools/scan.py` | Lê duração, fps e formato de cada clipe e monta pranchas com 3 quadros por clipe |
| Música | `tools/music.py` | Mede a energia segundo a segundo, os onsets e o tempo, e sugere cortes nos **inícios de frase** |
| Seleção | `tools/picks.py` | Grade de candidatas para comparar e escolher |
| Cor | `tools/grade.py` | Mede cada cena (detecta LOG), corrige preto, branco, exposição, balanço de branco e saturação, e aplica o look comum. `--preview` mostra antes e depois |
| Títulos | `tools/titles.py` | Cartões de título em PNG na resolução nativa (Bodoni, Gill Sans com tracking, Garamond itálico) |
| Render | `tools/render.py` | Um segmento graduado por cena, depois concat, música, títulos e fades. Entrega 1080 em H.264 e master 2160 em HEVC 10 bits |
| Revisão | `tools/review.py` | Confere a contagem de quadros, o loudness e uma prancha com um quadro por cena e pelos títulos |
| Metadados | `tools/metadata.py` | Grava título, autor, descrição, palavras-chave, copyright e créditos da música, com um capítulo por cena (remux sem perda) |
| Referências | `tools/reference_profile.py` | Mede vídeos que você admira (ritmo de corte, cortes na música, cor) para criar novos estilos |

## Specs

- [`specs/rules.md`](specs/rules.md): regras fixas, como nada de IA, pessoas da cintura para cima, música contínua e duração exata no quadro.
- [`specs/style.md`](specs/style.md): o estilo da casa (narrativa, ritmo, enquadramento, cor e tipografia).
- [`styles/golden-frames.json`](styles/golden-frames.json): os números desse estilo, que as ferramentas leem.
- [`specs/project.template.md`](specs/project.template.md): o formulário de cada vídeo novo.
- [`projects/example/project.json`](projects/example/project.json): um projeto real anonimizado (45 s, 20 cenas).

## O look "cinema quente"

A filmagem de câmeras pequenas mistura clipes em LOG (lavados) e em Rec.709. Por isso o grade tem duas camadas:

1. **Normalização por cena:**
   - Ponto de preto e de branco por percentis.
   - Mediana levada a uma exposição comum, com as cenas noturnas continuando escuras.
   - Balanço de branco gray-world parcial, que mantém o calor das luzes à noite.
   - Saturação levada a um alvo comum.
2. **Look comum:**
   - Curva em S suave com pretos lavados.
   - Sombras verde-água e altas luzes quentes.
   - Azuis puxados para o verde-água e verdes discretos.
   - Halation quente, vinheta e grão fino.

## Criando seu próprio estilo a partir de referências

```bash
python tools/reference_profile.py referencia.mp4 --name minha-ref
```

Para cada vídeo, gera `styles/refs/minha-ref.profile.json` (cortes por minuto, duração das cenas, se os cortes caem nos onsets, contraste, saturação e tons de sombra e luz) e uma prancha de quadros. Peça ao Claude: *"crie um estilo a partir de styles/refs/"*. Ele propõe um `styles/<nome>.json` explicando cada número.

## Privacidade

As pastas `projects/*/work/`, as mídias e as pranchas de referência ficam fora do git (veja `.gitignore`). O projeto de exemplo usa nomes de arquivo genéricos.

## Licença

MIT, veja [LICENSE](LICENSE). As músicas e filmagens usadas nos seus projetos continuam sendo de quem as detém.
