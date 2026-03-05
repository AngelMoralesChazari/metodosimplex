import customtkinter as ctk
import numpy as np
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import tempfile

from simplex_solver import SolucionadorSimplex
from plotter import GraficadorPL
from pdf_exporter import ExportadorPDF


# Fila de restricción.
class FilaRestriccion:

    def __init__(self, padre, num_vars, num_fila, callback_eliminar):
        self.padre = padre
        self.num_vars = num_vars
        self.num_fila = num_fila
        self.callback_eliminar = callback_eliminar

        self.marco = ctk.CTkFrame(padre)
        self.entradas = []
        self.var_desigualdad = None

        self._crear_widgets()

    # Crea los widgets de la fila de restricción
    def _crear_widgets(self):

        # Número de restricción
        etiqueta = ctk.CTkLabel(self.marco, text = f"R{self.num_fila}:", width = 40)
        etiqueta.pack(side = "left", padx = 5)

        # Entradas para coeficientes
        for i in range(self.num_vars):
            entrada = ctk.CTkEntry(self.marco, width = 60, placeholder_text = "0")
            entrada.pack(side = "left", padx = 2)
            self.entradas.append(entrada)

            if i < self.num_vars - 1:
                ctk.CTkLabel(self.marco, text = f"x{i + 1} +").pack(side = "left", padx = 2)
            else:
                ctk.CTkLabel(self.marco, text = f"x{i + 1}").pack(side = "left", padx = 2)

        # Selector de desigualdad
        self.var_desigualdad = ctk.StringVar(value="<=")
        menu_desigualdad = ctk.CTkOptionMenu(
            self.marco,
            values = ["<=", ">=", "="],
            variable = self.var_desigualdad,
            width = 60
        )
        menu_desigualdad.pack(side = "left", padx = 5)

        # Entrada para RHS
        self.entrada_rhs = ctk.CTkEntry(self.marco, width = 60, placeholder_text = "0")
        self.entrada_rhs.pack(side = "left", padx = 5)

        # Botón de eliminar
        btn_eliminar = ctk.CTkButton(
            self.marco,
            text = "✕",
            width = 30,
            command = lambda: self.callback_eliminar(self),
            fg_color = "red",
            hover_color = "darkred"
        )
        btn_eliminar.pack(side = "left", padx = 5)

    # Obtiene los valores de la restricción
    def obtener_restriccion(self):

        try:
            coeficientes = [float(e.get() or "0") for e in self.entradas]
            rhs = float(self.entrada_rhs.get() or "0")
            desigualdad = self.var_desigualdad.get()

            return coeficientes, desigualdad, rhs
        except ValueError:
            return None

    # Establece los valores de la restricción.
    def establecer_restriccion(self, coeficientes, desigualdad, rhs):

        for i, coef in enumerate(coeficientes):
            if i < len(self.entradas):
                self.entradas[i].delete(0, "end")
                self.entradas[i].insert(0, str(coef))

        self.var_desigualdad.set(desigualdad)
        self.entrada_rhs.delete(0, "end")
        self.entrada_rhs.insert(0, str(rhs))

    def pack(self, **kwargs):
        self.marco.pack(**kwargs)

    def destroy(self):
        self.marco.destroy()


