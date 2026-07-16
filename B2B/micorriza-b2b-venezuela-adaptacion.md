# Micorriza B2B — Adaptación Venezuela
## Corrección del sesgo UE: auditoría de decisiones y arquitectura re-anclada

> **Propósito.** El brief B2B original (`micorriza-brief-diseno.md`) fue diseñado para España/UE, y varias de sus decisiones son **contingentes a MiCA y al contexto español**, no universales. Trasladarlas sin auditar a Venezuela sería imponer soluciones para problemas que Venezuela no tiene, mientras se ignoran los problemas que sí tiene. Este documento (a) audita cada decisión y la clasifica como universal o UE-contingente, (b) sustituye las contingentes por decisiones ancladas en la realidad venezolana verificada (julio 2026), y (c) especifica dónde la tecnología cripto —que el brief original minimizó por razones regulatorias europeas— ahora sí gana su sueldo. Complementa el `prompt-fork-venezuela.md` (C2C) y sirve como anexo de especificación para el fork del prototipo B2B.
>
> **La corrección en una frase:** los argumentos anti-TOKEN eran universales y se mantienen (reforzados por el precedente Petro); los argumentos anti-RIELES-cripto eran UE-contingentes y en Venezuela se INVIERTEN — allí los rieles cripto son la infraestructura de pagos que funciona, y la banca es la capa rota.

---

## 1. Auditoría: decisión por decisión

### 1.1 Universales — SE MANTIENEN (no eran sesgo UE)

| Decisión | Evidencia (no europea) | Nota Venezuela |
|---|---|---|
| **NO token especulativo, NO token de gobernanza** | Plutocracia DAO (Gini >0,94; participación 1,77%); Beanstalk $182M; la especulación destruye la utilidad del medio de intercambio | **SE REFUERZA**: el precedente del Petro (moneda estatal fallida, terminada en 2024) y el escándalo Sunacrip (~$3.000M+ desaparecidos, regulador intervenido 2023) hacen que cualquier "moneda" nueva huela a estafa. Cero tokens, sin excepciones |
| Crédito mutuo *permissioned* con veteo | Sardex/WIR: el impago es contagioso; la confianza relacional es el motor | Se mantiene; el MÉTODO de veteo cambia (§3.4) |
| Líneas acotadas (~1% negativo / ~10% positivo) | Anti-acaparamiento + redistribución; universal | Se mantiene; calibración inicial más conservadora |
| *Clearing* multilateral determinista OFF-CHAIN | El solver de ciclos es matemática, no ideología; 25–50% de reducción de deuda neta (datos Sardex) | Se mantiene íntegro. Nunca un LLM ni un smart contract en la ruta de liquidación |
| Un socio, un voto (Rochdale) | Anti-plutocracia probada desde 1844 | Se mantiene |
| Cuotas de suscripción, no comisiones por transacción | No penalizar la circulación (modelo Sardex/WIR) | Se mantiene; denominadas en USD |

### 1.2 UE-contingentes — SE INVIERTEN en Venezuela

