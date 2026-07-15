# Spec — D10: branding, README B2B-VE y cierre de Fase 2

> Nodo TB.9 (depende de TB.2–TB.8). Ancla: anexo §8.10, §1.1, §2.10; N1, P2, M4, AC-9.
> Nodo DOCUMENTAL + los property tests de conservación. Análogo a TA.8 en Fase 1.

## 1. El branding no es marketing: es una restricción de diseño

**Prohibido en nombre y lenguaje de producto:** `moneda`, `coin`, `token`, `petro`, `comunal`,
`cripto` como promesa, «puntos», «billetera».

**Es:** un **circuito de crédito comercial** de la cámara/gremio. Un registro de compensación
de obligaciones.

*Porque:* el Petro (moneda estatal fallida, terminada en 2024) y el escándalo Sunacrip
(~$3.000M desaparecidos, regulador intervenido en 2023) dejaron **cicatrices simbólicas**:
cualquier «moneda» nueva huele a estafa. Y las monedas comunales y los «mercados de trueke»
estatales cargan con el bagaje clientelista (§2.10, H5). Un nombre equivocado no es un
problema de adopción: es el motivo por el que un comerciante no abre la puerta.

**Y hay una razón más dura:** N1 prohíbe el token de verdad, no solo su nombre. Si el
vocabulario dice «moneda», alguien acabará pidiendo que sea transferible fuera de la red — y
esa petición sonará razonable, porque el nombre ya lo prometió. **El branding es la primera
línea de defensa de N1**, no su decoración.

## 2. Alcance de la revisión de vocabulario

Todo lo que un humano lee: `README.md`, docstrings, mensajes de error, nombres de las APIs
nuevas, el documento de gobernanza (D4), los exportes (D7).

**Ojo con la herencia:** `moneda` **es** una clave del esquema (D1, `params["moneda"]`) y eso
está bien — describe la unidad de cuenta, no promete un activo. El prohibido es el **lenguaje
de producto**: «la moneda de la cámara», «nuestro token». La distinción es la misma de M5:
la palabra no es el problema; lo es qué nombra.

*(Y por eso `moneda` está admitida en B2B-VE y rechazada en C2C Capa 1 — AC-10.)*

## 3. El README B2B-VE

`B2B-VE/README.md`, en castellano (E2: los docs sí). Contiene:

1. **Qué es:** circuito de crédito comercial de la cámara/gremio. Qué NO es: moneda, token,
   inversión, banco.
2. **Filosofía heredada:** clearing determinista off-chain + crédito mutuo + confianza
   relacional + gestión activa. Las invariantes L1–L6 e I1–I5, **referenciando** el bundle
   upstream, no re-tecleadas.
3. **Los deltas VE** (D1–D10) con qué cambió y por qué, **enlazando** a este sub-bundle.
4. **Tabla de unidad de cuenta** referenciando la fuente única (D1), no copiada.
5. **Procedencia por módulo:** qué es upstream, qué es fork, qué área lo tocó.
6. **La lista Señalados consolidada** (§4).
7. **El seam bilingüe** que dejó E2, dicho sin disimulo (`context.md` §2).

*Porque el README es lo que un ejecutor futuro lee antes de romper algo*, y porque AC-9 es un
**checklist de honestidad**: el README no puede prometer lo que el código no hace.

## 4. La lista Señalados (consolidada, N10)

Recogida de los failure-models de D1–D9. **Nada de esto se resuelve en prosa.** Mínimo:

| Señalado | De |
|---|---|
| Riesgo Tether: contraparte + congelamiento OFAC; no eliminable | §6.1, D4 |
| Comité de crédito presionable; el multisig reparte la coerción, no la elimina | §6.2, ST-d4.1 |
| Cooptación política de una célula; el cortafuegos es que no arrastre a las demás | §6.3 |
| Cold-start con confianza erosionada por el éxodo | §6.4, ST-d5.3 |
| Reclasificación fiscal del crédito mutuo; sin neutralidad prometida | §6.7, D7 |
| La voluntad de cooperar no se fabrica | §6.8 |
| El motor no puede impedir que una célula VES incumpla su expiración | ST-d1 |
| «Corto» no está definido para `expira_en_dias` | D1 §3 |
| Dos células (USD/VES), un padrón: un panel que las sume exigiría una tasa | ST-d1.3 |
| La marca temporal del ancla depende de una publicación externa | ST-d2.1 |
| El anclaje no impide el doble libro; permite detectarlo si alguien compara | ST-d2.2 |
| Correlación entre salidas por seudónimo estable | ST-d3.1 |
| El motor no autentica; el scope es un contrato, no un guardia | F-d3.6 |
| La agregación no anonimiza en células diminutas | ST-d3.3 |
| Referencias no verificadas: un anillo de avales mutuos pasa | ST-d5.2 |
| Salidas en cascada: válidas una a una; el conjunto lo ve el comité | ST-d68.2 |
| Puente pausado + saldo positivo atrapado | ST-d68.3 |
| Ledger y on-chain pueden divergir; no hay oráculo | ST-d4.4, D6 |
| El seam bilingüe permanente que deja E2 (pospuesto, no cerrado) | `context.md` §2 |
| Los modos C2C: herencia documentada, no integrada | D9 §1 |
| La séptima copia del bloque firewall: acoplada por constante, sin test cross-árbol | ST-d9.4 |
| La colisión `veto`/`sancion` está evitada, no resuelta | D9 §3 |
| **Fase 1 publicó un md5 falso (`5d693ec`) en 4 DESIGN, el README de C2C-VE y 2 comentarios de `src/`; el real es `758094a9`. Las 6 capas C2C-VE siguen sin test de byte-identidad — solo B2B-VE lo tendrá** | D9 §2.1, ST-d9.4 |

## 5. Los property tests finales

`test_conservacion_hiperinflacion.py` (hypothesis):

- **PB-1 — Conservación a escala de hiperinflación (AC-4/M4).** Importes de **15+ dígitos** en
  centavos: `clear()` conserva las posiciones netas **exactamente**, y `sum(balance_cents) == 0`
  se mantiene. *Porque:* inflación ~229% (§2.1); los enteros de Python lo permiten y el test lo
  fija. Es el único sitio donde se prueba a esa escala (D1 §7 lo difirió aquí).
- **PB-2 — Ningún float en ninguna ruta de valor.** Type-walk sobre estados y eventos tras
  secuencias arbitrarias.
- **PB-3 — L1 tras cualquier secuencia de operaciones aceptada**, incluidas las nuevas
  (`member_exited`, `bridge_paused/resumed`).
- **PB-4 — Determinismo de `anclar`** sobre cadenas arbitrarias (complementa AC-7/D2).

## 6. Qué NO hace D10

- No renombra identificadores (E2). El seam se **documenta**, no se cierra.
- No resuelve ningún Señalado. Los enumera — que es exactamente el punto (N10:
  flagged, not fake-resolved).
- No cambia `src/` salvo lo que exija el vocabulario legible (mensajes, docstrings).
