# Failure model — D2: anclaje

## Modos de fallo (F-d2#)

- **F-d2.1 — La duplicación de la última hoja.** El ejecutor implementa Merkle copiando el
  patrón más común (Bitcoin clásico: `if n impar: hojas.append(hojas[-1])`). Con eso, dos
  conjuntos de eventos distintos producen la misma raíz — **la evidencia inviolable deja de
  serlo, en el delta cuyo único propósito es que lo sea**. *Mitigación:* C-d2.4 (promocionar).
  *Detección:* AC-d2.4, que construye el par colisionante explícitamente.
- **F-d2.2 — El motor que publica.** «`anclar()` ya calcula la raíz; que la mande él.» Ahora el
  motor tiene red: se cae en apagones (§2.9), necesita credenciales, y se vuelve capturable.
  *Mitigación:* C-d2.1/N5. *Detección:* AC-d2.2 (pureza).
- **F-d2.3 — Anclar una cadena rota.** Se emite la raíz sin verificar. El compromiso publicado
  **certifica** eventos manipulados; el sello le da la credibilidad que le faltaba al fraude.
  *Mitigación:* C-d2.2. *Detección:* AC-d2.5.
- **F-d2.4 — La prueba que necesita el libro.** `verificar_inclusion(events, seq, raiz)` — firma
  cómoda, y destruye el delta: el árbitro tendría que recibir el ledger completo (N7).
  *Mitigación:* C-d2.5 fija la firma **sin** `events`. *Detección:* AC-d2.3 (inspección de firma
  + el test corre sin los eventos en el alcance).
- **F-d2.5 — El orden por hash.** Ordenar las hojas por su hash «para canonicalizar» rompe la
  correspondencia con `seq` y hace la prueba de inclusión ambigua. *Mitigación:* orden = `seq`
  ascendente, fijado en spec §4. *Detección:* AC-d2.1 (determinismo + un caso donde el orden
  por hash difiere del orden por seq).
- **F-d2.6 — `anclar` con `ratified_by`.** El ejecutor lee M8 («toda operación de valor nueva
  pasa por la puerta»), ve `anclar` en la lista de M8 y le añade ratificación. No es un fallo de
  seguridad, es un fallo de comprensión que **añade fricción a una función pura** y sugiere al
  siguiente lector que `anclar` mueve valor. *Mitigación:* spec §5 — `anclar` no mueve valor;
  M8 nombra las tres operaciones nuevas, y para ésta la respuesta es que no necesita puerta
  porque no tiene radio.

## Hallazgos de estrés (ST-d2#)

- **ST-d2.1 — La raíz sola no prueba cuándo.** Merkle prueba «esto estaba en este conjunto», no
  «esto existía el martes». La marca temporal la da la **publicación** en una cadena pública,
  que está fuera del motor. *Consecuencia:* el motor no puede garantizar la propiedad que
  §2.11 necesita; solo produce el insumo. **Señalado**, no fake-resuelto.
- **ST-d2.2 — El anclaje no impide reescribir: permite detectarlo.** Una célula puede llevar
  dos libros y anclar el conveniente. Contra eso el mecanismo no es criptográfico sino social
  (réplica entre nodos de la célula, §3.3). **Señalado.**
- **ST-d2.3 — Auto-confirmación.** Los tests de Merkle los escribe quien implementó Merkle; una
  construcción mal entendida se verifica consigo misma. *Mitigación:* AC-d2.4 no comprueba la
  implementación contra sí misma, sino que **construye el par colisionante** que la
  duplicación produciría y exige raíces distintas. Es un test que solo pasa si la construcción
  es correcta, no si es consistente.
- **ST-d2.4 — Rango que cruza un hueco.** `desde_seq`/`hasta_seq` con `seq` faltantes en medio
  (eventos no entregados). `verify_chain` ya lo caza (exige `seq == i+1`), pero **sobre la
  lista que recibe** — si el llamador pasa una sublista, la verificación es de la sublista.
  *Mitigación:* `anclar` recibe la lista **completa** de eventos y el rango como enteros; nunca
  una sublista pre-recortada. Fijado en la firma (§4).

## Abierto — no fake-resolver (N10)

- La marca temporal depende de la publicación, que es del llamador (ST-d2.1).
- El anclaje no impide el doble libro, solo lo hace detectable si alguien compara (ST-d2.2).
- Publicar con qué cadencia, en qué cadena y quién paga el gas: decisión operativa del comité
  (Etapa 2, §7). El motor no opina.
