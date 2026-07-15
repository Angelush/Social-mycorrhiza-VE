# Acceptance — D4: multisig

> `tasks.md` TB.8: «doc presente; helpers testeados; motor sin claves (N9)». Gate humano
> además de máquina (el documento no tiene tests — ST-d4.3).

## AC-d4.0 — M9 cumplido (**bloqueante, se verifica primero**)

Existe `docs/verificaciones/AAAA-MM-DD-sanciones-multisig.md`, **fechado**, cubriendo:
sanciones (EOs, GLs aplicables, SDN), marco cripto, marco fiscal. Sin datos personales (N8).

Pass/fail: archivo presente + fecha parseable + secciones presentes. **Si falla, TB.8 no
empieza.** *Porque:* C-d4.1 — el §5 está en flujo; re-verificar, no recordar.

## AC-d4.1 — `verificar_umbral` rechaza lo incoherente

| Política | Resultado |
|---|---|
| `umbral=2, total=3`, 2 local + 1 diáspora | ✅ |
| `umbral=3, total=5`, 3 local + 2 diáspora | ✅ |
| `umbral=1, total=3` | `ValueError` — una wallet con pasos extra (F-d4.3) |
| `umbral=4, total=3` | `ValueError` |
| `umbral=2, total=6` | `ValueError` |
| `len(firmantes) != total` | `ValueError` |
| direcciones duplicadas | `ValueError` |
| alias duplicados | `ValueError` |
| **cero firmantes `diaspora`** | `ValueError` — un solo punto de presión física (F-d4.4) |
| **cero firmantes `local`** | `ValueError` — la célula pierde su fondo |

Pass/fail: raise / aceptación. *Porque:* C-d4.4/C-d4.5.

## AC-d4.2 — El motor no custodia (**el que importa**) (fija F-d4.1)

- Grep sobre `B2B-VE/src/`: ningún literal con forma de clave privada, semilla, mnemónico
  (BIP-39) ni WIF. Cero coincidencias.
- AST: ninguna función recibe, guarda ni devuelve material de clave; ningún import de librería
  criptográfica de firma (`ecdsa`, `eth_account`, `bitcoinlib`, `nacl`…). Solo `hashlib`, que
  ya estaba (hashes, no firmas).
- `politica` no tiene campo para clave privada: el esquema es cerrado y no la admite.

Pass/fail: grep vacío + AST limpio + `ValueError` al pasar una clave.

*Porque:* N9/I-VE4 — custodia en código = trono que capturar, y es el único que la
arquitectura no tiene todavía.

## AC-d4.3 — Los helpers son puros

Con `socket.socket` y `open` parcheados para lanzar, los tres helpers completan. No mutan su
entrada. Deterministas entre procesos. Pass/fail: completa + igualdad.
*Porque:* C-d4.2 (F-d4.2) — un helper que consulta la cadena le da red al motor.

## AC-d4.4 — Sin identidades en el documento ni en los fixtures (fija F-d4.7)

El documento de gobernanza y los fixtures usan **alias y roles**, jamás nombres reales,
direcciones reales con fondos, ni ciudades concretas de firmantes. Las direcciones de test son
sintéticas y están marcadas.

Pass/fail: revisión (gate humano) + los patrones de identidad del bloque heredado
(`_value_has_identity_shape`) no encuentran nada. *Porque:* N-d4.5/N8 — el repo es público; una
lista de quién controla el fondo es una lista de objetivos.

## AC-d4.5 — `verificar_formato_direccion` verifica formato, y solo formato

- Dirección TRC-20 sintáctica válida → `True`; con checksum roto → `False`; cadena vacía,
  `None`, no-str → `False`.
- **No hace ninguna llamada de red** (cubierto por AC-d4.3).
- La función **no** afirma que la dirección exista ni que tenga saldo: su docstring lo dice
  explícitamente.

Pass/fail: booleano + revisión del docstring. *Porque:* comprobar existencia exige red; un
checksum mal escrito es caro y barato de cazar, y lo demás es del comité.

## AC-d4.6 — El documento dice qué NO cubre

`gobernanza-multisig.md` contiene una sección explícita de límites: riesgo Tether no
eliminable, congelamiento OFAC mitigado-no-evitado, coerción repartida-no-eliminada, ledger y
on-chain pueden divergir sin oráculo.

Pass/fail: gate humano (M1). *Porque:* C-d4.6/N10 — un documento que solo enumere garantías
miente por omisión, y es el documento con el que un comité decide dónde pone su dinero.

## AC-d4.7 — `describir_politica` es legible y no filtra

Devuelve markdown con umbral, total, alias y roles. **Sin direcciones completas** (truncadas) y
sin ningún dato que no estuviera en la política. Pass/fail: subcadena + ausencia.
