# Tabla exhaustiva de renombrado — Área b (M7)

> Artefacto M7: se escribe ANTES del renombrado (C-b1). El renombrado es una transformación
> mecánica y verificable contra esta tabla + el grep-gate de `constraints.md`.
> Decisiones del humano (2026-07-14): `token`→`ficha`; castellanizar TODA la prosa
> (mensajes + docstrings + comentarios). Directorios de paquete NO se renombran (no son
> clave de esquema/valor/verdicto; acota el radio); sólo se renombran los ARCHIVOS `.py`.

## 0. PROTEGIDO — NO tocar (rompe tests o contratos externos)

1. **Bloque compartido del firewall** en las 6 capas, entre
   `# === BEGIN shared firewall machinery ... ===` y `# === END ... ===`:
   queda **byte-idéntico e inglés**. Es territorio de área a (TA.2), fijado por diff de revisión.
   No renombrar sus nombres ni traducir su prosa.
2. **Escáneres privados referenciados por `test_cross_layer_taxonomy.py`** (aunque estén FUERA
   del bloque): `_key_token_set`, `_contains_forbidden_key`, `_forbidden_key_path`,
   `_scan_forbidden`, `_scan_keys`, y el atributo `FORBIDDEN_KEYS`. Conservan nombre (privados
   `_`, no los toca el grep-gate).
3. **Listas-taxonomía** (contenido y nombre de variable): `FORBIDDEN_KEYS`, `MARKET_KEYS`,
   `RECIPROCITY_LEDGER_KEYS`, `ENGAGEMENT_KEYS`, `VOTE_WEIGHT_KEYS`. Su contenido es data
   bilingüe de detección (área a). Nombre de variable en inglés se conserva.
4. **Keywords JSON-schema / API Anthropic** en `claude_matcher.py`: `type`, `object`,
   `properties`, `array`, `items`, `string`, `enum`, `required`, `additionalProperties`,
   `schema`, `json_schema`, `format`, `output_config`, `thinking`, `adaptive`, `role`,
   `content`, `system`, `messages`, `model`, `max_tokens`, `text`. Y el id de modelo
   `"claude-sonnet-5"`. NO traducir.
5. **`ValueError`** en `aseguramiento.py`: se conserva (validación de entrada, deliberadamente
   distinta del abort interno). No convertir a excepción castellana.

## 1. Archivos (renombrar el `.py`; el dir queda igual)

| Antes | Después |
|---|---|
| `src/partition/membrane.py` | `src/partition/membrana.py` |
| `src/legibility/legibility_query.py` | `src/legibility/legibilidad.py` |
| `src/matcher/matcher.py` | `src/matcher/emparejador.py` |
| `src/matcher/claude_matcher.py` | `src/matcher/emparejador_claude.py` |
| `src/assurance/assurance_engine.py` | `src/assurance/aseguramiento.py` |
| `src/stigmergy/stigmergy.py` | `src/stigmergy/estigmergia.py` |
| `src/governance/governance.py` | `src/governance/gobernanza.py` |

Actualizar todas las constantes de ruta y `spec_from_file_location(...)` en `tests/` que
apunten a estos archivos.

## 2. Funciones públicas y excepciones

| Antes | Después |
|---|---|
| `admit()` | `admitir()` |
| `query()` | `consultar()` |
| `match(request, propose)` | `emparejar(solicitud, proponer)` |
| `resolve()` | `resolver()` |
| `sense()` | `sentir()` |
| `decide()` | `decidir()` |
| `make_claude_propose()` / interno `propose()` | `crear_proponer_claude()` / `proponer()` |
| `MembraneBreachError` | `ErrorDeBrechaMembrana` |
| `LegibilityBreachError` | `ErrorDeBrechaLegibilidad` |
| `MatcherBreachError` | `ErrorDeBrechaEmparejador` |
| `StigmergyBreachError` | `ErrorDeBrechaEstigmergia` |
| `GovernanceBreachError` | `ErrorDeBrechaGobernanza` |
| **`AssuranceInvariantError`** | **`ErrorDeInvarianteAseguramiento`** (NO «Brecha»: es abort interno de invariante, no breach de entrada) |

## 3. Claves transversales (aparecen en varias capas)

