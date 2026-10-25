# Estilo golden-frames

O padrão da casa: vlog cinematográfico, afetivo e calmo, feito para ser assistido em silêncio e com atenção. O ponto de partida é o perfil `styles/golden-frames.json`. Os perfis extraídos de vídeos de referência (`tools/reference_profile.py`) ajustam esses números.

## Narrativa
- **Abertura (0 a ~11 s):** 4 a 5 cenas lentas, com push-in de 5%. Começar por um plano simbólico (sombras, mãos, paisagem) com o título por cima, depois rostos sorrindo.
- **Meio:** a jornada em ordem mais ou menos cronológica, alternando pessoas e lugares. Nunca duas paisagens seguidas sem pessoas.
- **Fecho:** o momento mais afetivo (selfie dos dois, abraço com o rosto visível) dura mais e recebe o título final.

## Ritmo
| Trecho da música | Duração da cena | Corte |
|---|---|---|
| Introdução / piano solo | 2,5 a 3,5 s | início de frase |
| Desenvolvimento | 1,8 a 2,6 s | início ou meio de frase |
| Final da peça | 2 s ou mais, a última com 2 s ou mais | frase, com fade |

## Enquadramento
- **Formato:** quadrado 1:1. Entrega em 1080 (Instagram) e master em 2160.
- **Recorte:** `cx` centraliza os rostos. `zoom` de 1,2 a 2,2 com `cy` de ~0,4 fecha da cintura para cima.
- **Movimento:** push-in só na abertura. No resto, o movimento do próprio clipe.

## Cor: "cinema quente"
1. **Normalização por cena** (`tools/grade_build.py`):
   - Ponto de preto em p1 × 0,85 (máximo 0,16), que tira a névoa do LOG.
   - Ponto de branco em p99.
   - Mediana: 0,46 de dia, 0,30 à noite.
   - Balanço de branco gray-world parcial: 55% de dia, 35% à noite, para manter o calor das luzes.
   - Saturação levada a 0,40 de dia e 0,34 à noite.
2. **Look comum, aplicado a todas as cenas:**
   - Curva em S suave, com pretos lavados (0,035) e altas luzes que rolam até 0,955.
   - Sombras verde-água e altas luzes quentes.
   - Azuis puxados para o verde-água, verdes mais discretos e pele preservada.
   - Halation quente: brilho desfocado das luzes misturado em modo *screen*, com 22% de intensidade.
   - Vinheta suave e grão fino.
3. **Ajuste manual:** `exp` na cena (< 1 clareia) quando um rosto fica escuro contra o céu ou à noite.

## Tipografia
- **Abertura:** número grande em Bodoni, uma linha fina e uma palavra em Gill Sans caixa-alta, com tracking largo (~0,75 em).
- **Fecho:** linha pequena em Gill Sans caixa-alta, com a frase em Garamond itálico por baixo, no terço inferior.
- **Cor e animação:** branco a ~92%, com sombra difusa por trás (blur 12, 80%). Entra com fade de 1 s e sobe 10 px devagar.
- **Duração:** o título de abertura fica dentro da primeira cena e nunca invade a segunda.
