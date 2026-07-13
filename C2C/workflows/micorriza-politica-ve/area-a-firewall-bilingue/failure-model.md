# Failure model — Área a · Firewall bilingüe

## Falsos negativos residuales (una forma prohibida que se cuela)
- **Sinónimo no listado / lengua no cubierta.** El conjunto es explícito, no derivado; un término
  nuevo (`kredito`, jerga, otra lengua) no se captura hasta añadirlo. *Mitigación:* revisión
  periódica de gobernanza; el sesgo es sobre-rechazar. **Señalado.**
- **Escalar semántico en texto libre.** "Le pongo un 3 a Fulano" en un valor de prosa: no hay clave
  ni patrón de identidad; el firewall no lo ve. *Fuera de alcance por diseño* — la semántica es
  gobernanza humana. **Señalado en `lo-intocable.md`.**
- **Identidad ofuscada.** Una cédula escrita con letras ("uve doce...") evade el regex.
  *Mitigación:* ninguna determinista; señalado.

## Falsos positivos (algo legítimo rechazado)
- **Colisión con ayuda mutua** — la clase peligrosa. `banco_de_tiempo`, `zona_urbana`,
  `underscore`, `rango_de_fechas` eran rechazados por substring; el token exacto los admite. Cada
  uno tiene su test de regresión (AC-T1, AC-T4).
- **Raíz demasiado ávida.** `denominat`, `cents`, `saldo` como tokens exactos podrían capturar un
  uso legítimo (`saldo` es prohibido en libro de reciprocidad de Capa 1 **a propósito**; pero en un
  campo de dominio distinto podría ser inocente). *Mitigación:* auditoría de expansión de raíces
  (M6), documentada por raíz; el token exacto ya elimina las colisiones de substring conocidas.

## Análisis de sesgo (documentado, requerido por §B.8)
Sobre-rechazar sigue siendo la política segura **excepto** cuando colisiona con el dominio de ayuda
mutua, donde un falso positivo silencia coordinación legítima. El matching por tokens + la
auditoría de raíces resuelven las colisiones **conocidas**; las desconocidas se cubren con el
sesgo (rechazar) y la revisión de gobernanza, nunca fingiendo cobertura total.

## Vector de evasión por normalización
Un atacante podría intentar acentos exóticos o Unicode confusable (`ѕcore` con S cirílica). NFD
normaliza diacríticos latinos pero **no** homoglifos de otros alfabetos. **Señalado**; mitigación
futura opcional (normalización de confusables) es decisión de gobernanza, no de este núcleo.
