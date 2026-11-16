# Analizador del lenguaje AULA

Proyecto N° 1 de Lenguajes Formales, Autómatas y Compiladores (UTP, FISC).
Analizador léxico con validación sintáctica simple para AULA, un lenguaje para
definir horarios universitarios.

Cubre las dos etapas del proyecto:

| Punto | Contenido | Dónde |
|---|---|---|
| Etapa 1 | Definición del lenguaje AULA | este README, `docs/` |
| 2 | Validación de cadenas con AFD | `aula/afd.py`, `automatas.py`, `lexico.py`, `sintaxis.py` |
| 3 | Tabla de símbolos con función hash | `aula/tabla_simbolos.py` |
| 4 | Manejador de errores | `aula/manejador_errores.py` |
| 5 y 6 | Interfaz: pide el archivo, muestra los errores al evaluar y la tabla de símbolos | `interfaz.py` |

El informe completo está en `docs/` (Word y PDF). Los cambios hechos después de
la primera entrega están en `CHANGELOG.md`.

Requiere Python 3.10 o superior con Tkinter (incluido en el instalador de
python.org). No tiene dependencias externas.

## Uso

```bash
python3 interfaz.py                          # interfaz gráfica
python3 demo.py                              # consola, pide la ruta del archivo
python3 demo.py ejemplos/horario_valido.txt
python3 demo.py ejemplos/horario_errores.txt
python3 -m unittest discover -s tests -t .
```

## El lenguaje

Cada línea del archivo de entrada es una cadena y termina en `;`. Las líneas
vacías y los comentarios (`# ...`) se ignoran. El archivo puede estar en UTF-8
(con o sin BOM) o en ANSI (cp1252, el formato del Bloc de notas de Windows).

```
entero max_creditos = 18;
materia LFAC-301 "Lenguajes Formales" creditos 4;
profesor samaniego "Nicolas Samaniego";
aula 3-105 capacidad 40;
grupo 1IL142;
asignar LFAC-301 a 1IL142 con samaniego en 3-105 LU 7:00-8:30;
eliminar LFAC-301 de 1IL142;
verificar choque 1IL142;
mostrar horario de 1IL142;
si max_creditos > 18 o publicado == verdadero entonces mostrar "Revisar";
creditos_grupo = 8;
```

### Tokens

| Token | Expresión regular | Ejemplo |
|---|---|---|
| IDENTIFICADOR | `[a-z_][a-zA-Z0-9_]*` (máx. 31) | `max_creditos` |
| RESERVADA | 27 palabras en minúscula | `asignar` |
| DIA | `LU \| MA \| MI \| JU \| VI` | `LU` |
| CODIGO_MATERIA | `[A-Z]{2,4}-[0-9]{3}` | `LFAC-301` |
| GRUPO | `[0-9][A-Z]{2}[0-9]{3}` | `1IL142` |
| AULA | `[0-9]{1,2}-[0-9]{3}` | `3-105` |
| HORA | `([01]?[0-9]\|2[0-3]):[0-5][0-9]` | `7:00` |
| RANGO_HORA | `HORA-HORA` | `7:00-8:30` |
| ENTERO | `[0-9]+` | `40` |
| REAL | `[0-9]+\.[0-9]+` | `71.5` |
| CADENA | `"[^"\n]*"` | `"Lenguajes"` |
| OP_RELACIONAL | `== \| != \| < \| <= \| > \| >=` | `>=` |
| ASIGNACION | `=` | `=` |
| DELIMITADOR | `;` | `;` |

Palabras reservadas: `materia profesor aula grupo asignar eliminar verificar
mostrar a con en de creditos capacidad horario choque si entonces entero real
texto logico hora verdadero falso y o`.

### Sentencias

| | Forma |
|---|---|
| S1 | `tipo IDENTIFICADOR = valor ;` |
| S2 | `materia CODIGO_MATERIA CADENA creditos ENTERO ;` |
| S3 | `profesor IDENTIFICADOR CADENA ;` |
| S4 | `aula AULA capacidad ENTERO ;` |
| S5 | `grupo GRUPO ;` |
| S6 | `asignar CODIGO_MATERIA a GRUPO con IDENTIFICADOR en AULA DIA RANGO_HORA ;` |
| S7 | `eliminar CODIGO_MATERIA de GRUPO ;` |
| S8 | `verificar choque GRUPO ;` |
| S9 | `mostrar horario de GRUPO ;` o `mostrar (CADENA \| IDENTIFICADOR) ;` |
| S10 | `si condicion ((y \| o) condicion)* entonces mostrar (CADENA \| IDENTIFICADOR) ;` |
| S11 | `IDENTIFICADOR = valor ;` |

