# Intención — fork Venezuela (micorriza-ve)

## El objetivo real (no el aparente)

Aparente: "traducir el repo al castellano y añadirle cripto". Real: **recalibrar la
infraestructura de coordinación a un entorno donde la banca, los tribunales y el Estado no
cumplen su función** — Venezuela, julio 2026 — sin ceder ninguno de los invariantes que hacen
al sistema no-capturable y no-vigilante.

La corrección en una frase (del anexo B2B): los argumentos anti-TOKEN eran universales y se
mantienen (el precedente Petro/Sunacrip los REFUERZA); los argumentos anti-RIELES-cripto eran
UE-contingentes y en Venezuela se INVIERTEN — allí los rieles cripto son la infraestructura de
pagos que funciona y la banca es la capa rota. **Cripto como fontanería, nunca como promesa.**

## Auditoría de marco (¿es esta la pregunta correcta?)

- **Marco erróneo 1 — "es un port + traducción".** No: dos decisiones estructurales cambian de
  signo (rieles y formalidad) y dos correcciones de auditoría cambian el firewall (tokens
  bilingües, escaneo de valores). Tratarlo como traducción produciría un sistema español con
  acento venezolano.
- **Marco erróneo 2 — "añadir cripto porque cripto".** El fork no emite token alguno (N1); usa
  rieles cripto solo en los BORDES (liquidación, reserva multisig, anclaje de evidencia), donde
  ganan su sueldo contra la banca rota y los tribunales inexistentes.
- **Marco erróneo 3 — "más dolor = adopción fácil"** (riesgo 4 del anexo): el dolor es
  permanente pero la confianza social está erosionada por el éxodo. El sustrato son cámaras y
  gremios que YA confían entre sí; la herramienta amplifica, no fabrica.
- **Marco erróneo 4 — falacia del mini-yo:** copiar el flujo institucional español (registro
  cooperativo, cada transacción a Hacienda) sería importar la legibilidad ante un Estado
  parasitario. La formalidad aquí es un **dial**, no un default.
- **La pregunta debajo de la pregunta:** ¿qué partes del diseño original eran contexto europeo
  disfrazado de principio? El anexo §1 la responde decisión por decisión; este bundle la
  convierte en plan de construcción.

## Contrato de corrección

| Vector | Contrato |
|---|---|
| Veracidad | Fuentes autoritativas: los dos documentos fundacionales + los bundles upstream + el código SUT. Los hechos VE están fechados (jul-2026) y NO se re-derivan al construir: se re-verifican y se fechan (M9). |
| Completitud | Nada del prompt §A–§I ni de los deltas §8 se omite. Lo que no tenga mecanismo va a la lista **Señalados** (N10) — jamás se omite en silencio ni se resuelve en prosa. |
| Registro | Castellano técnico en todo artefacto del fork. Claves de esquema sin tildes; valores y mensajes con tildes correctas (M3). |
| Cumplimiento | Intocables 1–10 (C2C) + invariantes B2B originales; licencias copyleft heredadas (GPLv3 código, CC BY-SA 4.0 contenido); N8: cero datos reales de personas o células. |
| Velocidad-vs-precisión | Exactitud absoluta en dinero e invariantes (enteros de unidad mínima, conservación, determinismo byte a byte). Los defaults de calibración de modos son ajustables por gobernanza — documentados como defaults, no dogma. |
| Auditabilidad | Cada hallazgo → requisito con ID (audit.md). Commits por área con su porqué (M11). Verificaciones regulatorias fechadas en el repo (M9). Salida pytest real en cada gate (M2). |

## El haz de la linterna

**Centro:** los dos SUT adaptados (C2C-VE, B2B-VE) + el harness de simulación, con suites
verdes y los intocables testeados en los TRES modos.

**Bordes explícitos (fuera del alcance de este fork de código):**
- Transporte/malla física (SMS/LoRa): el núcleo solo respeta el límite de payload por modo.
- Apps/UI y despliegue de células reales (las "Etapas" del anexo §7 son despliegue, no build).
- Custodia de claves y operación del multisig (N9): el motor emite helpers de verificación.
- Asesoría legal/fiscal/sanciones: se consume fechada (M9), no se produce aquí.
- Modificar el repo upstream (E4): los hallazgos upstream se señalan, no se escriben.
- La voluntad de cooperar: no se fabrica con código (riesgo 8 del anexo).

## Éxito observable

- Fases 1–2 completas con AC-1..AC-10 verdes (evals/acceptance.md).
- Un tercero clona el repo y reproduce las tres suites sin tocar nada — lo que el upstream
  publicado hoy no permite (corregido aquí en Fase 0).
- Cada problema abierto vive en Señalados con su porqué; cero resueltos-en-prosa.
