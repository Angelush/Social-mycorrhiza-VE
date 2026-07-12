# Micorriza Política — Protocolo social C2C / B2C / C2B
## Síntesis de diseño para implementación

> **Propósito.** Destila la rama *social* de la conversación (relaciones interpersonales, comercio entre individuos, individuo↔empresa, colaboración cívica) en un brief importable a un proyecto que lo convertirá en código. Es el documento hermano del brief B2B (`micorriza-brief-diseno.md`) y comparte su método: conclusiones como principios, principios duros como **invariantes** (→ guardarraíles y tests), arquitectura como componentes etiquetados por naturaleza (`[HUMANO]` / `[DETERMINISTA]` / `[ESTOCÁSTICO·LLM]` / `[PROTOCOLO]`).
>
> **Diferencia esencial con el brief B2B:** el dominio social está hecho de otro material. El motor monetario de compensación (*clearing*) del lado B2B **NO se traslada** —las personas no tienen un grafo de deudas denominadas que netear—. Lo que se traslada es la capa de gobernanza, la de reputación y la de emparejamiento. El "nutriente" interpersonal es mayoritariamente *no fungible y no denominado*: cuidado, atención, confianza, conocimiento, tiempo, pertenencia. Tratar lo social como un mercado a optimizar es el error de categoría que destruye lo que se quiere proteger.

---

## 0. Tesis rectora (la estrella polar)

**Una sociedad culta que se organiza a pesar de sus diferencias es fuerte y resiliente, y eso es en parte un problema de infraestructura — pero la infraestructura NO es un protocolo de mercado ni de optimización.** Es *legibilidad de la confianza + afordancia prosocial + gobernanza de lo común + separación de modos relacionales + topología local acotada + suelo simbólico compartido*. El insumo más profundo —la voluntad de cooperar, el significado compartido— el protocolo solo puede **andamiarlo**, nunca fabricarlo.

**Cambio de metáfora obligatorio:** no eres un ingeniero que *construye* cooperación; eres un **jardinero** que *crea las condiciones* para que crezca sola. → La meta NO es la eficiencia (ese es el error de categoría); es la **fertilidad**: las condiciones bajo las cuales la confianza y la cooperación se reproducen solas. Se conecta con la permacultura del brief B2B: diseño para la *permanencia* y la *fertilidad*, no para la *producción*. **Métrica de éxito:** no "cuántas interacciones procesa", sino "¿es el suelo más fértil cada año? ¿la gente confía más, coopera más fácil, tolera mejor la diferencia tras pasar por aquí?".

---

## 1. Invariantes del sistema (NO negociables → guardarraíles y tests)

Cada invariante es, además, la **inversión de una decisión de arquitectura del crédito social chino** (ver §3, el ancla negativa).