### Errores

| Código | Descripción | Ejemplo |
|---|---|---|
| E01 | Carácter no válido | `samañego`, `$40` |
| E02 | Cadena sin cerrar | `"Hola;` |
| E03 | Número mal formado | `71.` |
| E04 | Hora inválida | `25:70` |
| E05 | Rango de horas invertido | `9:00-7:00` |
| E06 | Código de materia mal formado | `LFAC-30` |
| E07 | Grupo mal formado | `1IL14` |
| E08 | Identificador mal formado | `9creditos`, `Total` |
| E09 | Día inválido | `SA` |
| E10 | Aula mal formada | `3-1050` |
| E11 | Identificador de más de 31 caracteres | |
| S01 | Sentencia desconocida | `capacidad 40;` |
| S02 | Token inesperado | `materia LFAC-301 creditos 4;` |
| S03 | Falta `;` | `grupo 1IL142` |
| S04 | Tokens después de `;` | `grupo 1IL142; grupo 1IL143;` |

Una línea con errores léxicos no pasa al análisis sintáctico. Dentro de una
línea se reportan todos los errores léxicos (recuperación en modo pánico: se
descarta la palabra inválida y se continúa).

## Funcionamiento

Cada token tiene su AFD definido como tabla de transiciones en
`aula/automatas.py`. El alfabeto se agrupa en clases de caracteres (`0-9`,
`A-Z`, `:`...) y en cada estado las clases son disjuntas, así que cada
autómata es determinista (lo comprueba `tests/test_afd.py`).

El analizador léxico (`aula/lexico.py`) aplica la regla de la coincidencia
más larga: en cada posición ejecuta los AFD y toma el prefijo aceptado más
largo. Luego distingue palabras reservadas de identificadores y días de otras
palabras en mayúscula. Si ningún AFD acepta la palabra completa, el código de
error se elige según su forma (contiene `:` → hora, empieza con dígito y
contiene mayúsculas → grupo, etc.).

La validación sintáctica (`aula/sintaxis.py`) es un analizador descendente
por sentencia: la primera palabra de la línea determina la sentencia esperada.

```
aula/
  tokens.py            tipos de token, palabras reservadas, catálogo de errores
  afd.py               clase AFD (Q, Σ, δ, q0, F)
  automatas.py         un AFD por token
  lexico.py            análisis léxico
  sintaxis.py          validación de sentencias
  validador.py         API pública y lectura del archivo (UTF-8 o ANSI)
  tabla_simbolos.py    tabla de símbolos (tabla hash con encadenamiento)
  manejador_errores.py manejador de errores
interfaz.py            interfaz gráfica (Tkinter)
demo.py                versión de consola
ejemplos/              horario_valido.txt y horario_errores.txt
tests/                 pruebas unitarias
jflap/                 AFD en formato JFLAP 7 para ver los diagramas
jflap/simulacion/      los mismos AFD listos para simular, y las cadenas de prueba
diagramas/             AFD en PNG (Graphviz)
herramientas/          exportar_automatas.py y corridas_jflap.js
docs/                  informe del proyecto (Word y PDF)
```

## JFLAP

Hay dos versiones de cada autómata:

- `jflap/*.jff`: cada flecha lleva las clases de caracteres que lee
  (`a-z, A-Z, 0-9, _`). Es la versión para ver el diagrama; JFLAP toma esas
  etiquetas como texto literal, así que no sirve para simular.
- `jflap/simulacion/*.jff`: mismos estados, con una transición por cada
  carácter de la clase (`0-9` son diez transiciones). Las clases `Σ` y `Σ-{"}`
  se expanden a letras, dígitos, tildes, ñ y los símbolos del lenguaje; el
  espacio queda fuera porque en JFLAP una etiqueta vacía es λ.

`jflap/simulacion/cadenas_de_prueba.txt` tiene las 87 cadenas usadas en
Input > Multiple Run y el resultado que dio JFLAP 7.1. Para repetir las
corridas sin abrir JFLAP (usa el mismo simulador):

```bash
jjs -cp /ruta/JFLAP7.1.jar herramientas/corridas_jflap.js
```

`jjs` viene con Java 8. Los `.jff` y los diagramas se regeneran desde las
tablas de `aula/automatas.py` con `python3 herramientas/exportar_automatas.py`.

## API

```python
from aula import analizar_archivo, analizar_cadena

for r in analizar_archivo("entrada.txt"):   # generador, una línea a la vez
    r.numero, r.texto, r.valida, r.sentencia
    for t in r.tokens:     # Token: lexema, tipo, linea, columna
        ...
    for e in r.errores:    # Error: codigo, categoria, descripcion, mensaje, linea, columna, lexema
        ...
```

