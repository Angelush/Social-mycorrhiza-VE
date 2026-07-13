# Failure model — Área f · Convergencia

## `paso_maquinaria` mal usada como señal sobre persona
Un intento de `{"señal": "paso_maquinaria", "sobre": "persona:fulano"}`. *Prevención:* la señal solo
es válida sobre `zona:*`; una traza sobre persona se rechaza (regla de traza-ambiental). Es lo que
AC-C1 verifica.

## Estampida no amortiguada
Una ráfaga de `presencia` que supera el canal antes de que el cap actúe. *Mitigación:* el
velocity-cap por ventana throttlea; en `severa` el cap es estricto. El cap nunca se apaga (C-f3).

## Alerta sin contexto propagada
Una `alerta` desnuda que dispara pánico o marca informal. *Prevención:* cortacircuito
contexto-antes-de-juicio la amortigua hasta que porte contexto.

## Transporte/malla fuera de alcance (señalado)
El límite de 512 bytes en `severa` modela SMS/LoRa, pero el núcleo puro no implementa el transporte;
la entrega real es responsabilidad del llamador. **Señalado en `lo-intocable.md`.**

## Ejemplo no verificado en campo
El escenario La Guaira/Caracas es ilustrativo; los parámetros concretos del cap no están validados
en un desastre real. *Señalado:* el test verifica el *mecanismo* (throttling, no-persona,
amortiguación), no la calibración óptima.
