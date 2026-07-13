# Micorriza Económica B2B — Síntesis de diseño para implementación

> **Propósito de este documento.** Destila una conversación de diseño en un brief importable a un proyecto que lo convertirá en código y sistema concreto. No es un resumen narrativo: es un conjunto de directrices. Las **conclusiones** están redactadas como principios; los principios duros aparecen como **invariantes** (lo que siempre debe cumplirse → se convierte en guardarraíles, tests y validaciones); la arquitectura aparece como componentes con su naturaleza (determinista / estocástico / humano / smart contract), que es lo que decide qué se programa como *solver*, qué como llamada a LLM, qué como proceso humano y qué on-chain.

---

## 0. Tesis rectora (la estrella polar de toda decisión de diseño)

**La creación dejó de ser escasa; el juego entero se traslada a cómo se coordina lo común y se reparte el excedente, y eso nunca fue una pregunta técnica.** El sistema NO es "IA más potente" ni "una blockchain": es la *institución de coordinación y distribución* para una época de creación barata. La IA hace el trabajo de *solver* y de *matching*; la capa humana-cooperativa hace el trabajo de propiedad, comunes, confianza y gobernanza; **y el diseño consiste en no confundirlas jamás.** Cada componente del sistema debe poder etiquetarse sin ambigüedad como una de esas dos cosas.

Corolario operativo: el valor probado del modelo (Sardex, WIR) **no está en la descentralización**, está en el **clearing multilateral + crédito mutuo + confianza relacional veteada + gestión activa**. La tecnología cripto entra solo donde aporta de verdad: transparencia, portabilidad de reputación, asignación de bienes comunes e interoperabilidad. No como sustituto de la gobernanza.

---

## 1. Invariantes del sistema (NO negociables → guardarraíles y tests)

Estas reglas se derivan de conclusiones duras de la conversación. En código se traducen en validaciones, límites de configuración y aserciones que nunca deben violarse.

1. **Ningún proceso estocástico ejecuta irreversiblemente sobre el valor.** El *solver* de compensación es determinista (ver §3, Capa 1). Un LLM NUNCA está en la ruta de liquidación. Alucinación del 0,1% = inadmisible cuando el output mueve dinero.
2. **El agente propone, el humano dispone.** Todo emparejamiento y toda decisión de crédito es una *propuesta revisable* antes del compromiso. La alucinación en la capa de propuesta es barata porque ambas partes la ven antes de aceptar.
3. **Un socio, un voto** para gobernanza constitucional. NUNCA "un token, un voto" (reintroduce la plutocracia censitaria; ver §6).
4. **Líneas de crédito acotadas por miembro** (~1% de facturación en negativo, ~10% en positivo, calibrable por célula). **El tope positivo NO es opcional**: es el mecanismo de redistribución de nodos fuertes a débiles (la micorriza literal) y anti-acaparamiento.
5. **Sanciones únicamente graduadas**, nunca binarias: aviso → reducción de línea → suspensión temporal → expulsión, siempre con derecho de apelación. La gradualidad codifica la empatía en la regla y distingue al golpe genuino del defraudador reincidente.
6. **La red está deliberadamente NO completamente conectada.** Segmentación por célula; el contagio de impagos se cortafuega en la frontera celular. Conectancia intermedia, no máxima (paradoja de May).
7. **Blockchain = libro mayor de transparencia y auditoría, y nada más.** No es el dinero (denominar en euros) ni el voto (gobierna la cooperativa).
8. **Cortacircuitos obligatorios**: topes de exposición + límites de velocidad por ventana temporal + pausa automática ante anomalías. Críticos y *escalan en importancia* a medida que aumenta la velocidad de los agentes (riesgo de cascada tipo flash-loan a velocidad de máquina).
9. **Humano en el bucle obligatorio** para (a) denegación de crédito —exigencia del Art. 22 RGPD sobre decisiones únicamente automatizadas— y (b) juicio de fronteras y sanciones.
10. **Membresía veteada (permissioned) a nivel de célula. NUNCA permissionless.** El impago en crédito mutuo es contagioso; el veteo de solvencia es lo que hace funcionar a Sardex y choca a propósito con el ethos cripto sin permiso.