| Decisión original | Por qué se tomó (UE) | Decisión Venezuela | Por qué |
|---|---|---|---|
| Denominar en **euros**, sin token propio | MiCA: emitir EMT exige €1,5M + CNMV | Denominar en **USD como unidad de cuenta** (1 crédito = 1 USD de valor); pista VES secundaria con expiración corta | El USD es la unidad de cuenta de facto; el crédito mutuo denominado en USD resuelve SIMULTÁNEAMENTE la sequía de crédito y la inflación: contabilidad a prueba de devaluación **sin necesitar los dólares físicos escasos**. Es el truco WIR aplicado a la escasez de divisas |
| Puente de liquidación = **EMT autorizada de terceros** bajo MiCA | MiCA exige emisor autorizado | Puente = **USDT** (predominio TRC-20) + rieles alternos (Zelle, efectivo USD, Pago Móvil para VES). Agnóstico de riel en los bordes | USDT ≈90% del libro P2P de Binance en pares VES; ~$18.000M de volumen retail en Q1 2026. Es EL riel minorista funcional. La banca venezolana: corresponsalía cortada, mesas de dólar que cierran al agotar cupos, crédito evaporado |
| **Cooperativa registrada** con personalidad jurídica como capa de confianza | Confianza + responsable identificable ante regulador UE | **Anclarse en estructuras de confianza EXISTENTES** (cámaras de comercio regionales, gremios, asociaciones de comerciantes, iglesias); wrapper legal **offshore en manos de la diáspora** solo si/cuando la formalidad haga falta | En Venezuela, registrar = legibilidad ante un Estado parasitario (SUNACOOP) + bagaje del boom cooperativo clientelista chavista (cientos de miles registradas, mayoría fantasma) + convertirse en blanco de matraqueo. La formalidad es un **dial**, no un default |
| "Empezar **legal y simple**; la ventana MiCA se cierra" | Plazo transitorio español (jun. 2026) | "Empezar **informal y pequeño**; la formalidad escala con la tracción" | El "regulador" real es el riesgo político selectivo y el enforcement arbitrario, no la norma escrita. La mitad de la economía es informal; esa es la norma racional local |
| Cada transacción **registrada ante Hacienda** (modelo Sardex-España) | Sardex opera registrada; fiscalidad española clara | **Fiscal-compliance-READY, no compliance-DEPENDENT**: registros internos limpios y exportables por empresa, para que cada miembro cumpla donde y como decida | SENIAT + IGTF 3% a pagos en divisas/cripto fuera de la banca nacional; ofensiva fiscal sobre USDT en curso (2026); tratamiento del crédito mutuo (compensación de obligaciones) = ambiguo. El sistema no puede depender de una claridad fiscal que no existe |
| "Compite con el banco en tiempos buenos" (§7.4 del brief) | Realidad española: crédito bancario barato en bonanza | **No hay crédito bancario con el que competir.** La ventaja contracíclica es PERMANENTE | Encaje bancario altísimo durante años; cartera crediticia minúscula; las pymes venezolanas viven en un momento Sardex-2009 perpetuo. El dolor es máximo y constante |
| Toda la sección §5 (MiCA) | Vinculante en UE | Sustituir por §5 de este documento (realidad regulatoria VE) | MiCA no aplica; Sunacrip en limbo post-escándalo; sanciones en flexibilización revocable |

---

## 2. El contexto operativo venezolano que manda (verificado jul. 2026)

1. **Dolarización de facto + bolívar en depreciación persistente** (>70% perdido desde oct. 2025; inflación ~229%). Doble circulación real: USD para valor, VES para menudeo y obligaciones estatales.
2. **Brecha cambiaria viva y móvil**: **12,27% al 2026-07-15** (BCV 725,74 · paralelo medio 814,83; frente al «dólar digital», >18%) — dato VOLÁTIL: vale lo que diga la última verificación fechada, ver [`docs/verificaciones/2026-07-15-cripto.md`](../docs/verificaciones/2026-07-15-cripto.md) hallazgo 5 (corrigió el ~16,5% que este documento traía: la brecha se ESTRECHÓ; los rieles difieren ~8% entre sí, por eso el motor no elige tasa). Implicación de diseño: NO existe "el" tipo de cambio; cualquier conversión automática incrusta una decisión política → **el FX es irrepresentable en el motor** (invariante heredada del fork C2C, aquí con justificación empírica).
3. **Cripto como riel funcional, no especulación**: USDT domina P2P (~90% del libro VES); usado para nómina, remesas, pagos a proveedores y ahorro. La adopción la impulsan condiciones domésticas, no ciclos de mercado.
4. **Ni USDT es un dólar perfecto**: primas P2P de hasta ~40% en pánico (ene. 2026). El sistema JAMÁS asume 1 USDT = 1 USD en los bordes; los spreads de liquidación son decisión humana.
5. **Banca rota**: corresponsalía internacional cortada, controles de capital residuales, mesas de cambio con cupos, crédito comercial casi inexistente.
6. **Sanciones en flexibilización revocable**: EOs vigentes + 15+ licencias generales (petróleo/gas/minería) desde ene. 2026; ~150-200 designaciones SDN activas; responsabilidad estricta; riesgo de *snapback*. Licencias relevantes para este proyecto: comunicaciones por internet (GL 25), ONG/humanitario/desarrollo (GL 29), remesas.
7. **Fisco activo**: IGTF 3% a pagos en divisas/cripto fuera de la banca nacional (desde 2022); ofensiva de fiscalización SENIAT sobre USDT en curso (2026), sobre bases legales de reformas de 2020.
8. **Diáspora de ~7-8M** con miles de millones USD/año en remesas (~9% ya vía cripto en 2023, creciendo): el ancla externa de liquidez natural de la red — sin análogo español.
9. **Infraestructura frágil**: apagones, conectividad intermitente, gama de teléfonos baja → local-first obligatorio; enlaza con los modos del fork C2C.
10. **Bagaje simbólico**: Petro, Sunacrip, "mercados de trueke" y monedas comunales estatales dejaron cicatrices. **El branding importa**: nada que parezca Petro 2.0 ni moneda comunal chavista.
11. **Instituciones judiciales no funcionales**: el enforcement de contratos por tribunales es irreal → la evidencia inviolable y la resolución social de disputas sustituyen parcialmente al juez.

