# Spec — Área a · Firewall bilingüe (tokenización + normalización + escaneo de valores)

> `[INVARIANTE ARQUITECTÓNICA · MAQUINARIA COMPARTIDA]` — se construye **una vez** y las seis
> capas la reutilizan byte-idéntica (fijado por AC-X). Cubre prompt §B (taxonomías) y §C (valores).
> Corrige las auditorías 1, 2 y 3.

## Problema que corrige

El firewall actual es **solo-inglés**, **solo-claves** y matchea **por substring**. Consecuencias:
(a) deja pasar `puntuacion`, `calificacion`, `reputacion`, `veto`; (b) rechaza falsos positivos
como `banco_de_tiempo` (`'ban' in 'banco'`), `zona_urbana`, `underscore`; (c) no ve una cédula
escondida en un **valor** string.

## La solución (idéntica en las seis capas)

### 1. Tokenización de claves
Dividir cada clave por **límites no-alfanuméricos y camelCase**: `bancoDeTiempo` → `banco, de,
tiempo`; `banco_de_tiempo` → `banco, de, tiempo`. Minusculizar. **Normalizar acentos** con NFD +
eliminación de diacríticos: `puntuación` → `puntuacion`, `sanción` → `sancion`.

### 2. Matching por token EXACTO (no substring)
Cada token normalizado se compara por igualdad exacta contra el conjunto prohibido. Incluir las
variantes morfológicas explícitas en el conjunto (no derivarlas). Para claves compuestas, evaluar
también **bigramas de tokens adyacentes** (`lista`+`negra` → `lista_negra`).

### 3. Las cinco taxonomías (bilingües, byte-idénticas donde son compartidas)

- **`CLAVES_PROHIBIDAS`** (vigilancia — las seis capas, byte-idéntica):
  `score, puntuacion, puntaje, rating, calificacion, reputation, reputacion, rank, ranking,
  clasificacion, blacklist, lista_negra*, ban, veto, penalty, penalizacion, sancion, karma,
  global_id, dni, cedula, rif, pasaporte`
  (*compuestas como `lista_negra` se matchean por bigrama `lista`+`negra`*).
- **`CLAVES_MERCADO`** (Capa 1, bilingüe): `price, precio, cost, costo, coste, fee, tarifa, cents,
  centavos, centimos, currency, moneda, divisa, valuation, valoracion, denominat, denominacion,
  pago, cobro, usd, ves, dolar, dolares, bolivar, bolivares`.
- **`CLAVES_LIBRO_RECIPROCIDAD`** (Capa 1, bilingüe): `debt, deuda, owed, debe, balance, saldo,
  credit, credito, reciprocity, reciprocidad, iou, favor_balance, saldo_de_favores`.
- **`CLAVES_PESO_VOTO`** (Capa 6, bilingüe): `weight, peso, shares, acciones, voting_power,
  poder_de_voto, vote_count, conteo, tally, recuento, majority, mayoria, percent, porcentaje,
  proxy, seats, escanos, quorum, cuota`.
- **`CLAVES_ENGAGEMENT`** (Capa 3, bilingüe): base heredada + `clic, retencion, viralidad,
  impresiones, notificacion, racha, seguidores, me_gusta`.

### 4. Escaneo de VALORES string (patrones de identidad venezolanos)
En las seis capas, además de claves, escanear cada **valor** string por regex; una coincidencia =
forma de dossier → **rechazo**. Patrones (el exacto se fija en constraints; documentar):
- **Cédula:** `[VE]-?\d{1,2}\.?\d{3}\.?\d{3}` (con y sin puntos/guion).
- **RIF:** `[JGVEP]-?\d{8}-?\d`.
- **Teléfono:** `(\+58|0058|0)(4\d{2}|2\d{2})[\s.-]?\d{7}` (aprox.; patrón exacto en constraints).

El escáner **desciende en tuplas/estructuras anidadas** (mismo comportamiento que el escáner de
claves — AC-X).

### 5. Auditoría de expansión de raíces (M6)
Antes de fijar el conjunto, auditar cada raíz por sobre-captura: `denominat` captura `denominación`
pero no debe romper dominios legítimos; `_cents`/`cents` como token exacto no colisiona con
`centro`. Documentar el barrido en `failure-model.md`.

## Contrato
- **Rechazar, nunca reparar:** una clave o valor prohibido → `raise ErrorDeBrecha*` de la capa.
- **Sobre-rechazar es seguro salvo colisión con ayuda mutua**; el matching por token elimina las
  colisiones conocidas (`banco_de_tiempo`, `zona_urbana`, `underscore`, `rango_de_fechas`).
- **Puro, sin estado, sin red.** Determinista.