1. **La separación de modos relacionales es sagrada.** La lógica de mercado (precio, valoración, denominación, rastreo de reciprocidad) NUNCA entra en las habitaciones del don o de la igualdad. La membrana se hace cumplir arquitectónicamente. *(Sustento: el muro kula/gimwali de las Trobriand; el experimento de la guardería de Gneezy–Rustichini 2000; Titmuss sobre la sangre; Tetlock sobre taboo tradeoffs.)*
2. **NO existe un escalar global de la persona.** Ningún número único, ningún código uniforme, ninguna "vista de dios" de la confiabilidad humana. La reputación es contextual, relacional, consultada-desde-una-posición y específica. *(Inversión directa del código social unificado chino = DNI.)*
3. **La reputación abre puertas; estructuralmente NO puede cerrarlas con facilidad.** Asimetría por diseño: avalar/habilitar es fácil; excluir/vetar es difícil y acotado. Lógica de **lista blanca**, nunca de lista negra. *(Inversión de la lista de incumplidores judiciales "laolai".)*
4. **Visibilidad local acotada, JAMÁS broadcast global.** Federación de contextos a escala Dunbar (~150) con puentes finos de traducción. Sin "timeline de toda la humanidad". *(Sustento: boids/murmuración de Reynolds — cada ave atiende ~7 vecinos; anti-colapso de contexto.)*
5. **El olvido es un mecanismo central**, no un parche. Los datos caducan; el derecho al olvido es nativo. Sin dossier permanente. *(China está descubriendo tarde la "reparación de crédito"; aquí es de fábrica.)*
6. **SIN tenedor central del grafo de confianza.** Auto-soberano y distribuido. No hay trono que agregue la confiabilidad de todos → **no hay trono que capturar ni convertir en instrumento de vigilancia.** Este es el cortafuegos estructural decisivo: la diferencia con Pekín no es la buena intención, es que aquí *no existe el asiento desde el que se vigila*.
7. **La voz en la gobernanza es independiente de la reputación.** Una persona, una voz; jamás ponderada por el puntaje. Si la reputación pondera el voto → reputación → poder → disciplina, y has reconstruido el crédito social por la puerta de atrás. *(Anti-plutocracia + anti-crédito-social.)*
8. **La capa de emparejamiento optimiza COOPERACIÓN INICIADA, nunca *engagement*.** El pecado original de las plataformas fue optimizar *engagement*, y el camino más corto al *engagement* es la indignación. Función objetivo = cooperación exitosa iniciada, no tiempo-en-app.
9. **Cortacircuitos anti-cascada OBLIGATORIOS** donde haya propagación/viralidad: fricción antes de propagar, contexto antes de juzgar, límites de velocidad a la viralidad. *(Sustento: el "molino de hormigas" / espirales de la muerte estigmérgicas; cascadas de información; turbas.)*
10. **Opt-in, *forkable*, con salida.** Participación voluntaria; las comunidades pueden bifurcarse; el individuo puede salir sin perder su *personhood*. *(Inversión del diseño obligatorio y sin salida de China. Hirschman, "exit/voice/loyalty": un sistema del que no puedes salir es una jaula, sean cuales sean las intenciones. La salida es el control último.)*

---

## 2. Premisas refutadas (errores de categoría a evitar — el fundamento conceptual)

El mayor riesgo del proyecto no es técnico: es cometer uno de estos cuatro errores de categoría. Documentados para que el sistema no los repita.

1. **"La lógica B2B se traslada a C2C/B2C."** ❌ Solo en parte. NO se traslada el *clearing* (no hay grafo de deudas denominadas entre personas). SÍ se traslada gobernanza, reputación y emparejamiento. "Sardex para personas" es falso en su núcleo; quien lo persigue acaba construyendo un banco de favores con puntos → desliza al error 2.
2. **"Las relaciones comerciales y la colaboración social son la misma cosa y admiten un protocolo único."** ❌ Corren lógicas categóricamente distintas (modelos relacionales de Alan Fiske: *communal sharing* / *equality matching* / *market pricing*). **Introducir lógica de mercado en una relación comunal la corrompe, no la optimiza** —y de forma a menudo *irreversible* (en la guardería de Gneezy, al quitar la multa la tardanza no volvió a bajar: el contrato moral, una vez monetizado, no se regenera)—. → Origen de la Invariante 1.
3. **"Eficiencia y efectividad son las metas correctas también para lo social."** ❌ Para lo social, casi lo contrario. El tejido resiliente se construye con *redundancia, holgura, lazos débiles y rituales "inútiles"* (Granovetter, *The Strength of Weak Ties*; Putnam sobre capital social). Una sociedad "eficiente" donde toda interacción es óptima y transaccional es precisamente *de baja confianza y frágil* —la confianza se fabrica en la fricción y el juego repetido—. → Origen del reframe fertilidad-no-eficiencia (§0).
4. **"Un protocolo puede ser la herramienta para alcanzar la fortaleza social, local y globalmente."** ❌ con dos matices. (a) Riesgo *solucionista* (Morozov): la cohesión es un problema de *práctica y significado*, no de protocolo; la herramienta *abarata/andamia* pero no *fabrica* la voluntad de cooperar. (b) "Global" es el peligro mayor: confianza y significado son locales y encarnados (Dunbar ~150); "comunidad global" es una metáfora, no una cosa. Globalizar un grafo social produce *colapso de contexto* —lo que destruyó a las plataformas—. → El trabajo del protocolo a escala global NO es un único grafo planetario, sino **la traducción e interoperabilidad entre mundos locales de confianza.** Principio anti-Leviatán, con más fuerza que en B2B.