---

## 2. Regla de decisión: ¿cuándo una herramienta cripto/DAO está justificada?

**Criterio único:** una herramienta cripto entra **solo** donde el problema es *agregar preferencias* o *garantizar transparencia*. La forma cooperativa gobierna donde el problema es *control, responsabilidad legal y confianza*.

| Herramienta | ¿Justificada? | Función legítima |
|---|---|---|
| Libro mayor on-chain | ✅ | Transparencia/auditoría del *clearing* (monitorización de Ostrom) |
| Reputación *soulbound* / *attestations* | ✅ | Portabilidad de historial de pago entre células |
| *Quadratic funding* | ✅ | Asignación de un fondo común entre bienes públicos (único lugar donde brilla) |
| *Conviction voting* | ⚠️ Solo como **señal** | Sondear preferencias sobre parámetros operativos; la junta ratifica dentro de límites estatutarios |
| Token especulativo | ❌ Antipatrón | Destruye la utilidad como medio de intercambio |
| "Un token, un voto" | ❌ Antipatrón | Plutocracia (Gini >0,94; ver §6) |
| Membresía permissionless | ❌ Antipatrón | Riesgo de crédito incontrolable |
| Token *como* dinero | ❌ Antipatrón | Innecesario; complica MiCA (ver §5) |

**Bandera roja de parada inmediata:** si el diseño deriva hacia un token de oferta variable especulativo, hacia "1 token = 1 voto", hacia permissionless para evitar el veteo, o hacia exigir *wallets*/gas a pymes no-cripto → **parar y rediseñar.**

---

## 3. Arquitectura de referencia (la pila, a escala europea/mundial)

**Principio anti-Leviatán (decisión de diseño más importante):** a escala continental o global, *el sistema no es un sistema*. No hay "Sardex Mundial" con libro único ni CEO —fracasaría operativamente, sería imposible bajo MiCA (sin emisor identificable único) y traicionaría la lógica relacional. Lo global es **un protocolo fino + una red de células gobernadas localmente.** Lo global es fino *para poder* ser ancho y abarcar realidades locales incompatibles sin homogeneizarlas.

Subir la pila, etiquetando cada capa por su naturaleza:

### Capa 0 — La célula `[HUMANO]`
Cooperativa con personalidad jurídica (cooperativa ES/IT, *Genossenschaft* DE/CH, *SCIC* FR; transfronteriza: **Sociedad Cooperativa Europea (SCE)**). 50–500 empresas, densas sectorial o geográficamente (la densidad es matemática: sin solapamiento proveedor-cliente no hay ciclos que compensar). **Aquí vive todo lo humano irreemplazable:** comité de membresía/veteo, *ombudsman*, juicio de casos límite y sanciones graduadas, gobernanza constitucional. Es el núcleo de Sardex, conservado humano. Células existentes federables hoy: **WIR** (CH, 90 años), **Sardex** (IT), **RES** (BE).

### Capa 1 — El *solver* de compensación `[DETERMINISTA]`
Algoritmo de **flujo de coste mínimo con cancelación de ciclos** sobre el grafo de obligaciones (detecta A→B→C→A, netea el mínimo del ciclo). Intra- y entre-células. Output exacto, verificable, una sola respuesta correcta. **NO es un LLM.** Estructura de datos central: grafo dirigido de obligaciones. Aquí el blockchain gana su sueldo: libro mayor distribuido, auditable, a prueba de manipulación. **Dato de anclaje:** datos reales de Sardex muestran reducción de deuda neta interna ≈25% solo con *clearing*, ≈50% combinado con crédito mutuo. *Caveat:* por la estructura de ley de potencias de las redes comerciales, el beneficio del *clearing* es desigual (los nodos mejor conectados compensan más) → combinar siempre con crédito mutuo.

