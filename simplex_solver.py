import numpy as np
from typing import List, Tuple, Dict, Optional
import copy


class SolucionadorSimplex:
    def __init__(self):
        self.iteraciones = [] 
        self.solucion = None
        self.valor_optimo = None
        self.estado = None  # 'optimal', 'unbounded', 'infeasible'
        self.variables = []
        self.variables_basicas = []
        
    def resolver(self, c: np.ndarray, A: np.ndarray, b: np.ndarray, 
                 tipos_desigualdad: List[str], tipo_optimizacion: str = 'max',
                 nombres_variables: List[str] = None) -> Dict:
       
       # Resetear estado
        self.iteraciones = []
        self.solucion = None
        self.valor_optimo = None
        self.estado = None
        
        # Convertir minimización a maximización
        if tipo_optimizacion.lower() == 'min':
            c = -c.copy()
            es_minimizacion_original = True
        else:
            c = c.copy()
            es_minimizacion_original = False
            
        # Guardar número de variables originales
        n_vars_originales = len(c)
        
        # Configurar nombres de variables
        if nombres_variables is None:
            self.variables = [f'x{i+1}' for i in range(n_vars_originales)]
        else:
            self.variables = nombres_variables.copy()
            
        # Determinar si necesitamos el método de dos fases o Gran M
        necesita_artificiales = any(desig in ['>=', '='] for desig in tipos_desigualdad)
        
        if necesita_artificiales:
            resultado = self._resolver_dos_fases(c, A, b, tipos_desigualdad)
        else:
            resultado = self._resolver_estandar(c, A, b, tipos_desigualdad)
            
        # Si es minimización, ajustar el valor óptimo
        if es_minimizacion_original and self.valor_optimo is not None:
            self.valor_optimo = -self.valor_optimo
            
        return {
            'status': self.estado,
            'solution': self.solucion,
            'optimal_value': self.valor_optimo,
            'iterations': self.iteraciones,
            'variables': self.variables
        }
    
    # Resuelve problema estándar con restricciones <= usando el método simplex
    def _resolver_estandar(self, c: np.ndarray, A: np.ndarray, b: np.ndarray, tipos_desigualdad: List[str]) -> bool:
        
        m, n = A.shape
        
        # Añadir variables de holgura
        contador_holgura = 0
        tableau = np.zeros((m + 1, n + m + 1))
        
        # Configurar restricciones
        for i in range(m):
            tableau[i, :n] = A[i]
            tableau[i, n + i] = 1  # Variable de holgura
            tableau[i, -1] = b[i]
            contador_holgura += 1
            
        # Configurar función objetivo (fila Z)
        tableau[-1, :n] = -c
        
        # Variables básicas iniciales (variables de holgura)
        self.variables_basicas = [f's{i+1}' for i in range(m)]
        
        # Guardar primera iteración
        self._guardar_iteracion(tableau, n, m, 0)
        
        # Ejecutar simplex
        iteration = 1
        while True:
            # Verificar optimalidad
            if np.all(tableau[-1, :-1] >= -1e-9):
                self.estado = 'optimal'
                self._extraer_solucion(tableau, n, m)
                return True
                
            # Seleccionar columna pivote (variable entrante) - regla de Bland
            columna_pivote = np.argmax(tableau[-1, :-1] < -1e-9)
            
            # Verificar si es no acotado
            if np.all(tableau[:-1, columna_pivote] <= 1e-9):
                self.estado = 'unbounded'
                return False
                
            # Seleccionar fila pivote (variable saliente) - razón mínima
            razones = []
            for i in range(m):
                if tableau[i, columna_pivote] > 1e-9:
                    razones.append(tableau[i, -1] / tableau[i, columna_pivote])
                else:
                    razones.append(np.inf)
                    
            fila_pivote = np.argmin(razones)
            
            # Actualizar variable básica
            if columna_pivote < n:
                self.variables_basicas[fila_pivote] = self.variables[columna_pivote]
            else:
                self.variables_basicas[fila_pivote] = f's{columna_pivote - n + 1}'
            
            # Realizar operación de pivoteo
            tableau = self._pivote(tableau, fila_pivote, columna_pivote)
            
            # Guardar iteración
            self._guardar_iteracion(tableau, n, m, iteration)
            iteration += 1
            
            # Límite de iteraciones para evitar bucles infinitos
            if iteration > 100:
                self.estado = 'error'
                return False
    
    # Resuelve problema con restricciones >= o = usando el método de dos fases
    def _resolver_dos_fases(self, c: np.ndarray, A: np.ndarray, b: np.ndarray, tipos_desigualdad: List[str]) -> bool:
                
        m, n = A.shape
        
        # Convertir todas las restricciones a forma estándar
        # y contar variables de holgura, exceso y artificiales
        vars_holgura = 0
        vars_exceso = 0
        vars_artificiales = 0
        posiciones_artificiales = []
        
        # Crear tableau extendido
        total_columnas = n  # Variables originales
        
        for desig in tipos_desigualdad:
            if desig == '<=':
                total_columnas += 1  # Variable de holgura
            elif desig == '>=':
                total_columnas += 2  # Variable de exceso + artificial
            elif desig == '=':
                total_columnas += 1  # Variable artificial
                
        total_columnas += 1  # Columna RHS
        
        # Crear tableau de Fase 1
        tableau_fase1 = np.zeros((m + 1, total_columnas))
        
        # Llenar tableau
        indice_columna = n
        columnas_artificiales = []
        
        for i in range(m):
            # Copiar coeficientes de variables originales
            tableau_fase1[i, :n] = A[i]
            
            # Añadir variables según el tipo de restricción
            if tipos_desigualdad[i] == '<=':
                tableau_fase1[i, indice_columna] = 1  # Variable de holgura
                self.variables_basicas.append(f's{vars_holgura + 1}')
                vars_holgura += 1
                indice_columna += 1
            elif tipos_desigualdad[i] == '>=':
                tableau_fase1[i, indice_columna] = -1  # Variable de exceso
                vars_exceso += 1
                indice_columna += 1
                tableau_fase1[i, indice_columna] = 1  # Variable artificial
                columnas_artificiales.append(indice_columna)
                self.variables_basicas.append(f'A{vars_artificiales + 1}')
                vars_artificiales += 1
                indice_columna += 1
            elif tipos_desigualdad[i] == '=':
                tableau_fase1[i, indice_columna] = 1  # Variable artificial
                columnas_artificiales.append(indice_columna)
                self.variables_basicas.append(f'A{vars_artificiales + 1}')
                vars_artificiales += 1
                indice_columna += 1
                
            # RHS
            tableau_fase1[i, -1] = b[i]
            
        # Función objetivo de Fase 1: minimizar suma de artificiales
        # (equivalente a maximizar -suma de artificiales)
        for col in columnas_artificiales:
            tableau_fase1[-1, col] = -1
            
        # Hacer filas de artificiales compatibles con la fila objetivo
        for i, var in enumerate(self.variables_basicas):
            if var.startswith('A'):
                # Encontrar columna de esta variable artificial
                for col in columnas_artificiales:
                    if tableau_fase1[i, col] == 1:
                        # Eliminar de la fila Z
                        tableau_fase1[-1] += tableau_fase1[i]
                        break
        
        # Guardar primera iteración de Fase 1
        self._guardar_iteracion(tableau_fase1, n, m, 0, phase='Fase 1')
        
        # Resolver Fase 1
        iteracion = 1
        while True:
            # Verificar optimalidad
            if np.all(tableau_fase1[-1, :-1] >= -1e-9):
                # Verificar si hay artificiales en la base con valor > 0
                if tableau_fase1[-1, -1] > 1e-6:
                    self.estado = 'infeasible'
                    return False
                break
                
            # Seleccionar columna pivote
            columna_pivote = np.argmax(tableau_fase1[-1, :-1] < -1e-9)
            
            # Verificar si es no acotado (no debería pasar en Fase 1)
            if np.all(tableau_fase1[:-1, columna_pivote] <= 1e-9):
                self.estado = 'infeasible'
                return False
                
            # Seleccionar fila pivote
            razones = []
            for i in range(m):
                if tableau_fase1[i, columna_pivote] > 1e-9:
                    razones.append(tableau_fase1[i, -1] / tableau_fase1[i, columna_pivote])
                else:
                    razones.append(np.inf)
                    
            fila_pivote = np.argmin(razones)
            
            # Actualizar variable básica
            if columna_pivote < n:
                self.variables_basicas[fila_pivote] = self.variables[columna_pivote]
            elif columna_pivote in columnas_artificiales:
                indice_artificial = columnas_artificiales.index(columna_pivote)
                self.variables_basicas[fila_pivote] = f'A{indice_artificial + 1}'
            else:
                # Es variable de holgura o exceso
                self.variables_basicas[fila_pivote] = f's{columna_pivote - n + 1}'
            
            # Realizar operación de pivoteo
            tableau_fase1 = self._pivote(tableau_fase1, fila_pivote, columna_pivote)
            
            # Guardar iteración
            self._guardar_iteracion(tableau_fase1, n, m, iteracion, phase='Fase 1')
            iteracion += 1
            
            if iteracion > 100:
                self.estado = 'error'
                return False
                
        # Iniciar Fase 2
        # Eliminar columnas de variables artificiales
        tableau_fase2 = np.delete(tableau_fase1, columnas_artificiales, axis=1)
        
        # Reemplazar función objetivo con la original
        tableau_fase2[-1, :] = 0
        tableau_fase2[-1, :n] = -c
        
        # Hacer que las variables básicas tengan 0 en la fila Z
        for i, var in enumerate(self.variables_basicas):
            if var in self.variables:
                indice_var = self.variables.index(var)
                if abs(tableau_fase2[-1, indice_var]) > 1e-9:
                    tableau_fase2[-1] -= tableau_fase2[-1, indice_var] * tableau_fase2[i]
        
        # Guardar primera iteración de Fase 2
        self._guardar_iteracion(tableau_fase2, n, m, 0, phase='Fase 2')
        
        # Resolver Fase 2
        iteracion = 1
        while True:
            # Verificar optimalidad
            if np.all(tableau_fase2[-1, :-1] >= -1e-9):
                self.estado = 'optimal'
                self._extraer_solucion(tableau_fase2, n, m)
                return True
                
            # Seleccionar columna pivote
            columna_pivote = np.argmax(tableau_fase2[-1, :-1] < -1e-9)
            
            # Verificar si es no acotado
            if np.all(tableau_fase2[:-1, columna_pivote] <= 1e-9):
                self.estado = 'unbounded'
                return False
                
            # Seleccionar fila pivote
            razones = []
            for i in range(m):
                if tableau_fase2[i, columna_pivote] > 1e-9:
                    razones.append(tableau_fase2[i, -1] / tableau_fase2[i, columna_pivote])
                else:
                    razones.append(np.inf)
                    
            fila_pivote = np.argmin(razones)
            
            # Actualizar variable básica
            if columna_pivote < n:
                self.variables_basicas[fila_pivote] = self.variables[columna_pivote]
            else:
                self.variables_basicas[fila_pivote] = f's{columna_pivote - n + 1}'
            
            # Realizar operación de pivoteo
            tableau_fase2 = self._pivote(tableau_fase2, fila_pivote, columna_pivote)
            
            # Guardar iteración
            self._guardar_iteracion(tableau_fase2, n, m, iteracion, phase='Fase 2')
            iteracion += 1
            
            if iteracion > 100:
                self.estado = 'error'
                return False
    
    # Realiza la operación de pivoteo en el tableau
    def _pivote(self, tableau: np.ndarray, fila_pivote: int, columna_pivote: int) -> np.ndarray:
        
        tableau = tableau.copy()
        elemento_pivote = tableau[fila_pivote, columna_pivote]
        
        # Dividir fila pivote por el elemento pivote
        tableau[fila_pivote] = tableau[fila_pivote] / elemento_pivote
        
        # Hacer ceros en la columna pivote excepto en la fila pivote
        for i in range(len(tableau)):
            if i != fila_pivote:
                multiplicador = tableau[i, columna_pivote]
                tableau[i] = tableau[i] - multiplicador * tableau[fila_pivote]
                
        return tableau
    
    # Guarda el estado del tableau en una iteración
    def _guardar_iteracion(self, tableau: np.ndarray, n_vars: int, n_restricciones: int, iteracion: int, phase: str = None):
        
        datos_iteracion = {
            'iteration': iteracion,
            'tableau': tableau.copy(),
            'basic_vars': self.variables_basicas.copy(),
            'n_original_vars': n_vars,
            'phase': phase
        }
        
        self.iteraciones.append(datos_iteracion)
    
    # Extrae la solución del tableau final.
    def _extraer_solucion(self, tableau: np.ndarray, n_vars: int, n_restricciones: int):
        
        # Inicializar solución
        self.solucion = np.zeros(n_vars)
        
        # Extraer valores de variables básicas
        for i, var in enumerate(self.variables_basicas):
            if var in self.variables:
                indice_var = self.variables.index(var)
                self.solucion[indice_var] = tableau[i, -1]
                
        # Valor óptimo de la función objetivo
        self.valor_optimo = tableau[-1, -1]
        
    # Formatea un tableau para mostrar como texto    
    def formatear_tableau(self, datos_iteracion: Dict) -> str:
        
        tableau = datos_iteracion['tableau']
        variables_basicas = datos_iteracion['basic_vars']
        n_vars = datos_iteracion['n_original_vars']
        phase = datos_iteracion.get('phase', '')
        
        lineas = []
        
        if phase:
            lineas.append(f"\n{phase} - Iteración {datos_iteracion['iteration']}")
        else:
            lineas.append(f"\nIteración {datos_iteracion['iteration']}")
            
        lineas.append("=" * 80)
        
        # Encabezados de columnas
        encabezado = "VB\t"
        for i in range(n_vars):
            encabezado += f"x{i+1}\t"
        for i in range(tableau.shape[1] - n_vars - 1):
            encabezado += f"s{i+1}\t"
        encabezado += "RHS"
        lineas.append(encabezado)
        lineas.append("-" * 80)
        
        # Filas de restricciones
        for i in range(len(variables_basicas)):
            fila = f"{variables_basicas[i]}\t"
            for j in range(tableau.shape[1]):
                fila += f"{tableau[i, j]:.2f}\t"
            lineas.append(fila)
            
        # Fila Z
        fila = "Z\t"
        for j in range(tableau.shape[1]):
            fila += f"{tableau[-1, j]:.2f}\t"
        lineas.append(fila)
        
        return "\n".join(lineas)
