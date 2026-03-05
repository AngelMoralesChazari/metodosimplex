import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from typing import List, Tuple, Optional
import matplotlib
matplotlib.use('Agg')


class GraficadorPL:    
    def __init__(self):
        self.figura = None
        self.ejes = None
        
    def graficar_problema(self, c: np.ndarray, A: np.ndarray, b: np.ndarray,
                          tipos_desigualdad: List[str], solucion: Optional[np.ndarray] = None,
                          valor_optimo: Optional[float] = None,
                          tipo_optimizacion: str = 'max',
                          ruta_guardado: Optional[str] = None) -> plt.Figure:
        
        if len(c) != 2:
            raise ValueError("Este método solo funciona para problemas de 2 variables")
            
        # Crear figura
        self.figura, self.ejes = plt.subplots(figsize=(10, 8))
        
        # Encontrar región factible
        vertices = self._encontrar_region_factible(A, b, tipos_desigualdad)
        
        if len(vertices) == 0:
            self.ejes.text(0.5, 0.5, 'Región factible vacía', ha = 'center', va = 'center', fontsize = 16, color = 'red')
            self.ejes.set_xlim([0, 10])
            self.ejes.set_ylim([0, 10])
        else:
            # Graficar región factible
            self._graficar_region_factible(vertices)
            
            # Graficar restricciones
            self._graficar_restricciones(A, b, tipos_desigualdad)
            
            # Graficar función objetivo
            if solucion is not None:
                self._graficar_funcion_objetivo(c, valor_optimo, tipo_optimizacion)
                
                # Marcar punto óptimo
                self.ejes.plot(solucion[0], solucion[1], 'r*', markersize = 20, label = f'Punto óptimo ({solucion[0]:.2f}, {solucion[1]:.2f})', zorder = 5)
                
            # Marcar vértices
            for i, vertice in enumerate(vertices):
                self.ejes.plot(vertice[0], vertice[1], 'ko', markersize=8, zorder=4)
                self.ejes.annotate(f'  ({vertice[0]:.1f}, {vertice[1]:.1f})', xy = vertice, fontsize = 9, color = 'blue')
        
        # Configurar ejes
        self.ejes.set_xlabel('x₁', fontsize=12)
        self.ejes.set_ylabel('x₂', fontsize=12)
        
        titulo = f'Problema de Programación Lineal\n'
        if tipo_optimizacion.lower() == 'max':
            titulo += f'Maximizar Z = {c[0]:.1f}x₁ + {c[1]:.1f}x₂'
        else:
            titulo += f'Minimizar Z = {c[0]:.1f}x₁ + {c[1]:.1f}x₂'
            
        if valor_optimo is not None:
            titulo += f'\nZ* = {valor_optimo:.2f}'
            
        self.ejes.set_title(titulo, fontsize=14, fontweight='bold')
        self.ejes.grid(True, alpha=0.3)
        self.ejes.legend(loc='best', fontsize=10)
        
        # Ajustar límites
        self.ejes.set_xlim(left=-0.5)
        self.ejes.set_ylim(bottom=-0.5)
        
        plt.tight_layout()
        
        # Guardar si se especifica ruta
        if ruta_guardado:
            plt.savefig(ruta_guardado, dpi=150, bbox_inches='tight')
            
        return self.figura
    
    def _encontrar_region_factible(self, A: np.ndarray, b: np.ndarray, tipos_desigualdad: List[str]) -> List[Tuple[float, float]]:
        
        m, n = A.shape
        vertices = []
        
        # Añadir restricciones de no negatividad
        restricciones = []
        for i in range(m):
            restricciones.append((A[i], b[i], tipos_desigualdad[i]))
        
        # Límites del espacio de búsqueda
        max_valor = max(b) * 2 if max(b) > 0 else 10
        
        # Restricciones de no negatividad
        restricciones.append((np.array([1, 0]), 0, '>='))  # x1 >= 0
        restricciones.append((np.array([0, 1]), 0, '>='))  # x2 >= 0
        
        # Encontrar intersecciones de cada par de restricciones
        for i in range(len(restricciones)):
            for j in range(i + 1, len(restricciones)):
                punto = self._intersectar_rectas(restricciones[i], restricciones[j])
                
                if punto is not None:
                    # Verificar si el punto satisface todas las restricciones
                    if self._es_factible(punto, restricciones):
                        # Verificar si ya tenemos este vértice
                        es_duplicado = False
                        for v in vertices:
                            if np.allclose(punto, v, atol=1e-6):
                                es_duplicado = True
                                break
                        
                        if not es_duplicado:
                            vertices.append(punto)
        
        if len(vertices) > 2:
            vertices = self._ordenar_vertices(vertices)
            
        return vertices
    
    def _intersectar_rectas(self, restriccion1: Tuple, restriccion2: Tuple) -> Optional[np.ndarray]:
        a1, b1, _ = restriccion1
        a2, b2, _ = restriccion2
        
        matriz_A = np.array([a1, a2])
        vector_b = np.array([b1, b2])
        
        try:
            punto = np.linalg.solve(matriz_A, vector_b)
            return punto
        except np.linalg.LinAlgError:
            return None
    
    def _es_factible(self, punto: np.ndarray, restricciones: List[Tuple]) -> bool:
        for a, b, tipo_desig in restricciones:
            valor = np.dot(a, punto)
            
            if tipo_desig == '<=':
                if valor > b + 1e-6:
                    return False
            elif tipo_desig == '>=':
                if valor < b - 1e-6:
                    return False
            elif tipo_desig == '=':
                if abs(valor - b) > 1e-6:
                    return False
                    
        return True
    
    def _ordenar_vertices(self, vertices: List[np.ndarray]) -> List[np.ndarray]:
        
        # Calcular centroide
        centroide = np.mean(vertices, axis=0)
        
        # Calcular ángulos desde el centroide
        def angulo_desde_centroide(vertice):
            return np.arctan2(vertice[1] - centroide[1], vertice[0] - centroide[0])
        
        # Ordenar por ángulo
        vertices_ordenados = sorted(vertices, key=angulo_desde_centroide)
        
        return vertices_ordenados
    
    def _graficar_region_factible(self, vertices: List[np.ndarray]):
        if len(vertices) < 3:
            return
            
        # Crear polígono
        poligono = Polygon(vertices, alpha = 0.3, facecolor = 'lightblue', edgecolor = 'blue', linewidth = 2, label = 'Región factible')
        self.ejes.add_patch(poligono)
    
    def _graficar_restricciones(self, A: np.ndarray, b: np.ndarray, tipos_desigualdad: List[str]):
        limites_x = self.ejes.get_xlim()
        limites_y = self.ejes.get_ylim()
        
        # Determinar rango de graficación
        x_max = max(limites_x[1], max(b) * 1.5 if max(b) > 0 else 10)
        y_max = max(limites_y[1], max(b) * 1.5 if max(b) > 0 else 10)
        
        for i in range(len(A)):
            a1, a2 = A[i]
            bi = b[i]
            desig = tipos_desigualdad[i]
        
            if abs(a2) > 1e-10:
                x = np.array([0, x_max])
                y = (bi - a1 * x) / a2
            
            else:
                x = np.array([bi/a1, bi/a1])
                y = np.array([0, y_max])
            
            # Determinar estilo de línea según el tipo
            if desig == '<=':
                estilo_linea = '--'
                etiqueta = f'{a1:.1f}x₁ + {a2:.1f}x₂ ≤ {bi:.1f}'
            
            elif desig == '>=':
                estilo_linea = '-.'
                etiqueta = f'{a1:.1f}x₁ + {a2:.1f}x₂ ≥ {bi:.1f}'
            
            else:  # '='
                estilo_linea = '-'
                etiqueta = f'{a1:.1f}x₁ + {a2:.1f}x₂ = {bi:.1f}'
            
            self.ejes.plot(x, y, linestyle=estilo_linea, linewidth=1.5, alpha=0.7, label=etiqueta)
        
        # Actualizar límites
        self.ejes.set_xlim([0, x_max])
        self.ejes.set_ylim([0, y_max])
    
    def _graficar_funcion_objetivo(self, c: np.ndarray, valor_z: float, tipo_optimizacion: str):
        
        limites_x = self.ejes.get_xlim()
        
        # Línea: c1*x1 + c2*x2 = valor_z
        if abs(c[1]) > 1e-10:
            x = np.linspace(limites_x[0], limites_x[1], 100)
            y = (valor_z - c[0] * x) / c[1]
            
            self.ejes.plot(x, y, 'r--', linewidth=2, alpha=0.7, 
                       label=f'Función objetivo (Z = {valor_z:.2f})')
        else:
            # Línea vertical
            x_valor = valor_z / c[0]
            limites_y = self.ejes.get_ylim()
            self.ejes.plot([x_valor, x_valor], [limites_y[0], limites_y[1]], 'r--', 
                       linewidth=2, alpha=0.7, 
                       label=f'Función objetivo (Z = {valor_z:.2f})')
