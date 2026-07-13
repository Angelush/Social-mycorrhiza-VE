# Lo intocable — los diez invariantes en los tres modos + lista de señalados

> Contrato maestro del fork. Si cualquier spec de área parece pedir relajar uno de estos, la
> interpretación es errónea: el conflicto se documenta en `audit.md`, no se resuelve en silencio.
> **Ningún modo (`paz` / `catastrofe_acotada` / `catastrofe_severa`) toca ninguno de estos.**

## Los diez invariantes (irrepresentables en los tres modos)

1. **Ningún escalar global de la persona.** Score/puntuación/reputación numérica: forma rechazada
   en entrada, inconstruible en salida, en las seis capas.
2. **Ninguna lista negra / veto / sanción representable.** Whitelist-not-blacklist; una ausencia
   es "sin información desde tu posición", nunca una marca.
3. **Vista de dios irrepresentable.** `consultante` obligatorio en legibilidad; el grafo es
   suministrado, hop-bounded, y se descarta; la salida son caminos y hechos, jamás un número.
4. **Voz independiente de la reputación.** Un token, una voz; la ponderación no se puede ni
   escribir (taxonomía de peso de voto rechazada).
5. **Sin tenedor central.** Funciones puras; nada persistido; ningún trono que capturar.
6. **El agente propone, el humano dispone.** El LLM sigue inyectado, encajonado, y su orden se
   descarta con sort canónico.
7. **Ninguna señal de engagement representable** en el emparejador.
8. **Cortacircuitos anti-cascada** activos en toda propagación. *Los parámetros varían por modo;
   el mecanismo nunca se apaga.*
9. **Salida siempre disponible.** Participación opt-in; el fork mismo es prueba del derecho a
   bifurcar.
10. **Sin integración con canales estatales de identidad o denuncia** (VenApp o equivalente):
    constraint duro con cláusula-porque — el riesgo es la captura política de la coordinación, no
    solo la vigilancia.

**Lo que los modos SÍ calibran** (y nada más): retención (ventanas de expiración), alcance
(`max_hops`, portabilidad entre células), tamaño de payload, y parámetros de los cortacircuitos.

## Verificabilidad por test (criterio de aceptación global)

Los diez invariantes deben ser verificables por test **en los tres modos**. En la práctica: cada
test de forma prohibida (escalar, lista negra, peso de voto, engagement, vista de dios) se
parametriza sobre `modo ∈ {paz, catastrofe_acotada, catastrofe_severa}` y debe rechazar
idénticamente. Un modo que admitiera una forma prohibida es un fallo de invariante, no un ajuste.

## Señalado, no falsamente resuelto (lista consolidada)

Lo que el código **no** puede resolver se declara aquí abiertamente; ninguno se "resuelve" en
prosa sin mecanismo. Si no hay test que lo fije, vive en esta lista.

- **Sybil / person-binding.** Un token, una voz; ligar token↔persona está fuera de alcance
  (heredado). El motor cuenta tokens distintos, no personas.
- **Juicio escalar en texto libre.** "Esta persona es un 3/10" en prosa: la membrana detecta
  formas (claves, patrones de valor), no semántica. La semántica es gobernanza humana.
- **`depurar()` como convención del llamador.** Una función pura no puede obligar al llamador a
  ejecutarla tras una escalada; es convención documentada + test + helper, no garantía.
- **Escalada abusiva del modo.** Un miembro malicioso puede degradar la coordinación escalando
  repetidamente; la desescalada por consentimiento (Capa 6) es el contrapeso; el cooldown/fricción
  es una decisión de gobernanza abierta, no un mecanismo impuesto.
- **Transporte / malla fuera del núcleo.** SMS/LoRa en `catastrofe_severa` es el motivo del límite
  de 512 bytes, pero el transporte en sí no lo modela el núcleo puro.
- **Parámetros de modo como decisión de gobernanza.** La tabla de límites son *defaults*
  ajustables por Capa 6, no dogma incrustado.
- **Inflación no modelada.** El motor no modela inflación (sería otra tasa); `expira_en` corto en
  VES es convención documentada del llamador.
- **Correlación entre salidas.** Una función pura olvida por diseño; correlacionar salidas
  almacenadas es una preocupación de gobernanza/almacenamiento (rotación de tokens, `expira_en`),
  no algo que la función pueda cerrar.
