# Failure model — Área e · Doble moneda

## Conversión disfrazada (el modo de fallo que el área existe para bloquear)
Un llamador intenta meter una tasa como dato (`{"tasa_de_cambio": 3600}`) o mezclar monedas para
forzar una comparación. *Comportamiento:* rechazo por taxonomía (`tasa_de_cambio`, `fx`, `paralelo`,
`bcv`) o por `ErrorDeBrechaAseguramiento` (mezcla). El motor nunca convierte.

## Pérdida de precisión a escala de hiperinflación
Un importe VES de 15+ dígitos redondeado por un float. *Prevención:* enteros de unidad mínima; el
test AC-D2 fija la conservación exacta a esa escala.

## Inflación no modelada (señalado)
El valor real de una campaña VES se erosiona entre `ahora` y `expira_en`. El motor no lo modela
(sería otra tasa). *Mitigación:* convención de `expira_en` corto para VES — del llamador, no del
motor. **Señalado en `lo-intocable.md`.**

## Fuga de denominación a salas no-mercado
Una clave de precio en `don_comunal`/`igualdad`. *Prevención:* la taxonomía de mercado bilingüe la
rechaza en Capa 1 (membrana direccional).

## Resto del reparto del bono
El reparto entero deja un resto; su asignación debe ser determinista (regla heredada). Un resto mal
manejado rompería la conservación. *Prevención:* resto determinista testeado (heredado + AC-D2).