---

## 3. Ancla negativa: el crédito social chino (inversión sistemática)

Igual que en B2B usamos Sardex como ancla positiva, aquí usamos el sistema chino como ancla negativa: la arquitectura se diseña invirtiendo cada una de sus decisiones. **Importante (corrección del mito):** NO es el "puntaje único nacional de Black Mirror". La fuente autorizada (China Law Translate / Jeremy Daum) confirma que nunca se concibió como un ranking holístico del ciudadano. Es sobre todo una **herramienta administrativa de cumplimiento**: registro de crédito empresarial + ejecución de sentencias + listas regulatorias. La plataforma central (NCISP) acumulaba a inicios de 2025 >80.700 millones de registros sobre ~180 millones de *empresas*. El puntaje individual sigue fragmentado, ciudad por ciudad, ligado a conductas específicas; muchos pilotos municipales se cerraron. Sesame/Zhima Credit (Alibaba) quedó formalmente separado del sistema estatal en 2024. La ley nacional sigue en borrador. **Pero la parte coercitiva es real y arquitectónica:** la lista negra (sobre todo la de incumplidores judiciales, *laolai*) restringe viajes, financiación y acceso al mercado. Y se está internacionalizando vía Nueva Ruta de la Seda / BRICS.

| Dimensión | Crédito social chino (antipatrón) | Micorriza política (inversión) |
|---|---|---|
| Topología | Centralizado (NCISP / Credit China, hub estatal) | Federación de células locales, sin hub central |
| Gobernador | Estado único, top-down | Policéntrico, gobernado por miembros (sociocracia) |
| Función | Disciplinar conducta hacia "confiabilidad" estatal | Habilitar cooperación; legibilidad que informa |
| Mecanismo con dientes | Listas negras, prohibición de viajar, vergüenza pública | Sin listas negras; reputación abre puertas, no las cierra |
| Identidad | Código social unificado = DNI; dossier permanente | Reputación contextual, sin escalar global, con olvido |
| Consentimiento | Obligatorio para residentes; sin salida | Opt-in, *forkable*, con salida garantizada |
| Modos relacionales | Régimen único de legibilidad para toda la vida | Habitaciones separadas; el mercado no se filtra al don |
| Tenencia de datos | Agregación estatal central | Sin tenedor central → sin trono que capturar |
| Visibilidad | Nacional | Local acotada (Dunbar), puentes finos |
| Símbolo | Un único sistema de valores puntuado | Pluralidad de capas simbólicas opt-in |

**Ironía generativa (taoísmo / *wu wei*):** China es cuna del *wu wei* —el no-forzar, raíz oriental del *laissez-faire*— y construye el aparato de legibilidad más ambicioso de la historia. El *wu wei* es exactamente la postura del *jardinero* (§0); el sistema chino es el ingeniero forzando el jardín a una cuadrícula. **La sabiduría taoísta está del lado de este diseño, no del de Pekín.** La micorriza política es, bien hecha, *infraestructura wu wei*: prepara el suelo y se aparta.

---

## 4. Arquitectura de referencia (la pila, etiquetada)

### Capa 0 — La célula / círculo de confianza `[HUMANO · LOCAL]`
El átomo es local y acotado por *Dunbar* (~150) y por *contexto* (no por personalidad jurídica): un barrio, un gremio, una afinidad, una asociación de ayuda mutua, una ROSCA. Es el vecindario de la murmuración, el grupo de la *tanda*, la asociación cívica de Putnam. Aquí la reputación significa algo porque es contextual y la interacción es cara a cara y repetida.