### Capa 2 — El *matcher* / descubrimiento `[ESTOCÁSTICO / LLM AGÉNTICO]`
Reemplaza/aumenta al *broker* humano de Sardex. Parsea descripciones difusas de lo que cada empresa tiene/necesita, propone cruces no obvios (incluida **simbiosis industrial**: residuo de A = insumo de B, volviendo *diseñable* lo que en Kalundborg fue accidental en 20 años), redacta términos preliminares. A escala europea: descubre que el excedente de una empresa portuguesa es el insumo de una polaca. **Regla:** propuestas únicamente (invariante 2). Resuelve el problema de arranque del *matching*, que es lo que hace fracasar a la economía circular.

### Capa 3 — Protocolo de federación `[SMART CONTRACT / ESTÁNDAR — CAPA FINA GLOBAL]`
**No gobierna; estandariza.** Define: qué es una obligación válida, cómo se portan las *attestations* de reputación entre células, cómo liquidan saldo neto bilateral, reglas de paridad. Conexión bilateral estilo **Lightning / Cosmos IBC**: las células se conectan según términos acordados; los *hubs* emergen por competencia, no por mandato. Lo "global" = este protocolo + el grafo de conexiones voluntarias. **Sin autoridad de gobierno global.** Es lo que permite escala sin Leviatán y sin romper MiCA (cada célula es identificable y responsable en su jurisdicción; el protocolo es infraestructura neutral).

### Capa 4 — Puente de liquidación con fiat `[SMART CONTRACT + CUMPLIMIENTO]`
Frontera con el dinero real. **Lo más limpio: denominar en euros sin emitir EMT propio** (esquiva el grueso de MiCA y su requisito de €1,5M de capital). Liquidación entre monedas (célula-euro ↔ célula-złoty): EMT autorizado de terceros como puente, asumiendo el riesgo de contraparte. Mantener estrecha y conservadora.

### Capa 5 — Tesoro de bienes comunes `[GOBERNANZA: QUADRATIC FUNDING]`
Asigna el excedente: infraestructura compartida, cómputo de la IA de *matching*, y **dimensión ambiental**: inversión transfronteriza en microredes renovables e infraestructura de economía circular. Único lugar donde el *quadratic funding* brilla legítimamente.

---

## 4. Mapa de gobernanza por tipo de decisión (subsidiariedad)

Cada *tipo* de decisión recibe el mecanismo que le corresponde. Mezclarlas en un único mecanismo es el error de raíz.

| Decisión | Mecanismo | Naturaleza |
|---|---|---|
| Constitucional (estatutos, fusión, disolución) | Un socio, un voto + supermayoría; vinculante, legal, lento a propósito | Humano |
| Membresía y sanciones | Comité + apelación, reglas graduadas | Humano (no automatizable del todo) |
| Parámetros operativos (fórmulas de línea, cadencia de *clearing*, comisiones, *demurrage*) | *Conviction voting* como **señal**; la junta ratifica dentro de límites | Híbrido |
| Asignación del común | *Quadratic funding* | Cripto |
| Ejecución diaria (*matching*, ciclos, *scoring*) | Delegada a *solver* + agentes; cadena garantiza transparencia *ex-post* | IA |
| **Gobernanza del protocolo (Capa 3)** | **Cuerpo de estándares de alcance mínimo ("consejo de células")** | **⚠️ FRONTERA NO RESUELTA (ver §7)** |

---

## 5. Restricción regulatoria: MiCA (vinculante en la UE)

