# golden-frames

Repositório de edição de vídeo guiada por spec. Para editar um vídeo, siga a skill `.claude/skills/golden-frames/SKILL.md`. Ela manda ler `specs/rules.md` (regras que nunca mudam), `specs/style.md` e o perfil em `styles/`.

- Rode as ferramentas com `python tools/<ferramenta>.py <pasta-do-projeto> ...` a partir da raiz. Elas importam `tools/gf.py`.
- Nunca gere conteúdo com IA, nunca versione mídia ou dados pessoais, e nunca baixe música de fonte não oficial.
- Estilos novos vão em `styles/<nome>.json`. Não altere `golden-frames.json` para atender um projeto só.
- Mantenha as ferramentas genéricas: nada de caminhos fixos. Tudo vem de `project.json` ou do estilo.