### Capa 1 — Partición por modo relacional `[INVARIANTE ARQUITECTÓNICA — "las habitaciones"]`
**La capa más importante y la más novedosa.** Habitaciones explícitamente separadas que corren lógicas distintas (Fiske):
- **Don comunal** (ayuda mutua, cuidado): SIN puntaje, SIN denominación, SIN rastreo de reciprocidad (rastrearla la mata). Reciprocidad difusa y no contabilizada.
- **Emparejamiento por igualdad** (turnos, favores, bancos de tiempo, ROSCAs): simétrico y balanceado, pero NO precificado.
- **Precio de mercado** (comercio C2C/C2B real, venta, *gig*): aquí SÍ son apropiados denominación, precio y valoración.

**Regla cardinal (muro kula/gimwali):** la lógica de mercado NUNCA se filtra a las habitaciones del don o la igualdad. La arquitectura hace cumplir la membrana. → Invariante 1.

### Capa 2 — Legibilidad de la confianza `[EL FILO DE LA NAVAJA — vs. crédito social]`
Seis principios la mantienen del lado bueno de la navaja:
1. **Contextual, no global** — legible dentro de una habitación, no un número que te sigue a todas partes.
2. **Relacional, no absoluta** — responde "¿la gente en que confío confía en esta persona?" (red de confianza transitiva, tipo web-of-trust / grafo de Circles), consultada desde *tu* posición; no un puntaje con vista de dios.
3. **Específica, no totalizante** — hechos legibles ("completó 12 intercambios", "avalada por X"), no un veredicto moral.
4. **Con olvido incorporado** — los datos caducan; derecho al olvido nativo.
5. **De suma positiva** — *abre* puertas (lista blanca); estructuralmente no puede cerrarlas con facilidad (nunca lista negra).
6. **Sin tenedor central** — grafo distribuido y auto-soberano; no hay trono que capturar. → Invariante 6, el cortafuegos decisivo.

*Tensión sin resolver:* resistencia Sybil sin totalización de identidad (ver §6).

### Capa 3 — Afordancia prosocial / emparejamiento `[ESTOCÁSTICO · LLM — propone, no impone]`
Agentes que afloran "quién cerca de ti necesita lo que ofreces", "quién comparte este objetivo", y que **traducen entre contextos** (el verdadero trabajo de la capa "global"). Es la función *kula*: construir el sustrato de confianza sobre el que cabalga el intercambio real. **Regla:** propone, el humano dispone. **Bandera roja:** NUNCA optimiza *engagement* (Invariante 8).

### Capa 4 — Quórum / aseguramiento para acción colectiva `[CONTRATOS DE ASEGURAMIENTO — umbral bacteriano]`
El *solver* del arranque en frío de bienes sociales: "lo hago si lo hacen otros N" (contrato de aseguramiento; *dominant assurance contract* de Tabarrok, que paga prima al comprometido si el umbral no se alcanza → elimina el riesgo de comprometerse en vano). Convierte el huevo-y-gallina en característica. **Aquí emerge el poder C2B:** individuos que se agregan condicionalmente en una contraparte con peso negociador (compra colectiva, presión cívica, fondos de ayuda mutua). *(Sustento biomimético: quórum bacteriano — Vibrio fischeri enciende la bioluminiscencia solo al cruzar densidad umbral.)*

### Capa 5 — Coordinación estigmérgica + cortacircuitos anti-cascada `[FEROMONAS + CORTACIRCUITOS]`
Coordinación por trazas en el entorno (historiales de contribución, caminos, señales) — como el software libre, Wikipedia, o los precios de Hayek. **Lado oscuro obligatorio de mitigar:** la misma estigmergia produce el "molino de hormigas" (espirales de la muerte), las cascadas, las turbas. Cortacircuitos: fricción antes de propagar, inyección de contexto antes del juicio, límites de velocidad a la viralidad, cero broadcast global. → Invariante 9.