- **Transitorio español hasta el 30 jun. 2026** → ventana cerrándose; cualquier diseño con token tiene meses, no años.
- **EMT (E-Money Token):** token estable frente a una moneda fiat → exige **€1.500.000 de capital**, respaldo 1:1 en custodio autorizado, autorización CNMV, auditoría semestral, redención garantizada, segregación de fondos. **Sardex no podría haber nacido bajo estas reglas.**
- **Categoría 3 (token sin pretensión de estabilidad, p. ej. gobernanza):** capital €50k–125k, *whitepaper*, sin respaldo 1:1.
- **Exención "verdaderamente descentralizado"** (sin emisor identificable): casi imposible de demostrar en la práctica.
- **Estrategia recomendada:** empezar con crédito mutuo denominado en euros, **sin token** (esquiva casi toda MiCA); añadir EMT autorizada o de terceros solo si la tracción lo justifica. Empezar legal y simple; añadir complejidad después. No hay tercer camino tras junio 2026.
- Adyacente: AML/KYC (Travel Rule sin gracia desde dic. 2024), DORA (ene. 2025), **fiscalidad** (ver §8).

---

## 6. Por qué NO una DAO permissionless (evidencia)

- Chainalysis (2022): **<1% de titulares controla el 90% del poder de voto** en 10 DAOs grandes.
- Gini de poder de voto **>0,94 (hasta 0,99)** en Compound/ENS/Uniswap → más desigual que el país más desigual del mundo (Sudáfrica ≈0,63).
- Participación media de voto **1,77%** (estudio de 50 DAOs); Decentraland 0,79%. **53%** de 30.000 DAOs completamente inactivas.
- Ataque de gobernanza real: **Beanstalk, 182M USD** vía *flash loan* en una sola transacción (mayoría de voto momentánea → propuesta maliciosa → vaciado del tesoro).
- Buterin (2021): el voto por tokens lleva inevitablemente a la plutocracia.
- **Conclusión:** las cooperativas resolvieron esto en **1844** (principio de Rochdale: un socio, un voto). Los DAOs reinventaron la gobernanza colectiva y la hicieron *peor* que una cooperativa del s. XIX. **Heredar de Rochdale, no de Ethereum.**

---

## 7. Problemas abiertos (NO fingir resueltos en el código ni en el pitch)

1. **Arranque en frío.** Cada célula debe bootstrapear densidad local; la IA de *matching* ayuda pero NO resuelve el huevo-y-gallina de los primeros ~100 miembros.
2. **Gobernanza del protocolo (Capa 3): captura vs. osificación.** Sin solución conocida. No prometer neutralidad creíble sin diseñarla explícitamente.
3. **Confianza transfronteriza.** Los *haircuts*/colateral entre células pueden comerse las ganancias de *clearing*, reduciendo potencialmente "lo global" a un directorio de células aisladas. Validar empíricamente si el *clearing* entre células vale la pena.
4. **Competencia con "usa un banco / usa euros".** Para empresas sanas en tiempos buenos, el banco es *frictionless*. La ventaja comparativa real es **contracíclica** y **marginal**: gana en recesiones (cuando el crédito bancario se evapora) y con empresas mal atendidas por la banca. WIR (1934) y Sardex (2009) nacieron de crisis, no de diseños de escritorio en bonanza. → **Implicación de go-to-market: targetear márgenes del sistema bancario y/o lanzar/escalar en contracción crediticia.**
5. **Lo irreducible.** Las instituciones las levantan personas que *quieren* que funcionen, vigilándose mutuamente durante años. Ningún smart contract ni diagrama de capas codifica esa voluntad. El andamio no construye el edificio. (Ostrom describió sistemas que *sobrevivieron*; no vemos los miles que fracasaron antes de cumplir sus principios.)

---

## 8. Realidad fiscal (parámetros del modelo de negocio)

