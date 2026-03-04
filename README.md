# Método Simplex

Aplicación de escritorio para resolver problemas de **Programación Lineal** mediante el método simplex. Incluye interfaz gráfica, visualización de la región factible (2 variables) y exportación de resultados a PDF.

## Características

- **Resolución con simplex**: problemas de maximización y minimización.
- **Tipos de restricción**: ≤, ≥ e = (método de dos fases cuando hace falta).
- **Configuración flexible**: número de variables (2–10) y restricciones.
- **Visualización**: región factible, restricciones y punto óptimo para problemas con 2 variables.
- **Exportación a PDF**: problema planteado, resultados e iteraciones del simplex.

## Requisitos

- Python 3.8 o superior
- Dependencias:
  - `numpy`
  - `matplotlib`
  - `customtkinter`
  - `reportlab`

Instalación de dependencias:

```bash
pip install numpy matplotlib customtkinter reportlab
```

## Estructura del proyecto

| Archivo             | Descripción                                                  |
|---------------------|--------------------------------------------------------------|
| `main.py`           | Interfaz gráfica (CustomTkinter) y flujo principal.          |
| `simplex_solver.py` | Solver: simplex estándar y método de dos fases.              |
| `plotter.py`        | Gráfica de región factible y función objetivo (2 variables). |
| `pdf_exporter.py`   | Generación del informe en PDF.                               |

## Cómo ejecutar

Desde la raíz del proyecto:

```bash
python main.py
```

## Uso

1. Elige **Maximizar** o **Minimizar**.
2. Ajusta el **número de variables** y pulsa "Actualizar Variables".
3. Introduce los **coeficientes de la función objetivo** (Z).
4. Añade **restricciones** (coeficientes, tipo ≤/≥/= y término derecho).
5. Pulsa **RESOLVER** para ver la solución, las iteraciones del simplex y la gráfica (si hay 2 variables).
6. Usa **Exportar a PDF** para guardar el informe completo.
