# Brief de estilo visual

Rediseñar la interfaz del banco de pruebas para que sea visualmente continua con la presentación de la ponencia. Ahora mismo la app es un panel de instrumentos oscuro y la presentación es clara, enérgica y de cartel. Cuando el ponente cambia de las slides al navegador en pleno escenario, el salto se nota. El objetivo es que no se note.

## La sensación que hay que reproducir

Cartel serigrafiado, no dashboard. Fondo claro, tipografía enorme, colores planos, cero sombras y cero degradados. Todo respira. La energía viene del tamaño de la letra y de elementos ligeramente rotados, no de la densidad ni de la decoración.

Es una estética deliberadamente informal y hecha a mano, dentro de un marco profesional. Alegre pero no infantil.

## Paleta

Dos colores hacen todo el trabajo. Confirma los valores exactos con un cuentagotas sobre el PDF, estos son aproximaciones cercanas.

| Rol | Hex aprox. | Uso |
|---|---|---|
| Fondo | `#F3F4F2` | Fondo de toda la aplicación. Blanco roto, ligeramente frío. Nunca blanco puro. |
| Azul primario | `#0E63B3` | Titulares, texto principal, bordes de caja, iconos. Es el color dominante, alrededor del 70% del peso visual. |
| Azul marino | `#10256B` | Variante para algún titular puntual. Úsalo con moderación, no como segundo color. |
| Naranja | `#EF8C22` | Único acento. Énfasis, etiquetas rotadas, lo que el ojo debe encontrar primero. |
| Blanco | `#FFFFFF` | Relleno de cajas y tarjetas sobre el fondo. |

Reglas de color:

- No hay grises de texto. El texto secundario es el mismo azul en tamaño menor, no un gris apagado.
- El naranja nunca compite con el azul. Aparece en fragmentos cortos: una etiqueta, una frase, un dato.
- Nada de fondos oscuros. Si hoy hay superficies oscuras en la app, se invierten.

### Colores semánticos que faltan

La paleta original solo tiene azul y naranja, pero la app necesita distinguir tres estados en las métricas: correcto, alarma y neutro. Propuesta que respeta el espíritu:

- **Alarma / fallo**: el naranja `#EF8C22`. Ya es el color de énfasis, y funciona.
- **Correcto / verificado**: un verde de saturación equivalente, `#2E9E6B`. Es un añadido, pero hace falta para que la demo de consistencia se lea de un vistazo.
- **Neutro**: el azul primario.

No introduzcas un rojo. El naranja ya carga el peso de "atención" y añadir rojo rompería la paleta.

## Tipografía

Dos familias, con roles muy separados.

**Titulares: display pesado, itálico, de trazo grueso y curvas redondeadas.** Es el rasgo más reconocible de la presentación. Letras anchas, muy negras, inclinadas, con aspecto de rótulo pintado a mano. Se usa a tamaños grandes y a veces rotado unos grados.

Identifica la fuente exacta en Canva si puedes. Si no está disponible como fuente web, la alternativa gratuita más cercana en Google Fonts es **Fugaz One** (itálica, pesada, curvas redondeadas). Otras aproximaciones: Lilita One, Bowlby One. Ninguna es idéntica, así que prueba y elige.

**Cuerpo: sans geométrica, casi siempre en semibold o bold.** Nunca en peso ligero. Letras redondeadas, espaciado ajustado. Alternativa web: **Montserrat** en 600 y 700, o Poppins.

**Monoespaciada**: la presentación no usa ninguna, pero la app sí la necesita para mostrar la salida del modelo. Elige una con personalidad y bastante peso, no una monoespaciada de terminal delgada. JetBrains Mono en peso medio funciona.

Escala de tamaños: mucho contraste. Los titulares son enormes, el cuerpo es normal, y no hay muchos pasos intermedios. Evita las escalas tipográficas suaves de dashboard.

## Formas y motivos

**Esquinas rectas.** La presentación no usa ni un radio de borde. Todas las cajas son rectángulos limpios. Esto es importante y es lo contrario de lo que hay hoy en la app.

**Cajas de contorno, no rellenas.** El patrón dominante es un rectángulo con borde de 2 o 3px en azul, fondo blanco o transparente, y texto del mismo azul dentro. Sin sombra.

**Etiquetas rotadas.** El motivo con más carácter: cajas de contorno naranja con texto naranja, giradas entre 3 y 8 grados, en ángulos distintos entre sí, ligeramente solapadas. Dan sensación de recortes pegados sobre una superficie. Úsalas para lo que el ponente quiere que la sala note.

**Placa sólida.** Un rectángulo relleno de azul con texto blanco dentro, también rotado. Aparece en la portada sobre el titular. Sirve para un elemento y solo uno por pantalla.

**Cero sombras, cero degradados, cero brillos.** Todo es plano.

## Composición

- Márgenes generosos. La presentación deja mucho aire y no llena el espacio disponible.
- Los titulares a menudo van centrados y ocupan casi todo el ancho.
- El contenido puede ir centrado, a diferencia de la app actual. En bloques largos de texto sigue prefiriéndose alineación a la izquierda.
- Poca información por pantalla. Si algo no cabe cómodamente, va a otra vista.

## Cómo se traduce a la aplicación

| Elemento actual | Cómo debe quedar |
|---|---|
| Barra superior oscura | Fondo claro, borde inferior azul fino. El nombre de la app en la fuente display. |
| Pestañas de demo | Texto en display, la activa en azul sólido y la inactiva en contorno. Sin subrayado de color. |
| Botón principal de ejecutar | Rectángulo azul sólido, esquinas rectas, texto blanco en bold. Al pasar el ratón se invierte a contorno. |
| Botones secundarios | Solo contorno azul, sin relleno. |
| Panel de salida del modelo | Caja blanca con borde grueso. Naranja cuando la respuesta es la del prompt sin salvaguardas, verde cuando es la del prompt riguroso. Texto monoespaciado en azul oscuro sobre blanco. |
| Indicadores numéricos grandes | El número en la fuente display, muy grande. La etiqueta debajo en sans bold, pequeña. En alarma pasa a naranja. |
| Chips de datos detectados | Cajas de contorno rectas. Verde cuando el dato aparece en todas las ejecuciones, naranja cuando solo en algunas. Considera rotarlos ligeramente, cada uno un ángulo distinto, para recuperar el motivo de las etiquetas de la presentación. |
| Tarjetas de cada ejecución | Rectángulos blancos con borde azul fino. Sin sombra ni radio. |
| Resaltado de palabras volátiles | Fondo naranja translúcido, no rojo. |
| Interruptor de modo repetición | Rectangular, no de píldora. |

## Qué evitar

- Radios de borde. Ninguno, en ningún sitio.
- Sombras suaves bajo tarjetas.
- Grises de texto secundario. Usa el azul en tamaño menor.
- Fondos oscuros o modo oscuro.
- Pesos tipográficos ligeros.
- Más de un elemento rotado por zona de la pantalla, o la composición se vuelve ruidosa.

## Prueba de aceptación

Pon una captura de la app junto a una slide de la presentación. Alguien que no haya visto ninguna de las dos debería asumir que salieron del mismo sitio. Si la app sigue pareciendo una herramienta de monitorización y la slide un cartel, falta trabajo.

Y una prueba práctica: todo debe seguir siendo legible proyectado desde el fondo de una sala. El fondo claro ayuda con proyectores flojos, pero vigila el contraste del naranja sobre `#F3F4F2`, que es el par más débil de la paleta. Si no pasa el contraste mínimo en texto pequeño, usa naranja solo en bordes y en texto grande, y azul para el texto pequeño.