- **Cada transacción es hecho imponible**: se declara y se paga IVA + renta **en euros** sobre el valor de mercado, aunque internamente se denomine en la moneda de la red (modelo Sardex, registrado como intermediario ante Hacienda). **No es un agujero fiscal.**
- **No es contraproducente para el Estado**: genera actividad que de otro modo no existiría (pastel mayor → más recaudación) y reduce morosidad/quiebras. La tensión es **política** (disintermedia bancos; es contracíclico → reduce el apalancamiento de la política monetaria), no fiscal ni legal. La incomodidad política aparece *a escala* (WIR ≈1–2% PIB suizo; Sardex ≈0,01% PIB español = invisible).
- **Modelo de ingresos recomendado: cuotas de suscripción** (deducibles como gasto de asociación profesional), **no comisiones por transacción** (que penalizan la circulación). Sardex: €150–1.000 alta + €350–2.500/año.
- **Caveat fiscal del crédito sin interés:** el crédito mutuo a 0% ahorra el interés pero pierde la **deducción fiscal de intereses** que sí da el crédito bancario. La comparación real es "crédito mutuo (sin deducción) vs. crédito bancario (con deducción)". Limitante real pero no fatal: irrelevante para empresas en pérdidas o en recesión (cuando no hay crédito bancario a ningún precio).

---

## 9. Heurísticas importadas (modelos mentales, con banderas de honestidad)

Usar como **heurísticas de diseño**, NUNCA como "validación natural" del modelo. La disciplina intelectual es parte del diseño.

- **Micorriza** → ⚠️ ciencia del "wood wide web" en disputa (Karst et al., *Nature Ecology & Evolution*, 2023). Sirve para: redistribución de nodos fuertes a débiles, intermediario que toma su "corte" sostenedor, diversidad→resiliencia. NO como prueba de nada.
- **Moho mucilaginoso / *Physarum*** (Tero et al., *Science*, 2010) → el análogo **honesto y bien documentado** para la capa de agentes: computación distribuida sin cerebro central que halla redes eficientes y resilientes por reglas locales. (Es la metáfora buena para la Capa 2, en lugar del "internet de los árboles".)
- **Ventana de viabilidad** (Lietaer/Ulanowicz) → resiliencia pesa ≈2× la eficiencia. **Equilibrar, no maximizar eficiencia.** El monocultivo (un proveedor, una moneda) es estructuralmente frágil. → Justifica los invariantes 6 y 8.
- **Paradoja de May (1972)** → más conexiones ≠ más estabilidad; conectancia intermedia óptima. → Invariante 6.
- **8 principios de Ostrom** (Nobel 2009) → la columna vertebral de gobernanza: límites claros, reglas locales, elección colectiva, **monitorización (=blockchain)**, **sanciones graduadas**, resolución barata de conflictos, derecho a organizarse, **gobernanza policéntrica/anidada (=la federación)**. Método opuesto a cripto: observar qué sobrevivió siglos, no teorizar un mecanismo elegante.
- **Permacultura** → distinción **diseño para permanencia vs. diseño para producción**. Sardex está atrapada en "producción" (35 personas en nómina, supervisión constante, pérdidas). **Objetivo: permanencia** vía automatización estratégica (IA en *scoring*/*matching*/*clearing*) conservando el *embedding* relacional. "La solución es el problema": no hay perfección, solo *trade-offs*; decidir dónde se tolera intervención humana y dónde se elimina.
- **Rochdale (1844)**: un socio, un voto → anti-plutocracia. → Invariante 3.
- **Naval (creación ≠ captura)**: democratizar la creación NO democratiza la captura (imprenta→imperios mediáticos; internet→Google/Meta; la IA concentra *más fuerte* porque sus rendimientos escalan con cómputo+datos ya concentrados). **El sistema ES, precisamente, la institución de captura/distribución que la IA no provee.** La riqueza se captura con propiedad, no con creación; democratizar la creación vuelve la coordinación/distribución *más* importante, no menos.
- **IA y medio ambiente**: excelente *solver* para subproblemas con forma de optimización (balanceo de red renovable, descubrimiento de materiales, *matching* de simbiosis industrial, monitorización/MRV); **casi irrelevante para el núcleo, que es un comunal planetario** (quién paga, quién se obliga) = problema de Ostrom, no de cómputo. Cuidado con el solucionismo (Morozov: tomar el subproblema tratable por la restricción vinculante), con la huella energética de la propia IA, y con Goodhart (optimizar el carbono medible puede destrozar lo no medido).

