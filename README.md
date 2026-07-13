# Micorriza VE 🍄

**Fork Venezuela de [Social-mycorrhiza](https://github.com/Angelush/Social-mycorrhiza):
infraestructura de coordinación y distribución, recalibrada para un entorno donde la banca,
los tribunales y el Estado no cumplen su función.**

La corrección en una frase: los argumentos anti-TOKEN del diseño original eran universales y
se mantienen — reforzados por el precedente Petro/Sunacrip —; los argumentos anti-RIELES-cripto
eran contingentes a la UE (MiCA, banca funcional) y en Venezuela se **invierten**: allí los
rieles cripto son la infraestructura de pagos que funciona y la banca es la capa rota.
**Cripto como fontanería, nunca como promesa.** Sigue sin emitirse token alguno.

La disciplina heredada no se negocia:

> La IA hace el trabajo de **solver / emparejamiento**.
> La capa humana-cooperativa retiene **propiedad, confianza y gobernanza**.
> El agente *propone*; un humano *dispone*. La puerta de un solo sentido sobre el valor
> jamás se abre dentro del loop.

---

## Las tres partes

| Directorio | Qué es | Estado |
|---|---|---|
| [`B2B/`](B2B/) | **Crédito mutuo con clearing multilateral** entre empresas — obligaciones netas SIN banco, sin token, sin cadena en la ruta de liquidación. Por adaptar: USD como unidad de cuenta, pista VES con expiración, ledger hash-encadenado, visibilidad restringida (anexo §8) | ✅ heredado, 128/128 tests · 🔜 adaptación VE (Fase 2) |
| [`C2C/`](C2C/) | **Protocolo social** para cooperar a través de las diferencias, construido para que lo que *no puede volverse un score de vigilancia* venga primero. Por adaptar: castellano total, doble moneda USD/VES sin conversión, tres modos de calibración con trinquete | ✅ heredado, 293/293 tests · 🔜 adaptación VE (Fase 1) |
| [`Sim/`](Sim/) | **Harness de simulación** que maneja el código REAL B2B y C2C con poblaciones de actores buenos/neutros/malos — driver y oráculo, jamás una segunda copia del mecanismo | ✅ heredado, 121/121 tests · 🔜 adaptación VE (Fase 3) |

A diferencia del repo original publicado, **este fork contiene los tres árboles completos**
(el upstream publicó `B2B/` y `Sim/` como punteros de submódulo rotos; aquí son archivos
regulares y las tres suites corren de un clon limpio).

## Los documentos fundacionales y la hoja de ruta

| Documento | Qué contiene |
|---|---|
| [`C2C/prompt-fork-venezuela.md`](C2C/prompt-fork-venezuela.md) | El prompt ejecutable del workstream C2C-VE: los 10 intocables, áreas §A–§I (taxonomías bilingües por tokens, escaneo de valores de identidad, modos `paz`/`catastrofe_acotada`/`catastrofe_severa`, doble moneda, convergencia en desastre) |
| [`B2B/micorriza-b2b-venezuela-adaptacion.md`](B2B/micorriza-b2b-venezuela-adaptacion.md) | La auditoría decisión por decisión del sesgo UE (qué se mantiene, qué se invierte), el contexto operativo venezolano verificado (jul-2026), la arquitectura corregida y los 10 deltas accionables |
| [`workflows/micorriza-ve/`](workflows/micorriza-ve/) | **La hoja de ruta**: paquete de especificación completo (intención, contexto, constraints con porqués, grafo de tareas por fases, criterios de aceptación, modelo de fallos, auditoría del lazo) |

**Estado del build:** Fase 0 (fundación) ✅ — Fases 1–3 (C2C-VE → B2B-VE → Sim-VE) por
ejecutar según [`workflows/micorriza-ve/tasks.md`](workflows/micorriza-ve/tasks.md).

## Principios de diseño (los heredados + los del contexto VE)

- **Propone/dispone.** La IA propone; código determinista con puerta humana decide. La puerta
  de un solo sentido sobre valor real jamás se automatiza.
- **Cero tokens, cero especulación.** El crédito es un registro de compensación, no un activo.
  El precedente Petro no era una anomalía: era la lección universal con acento local.
- **Anti-vigilancia por construcción.** Ningún escalar global de persona; el tipo de cambio es
  **irrepresentable** en los motores (no existe "el" tipo de cambio en Venezuela — cualquier
  tasa en código es una decisión política incrustada).
- **El saldo no es público.** Un libro público de saldos es un mapa de extorsión; la
  visibilidad queda restringida al comité de crédito y todo export público va seudonimizado.
- **La formalidad es un dial, no un default.** Las células son cámaras y gremios que ya
  confían entre sí; sin registro estatal como requisito, sin integración con canales estatales
  de identidad o denuncia.
- **Probar contra la realidad.** Las simulaciones manejan los sistemas reales bajo prueba —
  jamás mocks; una invariante violada detiene la corrida, nunca se promedia.
- **Señalado, no falsamente resuelto.** Lo que el código no puede garantizar se declara
  abiertamente con su porqué.

## Inicio rápido

Cada subproyecto es un paquete Python autocontenido; un solo virtualenv en la raíz.

```bash
# preparación (una vez)
python3 -m venv .venv
.venv/bin/pip install pytest hypothesis networkx

# las tres suites
(cd B2B && ../.venv/bin/python -m pytest tests -q)   # 128 tests
(cd C2C && ../.venv/bin/python -m pytest tests -q)   # 293 tests
(cd Sim && ../.venv/bin/python -m pytest tests -q)   # 121 tests
```

## Relación con el upstream

Fork de [`Angelush/Social-mycorrhiza`](https://github.com/Angelush/Social-mycorrhiza) con
historia completa; el remoto `upstream` apunta al original y la política de sincronización
vive en `workflows/micorriza-ve/tasks.md` (TP.2). El derecho a bifurcar es un invariante del
protocolo (intocable 9): este repo es su ejercicio.

## Licencias

Doble licencia heredada — ver [`LICENSE.md`](LICENSE.md):

- **Código** → [GNU GPL v3.0](LICENSE-GPLv3)
- **Contenido y docs** → [CC BY-SA 4.0](LICENSE-CC-BY-SA-4.0)

Ambas copyleft con términos de compartir-igual.

## Contribuir

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md) (castellanización pendiente — tarea TP.4). Al
contribuir aceptas que tu código se licencia bajo GPLv3 y tu documentación bajo CC BY-SA 4.0.
Idioma de trabajo del fork: **castellano**.
