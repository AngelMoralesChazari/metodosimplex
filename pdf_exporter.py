import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from typing import Dict, List
import os


class ExportadorPDF:
    def __init__(self):
        self.estilos = getSampleStyleSheet()
        self._configurar_estilos_personalizados()
        
    def _configurar_estilos_personalizados(self):
        self.estilos.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.estilos['Title'],
            fontSize=18,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Subtítulo
        self.estilos.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.estilos['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#2ca02c'),
            spaceAfter=10
        ))
        
        # Texto normal
        self.estilos.add(ParagraphStyle(
            name='CustomBody',
            parent=self.estilos['BodyText'],
            fontSize=11,
            spaceAfter=8
        ))
    
    def exportar_resultados(self, nombre_archivo: str, datos_problema: Dict, resultados: Dict, 
                            ruta_grafica: str = None):
        
        doc = SimpleDocTemplate(nombre_archivo, pagesize = letter, topMargin = 0.75*inch, bottomMargin = 0.75*inch, leftMargin = 0.75*inch, rightMargin = 0.75*inch)
        
        # Lista de elementos del documento
        historia = []
        
        # Título
        titulo = Paragraph("Solución de Problema de Programación Lineal", self.estilos['CustomTitle'])
        historia.append(titulo)
        historia.append(Spacer(1, 0.2*inch))
        
        # Fecha
        texto_fecha = f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        historia.append(Paragraph(texto_fecha, self.estilos['CustomBody']))
        historia.append(Spacer(1, 0.3*inch))
        
        # Sección: Problema planteado
        historia.append(Paragraph("1. Problema Planteado", self.estilos['CustomHeading']))
        historia.append(Spacer(1, 0.1*inch))
        
        # Función objetivo
        tipo_objetivo = datos_problema['optimization_type'].capitalize()
        funcion_objetivo = self._formatear_funcion_objetivo(datos_problema['c'], datos_problema['optimization_type'])
        historia.append(Paragraph(f"<b>{tipo_objetivo}:</b> {funcion_objetivo}", self.estilos['CustomBody']))
        historia.append(Spacer(1, 0.1*inch))
        
        # Restricciones
        historia.append(Paragraph("<b>Sujeto a:</b>", self.estilos['CustomBody']))
        restricciones = self._formatear_restricciones(datos_problema['A'], datos_problema['b'], datos_problema['inequality_types'])
        
        for restriccion in restricciones:
            historia.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{restriccion}", self.estilos['CustomBody']))
        
        historia.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;xᵢ ≥ 0 para todo i", self.estilos['CustomBody']))
        historia.append(Spacer(1, 0.3*inch))
        
        # Sección: Resultados
        historia.append(Paragraph("2. Resultados", self.estilos['CustomHeading']))
        historia.append(Spacer(1, 0.1*inch))
        
        # Estado de la solución
        texto_estado = self._obtener_texto_estado(resultados['status'])
        historia.append(Paragraph(f"<b>Estado:</b> {texto_estado}", self.estilos['CustomBody']))
        
        if resultados['status'] == 'optimal':
            # Solución óptima
            texto_solucion = self._formatear_solucion(resultados['solution'], resultados['variables'])
            historia.append(Paragraph(f"<b>Solución óptima:</b>", self.estilos['CustomBody']))
            for linea_solucion in texto_solucion:
                historia.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{linea_solucion}", self.estilos['CustomBody']))
            
            # Valor óptimo
            historia.append(Paragraph(f"<b>Valor óptimo de Z:</b> {resultados['optimal_value']:.4f}", self.estilos['CustomBody']))
        
        historia.append(Spacer(1, 0.3*inch))
        
        # Gráfica (si existe)
        if ruta_grafica and os.path.exists(ruta_grafica):
            historia.append(PageBreak())
            historia.append(Paragraph("3. Representación Gráfica", self.estilos['CustomHeading']))
            historia.append(Spacer(1, 0.2*inch))
            
            # Redimensionar imagen para que quepa en la página
            imagen = Image(ruta_grafica, width = 6*inch, height = 4.8*inch)
            historia.append(imagen)
            historia.append(Spacer(1, 0.3*inch))
        
        # Iteraciones del Simplex
        if resultados['iterations']:
            historia.append(PageBreak())
            historia.append(Paragraph("4. Iteraciones del Método Simplex", self.estilos['CustomHeading']))
            historia.append(Spacer(1, 0.2*inch))
            
            for datos_iteracion in resultados['iterations']:
                # Título de iteración
                fase = datos_iteracion.get('phase', '')
                num_iteracion = datos_iteracion['iteration']
                
                if fase:
                    titulo_iteracion = f"{fase} - Iteración {num_iteracion}"
                else:
                    titulo_iteracion = f"Iteración {num_iteracion}"
                    
                historia.append(Paragraph(titulo_iteracion, self.estilos['Heading2']))
                historia.append(Spacer(1, 0.1*inch))
                
                # Tabla Simplex
                datos_tabla = self._crear_tabla_simplex(datos_iteracion)
                
                if datos_tabla:
                    tabla = Table(datos_tabla, hAlign='LEFT')
                    tabla.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                    ]))
                    
                    historia.append(tabla)
                    historia.append(Spacer(1, 0.2*inch))
        
        # Generar PDF
        doc.build(historia)
        
    def _formatear_funcion_objetivo(self, c: np.ndarray, tipo_opt: str) -> str:
        terminos = []
        for i, coef in enumerate(c):
            if abs(coef) < 1e-10:
                continue
                
            if i == 0:
                if coef < 0:
                    terminos.append(f"{coef:.2f}x<sub>{i+1}</sub>")
                else:
                    terminos.append(f"{coef:.2f}x<sub>{i+1}</sub>")
            else:
                if coef < 0:
                    terminos.append(f"- {abs(coef):.2f}x<sub>{i+1}</sub>")
                else:
                    terminos.append(f"+ {coef:.2f}x<sub>{i+1}</sub>")
        
        return "Z = " + " ".join(terminos)
    
    def _formatear_restricciones(self, A: np.ndarray, b: np.ndarray, tipos_desigualdad: List[str]) -> List[str]:
        
        restricciones = []
        
        for i in range(len(A)):
            terminos = []
            for j, coef in enumerate(A[i]):
                if abs(coef) < 1e-10:
                    continue
                    
                if j == 0:
                    if coef < 0:
                        terminos.append(f"{coef:.2f}x<sub>{j+1}</sub>")
                    else:
                        terminos.append(f"{coef:.2f}x<sub>{j+1}</sub>")
                else:
                    if coef < 0:
                        terminos.append(f"- {abs(coef):.2f}x<sub>{j+1}</sub>")
                    else:
                        terminos.append(f"+ {coef:.2f}x<sub>{j+1}</sub>")
            
            restriccion = " ".join(terminos) + f" {tipos_desigualdad[i]} {b[i]:.2f}"
            restricciones.append(restriccion)
        
        return restricciones
    
    def _formatear_solucion(self, solucion: np.ndarray, variables: List[str]) -> List[str]:
        lineas = []
        for i, valor in enumerate(solucion):
            nombre_var = variables[i] if i < len(variables) else f'x{i+1}'
            lineas.append(f"{nombre_var} = {valor:.4f}")
        
        return lineas
    
    def _obtener_texto_estado(self, estado: str) -> str:
        mapa_estado = {
            'optimal': 'Solución óptima encontrada',
            'unbounded': 'Problema no acotado',
            'infeasible': 'Problema no factible (sin solución)',
            'error': 'Error en el cálculo'
        }
        
        return mapa_estado.get(estado, 'Desconocido')
    
    def _crear_tabla_simplex(self, datos_iteracion: Dict) -> List[List]:
        tableau = datos_iteracion['tableau']
        variables_basicas = datos_iteracion['basic_vars']
        n_vars = datos_iteracion['n_original_vars']
        
        # Encabezados
        encabezados = ['VB']
        for i in range(n_vars):
            encabezados.append(f'x{i+1}')
        
        # Variables de holgura/exceso/artificiales
        n_holgura = tableau.shape[1] - n_vars - 1
        for i in range(n_holgura):
            encabezados.append(f's{i+1}')
        
        encabezados.append('RHS')
        
        # Crear filas
        datos_tabla = [encabezados]
        
        # Filas de restricciones
        for i in range(len(variables_basicas)):
            fila = [variables_basicas[i]]
            for j in range(tableau.shape[1]):
                fila.append(f"{tableau[i, j]:.2f}")
            datos_tabla.append(fila)
        
        # Fila Z
        fila_z = ['Z']
        for j in range(tableau.shape[1]):
            fila_z.append(f"{tableau[-1, j]:.2f}")
        datos_tabla.append(fila_z)
        
        return datos_tabla
