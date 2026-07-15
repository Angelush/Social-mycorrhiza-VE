# Failure model — D10: branding y cierre

## Modos de fallo (F-d10#)

- **F-d10.1 — El branding tratado como marketing.** Se cambia la portada del README y los
  mensajes de error siguen diciendo «saldo de tu billetera». El vocabulario del producto es lo
  que el usuario lee **cada día**, no la portada que lee una vez. *Mitigación:* C-d10.1 aplica a
  todo lo que un humano lee. *Detección:* AC-d10.1 (grep sobre toda salida legible).
- **F-d10.2 — El celo que rompe el esquema.** El ejecutor aplica N-d10.1 literalmente y
  renombra `params["moneda"]`. Rompe D1, los goldens y AC-10 — que existe precisamente para
  afirmar que `moneda` está **admitida** en B2B-VE. *Mitigación:* N-d10.2 — la palabra no es el
  problema; lo es qué nombra. *Detección:* AC-10 (D9).
- **F-d10.3 — El Señalado resuelto en prosa.** «La correlación entre salidas se mitiga con
  buenas prácticas del comité.» Ahora está en la columna de resueltos y nadie vuelve a mirarlo.
  Es el fallo que N10 nombra, y es más dañino que dejarlo abierto. *Mitigación:* C-d10.2/E-d10.1.
  *Detección:* AC-9 (gate humano).
- **F-d10.4 — La tabla copiada.** El README re-teclea la tabla de unidad de cuenta de D1 «para
  que se lea sin saltar». Diverge en el primer cambio, y **la copia es la que se lee**.
  *Mitigación:* C-d10.3 — la lección literal de TA.8. *Detección:* AC-d10.3.
- **F-d10.5 — El README optimista.** «Tus saldos son privados», «el multisig protege el fondo»,
  «compliance-ready». Cada frase es media verdad: el scope no autentica (F-d3.6), el multisig
  reparte la coerción (ST-d4.1), y compliance-READY significa explícitamente **que el sistema no
  declara por ti**. Un comité que se las crea toma decisiones sobre garantías inexistentes.
  *Mitigación:* C-d10.4/N-d10.4. *Detección:* AC-9.
- **F-d10.6 — La conservación probada a escala de juguete.** El property test usa importes de 6
  dígitos porque hypothesis los genera por defecto. **La conservación a escala de
  hiperinflación nunca se prueba** y el AC dice que sí. *Mitigación:* C-d10.5 — la estrategia
  fuerza 15+ dígitos explícitamente. *Detección:* AC-d10.4 revisa la estrategia, no solo que el
  test pase.
- **F-d10.7 — El nodo que se convierte en cajón de sastre.** TB.9 es el último: todo lo que
  quedó a medias «se cierra aquí». Se resuelven Señalados sin spec ni gate (M1) — que es como
  se cuela un invariante mal leído, justo en el nodo que menos revisión recibe porque «es
  documental». *Mitigación:* E-d10.1.

## Hallazgos de estrés (ST-d10#)

- **ST-d10.1 — El branding no sobrevive al contacto con el usuario.** Los miembros llamarán
  «los dólares de la cámara» a los créditos, digan los docs lo que digan. El vocabulario del
  repo no controla el vocabulario de la calle. Lo que sí controla es qué pide la gente: si el
  producto nunca dice «moneda», la petición de transferibilidad llega más tarde y con menos
  legitimidad. **Mitigación parcial y honesta**, no una solución. **Señalado.**
- **ST-d10.2 — Señalados: lista larga = lista no leída.** 22 entradas es mucho. Ordenarlas por
  quién las paga (el comerciante, el comité, la red) las hace accionables; ordenarlas por
  delta las hace un índice. *Preferencia:* por consecuencia, no por procedencia.
- **ST-d10.3 — AC-9 es el único AC sin máquina.** Un checklist de honestidad lo verifica un
  humano leyendo. *Mitigación:* que se diga (como en TA.8), en vez de fingir cobertura
  automática. El gate M1 es real precisamente donde la máquina no llega.
- **ST-d10.4 — El property test de conservación puede pasar por vacuidad.** Si la estrategia
  genera grafos sin ciclos, `clear()` no hace nada y la conservación se cumple trivialmente.
  *Mitigación:* la estrategia debe **garantizar** al menos un ciclo en una fracción de los
  casos, y el test lo afirma (`gross_after < gross_before` en esos). Es la lección ST5
  upstream (auto-confirmación) y el gate de vacuidad del harness Sim.

## Abierto — no fake-resolver (N10)

- El branding es mitigación parcial: no controla cómo llama la gente a las cosas (ST-d10.1).
- AC-9 no es automatizable; es un gate humano (ST-d10.3).
- El seam bilingüe de E2 queda abierto por decisión, no por olvido: `context.md` §2.
