# Constraints — D5: referencias comerciales

## MUST

- **C-d5.1 — El motor almacena las referencias; jamás deriva un número de ellas.** *Porque:*
  N2/I-VE6. Cualquier función que tome `referencias_comerciales` y devuelva un número **es** un
  score, se llame `confianza`, `fiabilidad` o `indice_relacional` (H1: el escalar con nombre
  benigno).
- **C-d5.2 — `referencias_comerciales` se escanea con el firewall heredado** (claves +
  patrones de identidad en valores, incluida la `nota`). *Porque:* C-d9.4 — es la **única**
  superficie de forma libre de la Fase 2, y por tanto el único sitio donde el firewall gana su
  sueldo. Si aquí no se aplica, D9 es decorativo (F-d9.5).
- **C-d5.3 — Esquema cerrado además del firewall:** clave desconocida → `ValueError`.
  *Porque:* la lista blanca es la defensa fuerte; la taxonomía es lint secundario (H1). Se usan
  las dos porque esta superficie es la que sí recibe forma libre.
- **C-d5.4 — Toda clave castellana nueva se audita contra `FORBIDDEN_KEYS` antes de fijarse.**
  *Porque:* C-d9.5 — `veto` y `sancion` están en la lista y son vocabulario legítimo de B2B.
  La colisión está dormida solo mientras se elijan bien los nombres.
- **C-d5.5 — Las referencias solo son visibles con `scope="comite_credito"`.** *Porque:* N7 —
  «quién avala a quién» es un grafo de relaciones comerciales. Público, es un mapa de la red
  para quien quiera presionarla.

## MUST-NOT

- **N-d5.1 — Ningún score, ranking, percentil ni ordenación de solicitantes.** *Porque:*
  intocable 1 + delta 5. Ni siquiera como adviser con gate humano — el upstream lo permitía
  (RGPD Art. 22); aquí **no existe**.
- **N-d5.2 — El motor no sugiere líneas de crédito.** *Porque:* una sugerencia es un score con
  otro nombre, y el comité la aceptaría por defecto — que es la automatización de la capa
  relacional que el intent prohíbe.
- **N-d5.3 — Ningún dato real de personas en fixtures, goldens ni notas.** Los vectores con
  forma de identidad son sintéticos y marcados. *Porque:* N8 — el repo es protocolo, no
  despliegue.
- **N-d5.4 — Sin auto-aval.** `avalista != member_id` del solicitante. *Porque:* un aval de uno
  mismo no es información; admitirlo invita a inflar la lista y convierte el conteo en el score
  que N-d5.1 prohíbe.
- **N-d5.5 — Las referencias no cruzan la frontera de la célula.** *Porque:* U4 — la reputación
  no viaja sin consentimiento explícito **y** sin que el modo vigente lo permita.

## PREFERENCIAS

- **P-d5.1 —** `referencias_comerciales` opcional, no obligatoria. *Porque:* el veteo **es la
  reunión del comité**, no el campo. Exigirlo haría que el comité rellene formularios para
  satisfacer al motor — «el gestor humano, pero más rápido» (Mini-Me, intent).

## ESCALADA

- **E-d5.1 —** Si alguien pide «solo un indicador para ayudar al comité» → E1. Es N-d5.2, y el
  argumento siempre suena razonable: por eso está codificado.
- **E-d5.2 —** Si una clave castellana necesaria colisiona con `FORBIDDEN_KEYS` → se renombra la
  clave (N-d9.1). Jamás se toca la taxonomía: es compartida con seis capas C2C-VE donde esos
  tokens sí nombran vigilancia.
