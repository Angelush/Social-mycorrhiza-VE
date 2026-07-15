# Constraints — D2: anclaje

## MUST

- **C-d2.1 — `anclar` es pura: sin I/O, sin red, sin reloj, sin aleatoriedad.** *Porque:* N5 —
  la publicación es integración del llamador. Un motor que publica necesita red, y un motor con
  red se cae en los apagones (§2.9) y se vuelve un punto capturable.
- **C-d2.2 — `anclar` verifica la cadena antes de emitir.** *Porque:* anclar una cadena rota
  publica un compromiso sobre evidencia inválida **y le da credibilidad**. Es peor que no
  anclar.
- **C-d2.3 — Determinismo byte a byte:** mismos eventos y mismo rango → misma raíz, en
  cualquier nodo. *Porque:* L4/I4 heredadas — los apagones no rompen la evidencia; cualquier
  nodo de la célula debe poder anclar y obtener lo mismo. Si dos nodos emiten raíces distintas
  para el mismo período, la célula tiene dos verdades.
- **C-d2.4 — Nivel impar: promocionar, jamás duplicar la última hoja.** *Porque:* duplicarla
  permite construir dos conjuntos de eventos distintos con la misma raíz (la vulnerabilidad
  Merkle de Bitcoin, CVE-2012-2459). La evidencia inviolable dejaría de serlo justo en el
  delta cuyo propósito es que lo sea.
- **C-d2.5 — `verificar_inclusion` NO recibe los eventos.** Solo hoja, prueba y raíz.
  *Porque:* es la función que corre el **árbitro**, que por N7 no debe recibir el libro. Si
  necesitara los eventos, el delta no habría resuelto nada.
- **C-d2.6 — Período vacío → `ValueError`.** *Porque:* una raíz que no compromete a nada da
  falsa sensación de evidencia; publicarla es afirmar algo sin contenido.

## MUST-NOT

- **N-d2.1 — Ni LLM ni smart contract en la ruta.** *Porque:* N5 heredada. La cadena pública
  recibe un hash; el clearing sigue off-chain y determinista.
- **N-d2.2 — `anclar` no toca el estado ni emite evento.** *Porque:* es read/emit, radio
  ninguno. Si anclar mutara, sería una operación de valor y necesitaría la puerta (M8).
- **N-d2.3 — Ningún manejo de claves, direcciones ni firmas.** *Porque:* N9/I-VE4 — eso es D4,
  y ni siquiera allí el motor custodia.
- **N-d2.4 — La raíz publicada jamás lleva identidades ni montos en claro.** *Porque:* N7 — un
  ancla pública legible es un mapa de matraqueo con sello de tiempo.

## PREFERENCIAS

- **P-d2.1 —** Cadencia de anclaje diaria/semanal (§3.3: timestamping barato). Es decisión
  operativa del comité, no del motor: `anclar` recibe el rango, no lo elige.

## ESCALADA

- **E-d2.1 —** Si alguien propone que el motor publique «para automatizar» → E1. La frontera
  es que el motor no tiene red, y esa frontera es lo que lo hace correr en un apagón.
