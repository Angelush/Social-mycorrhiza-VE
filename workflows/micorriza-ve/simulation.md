# Simulación en seco — micorriza-ve

> Tres líneas de tiempo del build completo, con el punto de pivote de cada una. Corridas
> ANTES de gastar una sola sesión de construcción real.

## Línea pesimista (~30% si se ignoran los pivotes)

TA.2 se salta la auditoría de raíces (M6) → `denominacion`/`centavos` pasan el firewall →
nadie lo nota porque los tests traducidos también olvidaron el caso → tres áreas después, el
área e descubre que la taxonomía de mercado no atrapa nada → bisección arqueológica de tres
commits, re-apertura del área a, AC-X obliga a mover las seis capas otra vez.

**Pivote:** el golden `denominacion` en `casos.json` — un caso de diez líneas que convierte
la regresión silenciosa en un rojo inmediato del gate TA.2.

**Segunda trampa de la línea:** castellanizar (b) ANTES de tener el firewall bilingüe (a).
El renombrado convierte claves inglesas en castellanas que el firewall inglés ya no ve; la
ventana entre (b) y (a) invertidas es un agujero de vigilancia representable. El orden
a→b→c del prompt es anti-colisión, no estética (ST3).

## Línea esperada (~el plan)

Fase 1: ocho episodios (TA.0–TA.8), cada uno una sesión acotada: cargar el sub-bundle del
área + la capa tocada (contexto mínimo), ejecutar, suite completa, commit con porqué, cerrar.
Fase 2 arranca al cerrar TA.2 (la maquinaria compartida existe) y corre en paralelo humano-
alternado con la Fase 1. Los puntos duros reales: TA.4/TA.5 (envelope + trinquete: tocan las
seis capas y la Capa 6 a la vez) y TB.6 (ops de valor nuevas por la puerta existente — leer
el ledger despacio antes de escribir). Fase 3 al final, con los dos SUT congelados.

**Recuperación ante crash/interrupción:** el estado vive en el repo (commits por área) y en
el bundle — ninguna sesión carga el transcript de otra. Retomar = leer `tasks.md`, el último
commit y el sub-bundle del área abierta. Una interrupción a mitad de área se retoma con
`git status` + suite: lo no commiteado se considera no hecho.

## Línea optimista (todo verde a la primera)

El riesgo de la línea feliz es declarar victoria con los normales en verde: los AC de cola
(15+ dígitos, 512 B, pausa-con-crédito-vivo, ciclo de escaladas) son EXACTAMENTE los que una
corrida fluida no ejercita sola. El gate exige los tres niveles A/B/C, no "pasó la suite".

## Puntos de contacto humano (dónde y por qué)

| Momento | Quién decide | Qué mira |
|---|---|---|
| Aprobación de cada sub-bundle (M1) | humano | ¿la spec del área contradice algún intocable? (E1/E5) |
| E2 antes de TB.1 | humano | alcance de castellanización B2B |
| Gate de cada área (M2) | humano + máquina | salida pytest real + diff legible + AC del área |
| Antes de TB.8/D8 | humano | verificación regulatoria FECHADA (M9) |
| Cierre de fase | humano | Señalados actualizado; nada resuelto en prosa (N10) |

## Chequeo episódico

Cada área es un episodio que EMPIEZA limpio (sin arrastrar contexto de otras áreas) y
PERSISTE todo su estado fuera (repo + bundle). Nada depende de la memoria de una sesión: si
`tasks.md`, los commits y los sub-bundles no bastan para retomar el build tras un mes, es un
defecto del bundle — arreglarlo ahí, no en la memoria de nadie.