---

## 3. Arquitectura corregida (deltas por capa sobre el brief B2B)

### 3.1 Unidad de cuenta y monedas
- **Crédito mutuo denominado en USD** (1 crédito = 1 USD de valor). Los créditos NO son dólares ni USDT: son compensación de obligaciones a la par con el dólar como unidad de cuenta.
- **Pista VES opcional** para células/sectores que la necesiten, con `expira_en` corto obligatorio (riesgo inflacionario) y contabilidad separada. Sin mezcla ni conversión automática entre pistas (herencia del fork C2C: campañas mono-moneda, FX irrepresentable).
- Enteros de unidad mínima siempre (centavos/céntimos); test de conservación a escala de hiperinflación.

### 3.2 Liquidación y reservas — donde cripto gana su sueldo (uso 1 y 2)
- **USDT como activo puente** para: liquidación de desequilibrios persistentes entre miembros, salidas de la red, y liquidación entre células. Rieles alternos documentados (Zelle, efectivo, Pago Móvil) — agnóstico de riel en los bordes; el núcleo solo registra la obligación saldada.
- **Fondo de garantía de la célula en MULTISIG** (2-de-3 o 3-de-5: firmantes = figuras locales respetadas de la cámara/gremio + un fideicomisario de la diáspora). Sustituye a la "cuenta de custodio autorizada" de MiCA-landia: **el escrow criptográfico reemplaza al banco de confianza que no existe.**
- Banderas duras: riesgo de contraparte Tether; **congelamiento de direcciones** (Tether congela a petición de OFAC) → autocustodia, rotación de direcciones, y nunca concentrar la reserva en una sola dirección/cadena; prima P2P en crisis → spreads de liquidación decididos por humanos, jamás hardcodeados.

### 3.3 Libro de obligaciones — donde cripto gana su sueldo (uso 3)
- **Local-first, append-only, hash-encadenado**, replicado entre nodos de la célula. El solver de *clearing* sigue **off-chain y determinista** (mismo input → mismo resultado en cualquier nodo; los apagones no lo rompen).
- **Anclaje periódico de hashes a una cadena pública** (timestamping barato, p. ej. diario/semanal): evidencia inviolable de qué obligaciones existían y cuándo. **Porqué**: sin tribunales funcionales, la resolución de disputas es social (comité + árbitro gremial) y necesita evidencia que nadie pueda reescribir — el anclaje sustituye parcialmente al enforcement judicial. NO smart contracts de clearing on-chain (gas, complejidad, apagones: sin beneficio que justifique el coste).
- **Visibilidad de saldos RESTRINGIDA al comité de crédito** de la célula. Un libro público de saldos = **mapa de matraqueo** (quién tiene superávit = lista de objetivos de extorsión). Cualquier dato anclado públicamente va con seudónimos/compromisos (hashes), nunca identidades ni montos en claro. Esto ENDURECE el diseño respecto a España.

### 3.4 Veteo y líneas de crédito (adaptación del método, no del principio)
- Sin estados financieros auditados ni registros fiables → **veteo relacional**: referencias comerciales verificadas (proveedores y clientes existentes del solicitante dentro de la red), antigüedad y reputación en cámara/gremio, aval de 2+ miembros.
- Líneas iniciales conservadoras; crecimiento por historial interno de cumplimiento (el propio ledger es el expediente de crédito, visible solo al comité).
- Sanciones graduadas (herencia intacta): aviso → reducción de línea → suspensión → salida, con apelación ante árbitro gremial.

### 3.5 Puente diáspora — donde cripto gana su sueldo (uso 4; sin análogo español)
- **Remesas → USDT → fondo de garantía / patrocinio**: la diáspora capitaliza el fondo multisig de su ciudad/gremio de origen, o patrocina **contratos de aseguramiento dominantes** (mecánica del fork C2C, Capa 4) para bienes comunes empresariales: un galpón compartido, una planta eléctrica del mercado municipal, capital semilla de reconstrucción post-terremoto.
- Cumplimiento del lado diáspora (miembros US-person): operar bajo las licencias vigentes (remesas; GL 29 vía ONG para lo humanitario/desarrollo), **screening SDN de contrapartes**, y nada que toque GoV/PDVSA/SDNs. Bandera: las licencias son revocables (*snapback*); la estructura debe poder pausar el puente sin matar la red local.

