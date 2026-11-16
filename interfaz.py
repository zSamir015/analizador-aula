"""Interfaz gráfica del analizador AULA (Etapa 2, puntos 5 y 6).

    python3 interfaz.py

Punto 6: el botón "Seleccionar archivo" solicita el archivo de entrada.
Punto 5: los errores se muestran mientras se evalúa el archivo (la interfaz se
suscribe al manejador de errores) y el botón "Ver tabla de símbolos" abre la
tabla de símbolos al terminar.
"""

import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from aula import ManejadorErrores, TablaSimbolos, analizar_archivo
from aula.sintaxis import SENTENCIAS
from aula.validador import leer_archivo

# Paleta
FONDO = "#F3F5F8"
SUPERFICIE = "#FFFFFF"
BORDE = "#D8DEE6"
TEXTO = "#1F2933"
TENUE = "#64707D"
ACENTO = "#2563EB"
ACENTO_ACTIVO = "#1D4ED8"
VERDE = "#15803D"
VERDE_FONDO = "#ECFDF3"
ROJO = "#B42318"
ROJO_FONDO = "#FEF3F2"
AZUL_FONDO = "#EFF4FF"

PAUSA_MS = 30   # tiempo entre líneas para mostrar el avance


class InterfazAULA:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("AULA - Analizador de horarios")
        self.ventana.geometry("1080x760")
        self.ventana.minsize(860, 600)
        self.ventana.configure(bg=FONDO)

        self.ruta = None
        self.proceso = None
        self.analizando = False
        self.validas = 0
        self.lineas = 0
        self.total_lineas = 0

        self.manejador = ManejadorErrores()
        self.tabla = TablaSimbolos()

        self.crear_estilos()
        self.crear_interfaz()

    # --- estilos ------------------------------------------------------------

    def crear_estilos(self):
        base = tkfont.nametofont("TkDefaultFont")
        familia = base.actual("family")
        self.f_titulo = (familia, 17, "bold")
        self.f_subtitulo = (familia, 10)
        self.f_seccion = (familia, 11, "bold")
        self.f_numero = (familia, 20, "bold")
        self.f_etiqueta = (familia, 9)
        mono = tkfont.nametofont("TkFixedFont").actual("family")
        self.f_mono = (mono, 10)
        self.f_mono_neg = (mono, 10, "bold")

        estilo = ttk.Style(self.ventana)
        estilo.theme_use("clam")
        estilo.configure(".", background=FONDO, foreground=TEXTO, font=(familia, 10))
        estilo.configure("TFrame", background=FONDO)
        estilo.configure("Superficie.TFrame", background=SUPERFICIE)

        estilo.configure("TButton", padding=(14, 7), background=SUPERFICIE,
                         bordercolor=BORDE, lightcolor=SUPERFICIE, darkcolor=SUPERFICIE,
                         focuscolor=SUPERFICIE, relief="flat")
        estilo.map("TButton",
                   background=[("disabled", FONDO), ("active", "#E9EDF2")],
                   foreground=[("disabled", "#A0A9B3")])
        estilo.configure("Acento.TButton", background=ACENTO, foreground="white",
                         bordercolor=ACENTO, lightcolor=ACENTO, darkcolor=ACENTO,
                         focuscolor=ACENTO, font=(familia, 10, "bold"))
        estilo.map("Acento.TButton",
                   background=[("disabled", "#A9C0F5"), ("active", ACENTO_ACTIVO)],
                   bordercolor=[("disabled", "#A9C0F5"), ("active", ACENTO_ACTIVO)],
                   foreground=[("disabled", "white")])

        estilo.configure("Horizontal.TProgressbar", troughcolor="#E4E8EE",
                         background=ACENTO, bordercolor=FONDO, lightcolor=ACENTO,
                         darkcolor=ACENTO, thickness=4)
        # Barras de desplazamiento delgadas, sin flechas
        for orient, lado in (("Vertical", "ns"), ("Horizontal", "ew")):
            nombre = f"{orient}.TScrollbar"
            estilo.layout(nombre, [(f"{orient}.Scrollbar.trough", {"sticky": lado, "children": [
                (f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
            estilo.configure(nombre, background="#CBD2DA", troughcolor=SUPERFICIE,
                             bordercolor=SUPERFICIE, lightcolor="#CBD2DA", darkcolor="#CBD2DA",
                             gripcount=0, arrowsize=10)
            estilo.map(nombre, background=[("active", "#AEB7C2")])
        estilo.configure("TPanedwindow", background=FONDO)

        estilo.configure("Treeview", background=SUPERFICIE, fieldbackground=SUPERFICIE,
                         foreground=TEXTO, rowheight=24, bordercolor=BORDE, font=self.f_mono)
        estilo.configure("Treeview.Heading", background="#E9EDF2", foreground=TEXTO,
                         relief="flat", font=(familia, 10, "bold"), padding=(6, 5))
        estilo.map("Treeview", background=[("selected", AZUL_FONDO)],
                   foreground=[("selected", TEXTO)])

    def tarjeta(self, padre, **grid):
        """Marco blanco con borde fino."""
        marco = tk.Frame(padre, bg=SUPERFICIE, highlightthickness=1,
                         highlightbackground=BORDE, highlightcolor=BORDE)
        if grid:
            marco.grid(**grid)
        return marco

    # --- construcción -------------------------------------------------------

    def crear_interfaz(self):
        v = self.ventana
        v.columnconfigure(0, weight=1)
        v.rowconfigure(3, weight=1)

        # Encabezado
        encabezado = tk.Frame(v, bg=SUPERFICIE, highlightthickness=1, highlightbackground=BORDE)
        encabezado.grid(row=0, column=0, sticky="ew")
        tk.Label(encabezado, text="Analizador del lenguaje AULA", font=self.f_titulo,
                 bg=SUPERFICIE, fg=TEXTO).pack(anchor="w", padx=24, pady=(16, 0))
        tk.Label(encabezado, text="Análisis léxico, validación de sentencias, tabla de "
                 "símbolos y manejo de errores", font=self.f_subtitulo, bg=SUPERFICIE,
                 fg=TENUE).pack(anchor="w", padx=24, pady=(2, 14))

        # PARTE 6: selección del archivo y acciones
        barra = ttk.Frame(v, padding=(24, 16, 24, 8))
        barra.grid(row=1, column=0, sticky="ew")
        barra.columnconfigure(1, weight=1)

        self.boton_archivo = ttk.Button(barra, text="Seleccionar archivo…",
                                        command=self.seleccionar_archivo)
        self.boton_archivo.grid(row=0, column=0)

        archivo = tk.Frame(barra, bg=FONDO)
        archivo.grid(row=0, column=1, sticky="ew", padx=14)
        self.etiqueta_archivo = tk.Label(archivo, text="Ningún archivo seleccionado",
                                         font=(self.f_subtitulo[0], 10, "bold"),
                                         bg=FONDO, fg=TEXTO, anchor="w")
        self.etiqueta_archivo.pack(fill="x")
        self.etiqueta_ruta = tk.Label(archivo, text="Formatos: .txt en UTF-8 o ANSI",
                                      font=self.f_etiqueta, bg=FONDO, fg=TENUE, anchor="w")
        self.etiqueta_ruta.pack(fill="x")

        self.boton_analizar = ttk.Button(barra, text="Analizar archivo", style="Acento.TButton",
                                         command=self.analizar, state="disabled")
        self.boton_analizar.grid(row=0, column=2, padx=(0, 8))

        self.boton_tabla = ttk.Button(barra, text="Ver tabla de símbolos",
                                      command=self.mostrar_tabla, state="disabled")
        self.boton_tabla.grid(row=0, column=3)

        # Contadores y avance
        contadores = ttk.Frame(v, padding=(24, 8, 24, 0))
        contadores.grid(row=2, column=0, sticky="ew")
        self.contadores = {}
        datos = [("lineas", "Líneas analizadas", TEXTO), ("validas", "Válidas", VERDE),
                 ("invalidas", "Con errores", ROJO), ("errores", "Errores reportados", ROJO)]
        for i, (clave, texto, color) in enumerate(datos):
            contadores.columnconfigure(i, weight=1, uniform="contador")
            tarjeta = self.tarjeta(contadores, row=0, column=i, sticky="ew",
                                   padx=(0 if i == 0 else 10, 0))
            numero = tk.Label(tarjeta, text="0", font=self.f_numero, bg=SUPERFICIE, fg=color)
            numero.pack(anchor="w", padx=14, pady=(10, 0))
            tk.Label(tarjeta, text=texto, font=self.f_etiqueta, bg=SUPERFICIE,
                     fg=TENUE).pack(anchor="w", padx=14, pady=(0, 10))
            self.contadores[clave] = numero

        self.progreso = ttk.Progressbar(contadores, mode="determinate",
                                        style="Horizontal.TProgressbar")
        self.progreso.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(12, 0))

        # Resultados y resumen
        paneles = ttk.PanedWindow(v, orient="vertical")
        paneles.grid(row=3, column=0, sticky="nsew", padx=24, pady=(12, 8))

        self.resultados = self.panel_texto(paneles, "Resultados y errores detectados",
                                           alto=14, peso=3)
        self.resumen_texto = self.panel_texto(paneles, "Resumen de errores", alto=6, peso=1)

        t = self.resultados
        t.tag_configure("valido", foreground=VERDE)
        t.tag_configure("valido_detalle", foreground=TENUE)
        t.tag_configure("error_titulo", foreground=ROJO, font=self.f_mono_neg)
        t.tag_configure("error", foreground=TEXTO)
        t.tag_configure("indicador", foreground=ROJO, font=self.f_mono_neg)
        t.tag_configure("sugerencia", foreground=ACENTO)
        t.tag_configure("titulo", font=self.f_mono_neg, spacing1=8)
        t.tag_configure("bloque_error", lmargin1=6, lmargin2=6)
        t.tag_configure("tenue", foreground=TENUE)
        self.resumen_texto.tag_configure("titulo", font=self.f_mono_neg)
        self.resumen_texto.tag_configure("tenue", foreground=TENUE)

        self.escribir(t, "Seleccione un archivo y pulse «Analizar archivo».\n", "tenue")

        # Barra de estado
        estado = tk.Frame(v, bg=SUPERFICIE, highlightthickness=1, highlightbackground=BORDE)
        estado.grid(row=4, column=0, sticky="ew")
        self.estado = tk.StringVar(value="Seleccione un archivo para comenzar.")
        tk.Label(estado, textvariable=self.estado, font=self.f_etiqueta, bg=SUPERFICIE,
                 fg=TENUE, anchor="w").pack(side="left", padx=24, pady=6)
        mod = "Cmd" if sys.platform == "darwin" else "Ctrl"
        tk.Label(estado, text=f"{mod}+O abrir   ·   {mod}+Enter analizar", font=self.f_etiqueta,
                 bg=SUPERFICIE, fg=TENUE).pack(side="right", padx=24)

        tecla = "Command" if sys.platform == "darwin" else "Control"
        v.bind(f"<{tecla}-o>", lambda e: self.seleccionar_archivo())
        v.bind(f"<{tecla}-Return>", lambda e: self.analizar())

    def panel_texto(self, paneles, titulo, alto, peso):
        marco = ttk.Frame(paneles)
        paneles.add(marco, weight=peso)
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(1, weight=1)
        tk.Label(marco, text=titulo, font=self.f_seccion, bg=FONDO, fg=TEXTO).grid(
            row=0, column=0, sticky="w", pady=(4, 6))
        tarjeta = self.tarjeta(marco, row=1, column=0, sticky="nsew")
        tarjeta.columnconfigure(0, weight=1)
        tarjeta.rowconfigure(0, weight=1)
        texto = tk.Text(tarjeta, wrap="none", font=self.f_mono, height=alto, bg=SUPERFICIE,
                        fg=TEXTO, relief="flat", borderwidth=0, highlightthickness=0,
                        padx=14, pady=10, spacing1=1, spacing3=1, state="disabled",
                        cursor="arrow", insertwidth=0)
        texto.grid(row=0, column=0, sticky="nsew")
        sv = ttk.Scrollbar(tarjeta, orient="vertical", command=texto.yview)
        sv.grid(row=0, column=1, sticky="ns")
        sh = ttk.Scrollbar(tarjeta, orient="horizontal", command=texto.xview)
        sh.grid(row=1, column=0, sticky="ew")
        texto.configure(yscrollcommand=sv.set, xscrollcommand=sh.set)
        return texto

    # --- utilidades ---------------------------------------------------------

    @staticmethod
    def escribir(widget, texto, *tags):
        widget.configure(state="normal")
        widget.insert(tk.END, texto, tags)
        widget.configure(state="disabled")

    @staticmethod
    def limpiar(widget):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.configure(state="disabled")

    def actualizar_contadores(self):
        invalidas = len(self.manejador.lineas_con_error)
        valores = {"lineas": self.lineas, "validas": self.validas,
                   "invalidas": invalidas, "errores": self.manejador.total}
        for clave, valor in valores.items():
            self.contadores[clave].config(text=str(valor))
        self.progreso.configure(maximum=max(self.total_lineas, 1), value=self.lineas)

    def actualizar_resumen(self):
        self.limpiar(self.resumen_texto)
        lineas = self.manejador.resumen().split("\n")
        self.escribir(self.resumen_texto, lineas[0] + "\n", "titulo")
        if len(lineas) > 1:
            self.escribir(self.resumen_texto, "\n".join(lineas[1:]) + "\n")

    @staticmethod
    def contar_lineas(ruta):
        """Líneas con contenido (las que se evalúan), para la barra de avance."""
        try:
            texto = leer_archivo(ruta)
        except (OSError, UnicodeError):
            return 0
        return sum(1 for l in texto.splitlines() if l.strip() and not l.strip().startswith("#"))

    # PARTE 6: abrir el archivo de entrada
    def seleccionar_archivo(self):
        if self.analizando:
            return

        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo AULA",
            initialdir=str(Path(__file__).resolve().parent / "ejemplos"),
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return

        self.ruta = ruta
        self.etiqueta_archivo.config(text=Path(ruta).name)
        self.etiqueta_ruta.config(text=str(Path(ruta).parent))
        self.estado.set("Archivo seleccionado. Listo para analizar.")
        self.boton_analizar.config(state="normal")
        self.boton_tabla.config(state="disabled")
        self.limpiar(self.resultados)
        self.limpiar(self.resumen_texto)
        self.escribir(self.resultados, "Pulse «Analizar archivo» para evaluar "
                      f"{Path(ruta).name}.\n", "tenue")

    # Iniciar el análisis
    def analizar(self):
        if self.analizando:
            return
        if not self.ruta:
            messagebox.showwarning("Archivo requerido", "Primero seleccione un archivo .txt.")
            return

        self.limpiar(self.resultados)
        self.limpiar(self.resumen_texto)

        self.manejador = ManejadorErrores()
        self.tabla = TablaSimbolos()
        self.validas = 0
        self.lineas = 0
        self.total_lineas = self.contar_lineas(self.ruta)

        # Suscripción al manejador de errores: cada error llega al detectarse
        self.manejador.suscribir(self.mostrar_error)

        self.analizando = True
        self.boton_tabla.config(state="disabled")
        self.boton_analizar.config(state="disabled")
        self.boton_archivo.config(state="disabled")
        self.estado.set("Analizando archivo…")
        self.actualizar_contadores()

        self.proceso = iter(analizar_archivo(self.ruta))
        self.ventana.after(PAUSA_MS, self.procesar_siguiente)

    # Procesamiento línea por línea
    def procesar_siguiente(self):
        try:
            resultado = next(self.proceso)
        except StopIteration:
            self.finalizar_analisis()
            return
        except (OSError, UnicodeError) as error:
            messagebox.showerror("Error de lectura", str(error))
            self.estado.set("No se pudo leer el archivo.")
            self.restablecer_controles()
            return
        except Exception as error:
            messagebox.showerror("Error inesperado", str(error))
            self.estado.set("El análisis se interrumpió.")
            self.restablecer_controles()
            return

        try:
            self.lineas += 1
            # Detectar y comunicar errores (llama a mostrar_error por cada uno)
            self.manejador.procesar(resultado)

            if resultado.valida:
                self.tabla.registrar(resultado)
                self.validas += 1
                self.escribir(self.resultados, f"✓ Línea {resultado.numero:<4}", "valido")
                self.escribir(self.resultados, f"{resultado.sentencia:<4} "
                              f"{SENTENCIAS.get(resultado.sentencia, '')}\n", "valido_detalle")

            self.actualizar_contadores()
            self.estado.set(f"Procesando línea {resultado.numero}…")
            self.resultados.see(tk.END)
            self.ventana.after(PAUSA_MS, self.procesar_siguiente)

        except Exception as error:
            messagebox.showerror("Error de procesamiento", str(error))
            self.estado.set("El análisis se interrumpió.")
            self.restablecer_controles()

    # PARTE 5: mostrar cada error en el momento en que se detecta
    def mostrar_error(self, registro):
        lineas = self.manejador.formatear(registro).split("\n")
        for i, linea in enumerate(lineas):
            if i == 0:
                tag = "error_titulo"
            elif linea.lstrip().startswith("Sugerencia:"):
                tag = "sugerencia"
            elif "^" in linea and linea.strip().replace("|", "").strip().strip("^") == "":
                tag = "indicador"
            else:
                tag = "error"
            self.escribir(self.resultados, linea + "\n", tag, "bloque_error")
        self.escribir(self.resultados, "\n")
        self.resultados.see(tk.END)
        self.actualizar_resumen()

    # Fin del análisis
    def finalizar_analisis(self):
        self.actualizar_resumen()
        self.actualizar_contadores()
        self.progreso.configure(value=self.progreso["maximum"])

        self.escribir(self.resultados, "\nAnálisis finalizado\n", "titulo")
        self.escribir(self.resultados,
                      f"{self.validas} línea(s) válida(s), "
                      f"{len(self.manejador.lineas_con_error)} con errores, "
                      f"{self.manejador.total} error(es) reportado(s).\n", "tenue")

        if self.manejador.hay_errores:
            self.estado.set(f"Análisis finalizado con {self.manejador.total} error(es).")
        else:
            self.estado.set("Análisis finalizado sin errores.")

        self.restablecer_controles()
        self.boton_tabla.config(state="normal")
        self.resultados.see("1.0")

    def restablecer_controles(self):
        self.analizando = False
        self.boton_archivo.config(state="normal")
        self.boton_analizar.config(state="normal" if self.ruta else "disabled")

    # PARTE 5: tabla de símbolos
    def mostrar_tabla(self):
        self.ventana_tabla = VentanaTabla(self.ventana, self.tabla,
                                          Path(self.ruta).name if self.ruta else "", self)


class VentanaTabla:
    COLUMNAS = (("hash", "Hash", 55, "e"), ("lexema", "Lexema", 270, "w"),
                ("tipo", "Tipo", 140, "w"), ("categoria", "Categoría", 135, "w"),
                ("linea", "Línea", 55, "e"), ("veces", "Veces", 55, "e"),
                ("atributos", "Atributos", 400, "w"))

    def __init__(self, padre, tabla, archivo, ui):
        self.tabla = tabla
        v = self.ventana = tk.Toplevel(padre)
        v.title("Tabla de símbolos - AULA")
        v.geometry("1120x600")
        v.minsize(700, 400)
        v.configure(bg=FONDO)
        v.columnconfigure(0, weight=1)
        v.rowconfigure(2, weight=1)

        e = tabla.estadisticas()
        encabezado = tk.Frame(v, bg=SUPERFICIE, highlightthickness=1, highlightbackground=BORDE)
        encabezado.grid(row=0, column=0, sticky="ew")
        tk.Label(encabezado, text="Tabla de símbolos", font=ui.f_titulo, bg=SUPERFICIE,
                 fg=TEXTO).pack(anchor="w", padx=20, pady=(14, 0))
        tk.Label(encabezado,
                 text=f"{archivo}   ·   {len(tabla.simbolos_usados())} símbolos usados   ·   "
                      f"capacidad {e['capacidad']}   ·   factor de carga {e['factor_carga']}   ·   "
                      f"colisiones {e['colisiones']}   ·   redimensiones {e['redimensiones']}",
                 font=ui.f_subtitulo, bg=SUPERFICIE, fg=TENUE).pack(anchor="w", padx=20,
                                                                   pady=(2, 12))

        filtro = ttk.Frame(v, padding=(20, 12, 20, 8))
        filtro.grid(row=1, column=0, sticky="ew")
        tk.Label(filtro, text="Buscar lexema:", bg=FONDO, fg=TENUE,
                 font=ui.f_etiqueta).pack(side="left")
        self.busqueda = tk.StringVar()
        self.busqueda.trace_add("write", lambda *a: self.llenar())
        entrada = tk.Entry(filtro, textvariable=self.busqueda, width=28, relief="flat",
                           highlightthickness=1, highlightbackground=BORDE,
                           highlightcolor=ACENTO, bg=SUPERFICIE, fg=TEXTO,
                           insertbackground=TEXTO, font=ui.f_mono)
        entrada.pack(side="left", padx=(8, 0), ipady=4)
        self.reservadas = tk.BooleanVar(value=True)
        tk.Checkbutton(filtro, text="Incluir palabras reservadas y días",
                       variable=self.reservadas, command=self.llenar, bg=FONDO, fg=TEXTO,
                       activebackground=FONDO, selectcolor=SUPERFICIE,
                       font=ui.f_etiqueta).pack(side="left", padx=16)

        marco = tk.Frame(v, bg=SUPERFICIE, highlightthickness=1, highlightbackground=BORDE)
        marco.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(0, weight=1)

        self.arbol = ttk.Treeview(marco, columns=[c[0] for c in self.COLUMNAS],
                                  show="headings", selectmode="browse")
        for clave, titulo, ancho, lado in self.COLUMNAS:
            self.arbol.heading(clave, text=titulo, anchor=lado)
            self.arbol.column(clave, width=ancho, anchor=lado,
                              stretch=(clave == "atributos"), minwidth=40)
        self.arbol.tag_configure("par", background="#F8FAFC")
        self.arbol.tag_configure("reservada", foreground=TENUE)
        self.arbol.grid(row=0, column=0, sticky="nsew")

        sv = ttk.Scrollbar(marco, orient="vertical", command=self.arbol.yview)
        sv.grid(row=0, column=1, sticky="ns")
        sh = ttk.Scrollbar(marco, orient="horizontal", command=self.arbol.xview)
        sh.grid(row=1, column=0, sticky="ew")
        self.arbol.configure(yscrollcommand=sv.set, xscrollcommand=sh.set)

        self.llenar()
        v.transient(padre)
        v.lift()
        entrada.focus_set()

    def llenar(self):
        self.arbol.delete(*self.arbol.get_children())
        texto = self.busqueda.get().strip().lower()
        fila = 0
        for s in self.tabla.simbolos_usados():
            fijo = s.tipo in ("RESERVADA", "DIA")
            if fijo and not self.reservadas.get():
                continue
            if texto and texto not in s.lexema.lower():
                continue
            attrs = ", ".join(f"{k}={v!r}" for k, v in s.atributos.items()
                              if k != "linea_declaracion")
            tags = (["par"] if fila % 2 else []) + (["reservada"] if fijo else [])
            self.arbol.insert("", "end", tags=tags, values=(
                self.tabla.indice(s.lexema), s.lexema, s.tipo, s.categoria, s.linea, s.veces,
                attrs))
            fila += 1


if __name__ == "__main__":
    ventana = tk.Tk()
    app = InterfazAULA(ventana)
    ventana.mainloop()
