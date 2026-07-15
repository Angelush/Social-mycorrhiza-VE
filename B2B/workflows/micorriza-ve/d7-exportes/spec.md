# Spec — D7: `exportar_registros(miembro, periodo)`

> Nodo TB.7 (depende de D3/TB.4). Ancla: anexo §8.7, §5, §2.7; N7, N8.

## 1. El encuadre: compliance-READY, no compliance-DEPENDENT

El upstream registra cada transacción ante Hacienda (modelo Sardex-España), porque la
fiscalidad española es clara. **Derogado.**

En Venezuela: IGTF 3% a pagos en divisas/cripto fuera de la banca nacional; ofensiva SENIAT
sobre USDT en curso (2026); y el tratamiento del crédito mutuo —compensación de
obligaciones— es **ambiguo** (§5). El sistema **no puede depender de una claridad fiscal que
no existe**.

**Consecuencia de diseño:** el motor da registros limpios y exportables **por empresa**, para
que cada miembro cumpla donde y como decida. **El sistema no declara por nadie y no promete
neutralidad fiscal.**

*Porque:* si el motor declarara, tomaría por el miembro una decisión con consecuencias legales
personales bajo un marco ambiguo y un enforcement arbitrario (§5: «el riesgo es enforcement
arbitrario, no incumplimiento de una norma clara»). Es exactamente la clase de decisión que I3
reserva al humano.

## 2. Contrato

```python
def exportar_registros(state, events, member_id, desde_ts, hasta_ts,
                       formato="json", scope="miembro", solicitante=None) -> str
```

- **Pura.** Sin I/O: devuelve la cadena; escribir el archivo es del llamador (mismo porqué que
  `anclar`: el motor no tiene disco ni red).
- `formato` ∈ `("json", "csv")`.
- `scope` reutiliza D3 — **no se inventa un control de acceso nuevo** (P4).

| `scope` | Contenido |
|---|---|
| `miembro` | todo lo del miembro: obligaciones, liquidaciones, clearing que le afectó, saldo. Exige `solicitante == member_id` |
| `comite_credito` | ídem, para cualquier miembro |
| `publico` | **seudonimizado** (D3 §3): sin identidad, sin importes individuales |

## 3. Qué contiene el exporte de un miembro

Derivado **de los eventos**, no del estado. *Porque:* un exporte fiscal es un histórico de
período; el estado es solo el presente. Y los eventos ya están encadenados y son verificables
(`verify_chain`) — el exporte hereda esa integridad gratis.

Por cada evento del período en que el miembro es parte:
`fecha` (`ts`) · `tipo` · `contraparte` · `importe_centavos` · `moneda` (de la célula, D1) ·
`referencia` (id de obligación) · `hash_evento`.

Más una cabecera: `celula_id`, `miembro_id`, `moneda`, `periodo`, `saldo_inicial`,
`saldo_final`, `raiz_ancla` del período (D2) si existe.

*Porque `hash_evento` y `raiz_ancla`:* sin tribunales (§2.11), un exporte que el miembro
presenta a un tercero vale lo que valga su verificabilidad. Con el hash y la raíz, el tercero
puede comprobar que la línea existía y no se fabricó después. Es el único delta donde la
evidencia de D2 llega a manos de un humano externo.

## 4. La moneda en el exporte

`moneda` sale de `params["moneda"]` (D1). Los importes van en **centavos enteros** y la
cabecera dice la moneda **una vez**, no por línea.

*Porque:* la célula es mono-moneda (I-VE2). Una columna `moneda` por línea sugeriría que puede
variar — y la primera pregunta de quien lo vea así sería «¿a qué tasa convierto?». **El
formato del exporte también puede hacer representable el FX.** No se le da la forma.

Ninguna conversión, ningún total en otra moneda, ninguna tasa (N-d1.1).

## 5. Qué NO hace D7

- **No declara nada, ni genera formularios SENIAT, ni calcula IGTF.** Da los registros; el
  miembro y su asesor deciden (§1).
- No promete neutralidad fiscal. **Señalado** (§6.7: una reclasificación agresiva del SENIAT
  —¿cada compensación = pago en divisa gravable?— es un escenario a modelar con asesoría
  local, no a ignorar).
- No escribe archivos (§2).
- No inventa control de acceso: reutiliza el scope de D3 (§2).
- No convierte (§4).
