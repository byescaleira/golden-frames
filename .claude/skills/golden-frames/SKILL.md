---
name: golden-frames
description: Edit a cinematic, warm, music-driven video from a folder of real footage (vlog, anniversary, trip) following the golden-frames spec — scan clips, map the song's phrases, pick and frame shots, grade each shot (log + normal footage) into one film look, add title cards, render 1080 + 4K and review. Use when the user asks to make/edit a video in the golden-frames style, says "/golden-frames", or wants to turn reference videos into a style profile.
---

# golden-frames: edição guiada por spec

Você edita **só a filmagem real** da pessoa. Antes de qualquer passo, leia:
`specs/rules.md` (regras fixas), `specs/style.md` (o padrão) e o perfil em `styles/<style>.json`.

Todos os comandos rodam da raiz do repositório com o Python do ambiente (`pip install -r requirements.txt`; precisa de `ffmpeg`/`ffprobe` no PATH). Um projeto é uma pasta com `spec.md` + `project.json`; tudo que é gerado vai para `<projeto>/work/`. Projetos reais ficam **fora** do repositório (ou em `projects/` com `work/` e mídia ignorados) — nunca versione mídia, quadros, nomes ou caminhos pessoais.

## 0. Spec do projeto
1. Copie `specs/project.template.md` para `<projeto>/spec.md` e preencha com o que a pessoa disse.
2. Pergunte **só** o que falta e muda o resultado: pasta de vídeos, música (arquivo), duração, textos, o que excluir. Para o resto use o padrão do estilo e diga qual usou.
3. Crie `<projeto>/project.json` com `source`, `music {file, start, end}`, `style`, `titles` (veja `projects/example/project.json`).

## 1. Inventário — `tools/scan.py <projeto>`
- Teste a velocidade do disco antes (ler ~256 MB); se for < 50 MB/s, avise (cabo/porta USB) antes de varrer centenas de GB.
- Rode em segundo plano; gera `work/clips.json`, miniaturas e pranchas `work/sheets/`.

## 2. Música — `tools/music.py <projeto> [--write]`
- Leia a curva de energia: identifique a parte calma e a intensa. Respeite o clima da spec (padrão: do início, contínua).
- `--write` grava os cortes sugeridos (onsets após as maiores pausas = inícios de frase). Ajuste à mão se precisar; `cuts` tem N+1 valores para N cenas.

## 3. Seleção de cenas
- Leia as pranchas (pode dividir entre subagentes, 12–13 pranchas cada, pedindo lista `#índice | quadro | nota | descrição`) e **confira pessoalmente** os candidatos com `tools/picks.py <projeto> idx:quadro ...`.
- Monte `shots` no `project.json`: `{"file", "at" (0–1 no clipe), "cx", opcional "zoom"/"cy"/"push"/"exp", "note"}`.
- Aplique as regras: cintura para cima (`zoom` 1.2–2.2, `cy` ~0.4), só as pessoas do tema, lista `excluir`, nunca duas paisagens seguidas. Abertura com `push: true`; o momento mais afetivo por último.

## 4. Cor — `tools/grade.py <projeto> --preview`
- Leia `work/grade_preview.jpg` (original | graduado). Rosto escuro contra céu/noite → `"exp": 0.78–0.9` na cena e rode de novo. Se a pessoa pedir outro look, crie um novo `styles/<nome>.json` em vez de editar o padrão.

## 5. Render — `tools/render.py <projeto> --size 1080` e `--size 2160`
- 1080 H.264 para redes; 2160 HEVC 10-bit como master (bem mais lento — rode em segundo plano).

## 6. Revisão — `tools/review.py <projeto> <video> --titles`
- Quadros = esperado, loudness, e olhe `work/review.jpg`: enquadramento (nada de corpo inteiro), título de abertura sem invadir a 2ª cena, legibilidade dos títulos. Corrija e renderize de novo.
- Metadados: preencha `metadata` no `project.json` (título, autor, álbum, data, gênero, descrição, palavras-chave, copyright, idioma; `music.credit` vira o nome da faixa de áudio) e rode `tools/metadata.py <projeto> <video>` nos arquivos finais — remux sem recodificar, com um capítulo por cena. Não invente nomes de pessoas: pergunte ou deixe de fora.
- Na entrega: caminho do arquivo, o que mudou, o que **não** foi verificado (ex.: ninguém assistiu com som), e o aviso sobre música comercial na plataforma.

## Vídeos de referência → estilo
`tools/reference_profile.py <video> --name <nome>` mede ritmo de corte (cortes/min, duração das cenas, se corta nos onsets), cor (preto, contraste, saturação, tons de sombra/luz) e salva uma prancha de quadros para ler a tipografia. Com 2–5 perfis, proponha à pessoa um `styles/<nome>.json` (ritmo, alvos de normalização, look, tipografia) explicando cada número, e só então use.
