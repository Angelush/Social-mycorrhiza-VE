# Verificación fechada — sanciones

> **M9 / TP.1.** Desbloquea **D4 (TB.8)** y **D8 (TB.6b)**.
>
> **Legwork de Claude (búsqueda web, fuentes primarias enlazadas); la FIRMA es humana.** Esto es
> un *snapshot con fuentes*, **no asesoría legal**. Para las Etapas de despliegue hace falta
> asesoría colegiada (intent.md: «asesoría legal/fiscal/sanciones se consume fechada, no se
> produce aquí»).
>
> **N8 aplicado:** los designados se describen por **cargo/rol**, nunca por nombre, aunque las
> designaciones sean públicas. La regla no distingue, y no se le hacen excepciones cómodas.

## 1. Alcance

**Qué se verifica:** el estado del programa Venezuela-related de OFAC al 2026-07-15, a los solos
efectos de decidir si el motor B2B-VE puede (a) construir el mecanismo de **pausa del puente**
(D8) y (b) documentar el **multisig de reserva** (D4).

**Qué NO se verifica, explícitamente:**
- Si una célula concreta, sus miembros o sus contrapartes están o no en la lista SDN. **Eso no lo
  hace ni lo hará el motor** (§3, hallazgo 5).
- El derecho venezolano de cambios, bancario o penal.
- Sanciones no-OFAC (UE, Reino Unido, Canadá, Suiza).
- La legalidad de operar un puente USDT bajo derecho venezolano. Es fiscal/cambiario → ver
  `2026-07-15-cripto.md`, y sigue siendo terreno de asesor colegiado.

## 2. Fecha y vigencia

