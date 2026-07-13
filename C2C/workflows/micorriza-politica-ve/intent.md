# Intent — el objetivo real del fork Venezuela + contrato de corrección

> Hereda `../micorriza-politica/intent.md`. Este documento NO lo reemplaza: lo **recalibra**
> para el contexto venezolano. Todo lo que el intent original declara sigue vigente; aquí se
> añade la capa de hostilidad ambiental y los invariantes de moneda y modo.

## El objetivo real (recalibración del marco)

El protocolo original construye **infraestructura para que una sociedad alfabetizada se
organice a través de sus diferencias** — fertilidad, no eficiencia; jardinero, no ingeniero.
El fork conserva ese marco intacto y le añade **una calibración por grado de hostilidad del
entorno**: coordinación y ayuda mutua venezolana bajo represión.

**La recalibración del enemigo (crítica, define todo lo demás):** el ancla negativa del
protocolo original es el crédito social chino — un aparato de **vigilancia masiva** con
puntuación nacional. El enemigo estructural en Venezuela **no es el mismo**. Es:

1. **Represión selectiva, no vigilancia masiva.** El riesgo no es que un puntaje global
   clasifique a 30 millones de personas; es que un dossier sobre *un* organizador o *una*
   célula caiga en manos de quien puede detener, extorsionar o desaparecer. El firewall no
   protege contra un panóptico; protege contra que un solo nodo comprometido revele una red.
2. **La captura política de la coordinación**, no solo la observación. Una herramienta de
   ayuda mutua que funcione es, por eso mismo, una herramienta de poder; el peligro es que
   un actor —estatal o faccioso— la capture y la vuelva instrumento de control, padrón de
   lealtad, o canal de denuncia (VenApp como anti-patrón vivo; ver `context.md`).
3. **El punto único de fallo.** Sin tenedor central no hay trono que capturar (invariante 5);
   en un entorno de represión selectiva esto deja de ser elegancia arquitectónica y pasa a
   ser supervivencia operativa: policentrismo por célula, nada persistido, nada federable sin
   consentimiento explícito.

## Qué añade el fork al contrato de corrección

Sobre el contrato del intent original (veracidad, no-pérdida, conservación, forma, política,
velocidad-vs-precisión, auditabilidad-con-olvido) el fork añade tres cláusulas:

- **Moneda sin conversión (nueva cláusula de forma).** Toda campaña de aseguramiento declara
  `moneda: 'USD' | 'VES'` y **nunca** las mezcla; el tipo de cambio es *irrepresentable*
  dentro del motor. Incrustar una tasa (BCV vs. paralelo) es incrustar una decisión política
  volátil y crear un punto capturable. La conversión es siempre una decisión humana fuera del
  protocolo. La conservación exacta se mantiene a escala de hiperinflación (enteros de 15+
  dígitos). Ver `area-e-doble-moneda/`.
- **Calibración por modo (nueva cláusula de alcance, no de forma).** Tres modos por célula —
  `paz`, `catastrofe_acotada`, `catastrofe_severa` — calibran **retención, alcance, tamaño de
  payload y parámetros de cortacircuitos, y NADA MÁS**. Ningún modo toca ningún invariante de
  `lo-intocable.md`. La transición es un trinquete asimétrico gobernado por Capa 6. Ver
  `area-c-modo/` y `area-d-trinquete/`.
- **Firewall bilingüe con escaneo de valores (endurecimiento de la cláusula de forma).** El
  firewall deja de ser solo-inglés y solo-claves: tokeniza y normaliza acentos, matchea por
  token exacto (no substring), es bilingüe en las cinco taxonomías, y escanea **valores** por
  patrones de identidad venezolanos (cédula/RIF/teléfono) porque su presencia = forma de
  dossier. Ver `area-a-firewall-bilingue/`.

## Mini-Me check (heredado, reforzado)

No codificar "un organizador comunitario pero más rápido y vigilando a todos". Y en el fork,
tampoco "un organizador que decide el modo de emergencia por ti": el modo es **por célula**,
lo escala cualquier token del círculo y lo desescala solo el consentimiento de Capa 6. El
código fuerza el *procedimiento* del trinquete; jamás la buena fe ni el juicio de la crisis.

## Límite honesto (señalado, no falsamente resuelto)

La membrana detecta **formas**, no **semántica**. Un juicio escalar en texto libre ("esta
persona es un 3/10") queda fuera del alcance de un firewall determinista y se declara
abiertamente aquí y en cada `failure-model.md` afectado. La semántica es gobernanza humana.
La lista consolidada de lo señalado vive en `lo-intocable.md`.