class AplicacionPL:

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.raiz = ctk.CTk()
        self.raiz.title("Método Simplex")
        self.raiz.geometry("1400x900")

        self.num_vars = 2
        self.filas_restriccion = []
        self.solver = SolucionadorSimplex()
        self.graficador = GraficadorPL()
        self.exportador_pdf = ExportadorPDF()
        self.ruta_grafica_actual = None

        self._crear_widgets()

    def _crear_widgets(self):

        # Frame de dos columnas
        contenedor_principal = ctk.CTkFrame(self.raiz)
        contenedor_principal.pack(fill = "both", expand = True, padx = 10, pady = 10)

        # CIZQ - Entrada de datos
        marco_izquierdo = ctk.CTkFrame(contenedor_principal)
        marco_izquierdo.pack(side = "left", fill = "both", expand = True, padx = (0, 5))

        # CDER - Resultados
        marco_derecho = ctk.CTkFrame(contenedor_principal)
        marco_derecho.pack(side = "right", fill = "both", expand = True, padx = (5, 0))


        # Columna IZQ
        titulo = ctk.CTkLabel(
            marco_izquierdo,
            text = "Configuración del Problema",
            font = ctk.CTkFont(size = 20, weight = "bold")
        )
        titulo.pack(pady = 10)

        marco_config = ctk.CTkFrame(marco_izquierdo)
        marco_config.pack(fill = "x", padx = 10, pady = 5)

        # Tipo de optimización
        etiqueta_opt = ctk.CTkLabel(marco_config, text = "Tipo de optimización:")
        etiqueta_opt.pack(anchor = "w", padx = 10, pady = (10, 0))

        self.var_tipo_opt = ctk.StringVar(value = "Maximizar")
        menu_opt = ctk.CTkOptionMenu(
            marco_config,
            values = ["Maximizar", "Minimizar"],
            variable = self.var_tipo_opt
        )
        menu_opt.pack(fill = "x", padx = 10, pady = (5, 10))

        # Número de variables
        etiqueta_vars = ctk.CTkLabel(marco_config, text = "Número de variables:")
        etiqueta_vars.pack(anchor = "w", padx = 10)

        self.entrada_num_vars = ctk.CTkEntry(marco_config, placeholder_text="2")
        self.entrada_num_vars.insert(0, "2")
        self.entrada_num_vars.pack(fill = "x", padx = 10, pady = (5, 10))

        btn_actualizar_vars = ctk.CTkButton(
            marco_config,
            text = "Actualizar Variables",
            command = self._actualizar_num_variables
        )
        btn_actualizar_vars.pack(fill = "x", padx = 10, pady = (0, 10))

        # Función objetivo
        marco_obj = ctk.CTkFrame(marco_izquierdo)
        marco_obj.pack(fill = "x", padx = 10, pady = 5)

        titulo_obj = ctk.CTkLabel(
            marco_obj,
            text = "Función Objetivo",
            font = ctk.CTkFont(size = 16, weight = "bold")
        )
        titulo_obj.pack(pady = 10)

        self.marco_entradas_obj = ctk.CTkFrame(marco_obj)
        self.marco_entradas_obj.pack(fill = "x", padx = 10, pady = (0, 10))

        self.entradas_obj = []
        self._crear_entradas_objetivo()

        # Restricciones
        marco_restricciones = ctk.CTkFrame(marco_izquierdo)
        marco_restricciones.pack(fill = "both", expand = True, padx = 10, pady = 5)

        titulo_restricciones = ctk.CTkLabel(
            marco_restricciones,
            text = "Restricciones",
            font = ctk.CTkFont(size = 16, weight = "bold")
        )
        titulo_restricciones.pack(pady=10)

        self.scroll_restricciones = ctk.CTkScrollableFrame(
            marco_restricciones,
            height = 300
        )
        self.scroll_restricciones.pack(fill = "both", expand = True, padx = 10, pady = (0, 10))

        # Botones de restricciones
        marco_btn_restricciones = ctk.CTkFrame(marco_restricciones)
        marco_btn_restricciones.pack(fill = "x", padx = 10, pady = (0, 10))

        btn_agregar_restriccion = ctk.CTkButton(
            marco_btn_restricciones,
            text = "➕ Agregar Restricción",
            command = self._agregar_restriccion
        )
        btn_agregar_restriccion.pack(side = "left", padx = 5, expand = True, fill = "x")

        # Botones de acción
        marco_acciones = ctk.CTkFrame(marco_izquierdo)
        marco_acciones.pack(fill = "x", padx = 10, pady = 10)

        btn_resolver = ctk.CTkButton(
            marco_acciones,
            text = "🚀 RESOLVER",
            command = self._resolver_problema,
            font = ctk.CTkFont(size = 16, weight = "bold"),
            height = 40,
            fg_color = "green",
            hover_color = "darkgreen"
        )
        btn_resolver.pack(side = "left", padx = 5, expand = True, fill = "x")

        btn_limpiar = ctk.CTkButton(
            marco_acciones,
            text = "🗑️ Limpiar",
            command = self._limpiar_todo,
            height = 40
        )
        btn_limpiar.pack(side = "left", padx = 5, expand = True, fill = "x")


        # Columna DER
        titulo_resultados = ctk.CTkLabel(
            marco_derecho,
            text = "Resultados",
            font = ctk.CTkFont(size = 20, weight = "bold")
        )
        titulo_resultados.pack(pady = 10)

        # Pestaña RES
        self.pestanas_resultados = ctk.CTkTabview(marco_derecho)
        self.pestanas_resultados.pack(fill = "both", expand = True, padx = 10, pady = (0, 10))

        # Pestaña  SOL
        self.pestanas_resultados.add("Solución")
        self.texto_solucion = ctk.CTkTextbox(
            self.pestanas_resultados.tab("Solución"),
            wrap = "word",
            font = ctk.CTkFont(family = "Courier", size = 11)
        )
        self.texto_solucion.pack(fill = "both", expand = True, padx = 5, pady = 5)

        # Pestaña ITE
        self.pestanas_resultados.add("Iteraciones Simplex")
        self.texto_iteraciones = ctk.CTkTextbox(
            self.pestanas_resultados.tab("Iteraciones Simplex"),
            wrap = "none",
            font = ctk.CTkFont(family = "Courier", size = 9)
        )
        self.texto_iteraciones.pack(fill = "both", expand = True, padx = 5, pady = 5)

        # Pestaña GRA
        self.pestanas_resultados.add("Gráfica")
        self.marco_grafica = ctk.CTkFrame(self.pestanas_resultados.tab("Gráfica"))
        self.marco_grafica.pack(fill = "both", expand = True, padx = 5, pady = 5)

        # Botón exportar PDF
        btn_exportar = ctk.CTkButton(
            marco_derecho,
            text = "📄 Exportar a PDF",
            command = self._exportar_pdf,
            height = 35,
            fg_color = "orange",
            hover_color = "darkorange"
        )
        btn_exportar.pack(fill = "x", padx = 10, pady = (0, 10))

    # Crea las entradas para la FO.
    def _crear_entradas_objetivo(self):

        # Limpiar entradas existentes
        for widget in self.marco_entradas_obj.winfo_children():
            widget.destroy()

        self.entradas_obj = []

        for i in range(self.num_vars):
            marco = ctk.CTkFrame(self.marco_entradas_obj)
            marco.pack(side = "left", padx = 5)

            entrada = ctk.CTkEntry(marco, width = 60, placeholder_text = "0")
            entrada.pack(side = "left", padx = 2)

            etiqueta = ctk.CTkLabel(marco, text = f"x{i + 1}")
            etiqueta.pack(side = "left", padx = 2)

            if i < self.num_vars - 1:
                ctk.CTkLabel(marco, text = "+").pack(side = "left", padx = 2)

            self.entradas_obj.append(entrada)

    # Actualiza el número de variables
    def _actualizar_num_variables(self):

        try:
            nuevo_num_vars = int(self.entrada_num_vars.get())

            if nuevo_num_vars < 2:
                messagebox.showerror("Error", "Debe haber al menos 2 variables")
                return

            if nuevo_num_vars > 10:
                messagebox.showerror("Error", "Máximo 10 variables permitidas")
                return

            self.num_vars = nuevo_num_vars
            self._crear_entradas_objetivo()

            # Actualizar restricciones existentes
            for fila in self.filas_restriccion:
                fila.destroy()
            self.filas_restriccion = []

            messagebox.showinfo("Éxito", f"Número de variables actualizado a {nuevo_num_vars}")

        except ValueError:
            messagebox.showerror("Error", "Ingrese un número válido")

    # Agrega una nueva restricción
    def _agregar_restriccion(self):
      
        num_fila = len(self.filas_restriccion) + 1
        fila_restriccion = FilaRestriccion(
            self.scroll_restricciones,
            self.num_vars,
            num_fila,
            self._eliminar_restriccion
        )
        fila_restriccion.pack(fill = "x", pady = 5)
        self.filas_restriccion.append(fila_restriccion)

    # Elimina una restricción
    def _eliminar_restriccion(self, fila_restriccion):

        if len(self.filas_restriccion) <= 1:
            messagebox.showwarning("Advertencia", "Debe haber al menos una restricción")
            return

        self.filas_restriccion.remove(fila_restriccion)
        fila_restriccion.destroy()

        # Renumerar restricciones
        for i, fila in enumerate(self.filas_restriccion):
            fila.num_fila = i + 1
            # Actualizar etiqueta
            for widget in fila.marco.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text").startswith("R"):
                    widget.configure(text = f"R{i + 1}:")
                    break

    # Limpia todos los campos.  
    def _limpiar_todo(self):
    
        # Limpiar función objetivo
        for entrada in self.entradas_obj:
            entrada.delete(0, "end")

        # Limpiar restricciones
        for fila in self.filas_restriccion:
            fila.destroy()
        self.filas_restriccion = []

        # Limpiar resultados
        self.texto_solucion.delete("1.0", "end")
        self.texto_iteraciones.delete("1.0", "end")

        # Limpiar gráfica
        for widget in self.marco_grafica.winfo_children():
            widget.destroy()

    def _resolver_problema(self):

        try:
            # Obtener tipo de optimización
            tipo_opt = "max" if self.var_tipo_opt.get() == "Maximizar" else "min"

            # Obtener coeficientes de FO
            c = np.array([float(e.get() or "0") for e in self.entradas_obj])

            # Verificar que hay restricciones
            if len(self.filas_restriccion) == 0:
                messagebox.showerror("Error", "Debe agregar al menos una restricción")
                return

            # Obtener restricciones
            lista_A = []
            lista_b = []
            tipos_desigualdad = []

            for fila in self.filas_restriccion:
                restriccion = fila.obtener_restriccion()
                if restriccion is None:
                    messagebox.showerror("Error", "Hay valores inválidos en las restricciones")
                    return

                coefs, desig, rhs = restriccion
                lista_A.append(coefs)
                lista_b.append(rhs)
                tipos_desigualdad.append(desig)

            A = np.array(lista_A)
            b = np.array(lista_b)

            # Validar que b >= 0
            if np.any(b < 0):
                messagebox.showerror("Error", "Los valores RHS deben ser no negativos")
                return

            # Resolver problema
            self.texto_solucion.delete("1.0", "end")
            self.texto_solucion.insert("1.0", "Resolviendo...\n")
            self.raiz.update()

            resultados = self.solver.resolver(c, A, b, tipos_desigualdad, tipo_opt)

            # Mostrar resultados
            self._mostrar_resultados(resultados, c, A, b, tipos_desigualdad, tipo_opt)

        except Exception as e:
            messagebox.showerror("Error", f"Error al resolver: {str(e)}")
            import traceback
            traceback.print_exc()

    # Muestra los resultados de la solución
    def _mostrar_resultados(self, resultados, c, A, b, tipos_desigualdad, tipo_opt):
    
        # Limpiar textos
        self.texto_solucion.delete("1.0", "end")
        self.texto_iteraciones.delete("1.0", "end")

        # Mostrar solución
        texto_solucion = "=" * 60 + "\n"
        texto_solucion += "RESULTADOS DE LA SOLUCIÓN\n"
        texto_solucion += "=" * 60 + "\n\n"

        # Estado
        mapa_estado = {
            'optimal': '✓ SOLUCIÓN ÓPTIMA ENCONTRADA',
            'unbounded': '⚠ PROBLEMA NO ACOTADO',
            'infeasible': '✗ PROBLEMA NO FACTIBLE',
            'error': '✗ ERROR EN EL CÁLCULO'
        }

        texto_solucion += f"Estado: {mapa_estado.get(resultados['status'], 'Desconocido')}\n\n"

        if resultados['status'] == 'optimal':
            texto_solucion += "Valores de las variables:\n"
            texto_solucion += "-" * 40 + "\n"

            for i, val in enumerate(resultados['solution']):
                nombre_var = f"x{i + 1}"
                texto_solucion += f"  {nombre_var} = {val:.6f}\n"

            texto_solucion += "\n"
            texto_solucion += f"Valor óptimo de Z: {resultados['optimal_value']:.6f}\n"

        elif resultados['status'] == 'unbounded':
            texto_solucion += "El problema no tiene cota superior/inferior.\n"
            texto_solucion += "La función objetivo puede crecer indefinidamente.\n"

        elif resultados['status'] == 'infeasible':
            texto_solucion += "No existe solución factible.\n"
            texto_solucion += "Las restricciones son contradictorias.\n"

        self.texto_solucion.insert("1.0", texto_solucion)

        # Mostrar iteraciones
        texto_iteraciones = ""
        for dato_iteracion in resultados['iterations']:
            texto_iteraciones += self.solver.formatear_tableau(dato_iteracion) + "\n\n"

        self.texto_iteraciones.insert("1.0", texto_iteraciones)

        # Graficar (solo para 2 variables)
        if len(c) == 2:
            self._graficar_solucion(c, A, b, tipos_desigualdad, resultados, tipo_opt)

    # Genera y muestra la gráfica
    def _graficar_solucion(self, c, A, b, tipos_desigualdad, resultados, tipo_opt):

        # Limpiar la GRAF
        for widget in self.marco_grafica.winfo_children():
            widget.destroy()

        try:
            # Crear GRAF
            solucion = resultados['solution'] if resultados['status'] == 'optimal' else None
            valor_optimo = resultados['optimal_value'] if resultados['status'] == 'optimal' else None

            # Guardar GRAF
            self.ruta_grafica_actual = os.path.join(tempfile.gettempdir(), "lp_plot.png")

            fig = self.graficador.graficar_problema(
                c, A, b, tipos_desigualdad,
                solucion, valor_optimo, tipo_opt,
                ruta_guardado=self.ruta_grafica_actual
            )

            # Mostrar en la interfaz
            lienzo = FigureCanvasTkAgg(fig, master=self.marco_grafica)
            lienzo.draw()
            lienzo.get_tk_widget().pack(fill = "both", expand = True)

            plt.close(fig)

        except Exception as e:
            etiqueta_error = ctk.CTkLabel(
                self.marco_grafica,
                text = f"Error al generar gráfica:\n{str(e)}",
                text_color = "red"
            )
            etiqueta_error.pack(pady = 20)

    # Exporta los resultados a PDF
    def _exportar_pdf(self):

        if not hasattr(self.solver, 'solucion') or self.solver.solucion is None:
            messagebox.showwarning("Advertencia", "Primero debe resolver un problema")
            return

        try:
            nombre_archivo = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile="solucion_PL.pdf"
            )

            if not nombre_archivo:
                return

            # Obtener datos del problema
            c = np.array([float(e.get() or "0") for e in self.entradas_obj])

            lista_A = []
            lista_b = []
            tipos_desigualdad = []

            for fila in self.filas_restriccion:
                coefs, desig, rhs = fila.obtener_restriccion()
                lista_A.append(coefs)
                lista_b.append(rhs)
                tipos_desigualdad.append(desig)

            A = np.array(lista_A)
            b = np.array(lista_b)

            tipo_opt = "Maximizar" if self.var_tipo_opt.get() == "Maximizar" else "Minimizar"

            datos_problema = {
                'c': c,
                'A': A,
                'b': b,
                'inequality_types': tipos_desigualdad,
                'optimization_type': tipo_opt
            }

            resultados = {
                'status': self.solver.estado,
                'solution': self.solver.solucion,
                'optimal_value': self.solver.valor_optimo,
                'iterations': self.solver.iteraciones,
                'variables': self.solver.variables
            }

            # Exportar a PDF
            self.exportador_pdf.exportar_resultados(
                nombre_archivo,
                datos_problema,
                resultados,
                ruta_grafica=self.ruta_grafica_actual if len(c) == 2 else None
            )

            messagebox.showinfo("Éxito", f"PDF exportado exitosamente:\n{nombre_archivo}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar PDF:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def ejecutar(self):
        self.raiz.mainloop()


def principal():
    app = AplicacionPL()
    app.ejecutar()


if __name__ == "__main__":
    principal()