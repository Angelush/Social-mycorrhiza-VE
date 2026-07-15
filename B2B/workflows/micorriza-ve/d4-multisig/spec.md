# Spec — D4: multisig del fondo de garantía

> Nodo TB.8 (depende de TB.1 + **M9**). Ancla: anexo §8.4, §3.2, §6.1; N9, I-VE4.
>
> **BLOQUEANTE (M9):** verificación regulatoria/sanciones **fechada** en
> `docs/verificaciones/AAAA-MM-DD-*.md` ANTES de construir este delta. Sin ella, TB.8 no
> empieza. Ver §5.

## 1. Qué es este delta (y qué no)

**Es:** un **documento de gobernanza** + **helpers de verificación** puros.

**No es:** una wallet, un firmante, un custodio, ni un gestor de claves.

El fondo de garantía de la célula vive en un multisig 2-de-3 o 3-de-5 (firmantes = figuras
locales respetadas de la cámara/gremio + un fideicomisario de la diáspora). **Sustituye a la
cuenta de custodio autorizada de MiCA-landia: el escrow criptográfico reemplaza al banco de
confianza que no existe** (§3.2).

*Porque el motor jamás custodia claves (N9/I-VE4):* custodia en código = **trono que
capturar**. Todo el diseño evita tronos (§4.6: sin tenedor central, células federadas, ningún
hub nacional). Poner las claves del fondo en el motor construiría el único trono que el resto
de la arquitectura se esfuerza en no tener.

## 2. El documento de gobernanza (el entregable principal)

`B2B-VE/docs/gobernanza-multisig.md`, con:

1. **Umbral y firmantes.** 2-de-3 (célula pequeña) o 3-de-5 (célula madura). Composición:
   mayoría local (cámara/gremio) + al menos un fideicomisario de la diáspora. *Porque:* un
   multisig cuyos firmantes viven todos en la misma ciudad es un multisig con un solo punto de
   presión física (§6.2: matraqueo).
2. **Procedimiento de rotación de direcciones.** Cadencia, disparadores (un firmante emigra,
   es presionado, o pierde la clave), y quórum para rotar.
3. **Nunca concentrar la reserva en una sola dirección ni en una sola cadena** (§3.2).
   *Porque:* Tether congela direcciones a petición de OFAC. Una dirección congelada con toda la
   reserva dentro es el fondo entero perdido de un plumazo.
4. **Autocustodia.** Ni exchange, ni custodio tercero.
5. **Qué NO cubre el multisig:** el riesgo de contraparte Tether no es eliminable (§6.1). El
   fondo puede evaporarse sin que ninguna firma falle.

## 3. Los helpers (lo poco que toca el código)

```python
def verificar_formato_direccion(direccion: str, cadena: str) -> bool
def verificar_umbral(politica: dict) -> None   # ValueError si es incoherente
def describir_politica(politica: dict) -> str  # markdown legible para el comité
```

```python
politica = {
    "umbral": 2, "total": 3,
    "firmantes": [{"alias": "str", "direccion": "str", "cadena": "str", "rol": "local"|"diaspora"}],
    "cadena": "TRC20" | "ERC20",
}
```

**Todos puros.** Sin red, sin claves privadas, sin firmar, sin consultar saldo on-chain.

`verificar_umbral` rechaza: `umbral > total`; `umbral < 2` (un multisig de umbral 1 es una
wallet con pasos extra); `total > 5`; `len(firmantes) != total`; direcciones duplicadas; alias
duplicados; **cero firmantes con rol `diaspora`** (§2.1); **todos con rol `diaspora`** (la
célula perdería control de su propio fondo).

*Porque `verificar_formato_direccion` solo verifica FORMATO:* comprobar que una dirección
existe o tiene saldo exige red — y el motor no tiene red (mismo porqué que `anclar`/D2). Un
checksum mal escrito es un error caro y barato de cazar; lo demás es del comité.

## 4. Por qué los helpers son tan poca cosa

Es deliberado. La tentación es que el motor «gestione» el fondo: consultar saldo, proponer
firmas, avisar de umbrales. Cada una de esas features le da al motor **red y conocimiento del
fondo**, y con eso el fondo se vuelve capturable a través del motor.

El multisig lo operan **humanos**. El código solo evita que se escriba mal un número en un
documento.

## 5. M9 — la verificación fechada (bloqueante)

Antes de TB.8, en `docs/verificaciones/AAAA-MM-DD-sanciones-multisig.md`:

- Estado de sanciones a la fecha: EOs vigentes, GLs aplicables (comunicaciones GL 25;
  ONG/humanitario GL 29; remesas), designaciones SDN activas.
- Screening SDN de las contrapartes previstas.
- Estado del marco cripto (Sunacrip) y fiscal (IGTF/SENIAT) a la fecha.
- **Sin datos personales** (N8).

*Porque:* **todo el §5 del anexo está EN FLUJO** tras la transición de enero 2026. El diseño
exige **re-verificar, no recordar**. Las licencias son revocables y la responsabilidad es
estricta: un dato de hace seis meses no es información, es una suposición con fecha.

**El fideicomisario de la diáspora es probablemente US-person** → responsabilidad estricta,
nada que toque GoV/PDVSA/SDNs. Esto no lo resuelve el código; lo documenta el §2.

## 6. Qué NO hace D4

- **No custodia claves, ni direcciones operativas, ni firma nada** (N9).
- No consulta la cadena, no tiene red.
- No mueve el fondo. El fondo entra al ledger como un miembro con líneas (D6/ST-d68.1); mover
  valor pasa por la puerta (M8).
- No elimina el riesgo Tether (§6.1). **Señalado.**
- No decide quiénes son los firmantes. Eso es gobernanza de la célula (I3: el humano dispone).
