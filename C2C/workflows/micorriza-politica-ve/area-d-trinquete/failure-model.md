# Failure model — Área d · Trinquete asimétrico

## Escalada abusiva (señalado principal)
Un miembro malicioso escala a `severa` repetidamente para degradar la coordinación (retención corta,
sin portabilidad, payload mínimo). *Contrapeso:* la desescalada por consentimiento de Capa 6 permite
volver; el código fuerza el procedimiento, no la buena fe. *Fricción opcional:* un cooldown entre
escaladas del mismo token es una decisión de gobernanza abierta — **no** se incrusta aquí. **Señalado
en `lo-intocable.md`.**

## Desescalada sin autorización
Un intento de volver a `paz` sin `decision_capa6.verdicto == 'adoptada'`, o con una decisión de otra
propuesta/otro círculo. *Comportamiento:* rechazo. Es el fallo que AC-M2 fija.

## Re-expansión de exposición al desescalar
Al volver a un modo más laxo, retención/alcance/payload se re-expanden: datos que estaban protegidos
por la ventana estricta vuelven a ser retenibles. *Mitigación:* esto es precisamente por qué la
desescalada exige consentimiento colectivo; la decisión de re-exponer es de la célula, con objeción
primordial disponible.

## Depuración omitida tras escalar
Ver `area-c-modo/failure-model.md`: la escalada obliga a `depurar()` por convención; si el llamador
no depura, los items viejos persisten en su almacén. **Señalado.**

## Ambigüedad de "salto directo a severa"
`paz`→`severa` directo es una escalada válida (más estricto). El test lo cubre para que no se
interprete como transición inválida por saltarse `acotada`.