### Capa 6 — Gobernanza sociocrática `[CONSENTIMIENTO, NO CONSENSO — el Ostrom social]`
Por *consentimiento* (ausencia de objeción razonada), no por consenso unánime ni por mayoría. Linaje Haudenosaunee (Gran Ley de la Paz) / cuáquero / sociocracia. Anidada y policéntrica (círculos dentro de círculos, *double-linking*). **Invariante crítica:** la voz es independiente de la reputación (Invariante 7).

### Capa 7 — Sustrato simbólico compartido `[SUELO SIMBÓLICO COMÚN]`
El lugar honesto del mito, el ritual, los calendarios y la astrología: NO como predicción (ver §6, nota de honestidad), sino como *vocabulario simbólico compartido* y *andamio ritual* que permite a personas heterogéneas coordinar significado, marcar el tiempo juntas y deliberar sobre el carácter — el suelo común que la cooperación a través de la diferencia requiere (generador de puntos de Schelling; deliberación proyectiva). **Bandera:** todo símbolo que une hacia dentro divide hacia fuera → la arquitectura admite *múltiples* capas simbólicas en plural; NUNCA impone una. *(Inversión del sistema único de valores puntuado de China.)*

---

## 5. Modelos biomiméticos, anclas históricas y nota astrológica

Usar como **heurísticas de diseño**, con honestidad sobre dónde cada una se rompe.

### Modelos biomiméticos (no limitados a la micorriza)
- **Sistema inmune — *tolerancia*** → el modelo que habla más directo a "organizarse a pesar de las diferencias". El reto no es atacar, es distinguir amenaza de *self* y aprender a NO atacar lo inofensivo-distinto. Dos fallos = dos fallos sociales: *inmunodeficiencia* (sin defensa: fraude, free-riders) y *autoinmunidad* (el cuerpo atacándose: espirales de pureza, linchamiento, polarización). Pluralismo = tolerancia inmune; polarización = autoinmunidad. → Prioriza mecanismos de *tolerancia* (fricción y contexto antes de la condena; reparación antes que expulsión) sobre maximizar detección/castigo. *Se rompe en:* el sistema inmune no perdona por razones; lo social debe.
- **Murmuración / boids (Reynolds)** → resuelve "local *y* global". Coherencia global desde reglas locales, cada nodo atiende ~7 vecinos. **Limitar la información de cada nodo a su vecindario es lo que produce el comportamiento colectivo sano.** Las plataformas hicieron lo contrario (información global → estampida, no bandada). → Invariante 4.
- **Quórum bacteriano** → resuelve el arranque en frío de bienes sociales (Capa 4).
- **Estigmergia (hormigas/termitas)** → coordinar sin mandar, vía trazas en el entorno (Capa 5). *Lado oscuro:* molino de hormigas / cascadas → exige cortacircuitos.
- **Micorriza** (modelo de partida) → su residuo honesto en lo social NO es el *clearing* (no hay grafo de deudas) sino la *redistribución del fuerte al débil vía intermediario* = **ayuda mutua**.

