# Intent — B2B-VE

> Extiende [`../micorriza/intent.md`](../micorriza/intent.md). El objetivo real del bundle
> upstream sigue vigente íntegro: **construir la institución de coordinación y distribución**,
> no una IA más potente ni una blockchain. Lo que cambia es dónde muerde.

## El objetivo real, re-anclado

El upstream construye crédito mutuo **contracíclico**: gana cuando el banco se retira, pierde
relevancia cuando el crédito bancario vuelve a ser barato (brief §7.4).

En Venezuela **no hay crédito bancario con el que competir** (§2.5: corresponsalía cortada,
encaje altísimo, cartera minúscula). La ventaja contracíclica no es una fase del ciclo: es
**permanente**. Las pymes venezolanas viven en un momento Sardex-2009 perpetuo.

**Consecuencia de diseño, no de marketing:** el upstream podía permitirse que el puente fiat
fuera la parte cómoda del sistema, porque la banca funcionaba detrás. Aquí el puente es la
parte **frágil** (Tether, OFAC, snapback) y el crédito interno es la parte **robusta**. El
sistema se diseña para sobrevivir a la muerte del puente — no como modo degradado, sino como
caso esperado (D8/TB.6, riesgo 1 y 6 del §6).

## Chequeo Mini-Me (AGD-014) — heredado y agudizado

Sigue prohibido codificar "un gestor humano, pero más rápido". Y en VE hay una segunda forma
del mismo error, más tentadora: **codificar al juez que no existe**. Sin tribunales
funcionales (§2.11), la tentación es que el motor arbitre disputas, calcule solvencia, o
"decida" quién tiene razón. No lo hace. El motor produce **evidencia que nadie puede
reescribir** (D2) y se la entrega a humanos que juzgan (comité + árbitro gremial). La
capa combinatoria se automatiza; la relacional se queda humana. Esa frontera no se mueve
porque el entorno sea más hostil — se mueve **menos**.

## Alcance de ESTE workstream (Fase 2, TB.0–TB.9)

Los deltas 1–10 del anexo §8 sobre el prototipo B2B existente. Concretamente:

1. Corregir la unidad de cuenta y hacer el FX irrepresentable (D1).
2. Convertir la cadena de hashes —que **ya existe y ya está testeada**— en evidencia
   anclable (D2).
3. Cerrar la visibilidad de saldos (D3) y abrir los exportes por miembro (D7).
4. Especificar los bordes que el upstream no tenía porque España no los tiene: salida con
   saldo (D6) y pausa del puente (D8).
5. Sustituir el veteo por estados financieros por veteo relacional (D5).
6. Documentar la gobernanza del multisig sin que el motor toque una clave (D4).
7. Heredar de C2C **solo lo que corresponde** (D9) y no llamar moneda a nada (D10).

## Fuera de alcance (bordes del haz)

- **La red.** El cuello de botella vinculante sigue siendo distribución/confianza
  (cold-start, §6.4), y el código no lo resuelve. Construimos el núcleo técnico; no fingimos
  que arranca la red.
- **Las Etapas 0–3 del §7** (validar → piloto → reservas/puente → federación): son trabajo de
  humanos con la herramienta ya construida.
- **La custodia.** Ni claves, ni direcciones, ni firmas (N9).
- **La asesoría legal y fiscal.** El sistema es compliance-READY, no compliance-DEPENDENT: da
  registros limpios para que cada miembro cumpla donde decida. **No declara por nadie y no
  promete neutralidad fiscal** (§5).
- **La conversión.** No existe "el" tipo de cambio. Convertir es una decisión humana
  documentada fuera del protocolo (N3/I5).