### 3.6 Célula y formalidad (el dial)
- **Etapa informal** (default): la célula ES la cámara/gremio/asociación existente usando la herramienta; sin registro nuevo ante el Estado.
- **Etapa formal** (si la escala lo exige): wrapper legal offshore en manos de fideicomisarios de la diáspora (jurisdicción a asesorar: p. ej. EEUU/España/Panamá), que contrata servicios y custodia lo que necesite existencia legal — manteniendo la operación local sin un registro capturable.
- **Nunca**: registro SUNACOOP como requisito de participación; integración con canales estatales de identidad/denuncia (herencia del fork C2C, constraint 10).

### 3.7 Resiliencia operativa
- Local-first con sincronización oportunista; funciona en LAN/offline durante apagones; el clearing corre en cualquier nodo (determinismo = mismo resultado).
- Hereda los **modos del fork C2C** (paz / catástrofe acotada / catástrofe severa) para retención, alcance y tamaño de payload; el B2B opera típicamente en `paz`, escalable en desastre (el crédito mutuo ES la capa de reconstrucción de Enjambre/Micelio).

---

## 4. Lo que NO cambia (y por qué decirlo explícitamente)

1. **Cero tokens.** Ni de valor, ni de gobernanza, ni "puntos". El crédito mutuo es un registro de compensación, no un activo transferible fuera de la red. (Universal + Petro.)
2. **El solver determinista off-chain** es intocable (invariante 1 del brief original).
3. **Veteo permissioned** — el fork C2C tiene habitaciones sin barrera; el B2B con crédito NO: el impago es contagioso.
4. **Un socio, un voto**; gobernanza de la célula por consentimiento (reutiliza Capa 6 del C2C).
5. **Cuotas, no comisiones por transacción** (en USD, deducibles o no según la formalidad que cada miembro elija — decisión suya, registros limpios provistos).
6. **Sin tenedor central**: federación de células; ningún hub nacional; ningún trono que capturar — en Venezuela esto protege contra la cooptación política tanto como contra la vigilancia.

---

## 5. Realidad regulatoria y fiscal VE (sustituye la sección MiCA del brief)

| Ámbito | Estado (jul. 2026) | Implicación de diseño |
|---|---|---|
| Regulador cripto | Sunacrip intervenida (2023, escándalo ~$3.000M); marco en limbo/reforma; Petro terminado (2024) | No hay ruta de "autorización" equivalente a MiCA que buscar; el riesgo es enforcement arbitrario, no incumplimiento de una norma clara |
| Fiscal | IGTF 3% a pagos en divisas/cripto fuera de banca nacional; ofensiva SENIAT sobre USDT en curso (bases legales de 2020) | Compliance-READY: exportes contables limpios por miembro; el crédito mutuo como compensación de obligaciones tiene tratamiento ambiguo → asesoría fiscal local antes de escalar; no prometer neutralidad fiscal a los miembros |
| Sanciones (lado diáspora/US-persons) | EOs vigentes; 15+ GLs de flexibilización revocables; ~150-200 SDN activos; responsabilidad estricta | Screening SDN; operar bajo GLs de remesas/ONG; diseño con botón de pausa del puente ante *snapback* |
| Cambiario | Brecha BCV/paralelo móvil (12,27% al 2026-07-15 — ver `docs/verificaciones/2026-07-15-cripto.md`, la fuente fechada manda sobre esta tabla) | FX irrepresentable en el motor; conversión = decisión humana documentada |
| **Bandera de verificación** | Todo lo anterior está EN FLUJO tras la transición de enero 2026 | Re-verificar sanciones, marco cripto y fiscal ANTES de cada etapa de despliegue; fechar cada verificación en el repo |

---

## 6. Riesgos nuevos / señalado-no-falsamente-resuelto