---

## 10. Qué construir primero (secuenciación)

0. **Validar el problema antes que la tecnología** (0–3 meses): entrevistar 30–50 pymes sobre dolor real de liquidez/cobros. *Umbral:* identificar ≥1 clúster denso con relaciones comerciales mutuas reales (sin ciclos no hay sistema).
1. **Piloto relacional mínimo, sin blockchain** (3–12 meses): replicar el núcleo de Sardex —50–150 empresas veteadas, líneas individuales, un *broker*, contabilidad de crédito mutuo simple, denominación en euros. *Métrica clave:* % de deuda neta reducida por *clearing*. *Umbral para añadir cripto:* >200 empresas y necesidad de interoperar o de reputación portable.
2. **Capa técnica componible** (12–24 meses): *clearing* on-chain auditable (Capa 1), reputación SBT, integración con EMT autorizada. Estructura: cooperativa/SCE, NO DAO permissionless. Introducir agentes de IA para *matching* y detección de ciclos (Capa 2).
3. **Comunes y escala/federación** (24+ meses): *quadratic funding* (Capa 5); gobernanza híbrida; replicación a otros clústeres con el protocolo de federación (Capa 3).

---

## Apéndice — Madurez de la evidencia (para no sobre-prometer)

- **PROBADO / operacional:** WIR, Sardex (con dificultades financieras: pérdidas 2023–2024, no alcanzó 20.000 pymes), Kalundborg, Sarafu/Grassroots Economics (Kenia, ~55.000 usuarios, dependiente de donantes, población sin fiat, no-B2B), Gitcoin *quadratic funding*.
- **EXPERIMENTAL:** Circles UBI (cooperativa **cerrada ene. 2024**), Holochain/HoloFuel, Regen/ReFi (~50% no genuinamente regenerativo), DePIN, agentes económicos de IA.
- **PURAMENTE TEÓRICO:** la "economía micorrízica" como tal, la federación global de células, y el diseño híbrido completo de este documento.

---

### Mapa de la conversación (índice de temas tratados)

1. La metáfora micorrízica como red de simbiosis económica B2B → §0, §9
2. Sardex / crédito mutuo como análogo probado (relacional, veteado, no escala, contracíclico) → §3 Capa 0, §7.4, §8
3. Implicaciones fiscales del crédito mutuo y el trueque → §8
4. El estado disputado de la ciencia del "wood wide web" → §9
5. Heurísticas de otras ciencias (inmunología, termodinámica, redes complejas, teoría de la información, juegos evolutivos, sucesión ecológica, morfogénesis) → §9
6. Principios de permacultura (permanencia vs. producción) → §9
7. Lightning Network → mallas de crédito federadas → §3 Capa 3
8. Regulación MiCA y entorno europeo → §5
9. Por qué fracasa la gobernanza DAO (plutocracia, apatía, ataques) → §6
10. Gobernanza híbrida vía los 8 principios de Ostrom → §4, §9
11. El rol de los agentes de IA (solver determinista vs. matcher estocástico, cortacircuitos) → §1, §3 Capas 1–2
12. Experimento mental: economía post-humana de puros agentes → (marco filosófico; informa §0)
13. Naval: creación ≠ captura; bonanza colectiva e IA; crisis ambiental → §9
14. Arquitectura concreta a escala europea/mundial → §3, §4, §7

> **Cita de anclaje (Gabriele Littera, cofundador de Sardex):** "No tenemos un algoritmo, solo relaciones; nuestros brokers ayudan a quien está en apuros sugiriéndole nuevos negocios. La tecnología es una ayuda." → El reto de ingeniería es automatizar la capa combinatoria (*clearing*, *matching*, *scoring*) **sin** destruir la capa relacional que hace funcionar al sistema.
