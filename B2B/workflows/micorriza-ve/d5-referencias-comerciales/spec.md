# Spec — D5: `referencias_comerciales` (veteo relacional, sin score)

> Nodo TB.5 (depende de D1/TB.2). Ancla: anexo §8.5, §3.4, §6.4; N2, I-VE6, U2, C-d9.4.
>
> **Esta es la única superficie de forma libre de la Fase 2** — y por tanto el único sitio
> donde el firewall heredado (D9) se aplica de verdad.

## 1. Qué deroga

`spec-ledger.md` fija las líneas desde `turnover_cents` (facturación declarada) por las
fórmulas `neg_line_bp`/`pos_line_bp`. Eso **supone estados financieros auditables**. En
Venezuela no los hay (§3.4).

**No se deroga la fórmula: se deroga el supuesto sobre su input.** El `turnover` sigue siendo
un número que el comité **acuerda**, no que un auditor certifica. D5 añade lo que el comité usa
para acordarlo — y no toca las líneas.

## 2. El esquema

```python
referencias_comerciales = [
    {
        "avalista": "member_id",            # quién avala — miembro de la célula
        "relacion_declarada": "proveedor" | "cliente" | "ambos",
        "antiguedad_meses": int >= 0,       # cuánto llevan operando juntos
        "nota": str,                        # texto libre del comité, opcional
    },
    ...
]
```

Se adjunta como **input del comité** en `add_member`/`update_member`, dentro del payload que ya
lleva `ratified_by`.

**Ningún score.** Ni computado, ni derivado, ni agregado. La lista es lo que el comité **lee**
para juzgar; el juicio sale de la reunión y entra al motor como `ratified_by` + las líneas que
el comité fija a mano.

*Porque:* N2/I-VE6. Medir «solvencia» naive reconstruye el dossier — y en Venezuela el dossier
es un mapa de matraqueo (H3). La solvencia es un **juicio del comité**, no un escalar del
sistema. El upstream ya lo tenía (scoring = `[ESTOCÁSTICO assist]` con gate RGPD); aquí el
scoring **no existe**, ni siquiera como adviser.

## 3. Por qué `antiguedad_meses` es un entero y NO un score

Es el borde peligroso del delta: `antiguedad_meses` es un número asociado a una relación, y
`len(referencias_comerciales)` es un número asociado a una empresa. **Sumarlos, promediarlos o
ponderarlos produce un score.** La línea:

| Permitido | Prohibido |
|---|---|
| El motor **almacena** `antiguedad_meses: 36` | El motor **computa** `confianza = f(antiguedad, n_avales)` |
| El comité lee «3 avalistas, 36 meses, proveedor» y decide | El motor ordena/rankea/percentila a los solicitantes |
| El motor guarda la decisión del comité (`ratified_by` + líneas) | El motor **sugiere** una línea a partir de las referencias |

**Regla:** el motor no deriva **ningún** número nuevo a partir de `referencias_comerciales`.
Las almacena y las devuelve tal cual, al comité. Cualquier función que las tome como entrada y
devuelva un número es un score, se llame como se llame (H1).

## 4. Firewall (la aplicación real de D9)

`referencias_comerciales` es texto y estructura provista por humanos → **superficie de forma
libre** → se escanea con `_contains_forbidden_key` + `FORBIDDEN_KEYS` + los patrones de
identidad del bloque heredado (C-d9.4).

Rechaza:
- Una clave `puntuacion`, `score`, `rating`, `reputacion`, `lista_negra`… (`FORBIDDEN_KEYS`).
- Un **valor** con forma de cédula/RIF/teléfono (`_value_has_identity_shape`) — incluida la
  `nota` de texto libre. *Porque:* N8 (el repo jamás contiene datos reales de personas) y
  porque una cédula en la nota del comité es el dossier entrando por la puerta de servicio.

**Auditoría M6 de las claves elegidas** (C-d9.5, verificada en TB.1):
`referencias_comerciales`, `avalista`, `relacion_declarada`, `antiguedad_meses`, `nota` →
ninguna coincide con `FORBIDDEN_KEYS` por token exacto. **Se evitó deliberadamente `veto` y
`sancion`**, que sí están en la lista (ver `../d9-herencia-scoping/spec.md` §3). El campo se
llama `avalista`, no `veto_del_comite`.

## 5. Contrato de implementación (TB.5)

1. `referencias_comerciales` es **opcional** en el payload. *Porque:* U2 — B2B es
   *permissioned* con veteo relacional, pero el veteo **es la reunión**, no el campo. Exigir el
   campo haría que el comité rellenara formularios para satisfacer al motor, que es
   exactamente «codificar al gestor humano pero más rápido» (Mini-Me).
2. Si viene: lista de dicts; cada dict con `avalista` ∈ `state["members"]`,
   `relacion_declarada` ∈ el enum, `antiguedad_meses` entero ≥ 0 (no bool). Cualquier clave
   desconocida → `ValueError` (esquema cerrado **además** del firewall).
3. `avalista` no puede ser el propio solicitante (auto-aval).
4. Se guarda en el payload del evento → queda en la cadena → auditable y anclable (D2).
5. Visible **solo** con `scope="comite_credito"` (D3). Jamás en `publico`.
6. **Cero derivación.** Ninguna función nueva que las tome y devuelva un número.

## 6. Qué NO hace D5

- No computa score, ranking, percentil ni «confianza» (§3).
- No sugiere líneas. El comité las fija a mano.
- No verifica las referencias. Que el avalista diga la verdad es problema social, no técnico.
  **Señalado.**
- No cruza referencias entre células. La reputación no viaja sin consentimiento explícito (U4)
  — y la federación es Etapa 3.
- No resuelve el cold-start (§6.4: la confianza está erosionada por el éxodo y la informalidad
  dificulta el veteo). El código no fabrica voluntad de cooperar. **Señalado.**