### Anclas históricas (la historia SOSTIENE la tesis; las restricciones están en los mecanismos, no en el fin)
- **ROSCAs** (tandas, cundinas, susu, hui, chit funds) → prueba de que la cooperación C2C funciona sobre puro colateral social, milenaria y global. **Escala fatal por la misma razón que Sardex:** el colateral social *es* la red local densa y se diluye al estirarla. → El teorema recurrente: lo que da fuerza a la cooperación interpersonal (el *embedding* local) es lo que le impide escalar.
- **Confederación Haudenosaunee (iroquesa)** → unidad *en* la diferencia mediante estructura federal, no homogeneización. Siglos de durabilidad. La tesis hecha historia.
- **Consenso cuáquero / sociocracia** → protocolo procedimental para decidir entre el desacuerdo sin tiranía de la mayoría: **consentimiento, no consenso**. Directamente importable como Capa 6.
- **Kula ring (Malinowski, Trobriand)** → el ancla más hermosa: un circuito ceremonial de don (kula) que construye el sustrato de confianza sobre el que cabalga el comercio real (gimwali), **rigurosamente separados**. Sabían hace milenios que mezclar don y mercado envenena el don → Invariante 1.
- **Putnam, *Making Democracy Work*** → la columna evidencial más sólida: regiones con densas asociaciones cívicas *horizontales* desarrollaron gobiernos eficaces y resilientes; las de lazos *verticales* (clientelismo) no — diferencia rastreable siglos atrás. Densidad cívica → fortaleza institucional. **Advertencia heredada:** el capital social se acumula lento y se destruye rápido; no se inyecta por decreto ni por app, solo se *cultiva*.

### Nota astrológica (honestidad exacta)
Como mecanismo causal/predictivo, **fracasa** en pruebas controladas (Carlson, *Nature* 1985: astrólogos a nivel de azar emparejando cartas con perfiles; metaanálisis posteriores no la rescatan). No se usará como motor de predicción — sería fraude. **PERO** los sistemas simbólicos compartidos (astrología, mito, tarot, I Ching, calendarios rituales) sí han funcionado como *tecnologías sociales*: vocabularios comunes y andamios rituales para coordinar significado, marcar el tiempo y deliberar sobre carácter y decisiones (Jung: arquetipos y lenguaje proyectivo; generadores de puntos de Schelling). **Su lugar honesto = una posible capa de símbolo compartido (Capa 7), una de varias, con la bandera in-group/out-group encendida.** Su función no es predecir; es construir suelo simbólico común.

---

## 6. Problemas abiertos (apuestas MÁS altas que en B2B: el fallo no es una red muerta, es una jaula de vigilancia)

1. **El filo de la navaja puede ser intransitable.** Toda capa de legibilidad puede deslizarse al polo del puntaje/vigilancia. Las invariantes lo hacen *estructuralmente difícil* (sobre todo la 6, no tener trono), pero **quién gobierna y para qué decide al final**: protocolo benigno + mano maligna = la pesadilla. La arquitectura no puede garantizar su propio uso. *(El problema más profundo. Stakes: una jaula, no solo un fracaso.)*
2. **Resistencia Sybil sin totalización de identidad.** Frenar cuentas falsas sin construir el dossier-DNI obligatorio: sin resolver. La red de confianza ayuda pero excluye al recién llegado y al no-avalado (problema de bootstrapping y exclusión).
3. **No se puede fabricar la voluntad de cooperar.** Se andamia, no se manufactura. Una sociedad de baja confianza puede no arrancar (Putnam: no se inyecta). Más severo que en B2B.
4. **La métrica de fertilidad es difícil de medir y fácil de Goodhart.** "¿Es el suelo más fértil?" resiste la cuantificación; cualquier proxy (interacciones, avales) se gamifica y corrompe al optimizarlo. La misma inmedibilidad que la protege de volverse puntaje dificulta demostrar el "éxito" a financiadores.
5. **Federación / traducción global = frontera no resuelta** (como en B2B la gobernanza del protocolo), con riesgo añadido: la capa de "traducción entre mundos de confianza" puede volverse un cuello de botella recentralizador.
6. **Salida y reputación se contradicen.** Si puedes salir y volver limpio, blanqueas mala reputación; si no puedes, es un dossier. Equilibrar derecho de salida y rendición de cuentas: genuinamente duro.

---

## 7. Qué construir primero (la secuenciación es la inversión más bella de China)

**Principio:** un sistema con mentalidad de "crédito social" construye el puntaje primero y los servicios después. **Tú haces lo contrario: construye primero las partes que NO PUEDEN convertirse en un puntaje de vigilancia, y añade la legibilidad la última y con máximo cuidado.**