`aula.ERRORES` contiene el catálogo completo (`codigo -> (categoria, descripcion)`).

## Tabla de símbolos

`aula/tabla_simbolos.py`: tabla hash con encadenamiento separado. La función
hash es polinomial (`h = h*31 + código del carácter`, 32 bits) y el índice es
`hash % capacidad`. Empieza con capacidad 53 (primo), se precarga con las 27
palabras reservadas y los 5 días, y se duplica a un primo mayor cuando el
factor de carga pasa de 0.75.

Cada `Simbolo` guarda `lexema`, `tipo`, `categoria`, `linea`/`columna` de la
primera aparición, `ocurrencias` (todas las posiciones, `veces` = cuántas) y
`atributos` para las fases siguientes: `tipo_dato`, `valor`, `declarado`,
`linea_declaracion`, `nombre`, `creditos`, `capacidad`, `redeclaraciones`.

```python
from aula import TablaSimbolos, analizar_archivo

tabla = TablaSimbolos()
for r in analizar_archivo("entrada.txt"):
    tabla.registrar(r)         # solo instala las líneas válidas

tabla.buscar("max_creditos").atributos   # {'declarado': True, 'tipo_dato': 'entero', 'valor': 18, ...}
print(tabla.formatear())                 # contenido de la tabla (punto 5)
print(tabla.formatear_cubetas())         # estructura interna por cubeta
tabla.estadisticas()                     # factor de carga, colisiones, ...
```

Las líneas con errores no se instalan: sus declaraciones no son confiables.

## Manejador de errores

`aula/manejador_errores.py`: recibe los errores léxicos y sintácticos, los
registra y los informa con el texto de la línea, un indicador de la columna y
una sugerencia de corrección. La interfaz se suscribe con un callback que se
invoca en el momento en que se detecta cada error, es decir, durante la
evaluación de la cadena.

```python
from aula import ManejadorErrores, analizar_archivo

manejador = ManejadorErrores()
manejador.suscribir(lambda reg: print(manejador.formatear(reg)))

for r in analizar_archivo("entrada.txt"):
    manejador.procesar(r)      # reporta todos los errores de la línea

print(manejador.resumen())     # totales por código y por categoría
```

```
✗ [E07] Grupo mal formado (línea 6, columna 7)
    Grupo mal formado '1IL14' (formato: 1IL142)
       6 | grupo 1IL14;
         |       ^^^^^
    Sugerencia: El grupo lleva un dígito, dos letras mayúsculas y tres dígitos (1IL142).
```

Consultas: `registros`, `total`, `hay_errores`, `lineas_con_error`,
`errores_de_linea(n)`, `por_categoria("LEXICO"|"SINTACTICO")`,
`conteo_por_codigo()`.

### Integración de ambos módulos

```python
for r in analizar_archivo(ruta):
    manejador.procesar(r)
    tabla.registrar(r)
# al final, si el usuario lo pide:
print(tabla.formatear())
```

## Interfaz

`python3 interfaz.py` abre la ventana principal:

- **Seleccionar archivo** (Ctrl/Cmd+O) pide el archivo de entrada; los botones
  *Válido* y *Con errores* cargan los ejemplos. El contenido se muestra con
  números de línea y resaltado.
- **Analizar archivo** (Ctrl/Cmd+Enter) evalúa una línea a la vez. Cada error
  aparece cuando el manejador lo reporta; en el código se marca la línea y se
  subraya el lexema. Las pestañas muestran el diagnóstico (filtrable), la tabla
  de errores (al elegir uno salta a la línea) y los tokens.
- **Ver tabla de símbolos** (Ctrl/Cmd+T) abre la tabla con tres vistas:
  tabular (ordenable y con buscador), cubetas hash y texto formateado.
- Tema claro u oscuro y evaluación paso a paso opcional.

Usa solo Tkinter con el tema `clam` y colores propios, así que se ve igual en
Windows, macOS y Linux.

## Pruebas

```bash
python3 -m unittest discover -s tests -t .
```

52 pruebas: aceptación y rechazo de cada AFD y determinismo de las tablas
(`test_afd.py`); tokens, posiciones, los 15 errores, las 11 sentencias,
archivos de ejemplo y codificaciones (`test_validador.py`); función hash,
colisiones, redimensionamiento, atributos, formato y suscripción del manejador
(`test_tabla_y_errores.py`).

## Integrantes

- Batista, Rafael
- Lorenzo Herrera, Samir Alexis
- Messam, Alan
- Saez, Daniel
