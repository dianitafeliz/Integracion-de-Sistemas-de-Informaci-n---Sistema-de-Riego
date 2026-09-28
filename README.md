# Machine Learning Tools — Taller Segundo Corte

**Universidad Santo Tomás**
Facultad de Ingeniería en Tecnologías de la Información y las Comunicaciones
Programa de Ingeniería en Informática
Espacio Académico: Machine Learning Tools (74273 — Plan 4, Nivel IX)
Docente: Crisman Martinez B.
Ciclo: 2026-02

---

## 1. Descripción del proyecto

Este proyecto desarrolla el **Anexo N.3 — Taller de Algoritmos de Machine Learning** del Segundo Corte. Una empresa dispone de datos históricos de clientes, compras, visitas al sitio web, inversión publicitaria, productos y comportamiento de usuarios, y requiere modelos capaces de:

- Predecir el valor generado por un cliente (**regresión**).
- Determinar si un cliente realizará o no una compra (**clasificación binaria**).
- Clasificar nuevos clientes según su similitud con clientes históricos (**K-NN**).
- Clasificar clientes mediante reglas obtenidas de sus características (**Árbol de Decisión**).

Para ello se investigan, implementan y comparan cuatro algoritmos de aprendizaje supervisado:

| Algoritmo | Tipo | Uso en el caso |
|---|---|---|
| Regresión Lineal | Regresión | Predecir el valor generado por el cliente |
| Regresión Logística | Clasificación | Determinar compra / no compra |
| K-Nearest Neighbors (K-NN) | Clasificación | Clasificar clientes por similitud |
| Árbol de Decisión | Clasificación | Clasificar clientes mediante reglas |

## 2. Dataset

**Nombre:** Online Shoppers Purchasing Intention Dataset
**Fuente:** UCI Machine Learning Repository / Kaggle
**Enlace:** https://www.kaggle.com/datasets/henrysue/online-shoppers-intention
**Registros:** 12,330 sesiones de usuario
**Variable objetivo (clasificación):** `Revenue` (True/False — compró o no)
**Variable objetivo (regresión):** `PageValues` (usada como proxy del valor generado por el cliente, dado que el dataset no incluye un monto de venta directo; se documenta y justifica esta decisión en el desarrollo del taller)

### Variables principales

| Variable | Descripción |
|---|---|
| Administrative / Administrative_Duration | Páginas administrativas visitadas y tiempo en ellas |
| Informational / Informational_Duration | Páginas informativas visitadas y tiempo en ellas |
| ProductRelated / ProductRelated_Duration | Páginas de producto visitadas y tiempo en ellas |
| BounceRates / ExitRates | Comportamiento de navegación / abandono |
| PageValues | Valor promedio de páginas antes de una transacción |
| SpecialDay | Cercanía a una fecha especial |
| Month, Weekend | Temporalidad de la visita |
| OperatingSystems, Browser, Region, TrafficType | Datos técnicos y de canal (proxy de inversión publicitaria) |
| VisitorType | Nuevo / recurrente (comportamiento de usuario) |
| Revenue | Variable objetivo de clasificación |

## 3. Estructura del proyecto

```
├── README.md                  # Este archivo
├── data/
│   └── online_shoppers_intention.csv
├── notebooks/
│   ├── 01_eda.ipynb            # Análisis exploratorio de datos
│   ├── 02_regresion_lineal.ipynb
│   ├── 03_regresion_logistica.ipynb
│   ├── 04_knn.ipynb
│   ├── 05_arbol_decision.ipynb
│   └── 06_comparacion_modelos.ipynb
├── src/
│   ├── preprocessing.py        # Imputación, escalado, codificación
│   ├── models.py                # Entrenamiento de los 4 algoritmos
│   └── evaluation.py            # Métricas y validación cruzada
├── docs/
│   └── taller_ml_tools.docx     # Documento de entrega (Anexo N.4)
├── requirements.txt
└── video/
    └── url_video.txt            # URL del video (Anexo N.5)
```

## 4. Requisitos

- Python 3.10+
- pandas
- numpy
- scikit-learn
- matplotlib
- seaborn
- jupyter

Instalación:

```bash
pip install -r requirements.txt
```

## 5. Metodología (pipeline general)

1. **Carga y exploración de datos** (EDA): tipos de variable, valores nulos, distribución de clases.
2. **Ingeniería de datos**: imputación de valores faltantes, codificación de variables categóricas, escalado de características.
3. **División de datos**: entrenamiento / prueba (train_test_split), estratificado según la variable objetivo.
4. **Entrenamiento de modelos**: Regresión Lineal, Regresión Logística, K-NN y Árbol de Decisión.
5. **Validación cruzada (K-Fold)** y ajuste de hiperparámetros con GridSearchCV.
6. **Evaluación**:
   - Regresión: MAE, MSE, RMSE, R².
   - Clasificación: Accuracy, Precision, Recall, F1-score, ROC-AUC, PR-Curve.
7. **Comparación de modelos** y selección del umbral de decisión óptimo según el impacto de falsos positivos y falsos negativos.
8. **Conclusiones** y recomendaciones para producción (monitoreo, robustez, control de cambios en los datos).

## 6. Resultados

*(Se completa una vez ejecutados los notebooks)*

| Modelo | Métrica principal | Resultado |
|---|---|---|
| Regresión Lineal | R² | — |
| Regresión Logística | ROC-AUC | — |
| K-NN | F1-score | — |
| Árbol de Decisión | F1-score | — |

## 7. Autor

- **Nombre del estudiante:** _[Completar]_
- **Código:** _[Completar]_
- **Programa:** Ingeniería en Informática
- **Universidad Santo Tomás**

## 8. Referencias (APA 7)

Martinez Barrera, C. (2026). *Aula Virtual USTA. Machine Learning Tools*. Universidad Santo Tomás. Consultado en julio de 2026.

Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research*, 12, 2825-2830.

Sakar, C., & Kastro, Y. (2018). *Online Shoppers Purchasing Intention Dataset*. UCI Machine Learning Repository.
