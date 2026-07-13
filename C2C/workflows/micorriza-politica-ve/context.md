# Context — entorno de información del fork Venezuela

> Hereda `../micorriza-politica/context.md`. Añade el data-room específico venezolano:
> doble moneda, diáspora, VenApp como anti-patrón, e infraestructura frágil.

## Dominio (recalibrado)

El mismo dominio social de Micorriza Política —cooperación interpersonal, comercio C2C/C2B,
colaboración cívica— operando bajo **hostilidad ambiental variable**. El "nutriente" sigue
siendo mayormente no fungible y no denominado (cuidado, atención, confianza, tiempo,
pertenencia), pero ahora conviven dos hechos duros venezolanos: una economía **bimonetaria**
de facto y un entorno de **represión selectiva** con infraestructura degradada.

## El ancla negativa, recalibrada

El protocolo original invierte el crédito social chino (vigilancia masiva, puntaje nacional).
El fork mantiene esas inversiones **y** ancla contra un anti-patrón local y vivo:

- **VenApp (y equivalentes) como anti-patrón.** Un canal estatal que combina servicio,
  identidad y **denuncia** en una sola superficie es exactamente el punto de captura que el
  protocolo existe para no construir. De ahí el constraint duro (invariante 10 del fork): **sin
  integración con canales estatales de identidad o denuncia**. No es solo privacidad: es evitar
  que la coordinación se vuelva padrón de lealtad o instrumento de delación.

## Doble moneda (hecho duro del entorno)

- Circulan **USD** y **VES** simultáneamente; ninguno es "el" numerario. La diáspora patrocina
  en dólares; la economía local opera en bolívares.
- **El tipo de cambio es volátil y políticamente disputado** (BCV vs. paralelo). No existe una
  tasa "correcta" y neutral que un motor pueda incrustar sin tomar partido. → El motor **no**
  convierte, **no** representa FX, y **no** modela inflación (sería otra tasa). Ver
  `area-e-doble-moneda/constraints.md`.
- **Hiperinflación:** los importes en VES alcanzan 15+ dígitos en unidad mínima (céntimos). Los
  enteros de Python lo soportan de forma nativa; la conservación exacta se testea explícitamente
  a esa escala. Prohibido float (regla heredada del repo).
- **Patrón de uso (documentado, no forzable):** campañas de diáspora en USD **junto a**, jamás
  mezcladas con, campañas locales en VES — dos campañas paralelas mono-moneda. Se recomienda
  `expira_en` corto para VES por riesgo inflacionario; convención del llamador, no del motor.

## La diáspora

~7–8 millones de venezolanos fuera del país son una fuente estructural de patrocinio (bonos de
aseguramiento en USD) y un vector de coordinación transfronteriza. Arquitectónicamente esto
refuerza dos cosas: la moneda como dato explícito de la campaña, y la portabilidad entre células
como operación **con consentimiento explícito vía puente**, nunca automática (ver modos).

## Infraestructura frágil (restricción de entorno)

- Cortes de electricidad e Internet frecuentes; conectividad intermitente y de baja capacidad.
- En `catastrofe_severa` el transporte asumible baja a **SMS/LoRa**: de ahí el límite de payload
  de **512 bytes** en ese modo (ver tabla en `area-c-modo/spec.md`). El transporte/malla en sí
  queda **fuera del alcance del núcleo puro** y se declara como señalado.
- Todo el motor sigue siendo **offline, determinista, stdlib + pytest/hypothesis**. Ninguna capa
  importa red. La fragilidad del entorno es una razón más para que nada dependa de un servicio.

## Tools / stack (estable)

Idéntico al bundle original: Python 3.11+, `pytest`, `hypothesis`, aritmética entera exacta,
sin servicios externos, sin LLM salvo el de Capa 3 (inyectado y encajonado), sin base de datos de
personas. Añadido del fork: el módulo `src/modo/modo.py` (puro, sin estado global).

## Ejemplos bueno/malo (recalibrados)

- **Bueno:** dos campañas paralelas —una USD de diáspora, una VES local— cada una mono-moneda,
  cada una conservando su bono exacto; una célula en La Guaira que escala a `catastrofe_severa`
  tras un deslave y `depurar()` recorta sus trazas a la ventana de 72 h.
- **Malo:** una campaña que acepta compromisos USD y VES y "convierte" al paralelo; un request
  que en `catastrofe_severa` intenta un payload de 64 KB y el motor lo **recorta** en vez de
  rechazarlo (rechazar, nunca reparar); una clave `tasa_de_cambio` que el firewall deja pasar.

## Honesty flags (heredadas + del fork)

- La calibración por modo es una **decisión de gobernanza**, no un dogma: los valores de la tabla
  de límites son *defaults* ajustables por decisión de Capa 6.
- El riesgo más profundo sigue siendo no técnico: una herramienta benigna con un gobernador
  maligno. La arquitectura quita el trono (invariante 5) y mantiene la salida abierta (invariante
  9); no puede garantizar su propio buen uso.