- **Etapa 0 — Validar** (0–3 meses): encuentra una comunidad real con un coste de cooperación real (ayuda mutua, acción colectiva, comercio local) que *quiera* esto. (Putnam: busca suelo ya algo fértil; no se cultiva en roca.)
- **Etapa 1 — Una célula, un modo, SIN puntaje** (3–9 meses): herramienta de ayuda mutua o banco de tiempo para UNA comunidad local. Solo habitaciones de don/igualdad. SIN habitación de mercado. SIN escalar de reputación. Solo visibilidad local acotada (Capa 0) + contratos de aseguramiento para acción colectiva (Capa 4). **Demuestra fertilidad** (¿la gente confía y coopera más?) antes de añadir una sola capa de legibilidad.
- **Etapa 2 — Legibilidad mínima + habitación de mercado separada** (9–18 meses): añade la Capa 2 SOLO como red de confianza (relacional, contextual, que abre puertas), con olvido nativo y sin tenedor central. Añade la habitación de mercado como espacio *separado* y particionado (Capa 1).
- **Etapa 3 — Federación** (18+ meses): conecta células con puentes finos de traducción (Capa 3); gobernanza sociocrática (Capa 6); capa simbólica como pluralidad opt-in (Capa 7).

---

## Apéndice — Madurez de la evidencia y notas de fuente

- **PROBADO histórica/empíricamente:** ROSCAs (global, milenario), capital social → instituciones (Putnam), consenso cuáquero/sociocracia (siglos), separación don/mercado (kula/gimwali; replicado por Gneezy, Titmuss, Tetlock), federación en la diferencia (Haudenosaunee).
- **MODELO / HEURÍSTICA (no implementación probada):** todos los modelos biomiméticos (inmune, boids, quórum, estigmergia) — son lentes de diseño, no sistemas validados a esta escala.
- **ESPECULATIVO / FRONTERA:** la legibilidad-de-confianza-sin-vigilancia (el filo de la navaja), la federación global de mundos de confianza, los agentes LLM de emparejamiento prosocial, y el protocolo completo de este documento.
- **REFUTADO como mecanismo:** la astrología como predicción/causación (Carlson 1985) — admitida SOLO como capa simbólica.
- **Sobre China:** caracterización basada en fuentes de 2025–2026 (China Law Translate / J. Daum como referencia académica; directriz estatal de 23 medidas de marzo 2025; ley nacional aún en borrador). El "puntaje único nacional" es mito; la coerción real opera vía listas negras (laolai). Verificar estado actual antes de citar, por ser sistema en evolución activa.

---

### Mapa de la conversación (rama social)

1. Extensión del modelo B2B a C2C/B2C/C2B → §0, §2.1
2. Las cuatro premisas refutadas (errores de categoría) → §2
3. Separación de modos relacionales / "las habitaciones" → §4 Capa 1, Invariante 1
4. Legibilidad de la confianza vs. crédito social (el filo de la navaja) → §4 Capa 2, §6.1
5. El crédito social chino como ancla negativa + ironía taoísta → §3
6. Modelos biomiméticos (inmune-tolerancia, boids, quórum, estigmergia) → §5
7. Anclas históricas (ROSCAs, Haudenosaunee, cuáqueros, kula, Putnam) → §5
8. El lugar honesto del mito y la astrología → §4 Capa 7, §5
9. Reframe jardinero/fertilidad (no ingeniero/eficiencia) → §0
10. Arquitectura concreta por capas → §4
11. Secuenciación (construir lo no-vigilante primero) → §7

> **Frase rectora para destilar a código:** no construyes cooperación, cultivas las condiciones para que crezca sola; la meta no es la eficiencia sino la fertilidad; y la línea entre "reputación que habilita" y "puntaje que disciplina" no la decide la tecnología sino quién la gobierna — por eso la arquitectura quita el trono (sin tenedor central) y deja la salida abierta (forkable), que es lo más cerca que el diseño puede estar de garantizar que la herramienta no se vuelva jaula.