1. **Riesgo Tether**: contraparte + congelamiento de direcciones a petición OFAC. Mitigación parcial (autocustodia, rotación, multi-riel); no eliminable. El sistema debe sobrevivir a "USDT deja de ser viable" (los créditos internos siguen funcionando; solo el puente sufre).
2. **Matraqueo/extorsión**: la visibilidad restringida de saldos y la ausencia de hub central reducen la superficie; no la eliminan. Un comité de crédito puede ser presionado. Quién gobierna decide.
3. **Cooptación política**: el riesgo real no es prohibición sino captura ("el partido salvó a los comerciantes"). Sin trono + células federadas + branding neutral; aún así, una célula puede ser cooptada — el cortafuegos es que su captura no arrastra a las demás.
4. **Cold-start distinto al español**: el dolor es permanente (ventaja), pero la confianza social está erosionada por el éxodo y la informalidad dificulta el veteo (desventaja). No asumir que "más dolor = adopción fácil".
5. **Éxodo continuo**: miembros que emigran a mitad de ciclo de crédito → reglas de salida con saldo negativo (liquidación vía puente o aval que absorbe) especificadas desde el día 1.
6. **Snapback de sanciones**: el puente diáspora puede cerrarse de un plumazo; la red local debe ser autónoma sin él.
7. **Tratamiento fiscal del crédito mutuo**: ambiguo; una reclasificación agresiva del SENIAT (¿cada compensación = pago en divisa gravable con IGTF?) es un escenario a modelar con asesoría local, no a ignorar.
8. **Lo irreducible** (herencia de toda la conversación): la voluntad de cooperar no se fabrica; las cámaras y gremios que ya confían entre sí son el sustrato — la herramienta amplifica, no sustituye.

---

## 7. Secuenciación corregida (VE)

- **Etapa 0 — Validar** (0–3 meses): 30–50 pymes de UNA cámara/gremio con relaciones comerciales mutuas densas (sin ciclos no hay clearing). Verificar estado regulatorio/sanciones a la fecha.
- **Etapa 1 — Piloto informal** (3–9 meses): 30–80 empresas veteadas relacionalmente; crédito mutuo en USD como unidad de cuenta; ledger local-first hash-encadenado; comité de crédito; SIN puente cripto todavía (liquidación de bordes en rieles existentes: Zelle/efectivo). Métrica: % de deuda neta reducida por clearing.
- **Etapa 2 — Reservas y puente** (9–18 meses): fondo de garantía multisig; puente USDT con política de spreads humana; primer patrocinio diáspora vía contrato de aseguramiento; anclaje público de hashes.
- **Etapa 3 — Federación** (18+ meses): segunda y tercera célula (otra ciudad/gremio); protocolo de federación del brief original (haircuts entre células, reputación portable SOLO con consentimiento y bajo el modo vigente); wrapper offshore si la escala lo exige.

---

## 8. Deltas accionables para el prototipo B2B (para el pipeline de código)

1. Unidad de cuenta: `USD` por defecto; `VES` como pista opcional con `expira_en` obligatorio corto; enteros de unidad mínima; sin FX representable (taxonomía rechazada: `tasa_de_cambio, tipo_de_cambio, exchange_rate, fx, bcv, paralelo`).
2. Ledger: append-only + hash-encadenado + función pura `anclar()` que emite el hash raíz del período (el anclaje efectivo a cadena pública es integración del llamador, documentada).
3. Visibilidad: API de saldos con scope `comite_credito`; toda exportación pública pasa por seudonimización; test que verifica que ningún endpoint público expone saldo+identidad.
4. Reservas: especificación del multisig (umbral, firmantes, procedimiento de rotación de direcciones) como documento de gobernanza + helpers de verificación de dirección; el motor NUNCA custodia claves.
5. Veteo: esquema de `referencias_comerciales` (quién avala, relación declarada, antigüedad) como input del comité — sin score numérico (herencia FORBIDDEN del C2C: la solvencia es un juicio del comité, no un escalar del sistema).
6. Salida de miembros: procedimiento `salida_con_saldo` (positivo: liquidación vía puente; negativo: plan de pago o absorción por avalista) especificado y testeado.
7. Exportes fiscales: `exportar_registros(miembro, periodo)` → CSV/JSON limpio por empresa; el sistema no declara por nadie.
8. Botón de pausa del puente: `puente.pausar()` reversible, activable por el comité, que NO detiene el crédito interno.
9. Herencia C2C: reutilizar verbatim las taxonomías bilingües, el matching por tokens con normalización de acentos, el escaneo de valores de identidad (cédula/RIF/teléfono), y los modos de calibración del `prompt-fork-venezuela.md`.
10. Branding: nombre y lenguaje de producto sin "moneda", "coin", "token", "petro", "comunal" — es un "circuito de crédito comercial" de la cámara/gremio.

> **Frase rectora de la corrección:** en España el diseño evitaba cripto porque la banca funcionaba y MiCA cobraba caro el token; en Venezuela el diseño usa los rieles cripto porque son la única infraestructura de pagos que funciona — y sigue sin emitir ningún token, porque esa lección (especulación, plutocracia, Petro) no era europea: era universal. Cripto como fontanería, nunca como promesa.
