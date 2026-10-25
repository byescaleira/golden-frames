# Regras fixas

Valem para todo projeto. A spec do projeto pode **acrescentar** regras, nunca remover estas.

## Conteúdo
1. **Nada gerado por IA.** Só edição da filmagem real: corte, enquadramento, velocidade, cor e tipografia. Não gerar imagem, vídeo, voz nem música.
2. **Música real e licenciada.** Usar o arquivo que a pessoa fornecer. Nunca baixar música comercial de fonte não oficial. Se o projeto for para rede social, avisar que a plataforma pode silenciar o vídeo e que a mesma faixa pode ser adicionada pela biblioteca dela.
3. **Pessoas da cintura para cima.** Nada de corpo inteiro em roupa de banho, e evitar enquadrar o corpo de forma geral. Quando a cena tiver corpo inteiro, fechar o quadro (`zoom`/`cy`) ou descartar.
4. **Só o casal ou as pessoas do tema.** Família, amigos, colegas e desconhecidos não são o assunto: descartar as cenas em que eles dominam o quadro.
5. **Respeitar a lista `excluir` da spec do projeto** (ex.: "avião", "academia", "telas").

## Música e ritmo
6. **Música contínua a partir do início**, a menos que a spec diga outra coisa. Não emendar trechos e não usar a parte agitada se a spec pedir um clima calmo.
7. **Cortar nas frases da música, não em toda batida.** Os cortes caem em onsets detectados (`tools/music.py`). Cada cena dura de 2 a 3 s nas partes calmas, e no mínimo 0,9 s.
8. **O vídeo termina junto com a música**, com fade de áudio de 2 s e fade para preto de 1,2 s.

## Técnica
9. **A duração bate no quadro.** O número de quadros do vídeo final tem que ser igual a `round(duração × 23,976)`. Clipe mais curto que o seu espaço ganha câmera lenta suave, nunca encurta a timeline.
10. **O recorte quadrado vem do 4K original**, sem upscale.
11. **Cada cena tem correção própria** (pretos e brancos, exposição, balanço de branco, saturação) antes do look comum, porque a filmagem mistura LOG e cor normal.
12. **Revisar antes de entregar:** uma prancha com um quadro de cada cena (enquadramento e títulos), a contagem de quadros e o loudness. Avisar o que não foi verificado, como assistir com som.

## Privacidade
13. Nunca versionar quadros, vídeos, nomes ou caminhos pessoais. `projects/*/work/` e as mídias ficam fora do git.
