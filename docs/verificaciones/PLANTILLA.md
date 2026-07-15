# Verificación fechada — <área: sanciones | fiscal | cripto>

> **M9 / TP.1.** Copiar a `docs/verificaciones/AAAA-MM-DD-<area>.md` y rellenar.
> Bloquea **D4 (TB.8)** y —alcance por decidir, ver §5— **D8 (TB.6)**.
>
> **Esta plantilla la creó Claude; el CONTENIDO no.** Los hechos regulatorios cambian y deben
> venir de fuente primaria consultada en la fecha del nombre del archivo, no de la memoria de
> un modelo. Un dato regulatorio inventado con formato de verificación es peor que un hueco:
> el hueco se ve.
>
> **N8 — sin datos personales.** Ni nombres de firmantes, ni cédulas, ni RIF, ni direcciones.
> Cargos y roles, no personas.

## 1. Alcance

Qué se verifica exactamente, y qué NO. (Un alcance implícito es un alcance que nadie revisa.)

## 2. Fecha y vigencia

- **Verificado el:** AAAA-MM-DD
- **Fuentes consultadas:** <enlace/documento primario + fecha de la fuente>
- **Caduca / re-verificar antes de:** AAAA-MM-DD
  *Porque:* una verificación sin caducidad se convierte en folclore — se cita durante años sin
  que nadie recuerde cuándo fue cierta.

## 3. Hallazgos

| # | Hallazgo | Fuente | Impacto en el motor |
|---|---|---|---|

## 4. Qué cambia en el código (si algo)

Si la respuesta es «nada», **decirlo explícitamente y por qué** — es un resultado, no un vacío.

## 5. Alcance de «D8» en TP.1 — decisión pendiente (2026-07-15)

**Tensión spec↔spec detectada en TB.3 y confirmada en TB.4** leyendo `workflows/micorriza-ve/
tasks.md` (filas 48/50/66):

- fila 48: **TB.6 = D6+D8**, deps `TB.3` — **M9 no aparece**.
- fila 50: **TB.8 = D4**, deps `TB.1, M9` — M9 **sí** aparece.
- fila 66: **TP.1** exige re-verificación fechada «ANTES de **D4/D8**».

O TB.6 está bloqueado por M9 y el grafo no lo dice, o «D8» en TP.1 es más estrecho de lo que
parece. **Es spec contra spec: la regla «manda el código» NO aplica** — no hay código que
mande. Decisión humana, a tomar con este documento delante.

*Las dos lecturas, sin recomendación:* pausar el puente solo **reduce** exposición, lo que
argumenta que no necesita verificación previa; pero `puente.pausar()` **es** el mecanismo de
respuesta a sanciones, que es justo lo que M9 vigila.

**Resuelto:** ☐ sí / ☐ no — **Decisión:** ______________ **Fecha:** __________
