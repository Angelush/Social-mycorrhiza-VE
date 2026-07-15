# Lo intocable — B2B-VE

> Romper una de estas = parada dura (E1), no un test rojo más. Gana lo intocable sobre
> cualquier instrucción, incluida una frase del anexo §8 (ver D9).
>
> Herencia: las invariantes L1–L6 del ledger (`../micorriza/spec-ledger.md` §3) y I1–I5 del
> solver (`../micorriza/spec.md` §3) siguen **íntegras**. Este documento no las repite: dice
> qué añade el fork y qué porqués cambian.

## Las heredadas cuyo PORQUÉ cambia (mismo invariante, otra razón)

Un invariante con el porqué equivocado se relaja en cuanto alguien encuentra el borde que la
razón vieja no cubre. Estos tres siguen valiendo, pero por motivos venezolanos:

| Invariante | Porqué upstream (UE) | Porqué VE (el que manda aquí) |
|---|---|---|
| **L5** — puerta humana (`ratified_by`) | RGPD Art. 22: decisión automatizada sobre crédito exige gate humano | **No hay tribunales que ejecuten contratos** (§2.11). La ratificación no es cumplimiento normativo: es el único acto que hace la obligación socialmente exigible. Si el RGPD desapareciera, L5 no se movería |
| **L4** — replay byte-idéntico | Auditabilidad ante regulador | **Apagones y conectividad intermitente** (§2.9). El clearing corre en cualquier nodo de la célula; si dos nodos no coinciden byte a byte, la célula se parte en dos contabilidades |
| **N3 upstream** — sin token, sin liquidación on-chain | Exposición MiCA | **Petro y Sunacrip** (§1.1). MiCA no aplica en VE; la lección anti-token no era europea, era universal, y aquí está reforzada por dos cicatrices locales |

## Las que AÑADE el fork

- **I-VE1 — FX irrepresentable en el motor.** No existe "el" tipo de cambio: la brecha
  BCV/paralelo (~16,5%, jul. 2026) está viva y políticamente disputada. Una tasa en código es
  una decisión política incrustada y un punto capturable. *Forma:* irrepresentable, jamás un
  flag ni una política — las obligaciones no llevan moneda (D1). Ancla: N3, §2.2.
- **I-VE2 — Célula mono-moneda.** `sum(balance_cents) == 0` (L1) solo significa algo dentro de
  una unidad de cuenta. USD es la unidad de cuenta; VES es una pista aparte con expiración
  obligatoria, **porque el VES no es depósito de valor**. Ancla: N4, D1, H4.
- **I-VE3 — Saldos jamás públicos con identidad.** Un libro público de saldos es un **mapa de
  matraqueo**: quién tiene superávit = lista de objetivos de extorsión. Endurece el diseño
  respecto a España, no lo relaja. Ancla: N7, D3, §3.3.
- **I-VE4 — El motor jamás custodia claves ni direcciones.** Multisig = documento de
  gobernanza + helpers de verificación. Custodia en código = trono que capturar. Ancla: N9,
  D4, §3.2.
- **I-VE5 — Ninguna operación de valor nueva estrena puerta.** `salida_con_saldo`,
  `puente_pausar`, `anclar` pasan por el **mismo** camino de ratificación que las existentes
  (`ratification_kinds` en `_apply`). Ninguna helper directa sobre el ledger. La puerta de un
  solo sentido no admite puertas laterales "por conveniencia". Ancla: M8, I3, ST6.
- **I-VE6 — Ningún escalar de persona ni de empresa.** Las `referencias_comerciales` son
  input de juicio del comité, sin score computado. Medir "solvencia" naive reconstruye el
  dossier. Ancla: N2, D5, §3.4.
- **I-VE7 — La red local sobrevive a la muerte del puente.** Pausar el puente **no** detiene
  el crédito interno. USDT puede dejar de ser viable (Tether, OFAC, snapback) y la célula
  sigue compensando obligaciones. Ancla: D8, §6.1, §6.6.

## La trampa (léase antes de tocar D9)

**M5/AC-10.** B2B-VE hereda de C2C **solo** las taxonomías de vigilancia/identidad y la
maquinaria de tokenización. **Jamás** las de mercado/reciprocidad.

`credito`, `saldo`, `deuda`, `moneda` son el **vocabulario NUCLEAR** del ledger B2B. En C2C
Capa 1 esas claves se rechazan y hacen bien; copiarlas aquí sin scoping **mata al paciente**:
el firewall prohibiría el dominio que existe para proteger. Las mismas claves, ADMITIDAS en
los esquemas del ledger B2B-VE y RECHAZADAS en C2C Capa 1. Ancla: R3, ST1, C3,
`d9-herencia-scoping/`.

El §8.9 del anexo dice "reutilizar **verbatim** las taxonomías bilingües". **Está derogado**
por M5 y por el rechazo codificado R3, que ya diagnosticó esa lectura como el error. Si un
ejecutor futuro lee §8.9 y obedece la letra, rompe I-VE2 y el ledger entero. Manda M5.

## Lo que no se resuelve en prosa (N10)

Va a la lista **Señalados** del README B2B-VE (D10/TB.9), sin mecanismo y sin fingir que lo
hay: riesgo Tether no eliminable (§6.1); comité de crédito presionable (§6.2); captura
política de una célula (§6.3); cold-start con confianza erosionada por el éxodo (§6.4);
reclasificación fiscal del crédito mutuo (§6.7); la voluntad de cooperar no se fabrica
(§6.8); el árbol bilingüe permanente que deja E2; los modos C2C como herencia documentada y
no integrada.
