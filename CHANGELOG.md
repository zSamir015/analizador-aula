# Cambios

## 2026-11-16 (correcciones de la revisión)

- Alcance limitado a la parte léxica. Se eliminó la validación de sentencias
  (`aula/sintaxis.py`, errores S01-S04) y el error E05 "rango de horas
  invertido", que comparaba valores (semántica). Los errores léxicos quedan
  numerados E01-E10.
- La tabla de símbolos ya no guarda atributos semánticos (tipo de dato, valor,
  declarado, créditos, capacidad). Instala todo token reconocido, también en
  líneas con errores.
- El manejador de errores informa para cada error: ubicación, lexema
  encontrado, token esperado (expresión regular), línea subrayada, cómo se
  recuperó el analizador y sugerencia.
- El lenguaje se delimita a asignación de horarios (no matrícula). Ejemplos sin
  variables de créditos ni notas.
- Se quitó la palabra reservada `creditos` (dato de matrícula): la sentencia
  de materia queda `materia CODIGO_MATERIA CADENA ;`. Quedan 26 reservadas.
- La tabla de símbolos se muestra ordenada por índice hash, con las columnas
  Índice, Lexema, Token, Categoría, Línea y Apariciones, y una leyenda.

## 2026-11-15 (revisión y entrega)

### Analizador

- Los archivos se leen en UTF-8 (con o sin BOM) y, si no lo son, en ANSI
  (cp1252), el formato del Bloc de notas de Windows. Antes el BOM producía un
  error E01 falso en la primera línea y un archivo ANSI con tildes detenía el
  análisis con `UnicodeDecodeError`.
- Los saltos de línea `\r\n`, `\r` y `\n` se tratan igual, sin cambiar la
  numeración de las líneas.
- E01 marca solo el carácter no válido (`ñ` en `samañego`). Antes guardaba la
  palabra completa como lexema y el indicador `^` se salía de la palabra.

### Interfaz

- Rediseño con Tkinter y tema `clam` para que se vea igual en Windows y
  macOS: acciones en una fila, contadores en vivo, barra de avance, visor del
  código con resaltado, pestañas de diagnóstico, tabla de errores y tokens,
  tema claro u oscuro y atajos de teclado.
- La tabla de símbolos se muestra en un `Treeview` con buscador, columnas
  ordenables, filtro de palabras reservadas y las vistas de cubetas hash y
  texto formateado.
- En macOS el texto del botón "Ver tabla de símbolos" era invisible (blanco
  sobre el botón claro del sistema, porque Aqua ignora `bg`).
- Si la ventana de la tabla de símbolos quedaba abierta y se analizaba otro
  archivo, seguía mostrando los símbolos del anterior. Ahora se vuelve a
  crear.
- Fuente monoespaciada portable (`TkFixedFont`): Consolas no existe fuera de
  Windows y desalineaba la tabla y el indicador de columna.
- Tildes en todos los mensajes y la carpeta del archivo abreviada con `~`.

### JFLAP

- `jflap/simulacion/`: versión de cada AFD que JFLAP puede simular, con una
  transición por carácter de cada clase. Las etiquetas de clase de `jflap/`
  (`0-9`, `A-Z`) JFLAP las toma como texto literal.
- `cadenas_de_prueba.txt` con las 87 cadenas de Input > Multiple Run y el
  resultado obtenido en JFLAP 7.1; todas coinciden con el AFD del programa.
- `herramientas/corridas_jflap.js` repite esas corridas con el simulador de
  JFLAP y compara los resultados.
- Diagramas legibles en JFLAP: una sola etiqueta por flecha
  (`a-z, A-Z, 0-9, _`), estados que no quedan sobre otras transiciones y el
  rango de horas en dos filas.

### Pruebas

- 52 pruebas (antes 48): BOM, ANSI, saltos de línea mixtos y posición del
  error E01.

### Documentación

- `docs/`: informe del proyecto con las dos etapas, los diagramas y las
  corridas en JFLAP, la tabla de símbolos, el manejador de errores y la
  interfaz.
- README con la estructura completa, JFLAP, la interfaz, las pruebas y los
  integrantes.

## 2026-11-15 (primera versión)

- Etapa 1: definición del lenguaje AULA, 14 AFD como tablas de transición,
  análisis léxico con coincidencia más larga y validación de las sentencias
  S1 a S11.
- Tabla de símbolos con función hash y manejador de errores.
- Interfaz gráfica que solicita el archivo de entrada.