| Antes | Después |
|---|---|
| `cell_id` | `celula_id` |
| `circle_id` | `circulo_id` |
| `now` | `ahora` |
| `expires_at` | `expira_en` |
| `audit_trace` | `traza_auditoria` |
| `rule` | `regla` |
| `note` | `nota` |
| `verdict` | `veredicto` |
| `reason` | `razon` |
| `kind` | `tipo` |
| `token` | `ficha` |
| `participant_token` | `ficha_participante` |
| `facts` | `hechos` |
| `statement` | `afirmacion` |
| `about` | `sobre` |

## 4. Capa 1 — membrana (`membrana.py`)

| Antes | Después |
|---|---|
| `mode` (clave y var) | `sala` |
| valores: `communal_gift` / `equality_matching` / `market_price` | `don_comunal` / `igualdad` / `precio_de_mercado` |
| `interaction` / `interaction_id` | `interaccion` / `interaccion_id` |
| `participants` | `participantes` |
| `payload` | `carga` |
| `admitted` | `admitido` |
| `checked_keys` | `claves_revisadas` |
| `_ENVELOPE_KEYS` → contenido | `('sala','celula_id','interaccion_id','expira_en','participantes','carga')` |

## 5. Capa 2 — legibilidad (`legibilidad.py`)

| Antes | Después |
|---|---|
| `asker` | `consultante` |
| `target` | `objetivo` |
| `max_hops` | `saltos_max` |
| `graph` | `grafo` |
| `vouches` | `avales` |
| `from` / `to` (dentro de un aval) | `de` / `a` |
| `from_your_position` | `desde_tu_posicion` |
| `reachable` | `alcanzable` |
| `nearest_hops` | `saltos_minimos` |
| `vouch_paths` | `rutas_de_aval` |
| `vouched_by_people_you_trust` | `avalado_por_gente_de_tu_confianza` |
| verdicto `known_via_trust` | `conocido_via_confianza` |
| verdicto `no_info_from_your_position` | `sin_informacion_desde_tu_posicion` |
| `considered_vouches` / `considered_facts` | `avales_considerados` / `hechos_considerados` |
| `max_vouch_paths` / `paths_truncated` | `rutas_de_aval_max` / `rutas_truncadas` |
| `_MAX_VOUCH_PATHS` (const priv.) | `_MAX_RUTAS_DE_AVAL` |
| `_is_unexpired` (priv.) | `_no_expirado` |

## 6. Capa 3 — emparejador (`emparejador.py` + `emparejador_claude.py`)

| Antes | Después |
|---|---|
| `asker` | `consultante` |
| `cell_ids` | `celulas_ids` |
| `max_proposals` | `propuestas_max` |
| `self` (declaración propia) | `propio` |
| `candidates` / `candidate` | `candidatos` / `candidato` |
| `offers` / `needs` / `goals` | `ofertas` / `necesidades` / `metas` |
| `consent` | `consentimiento` |
| `surfaceable` | `mostrable` |
| `cite_facts` / `cited_facts` | `citar_hechos` / `hechos_citados` |
| valores `kind`: `offer_meets_need` / `shared_goal` / `translation` | `oferta_cubre_necesidad` / `meta_compartida` / `traduccion` |
| `proposals` | `propuestas` |
| verdicto `proposals_surfaced` | `propuestas_mostradas` |
| verdicto `no_matches_from_your_position` | `sin_coincidencias_desde_tu_posicion` |
| `eligible_candidates` | `candidatos_elegibles` |
| `proposed_by_model` | `propuestas_del_modelo` |
| `dropped_off_schema` | `descartadas_fuera_de_esquema` |
| `dropped_off_cell` | `descartadas_fuera_de_celula` |
| `dropped_non_consenting` | `descartadas_no_consintientes` |
| `dropped_surveillance_shape` | `descartadas_forma_vigilancia` |
| `dropped_unknown_token` | `descartadas_ficha_desconocida` |
| `emitted` | `emitidas` |
| `_ALLOWED_KINDS` / `_SELF_KEYS` / `_CANDIDATE_KEYS` | actualizar contenido a lo de arriba |
| `_validate_request` etc. (priv.) | `_validar_solicitud`, `_validar_listas_declaracion`, `_validar_lista_str`, `_scan_forbidden` **queda** |

`emparejador_claude.py`: en `_PROPOSAL_SCHEMA` traducir SÓLO los nombres de campo de dominio
(`proposals`→`propuestas`, `token`→`ficha`, `kind`→`tipo`, `reason`→`razon` y los valores del
`enum`); conservar todo keyword JSON-schema (§0.4). `_SYSTEM`→prompt en castellano. `_PROPOSAL_SCHEMA`→`_ESQUEMA_PROPUESTA`, `_SYSTEM`→`_SISTEMA`.

