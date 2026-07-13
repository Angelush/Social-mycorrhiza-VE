# Constraints — Área e · Doble moneda (con cláusulas-porque)

- **C-e1. `moneda` obligatoria por campaña; una campaña es mono-moneda.**
  *Porque:* una campaña mixta obligaría a comparar USD con VES, y esa comparación **es** una tasa de
  cambio incrustada — la decisión política que el motor se niega a tomar.
- **C-e2. Mezcla de monedas → `ErrorDeBrechaAseguramiento`, sin excepción.**
  *Porque:* rechazar-no-reparar; el motor no "convierte" el compromiso disidente, lo rechaza para
  que el llamador (humano) decida.
- **C-e3. El tipo de cambio es irrepresentable en el motor (tokens `tasa_de_cambio`, `fx`,
  `paralelo`, `bcv`, … rechazados).**
  *Porque (cláusula central):* en Venezuela la tasa (BCV vs. paralelo) es volátil y políticamente
  disputada; incrustar una tasa en código es incrustar una decisión política y crear un punto
  capturable. La conversión es siempre una decisión humana fuera del protocolo.
- **C-e4. Importes en enteros de unidad mínima; float prohibido.**
  *Porque:* la conservación exacta a 15+ dígitos (hiperinflación) solo es posible con enteros; un
  float perdería precisión y violaría la conservación del bono.
- **C-e5. `expira_en` corto para VES es convención del llamador, no regla del motor.**
  *Porque:* el motor no modela inflación (sería otra tasa disputada); recomendar una ventana corta es
  higiene documentada, no un mecanismo — señalado.
- **C-e6. La moneda solo es representable en la sala `precio_de_mercado` (Capa 1).**
  *Porque:* denominación en `don_comunal` o `igualdad` violaría la separación sagrada de salas
  (kula/gimwali wall); la taxonomía de mercado bilingüe la mantiene fuera de esas salas.

## Alcance
Esta área toca Capa 4 (motor) y Capa 1 (taxonomía de mercado). No toca legibilidad, emparejador ni
gobernanza salvo por la maquinaria compartida del firewall.
