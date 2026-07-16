# TS.1 — Adaptadores del harness a los contratos VE

## Qué cambia y qué no

**Cambia el CABLE, no el harness.** El motor del sim (engine, mundos, policies, tracks,
campañas) conserva sus identificadores ingleses upstream — no son API nueva del sistema VE,
son el harness hablándose a sí mismo, y renombrarlos alejaría `Sim-VE/` de `Sim/` sin ganar
verificación (la forma E2 aplicada a este árbol). Lo que se adapta es **todo lo que cruza la
frontera hacia el SUT**:

1. **Raíces:** `C2C/`→`C2C-VE/`, `B2B/`→`B2B-VE/`. El pin de contenido (SUTAdapter) pasa a
   fijar los archivos VE.
2. **C2CAdapter:** módulos `membrana/legibilidad/emparejador/aseguramiento/estigmergia/
   gobernanza`; métodos pass-through verbatim `admitir/consultar/emparejar/resolver/sentir/
   decidir`; excepciones `ErrorDeBrecha*` + `ErrorDeInvarianteAseguramiento`. Los nombres de
   método del adaptador SON los nombres reales de las funciones (uno-a-uno, ninguno
   inventado), como en el upstream.
3. **Envelopes C2C:** claves castellanas según la tabla M7 de TA.3
   (`C2C/workflows/micorriza-politica-ve/area-b-castellanizacion/rename-table.md`) — la
   fuente única del mapeo; este spec no la re-teclea. **Más `modo`** (string ∈
   `MODOS = ('paz','catastrofe_acotada','catastrofe_severa')`) en todo envelope que el mundo
   construya: es la superficie nueva de TA.4 y el harness la ejercita siempre (knob
   `modo` en RoundConfig, default `'paz'`).
4. **B2BAdapter:** mismas firmas del ledger VE. Deltas de contrato: `create_cell` exige
   `moneda` y `sal_seudonimo` en params; `member_statement(state, member_id, scope,
   solicitante=None)` — **el scope lo pasa el llamador del harness, jamás lo elige el
   adaptador** (elegirlo sería adjudicar); `turnover_eur_cents`→`turnover_cents` en los
   members que el harness registra. Pass-throughs nuevos uno-a-uno para los públicos VE del
   ledger que el upstream no tenía (`salida_con_saldo`, `puente_pausar`, `puente_reanudar`).
5. **Fixtures de control negativo:** re-derivadas del SUT VE re-aplicando **la misma
   planta** documentada en la cabecera de cada fixture. La planta debe seguir siendo
   silenciosa contra los guards VE (incluida la puerta `proposal_moneda` de TB.8b).

## Criterios de aceptación

- **AC-s1.1 (pass-through):** los métodos del C2CAdapter VE reenvían verbatim — devuelven lo
  que el SUT devuelve y dejan subir lo que el SUT lanza. Test con control negativo: un sobre
  que la membrana VE rechaza sube como `ErrorDeBrechaMembrana`, no filtrado ni traducido.
- **AC-s1.2 (envelope VE + modo):** el envelope que `C2CWorld` construye usa las claves
  castellanas y lleva `modo`; con `modo` inválido el SUT real lo rechaza a través del
  adaptador (prueba de que la clave llega al cable, no se pierde por el camino).
- **AC-s1.3 (contrato B2B-VE):** `create_cell` del mundo lleva `moneda` y `sal_seudonimo`;
  una campaña B2B corre contra el ledger real VE. Control negativo: sin `moneda` el SUT
  real lanza `ValueError("moneda")` a través del adaptador.
- **AC-s1.4 (scope explícito):** `member_statement` del adaptador VE exige `scope`
  posicional (sin default — F-d3.1 se respeta también en el harness).
- **AC-s1.5 (suite equivalente):** suite `Sim-VE/` completa verde con el mismo número de
  tests que el upstream (121) salvo los añadidos por TS.1; `Sim/` upstream intacto en 121.
- **AC-s1.6 (pin VE):** el `SutPin` del adaptador VE apunta a rutas dentro de `C2C-VE/` /
  `B2B-VE/` (si alguien re-apunta al upstream, este test lo dice).
- **AC-s1.7 (plantas siguen silenciosas):** los tests de control negativo existentes pasan
  contra las fixtures re-derivadas — el harness (no el SUT) sigue cazando la planta.

## Verificación por mutación (obligatoria, técnica TB.3)

Mínimo: (1) adaptador que atrapa y traga la excepción del SUT → AC-s1.1 rojo; (2) envelope
con `mode` en vez de `sala` → el SUT real lo rechaza, suite roja; (3) quitar `modo` del
envelope → AC-s1.2 rojo (la clave es guardada por capa: sin test propio, su ausencia sería
VERDE — vacuidad); (4) re-apuntar una raíz al upstream → AC-s1.6 rojo; (5) fixture derivada
del upstream en vez del VE → AC-s1.7 o el pin-check de la fixture rojo.