## 7. Capa 4 — aseguramiento (`aseguramiento.py` + goldens)

| Antes | Después |
|---|---|
| `campaign` / `campaign_id` | `campana` / `campana_id` |
| valores `kind`: `binary` / `monetary` | `binario` / `monetario` |
| `threshold` | `umbral` |
| `sponsor_bonus_cents` | `bono_patrocinador_centavos` |
| `pledges` / `pledge_id` | `compromisos` / `compromiso_id` |
| `amount_cents` | `monto_centavos` |
| `status` | `estado` |
| valores `status`: `fires` / `refunds` | `se_activa` / `reembolsa` |
| `distinct_committers` | `comprometidos_distintos` |
| `resolution` | `resolucion` |
| clave `fires` (en resolution) | `se_activa` |
| `total_pledged_cents` | `total_comprometido_centavos` |
| `refunds` (lista en resolution) | `reembolsos` |
| `refund_cents` | `reembolso_centavos` |
| `bonus_cents` | `bono_centavos` |
| `deduped_from_pledges` | `deduplicado_de_compromisos` |
| regla `"distinct_committers >= threshold"` | `"comprometidos_distintos >= umbral"` |

Goldens `workflows/micorriza-politica/evals/golden-set/{test_A,test_B,test_C_crosscampaign}.json`:
renombrar TODAS las claves de `input` y `expected` con la tabla (entrada y salida cambian juntas).

## 8. Capa 5 — estigmergia (`estigmergia.py`)

| Antes | Después |
|---|---|
| `window` | `ventana` |
| `velocity_cap` | `tope_velocidad` |
| `half_life` | `vida_media` |
| `min_strength` | `fuerza_min` |
| `traces` | `trazas` |
| `signal` | `senal` |
| `strength` | `fuerza` |
| `created_at` | `creado_en` |
| `context` | `contexto` |
| valores `signal`: `contribution`/`path`/`endorsement`/`presence`/`flag` | `contribucion`/`ruta`/`respaldo`/`presencia`/`bandera` |
| `effective_strength` | `fuerza_efectiva` |
| `sensed` (lista de salida y conteo en audit) | `sentidas` |
| verdicto `signals_sensed` / `quiet_from_your_cell` | `senales_sentidas` / `silencio_desde_tu_celula` |
| `considered_traces` | `trazas_consideradas` |
| `dropped_off_cell` / `dropped_future` | `descartadas_fuera_de_celula` / `descartadas_futuras` |
| `damped_no_context` / `damped_velocity` | `amortiguadas_sin_contexto` / `amortiguadas_velocidad` |
| `evaporated` | `evaporadas` |
| `ALLOWED_SIGNALS` / `JUDGMENT_SIGNALS` / `_TRACE_KEYS` | actualizar contenido |
| `_scan_forbidden` **queda**; `_window_bucket` (priv.) | `_cubeta_ventana` |

## 9. Capa 6 — gobernanza (`gobernanza.py`)

| Antes | Después |
|---|---|
| `proposal_id` | `propuesta_id` |
| `dispositions` | `posturas` |
| `disposition` | `postura` |
| valores: `consent` / `object` / `abstain` | `consentir` / `objetar` / `abstenerse` |
| `objection` | `objecion` |
| `paramount` | `primordial` |
| verdicto `adopted` / `revisit` | `adoptada` / `revisar` |
| `paramount_objections` | `objeciones_primordiales` |
| `concerns` | `inquietudes` |
| `considered_dispositions` | `posturas_consideradas` |
| `dropped_off_circle` / `dropped_expired` | `descartadas_fuera_de_circulo` / `descartadas_expiradas` |
| `_ALLOWED_DISPOSITIONS`/`_DISPOSITION_KEYS`/`_OBJECTION_KEYS` | actualizar contenido |
| `_scan_keys` **queda**; `_is_expired`/`_validate_envelope` (priv.) | `_esta_expirada` / `_validar_sobre` |

## 10. Gate de cierre (de `constraints.md` + `acceptance.md`)

- `grep -rniE '\b(mode|asker|target|expires_at|vouches|facts|traces|adopted|revisit|admit|query|match|sense|decide)\b' src/ tests/` → **vacío** salvo el bloque firewall protegido / procedencia.
- Suite: **341 verdes** (293 originales + 48 de área a), comportamiento idéntico.
- Convención de tildes: claves SIN tildes (ya reflejado arriba); mensajes/prosa CON tildes correctas.
