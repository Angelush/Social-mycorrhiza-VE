# Constraints — D9: herencia con alcance

> Cada regla con su porqué. IDs locales `C-d9*`; los globales (M5, M6, R3) viven en
> [`../../../workflows/micorriza-ve/constraints.md`](../../../../workflows/micorriza-ve/constraints.md).

## MUST

- **C-d9.1 — El bloque `BEGIN…END shared firewall machinery` se copia byte a byte, md5
  `5d693ec` (span canónico: bloque completo con su `\n` final, 3023 bytes — el span es parte de
  la constante, ver spec §2.1).** *Porque:* el md5 es lo que convierte «se respetó el scoping» de afirmación en
  test. Un byte distinto y AC-10 deja de significar nada. Si hace falta cambiar el bloque, se
  cambia en las **siete** copias a la vez (seis capas C2C-VE + B2B-VE) o no se cambia.
- **C-d9.2 — Nada de fuera del bloque se copia.** Ni `MARKET_KEYS`, ni
  `RECIPROCITY_LEDGER_KEYS`, ni `CLAVES_MERCADO`, ni `TASA_KEYS` de C2C-VE, ni `_ENVELOPE_KEYS`,
  ni `_contains_forbidden_key`. *Porque:* M5. Es el vocabulario nuclear del ledger; heredarlo
  mata al paciente (R3).
- **C-d9.3 — Las taxonomías de DOMINIO de B2B-VE van en listas privadas del delta que las
  necesita, FUERA del bloque compartido.** *Porque:* patrón fijado en TA.6 y TA.7; es lo que
  mantiene el md5 intacto mientras el dominio crece. Copiar la tabla dentro del bloque es el
  único modo garantizado de romper AC-10.
- **C-d9.4 — El firewall se aplica SOLO a superficies de entrada de forma libre.** En Fase 2
  eso es exactamente `referencias_comerciales` (D5). *Porque:* los esquemas del ledger son
  cerrados (lista blanca en `_apply`/`allowed_keys`), que es una defensa más fuerte que un
  escáner de taxonomía; añadir el escáner encima solo puede rechazar dominio legítimo.
- **C-d9.5 — Cualquier clave nueva en castellano se audita contra `FORBIDDEN_KEYS` ANTES de
  fijarse** (M6, expansión de raíces aplicada al vocabulario B2B). *Porque:* `veto`,
  `sancion`, `penalizacion` están en la lista y son vocabulario legítimo de B2B; la colisión
  está dormida solo mientras E2 mantenga los identificadores en inglés.

## MUST-NOT

- **N-d9.1 — Jamás relajar `FORBIDDEN_KEYS` para acomodar una clave B2B.** Si una clave nueva
  colisiona, **se renombra la clave**, no se toca la taxonomía. *Porque:* la taxonomía es
  compartida con seis capas C2C-VE donde esos tokens sí nombran vigilancia; relajarla aquí
  abre un agujero allí. La dirección del fallo (P1: sobre-rechazo) se conserva.
- **N-d9.2 — Jamás aplicar el firewall a los esquemas heredados del ledger.** *Porque:*
  C-d9.4. Rechazaría `credit_min_cents`… no (token-exacto: `credit` ∉ `FORBIDDEN_KEYS`), pero
  sí abriría la puerta a que alguien "complete" el firewall heredando también mercado — que es
  R3 exactamente.
- **N-d9.3 — Ningún import de C2C-VE desde B2B-VE.** *Porque:* son dos árboles de fork
  independientes; acoplarlos ata sus ciclos de vida y rompe la carga standalone. La
  duplicación es deliberada, y el md5 la hace segura.

## PREFERENCIAS

- **P-d9.1 —** Ante duda sobre si una clave nueva es dominio o vigilancia, aplicar el test de
  §3 de `spec.md`: ¿es un escalar que el sistema computa sobre una persona, o una posición que
  un humano ratifica en un esquema cerrado? Lo primero es vigilancia; lo segundo, gobernanza.

## ESCALADA

- **E-d9.1 —** Si un delta futuro necesita una superficie de forma libre nueva (más allá de
  D5), **parar**: C-d9.4 se escribió enumerando las superficies conocidas en 2026-07-15. Una
  superficie nueva exige re-derivar el alcance, no extender la lista por analogía.
- **E-d9.2 —** Si alguien propone heredar mercado/reciprocidad «solo para esta clave» → E1.
  Gana lo intocable, y R3 ya documenta por qué el argumento suena bien.
