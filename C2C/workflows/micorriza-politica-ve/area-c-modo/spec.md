# Spec — Área c · Módulo `modo` (calibración por hostilidad)

> Nuevo módulo `src/modo/modo.py` — `[DETERMINISTA]`, puro, sin estado global. Maquinaria
> compartida: se construye una vez, la consultan las seis capas. Cubre prompt §E.

## El modo es POR CÉLULA (policéntrico)
El `modo` viaja en el **envelope** de cada request, obligatorio junto a `celula_id`. No hay estado
global de modo. Cada capa valida sus propios límites contra la tabla. Valores:
`paz`, `catastrofe_acotada`, `catastrofe_severa`.

## Tabla de límites por defecto
> *Defaults ajustables por decisión de Capa 6, NO dogma.*

| Límite | `paz` | `catastrofe_acotada` | `catastrofe_severa` |
|---|---|---|---|
| Retención máx. (`expira_en` − `ahora`) | 365 días | 45 días | 7 días |
| Retención de trazas (Capa 5) | 90 días | 14 días | 72 horas |
| `max_hops` (Capa 2) | ≤ 4 | ≤ 3 | ≤ 2 |
| Portabilidad entre células | permitida con consentimiento explícito vía puente | solo hechos operativos/logísticos | prohibida (estrictamente celular) |
| Tamaño máx. de payload | 64 KB | 8 KB | **512 bytes** (SMS/LoRa) |
| `max_proposals` (Capa 3) | ≤ 20 | ≤ 10 | ≤ 5 |
| `velocity_cap` mínimo exigido (Capa 5) | laxo | medio | estricto |

**Hueco declarado:** los valores numéricos concretos de `velocity_cap` (laxo/medio/estricto) se
**proponen** en la implementación de esta área y se documentan; no vienen dados por el prompt.

## Superficie del módulo
- **`validar_modo(request)`** — aplicada por cada capa. Si `expira_en`, `max_hops` o el tamaño de
  payload del request exceden el límite de su `modo` → **rechazo** (`raise`), **no recorte**.
- **`validar_transicion(actual, propuesto, decision_capa6=None)`** — trinquete asimétrico; su spec
  completa vive en `area-d-trinquete/`.
- **`depurar(items, modo, ahora)`** — función pura determinista: recibe items almacenados por el
  llamador y devuelve solo los que sobreviven a la ventana del modo. Los que exceden se **eliminan**
  (no se recortan a la ventana), salvo trazas con TTL que se recortan a la ventana; especificar por
  tipo. Es convención del llamador + helper + test (señalado: una función pura no puede obligar a
  ejecutarse).

## Tiempo
Cada capa conserva su modelo temporal: ISO-8601 lexicográfico donde ya se usa; ticks enteros en
Capa 5. `validar_modo` compara `expira_en − ahora` en la unidad de la capa.

## Integración
Cada una de las seis capas llama `validar_modo` sobre su request antes de su lógica propia. El
módulo `modo` **no importa** ninguna capa (sin ciclos); las capas importan `modo`.
