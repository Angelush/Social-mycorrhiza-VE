# Spec — Área b · Castellanización completa

> Renombrado mecánico y consistente en **código + tests + docs**. La tabla exhaustiva se escribe
> PRIMERO (M7); el renombrado es transformación mecánica con gate. Cubre prompt §A.

## Regla de oro
Consistencia total: ningún identificador público, clave de esquema, valor enumerado, mensaje,
verdicto o excepción queda en inglés. `grep` de residuos (`mode`, `asker`, `expires_at`, …) debe
volver vacío al cerrar el área.

## Convención de tildes
- **Claves de esquema: SIN tildes** (`celula_id`, no `célula_id`) — robustez de matching y
  portabilidad.
- **VALORES enumerados, mensajes y verdictos: CON tildes correctas** (`catastrofe_severa` es un
  valor; los mensajes al humano llevan acentuación castellana correcta).

## Tabla principal de renombrado (completar exhaustiva en implementación)

| Original | Castellano |
|---|---|
| `membrane.py` / `admit()` | `membrana.py` / `admitir()` |
| `legibility_query.py` / `query()` | `legibilidad.py` / `consultar()` |
| `matcher.py` / `match()` | `emparejador.py` / `emparejar()` |
| `assurance_engine.py` | `aseguramiento.py` |
| `stigmergy.py` / `sense()` | `estigmergia.py` / `sentir()` |
| `governance.py` / `decide()` | `gobernanza.py` / `decidir()` |
| `mode` (Capa 1, sala relacional) | **`sala`** — `don_comunal`, `igualdad`, `precio_de_mercado` |
| *(nuevo)* modo de calibración | **`modo`** — `paz`, `catastrofe_acotada`, `catastrofe_severa` |
| `cell_id` / `circle_id` | `celula_id` / `circulo_id` |
| `asker` / `target` | `consultante` / `objetivo` |
| `now` / `expires_at` | `ahora` / `expira_en` |
| `vouches` / `facts` / `traces` | `avales` / `hechos` / `trazas` |
| `dispositions`: `consent`/`object`/`abstain` | `posturas`: `consentir`/`objetar`/`abstenerse` |
| verdictos `adopted`/`revisit` | `adoptada`/`revisar` |
| `known_via_trust` / `no_info_from_your_position` | `conocido_via_confianza` / `sin_informacion_desde_tu_posicion` |
| excepciones `*BreachError` | `ErrorDeBrecha*` (p. ej. `ErrorDeBrechaMembrana`, `ErrorDeBrechaAseguramiento`) |

## Nota crítica sobre la colisión `mode`
El renombrado `mode`→`sala` **debe** hacerse porque el fork introduce un `modo` de calibración
distinto (área c). Dejar ambos como `mode`/`modo` sería una colisión semántica que rompe la
legibilidad y el matching. `sala` = habitación relacional (Capa 1); `modo` = calibración por
hostilidad (transversal).

## Orden de trabajo
1. Tabla exhaustiva primero (M7): recorrer los 7 módulos y extraer cada símbolo público.
2. Renombrado mecánico módulo a módulo.
3. Tests traducidos en paralelo; los 293 equivalentes deben pasar.