- **Verificado el:** 2026-07-15
- **Fuentes consultadas** (todas públicas, consultadas en esta fecha):
  - OFAC — [Venezuela-Related Sanctions](https://ofac.treasury.gov/sanctions-programs-and-country-information/venezuela-related-sanctions) (página de programa)
  - OFAC — [Recent Actions](https://ofac.treasury.gov/recent-actions) · [General Licenses](https://ofac.treasury.gov/recent-actions/general-licenses)
  - OFAC — [Emisión de GL, 2026-06-10](https://ofac.treasury.gov/recent-actions/20260610) · [2026-04-14: retirada de designación + GL 56/57](https://ofac.treasury.gov/recent-actions/20260414_33) · [2026-03-27](https://ofac.treasury.gov/recent-actions/20260327_33) · [2026-02-13](https://ofac.treasury.gov/recent-actions/20260213)
  - Treasury — [Targets Oil Traders Engaged in Sanctions Evasion](https://home.treasury.gov/news/press-releases/sb0348) (acción de jul-2026)
  - CRS — [Venezuela: Overview of U.S. Sanctions Policy, IF10715](https://www.congress.gov/crs-product/IF10715) *(403 al fetch automático; citado por referencia, **no leído** — ver hueco H2)*
  - Morgan Lewis — [Compliance Landscape Following Maduro's Removal](https://www.morganlewis.com/pubs/2026/01/compliance-landscape-in-venezuela-following-nicolas-maduros-removal-from-power) (análisis, ene-2026)
  - Baker McKenzie — [OFAC Updates Venezuela General Licenses](https://sanctionsnews.bakermckenzie.com/ofac-updates-venezuela-general-licenses-and-issues-new-venezuela-faqs/) · Faegre Drinker — [Unpacking the Recent Changes](https://www.faegredrinker.com/en/insights/publications/2026/3/unpacking-the-recent-changes-to-the-venezuela-sanctions-program) (análisis, mar-2026)
- **Caduca / re-verificar antes de:** **2026-10-15** (3 meses).
  *Porque:* el programa se movió **en los dos sentidos** en los últimos 6 meses (alivios en feb–jun;
  designaciones nuevas en jul). Un plazo más largo convertiría esto en folclore. **Y re-verificar
  ANTES si:** hay *snapback* anunciado, se revocan GL, o el puente cambia de riel.

## 3. Hallazgos

| # | Hallazgo | Fuente | Impacto en el motor |
|---|---|---|---|
| 1 | **La arquitectura sancionadora sigue EN PIE.** Tras la captura del ex-presidente (2026-01-03) hubo alivio **selectivo**, pero las EO **13692** (2015), **13808** (2017) y **13884** (2019, bloqueo a PdVSA y al GoV) **siguen vigentes**. «All Venezuela sanctions remain in place.» | Morgan Lewis (ene-2026); OFAC programa | **Ninguno directo.** Confirma que D8 no es paranoia: el marco existe y puede volver a apretarse. |
| 2 | **El alivio va por licencia general, no por derogación.** GL 49/50 (2026-02-13), GL 51 (03-06), GL 52 (03-18), GL 51A/54/55 (03-27), GL 56/57 (04-14), GL 46C/47A/48B (06-10). Una GL **se revoca con un anuncio**. | OFAC Recent Actions | **Ninguno en código.** Es exactamente el escenario de I-VE7: lo que hoy es legal deja de serlo de un plumazo. |
| 3 | **En julio de 2026 OFAC volvió a designar**: familiares del entorno del ex-presidente, un empresario afín, **seis navieras y seis buques** del sector petrolero. Es **reasserción dirigida, no un *snapback* general**. | Treasury sb0348 | **Ninguno.** Matiza `context.md`: el riesgo hoy es de designación **puntual**, no de reversión en bloque. |
| 4 | **La lista se mueve en los DOS sentidos**: hubo **retiradas** de designación en abr-2026 (incl. una figura del más alto nivel del ejecutivo). | OFAC 20260414_33, 20260401 | **Ninguno.** Refuerza la caducidad de §2: una verificación sin fecha aquí es mentira con formato. |
| 5 | **El motor NO cribará contra la lista SDN, y eso es una decisión, no un olvido.** Ninguna de las capas construidas consulta ni consultará la SDN. | Diseño (N8/N9/I3) | **Señalado → README de TB.9.** El cribado es del **comité**, con datos que el motor **no tiene y no debe tener** (N8). Un motor que dijera «este miembro está limpio» estaría emitiendo un juicio de cumplimiento que no puede sostener — sería la clase de fake-resolve que N10 prohíbe. |
| **H1** | **HUECO DECLARADO — no se pudo sourcear el número de designados Venezuela-related vigentes.** `context.md` dice «~150–200 SDN activos». **No hay fuente primaria que lo confirme ni lo desmienta**: OFAC no publica un conteo por programa; habría que contar la SDN completa. | — | **Ninguno**: ningún invariante depende del número. Se deja el hueco **porque se ve**. |
| **H2** | **HUECO DECLARADO — el CRS IF10715 devolvió 403** y no se leyó. Es la mejor síntesis oficial disponible; queda para la firma humana. | congress.gov | Ninguno. |

## 4. Qué cambia en el código

**En el motor: NADA. Y decirlo es el resultado, no un vacío.**

Ni un invariante, ni una firma, ni un test. Concretamente:

1. **D8 (TB.6b) queda DESBLOQUEADO y su diseño CONFIRMADO.** El hallazgo 2 es literalmente la
   premisa de I-VE7: el alivio va por GL revocable, así que «USDT puede dejar de ser viable de un
   plumazo» es un hecho verificado, no una intuición de diseño. La pausa del puente **reversible**
   (§4 de la spec de D6+D8) encaja con un programa que se mueve en los dos sentidos (hallazgo 4):
   un dial, no un interruptor de un solo uso.
2. **`puente_pausado` ≠ `paused` sale REFORZADO.** El hallazgo 3 (designación puntual, no reversión
   en bloque) es exactamente el caso donde hay que parar el puente **sin** matar el crédito
   interno. Si el escenario real fuera un apagón total, la distinción daría igual; como es
   puntual, la distinción **es** el delta.
3. **D4 (TB.8) queda DESBLOQUEADO en su parte regulatoria.** Lo que falta ahí ya no es M9: es
   **gobernanza** (umbral, roles, rotación), que es del humano (I3). El hallazgo 1 sí manda un
   requisito al **documento**: el multisig no puede tener como firmante a nadie designado, y esa
   comprobación es del comité, no del motor (hallazgo 5).
4. **`context.md` NO se corrige desde aquí.** Sus datos VOLÁTILes de sanciones («~150–200 SDN;
   *snapback* posible») quedan **matizados** por los hallazgos 3 y H1, no refutados. La corrección
   de `context.md` la hace TB.9 citando **este** archivo, que es lo que M9 quiere: el dato vive en
   una verificación fechada, y el bundle apunta a ella.

## 5. Firma

- **Leído y asumido por:** ______________________  **Fecha:** __________
- ☐ Me basta para construir D8 y documentar D4.
- ☐ No me basta: quiero asesoría colegiada antes de ______________________.
