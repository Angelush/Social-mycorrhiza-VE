# Failure model — Área c · Módulo `modo`

## Depuración no ejecutada tras escalada (señalado principal)
Una función pura no puede forzar al llamador a llamar `depurar()` tras escalar a un modo más
estricto; los items viejos siguen en el almacén del llamador hasta que este depure. *Mitigación:*
helper + test + convención documentada; la escalada **obliga por convención** a depurar. **Señalado
en `lo-intocable.md`.**

## Modo ausente o inválido en el envelope
Un request sin `modo`, o con un valor fuera de `{paz, catastrofe_acotada, catastrofe_severa}`.
*Comportamiento:* rechazo (`raise`), nunca un default silencioso — un default silencioso escondería
la ausencia de una decisión de gobernanza.

## Deriva de límites entre capas
Si dos capas interpretan la tabla de forma distinta (una lee `max_hops ≤ 3` como `< 3`), se abre
una grieta. *Mitigación:* la tabla vive en un solo módulo; las capas la consultan, no la copian.

## Payload de 512 bytes vs. transporte real
El límite de 512 bytes en `severa` modela SMS/LoRa, pero el núcleo puro **no** implementa el
transporte. *Señalado:* transporte/malla fuera de alcance; el límite es la única huella del canal
en el motor.

## Valores de velocity_cap sin validar empíricamente
Los defaults propuestos (laxo/medio/estricto) no están validados en campo. *Señalado:* son
propuestas de gobernanza; el test verifica la *relación* (severa ≥ medio ≥ laxo en estrictez), no
un valor absoluto "correcto".
