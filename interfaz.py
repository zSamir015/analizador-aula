
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from aula import analizar_archivo, ManejadorErrores, TablaSimbolos


class InterfazAULA:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("AULA - Analizador de Horarios")
        self.ventana.geometry("1050x750")
        self.ventana.minsize(800, 550)

        self.ruta = None
        self.proceso = None
        self.analizando = False
        self.validas = 0

        self.manejador = ManejadorErrores()
        self.tabla = TablaSimbolos()

        self.crear_interfaz()

    def crear_interfaz(self):
        # Distribucion principal
        self.ventana.columnconfigure(0, weight=1)
        self.ventana.rowconfigure(3, weight=1)

        # Titulo
        titulo = ttk.Label(
            self.ventana,
            text="Analizador del Lenguaje AULA",
            font=("Arial", 20, "bold")
        )
        titulo.grid(
            row=0, column=0,
            pady=(15, 10)
        )

        # PARTE 6: Seleccion de archivo
        marco_archivo = ttk.Frame(self.ventana)
        marco_archivo.grid(
            row=1, column=0,
            sticky="ew",
            padx=20, pady=8
        )

        self.boton_archivo = ttk.Button(
            marco_archivo,
            text="Seleccionar archivo",
            command=self.seleccionar_archivo,
            width=22
        )
        self.boton_archivo.pack(side="left")

        self.etiqueta_archivo = ttk.Label(
            marco_archivo,
            text="Ningún archivo seleccionado"
        )
        self.etiqueta_archivo.pack(
            side="left", padx=15
        )

        # Boton de analisis
        marco_acciones = ttk.Frame(self.ventana)
        marco_acciones.grid(
            row=2, column=0,
            pady=5
        )

        self.boton_analizar = ttk.Button(
            marco_acciones,
            text="Analizar archivo",
            command=self.analizar,
            width=24
        )
        self.boton_analizar.pack(pady=5)

        self.estado = tk.StringVar(
            value="Seleccione un archivo para comenzar."
        )

        ttk.Label(
            marco_acciones,
            textvariable=self.estado
        ).pack(pady=5)

        # Panel principal
        panel = ttk.Frame(self.ventana)
        panel.grid(
            row=3, column=0,
            sticky="nsew",
            padx=20, pady=8
        )

        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(1, weight=3)
        panel.rowconfigure(3, weight=1)

        # Resultados individuales
        ttk.Label(
            panel,
            text="Resultados y errores detectados",
            font=("Arial", 12, "bold")
        ).grid(
            row=0, column=0,
            sticky="w", pady=(0, 5)
        )

        marco_resultados = ttk.Frame(panel)
        marco_resultados.grid(
            row=1, column=0,
            sticky="nsew"
        )

        marco_resultados.columnconfigure(0, weight=1)
        marco_resultados.rowconfigure(0, weight=1)

        self.resultados = tk.Text(
            marco_resultados,
            wrap="word",
            font="TkFixedFont",
            padx=10,
            pady=10
        )
        self.resultados.grid(
            row=0, column=0,
            sticky="nsew"
        )

        scroll_resultados = ttk.Scrollbar(
            marco_resultados,
            orient="vertical",
            command=self.resultados.yview
        )
        scroll_resultados.grid(
            row=0, column=1,
            sticky="ns"
        )

        self.resultados.configure(
            yscrollcommand=scroll_resultados.set
        )

        # Colores de resultados
        self.resultados.tag_configure(
            "error",
            foreground="#B91C1C"
        )
        self.resultados.tag_configure(
            "valido",
            foreground="#15803D"
        )
        self.resultados.tag_configure(
            "titulo",
            font=("TkFixedFont", 10, "bold")
        )

        # Resumen
        ttk.Label(
            panel,
            text="Resumen del análisis",
            font=("Arial", 12, "bold")
        ).grid(
            row=2, column=0,
            sticky="w", pady=(12, 5)
        )

        marco_resumen = ttk.Frame(panel)
        marco_resumen.grid(
            row=3, column=0,
            sticky="nsew"
        )

        marco_resumen.columnconfigure(0, weight=1)
        marco_resumen.rowconfigure(0, weight=1)

        self.resumen_texto = tk.Text(
            marco_resumen,
            wrap="none",
            font="TkFixedFont",
            height=7,
            padx=8,
            pady=8
        )
        self.resumen_texto.grid(
            row=0, column=0,
            sticky="nsew"
        )

        scroll_resumen = ttk.Scrollbar(
            marco_resumen,
            orient="vertical",
            command=self.resumen_texto.yview
        )
        scroll_resumen.grid(
            row=0, column=1,
            sticky="ns"
        )

        self.resumen_texto.configure(
            yscrollcommand=scroll_resumen.set
        )

        # BARRA INFERIOR FIJA
        # El boton no se comprime con los resultados
        barra_inferior = ttk.Frame(self.ventana)
        barra_inferior.grid(
            row=4, column=0,
            sticky="ew",
            padx=20, pady=(10, 15)
        )

        barra_inferior.columnconfigure(0, weight=1)

        self.boton_tabla = tk.Button(
            barra_inferior,
            text="Ver tabla de símbolos",
            command=self.mostrar_tabla,
            width=26,
            height=2,
            font=("Arial", 11, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            disabledforeground="#666666",
            relief="raised",
            state="disabled",
            cursor="hand2"
        )
        self.boton_tabla.grid(
            row=0, column=0,
            pady=5
        )

        # En macOS (Aqua) tk.Button ignora bg: el texto blanco quedaría
        # sobre el botón claro del sistema. Se usan los colores del sistema.
        if self.ventana.tk.call("tk", "windowingsystem") == "aqua":
            self.boton_tabla.config(fg="systemButtonText",
                                    activeforeground="systemButtonText")

    # PARTE 6: Abrir archivo TXT
    def seleccionar_archivo(self):
        if self.analizando:
            return

        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo AULA",
            initialdir=str(
                Path(__file__).resolve().parent / "ejemplos"
            ),
            filetypes=[
                ("Archivos de texto", "*.txt"),
                ("Todos los archivos", "*.*")
            ]
        )

        if not ruta:
            return

        self.ruta = ruta

        self.etiqueta_archivo.config(
            text=Path(ruta).name
        )

        self.estado.set(
            "Archivo seleccionado. Listo para analizar."
        )

        self.resultados.delete("1.0", tk.END)
        self.resumen_texto.delete("1.0", tk.END)

        self.boton_tabla.config(state="disabled")

    # Iniciar analisis
    def analizar(self):
        if self.analizando:
            return

        if not self.ruta:
            messagebox.showwarning(
                "Archivo requerido",
                "Primero seleccione un archivo .txt."
            )
            return

        self.resultados.delete("1.0", tk.END)
        self.resumen_texto.delete("1.0", tk.END)

        self.manejador = ManejadorErrores()
        self.tabla = TablaSimbolos()
        self.validas = 0

        # Suscripcion al manejador de errores
        self.manejador.suscribir(
            self.mostrar_error
        )

        self.analizando = True

        self.boton_tabla.config(state="disabled")
        self.boton_analizar.config(state="disabled")
        self.boton_archivo.config(state="disabled")

        self.estado.set("Analizando archivo...")

        self.proceso = iter(
            analizar_archivo(self.ruta)
        )

        self.ventana.after(
            30, self.procesar_siguiente
        )

    # Procesamiento linea por linea
    def procesar_siguiente(self):
        try:
            resultado = next(self.proceso)

        except StopIteration:
            self.finalizar_analisis()
            return

        except (OSError, UnicodeError) as error:
            messagebox.showerror(
                "Error de lectura",
                str(error)
            )
            self.estado.set("Error al leer el archivo.")
            self.restablecer_controles()
            return

        except Exception as error:
            messagebox.showerror(
                "Error inesperado",
                str(error)
            )
            self.estado.set("El análisis se interrumpió.")
            self.restablecer_controles()
            return

        try:
            # Detectar y comunicar errores
            self.manejador.procesar(resultado)

            if resultado.valida:
                self.tabla.registrar(resultado)
                self.validas += 1

                mensaje = (
                    f"Línea {resultado.numero}: "
                    f"VÁLIDA ({resultado.sentencia})\n"
                )

                self.resultados.insert(
                    tk.END, mensaje, "valido"
                )

            self.estado.set(
                f"Procesando linea {resultado.numero}..."
            )

            self.resultados.see(tk.END)

            # Continuar en el siguiente ciclo
            self.ventana.after(
                30, self.procesar_siguiente
            )

        except Exception as error:
            messagebox.showerror(
                "Error de procesamiento",
                str(error)
            )
            self.estado.set("El análisis se interrumpió.")
            self.restablecer_controles()

    # PARTE 5: Mostrar cada error
    def mostrar_error(self, registro):
        mensaje = self.manejador.formatear(
            registro
        )

        self.resultados.insert(
            tk.END,
            mensaje + "\n\n",
            "error"
        )

        self.resultados.see(tk.END)

        # Actualizar resumen durante el analisis
        self.resumen_texto.delete("1.0", tk.END)

        self.resumen_texto.insert(
            tk.END,
            self.manejador.resumen()
        )

    # Finalizar analisis
    def finalizar_analisis(self):
        self.resumen_texto.delete("1.0", tk.END)

        self.resumen_texto.insert(
            tk.END,
            self.manejador.resumen()
        )

        self.resultados.insert(
            tk.END,
            "\n===== ANÁLISIS FINALIZADO =====\n",
            "titulo"
        )

        self.resultados.insert(
            tk.END,
            f"Líneas válidas: {self.validas}\n"
            f"Errores detectados: {self.manejador.total}\n"
        )

        self.estado.set("Análisis finalizado.")

        self.restablecer_controles()

        # Habilitar el boton al finalizar
        self.boton_tabla.config(
            state="normal"
        )

        # Mostrar el principio de los resultados
        self.resultados.see("1.0")

    def restablecer_controles(self):
        self.analizando = False

        self.boton_archivo.config(
            state="normal"
        )
        self.boton_analizar.config(
            state="normal"
        )

    # PARTE 5: Tabla de simbolos
    def mostrar_tabla(self):
        ventana_tabla = tk.Toplevel(
            self.ventana
        )

        ventana_tabla.title(
            "Tabla de símbolos - AULA"
        )

        ventana_tabla.geometry("1100x600")
        ventana_tabla.minsize(650, 400)

        marco = ttk.Frame(ventana_tabla)
        marco.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        marco.columnconfigure(0, weight=1)
        marco.rowconfigure(1, weight=1)

        ttk.Label(
            marco,
            text="Tabla de símbolos del lenguaje AULA",
            font=("Arial", 14, "bold")
        ).grid(
            row=0, column=0,
            sticky="w", pady=(0, 10)
        )

        contenido = tk.Text(
            marco,
            wrap="none",
            font="TkFixedFont",
            padx=10,
            pady=10
        )

        contenido.grid(
            row=1, column=0,
            sticky="nsew"
        )

        scroll_vertical = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=contenido.yview
        )

        scroll_vertical.grid(
            row=1, column=1,
            sticky="ns"
        )

        scroll_horizontal = ttk.Scrollbar(
            marco,
            orient="horizontal",
            command=contenido.xview
        )

        scroll_horizontal.grid(
            row=2, column=0,
            sticky="ew"
        )

        contenido.configure(
            yscrollcommand=scroll_vertical.set,
            xscrollcommand=scroll_horizontal.set
        )

        contenido.insert(
            tk.END,
            self.tabla.formatear()
        )

        contenido.config(state="disabled")

        # Colocar la ventana de tabla al frente
        ventana_tabla.transient(self.ventana)
        ventana_tabla.lift()
        ventana_tabla.focus_set()


if __name__ == "__main__":
    ventana = tk.Tk()
    app = InterfazAULA(ventana)
    ventana.mainloop()
