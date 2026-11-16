# Analizador del lenguaje AULA

Proyecto N° 1 de Lenguajes Formales, Autómatas y Compiladores (UTP, FISC).
Analizador léxico con validación sintáctica simple para AULA, un lenguaje para
definir horarios universitarios.

Este repositorio cubre la Etapa 1 (definición del lenguaje) y los puntos 2
(validación de cadenas), 3 (tabla de símbolos con función hash) y 4 (manejador
de errores) de la Etapa 2. `interfaz.py` es la interfaz de usuario (punto 5):
pide el archivo de entrada (punto 6), muestra los errores mientras se evalúa y
permite ver la tabla de símbolos.

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
  tokens.py     tipos de token, palabras reservadas, catálogo de errores
  afd.py        clase AFD (Q, Σ, δ, q0, F)
  automatas.py  un AFD por token
  lexico.py     análisis léxico
  sintaxis.py   validación de sentencias
  validador.py  API pública
  tabla_simbolos.py    tabla de símbolos (tabla hash con encadenamiento)
  manejador_errores.py manejador de errores
jflap/          AFD en formato JFLAP 7
diagramas/      AFD en PNG
herramientas/   exportar_automatas.py genera jflap/ y diagramas/
```

En los `.jff` cada transición muestra la clase de caracteres que lee. Para
simular en JFLAP se reemplaza la etiqueta por un carácter de la clase.

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
