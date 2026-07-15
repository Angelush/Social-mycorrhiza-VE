# Constraints — D7: exportes

## MUST

- **C-d7.1 — `exportar_registros` es pura: devuelve la cadena, no escribe.** *Porque:* mismo
  porqué que `anclar` (C-d2.1) — el motor no tiene disco ni red; es lo que lo hace correr en un
  apagón y no ser capturable.
- **C-d7.2 — El exporte se deriva de los EVENTOS, no del estado.** *Porque:* un exporte fiscal
  es un histórico de período; el estado es el presente. Y los eventos ya están encadenados: el
  exporte hereda la verificabilidad gratis.
- **C-d7.3 — Reutilizar el scope de D3.** *Porque:* P4 (reutilizar antes que crear) y porque
  dos controles de acceso divergen: se arregla uno y el otro queda con el agujero.
- **C-d7.4 — Todo exporte público pasa por seudonimización.** *Porque:* N7/C-d3.4 — jamás
  identidad + monto en claro.
- **C-d7.5 — La moneda va una vez en la cabecera, jamás por línea.** *Porque:* la célula es
  mono-moneda (I-VE2). Una columna por línea sugiere que puede variar, y la pregunta siguiente
  es «¿a qué tasa convierto?». **El formato también puede hacer representable el FX.**
- **C-d7.6 — Importes en centavos enteros.** *Porque:* M4. Un exporte con decimales
  reintroduce el float en el punto exacto donde el número sale del sistema y entra en una hoja
  de cálculo.

## MUST-NOT

- **N-d7.1 — El sistema no declara por nadie.** Ni formularios, ni cálculo de IGTF, ni
  clasificación fiscal. *Porque:* §5 — el tratamiento del crédito mutuo es **ambiguo** y el
  enforcement, arbitrario. Declarar por el miembro sería tomarle una decisión con
  consecuencias legales personales bajo un marco que no existe. Es lo que I3 reserva al humano.
- **N-d7.2 — No prometer neutralidad fiscal.** Ni en el código, ni en los docs, ni en el
  README. *Porque:* §5/§6.7. Es una promesa que el fork no puede cumplir y que expondría a los
  miembros.
- **N-d7.3 — Ninguna conversión, total en otra moneda ni tasa en el exporte.** *Porque:*
  N-d1.1/I-VE1.
- **N-d7.4 — Ningún dato real de personas en fixtures ni goldens de exporte.** *Porque:* N8.

## PREFERENCIAS

- **P-d7.1 —** Incluir `hash_evento` y `raiz_ancla` (D2) en el exporte. *Porque:* sin
  tribunales (§2.11), un exporte vale lo que valga su verificabilidad ante un tercero.

## ESCALADA

- **E-d7.1 —** Si alguien pide que el exporte «ya calcule el IGTF para facilitar» → E1. Es
  N-d7.1: facilita hoy y clasifica al miembro mañana, bajo un marco que puede cambiar.
- **E-d7.2 —** Reclasificación fiscal material (SENIAT tratando cada compensación como pago
  gravable) → E3: pausar la fase afectada; no incrustar la interpretación en el código.
