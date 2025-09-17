# ⏱️ Laboura Time

Aplicación de escritorio en **Python + PySide6 (Qt)** para cronometrar tiempo por **secciones** y **subdivisiones**, con histórico filtrable y exportación a CSV.  

## ✨ Funcionalidades
- Cronómetro por secciones y subdivisiones.  
- Histórico de sesiones con filtros por:
  - Rango de fechas
  - Sección y subdivisión
  - Agrupación (día / semana / mes)
- Edición y borrado de sesiones.  
- Exportación de:
  - Totales por sección/subdivisión → CSV  
  - Sesiones individuales → CSV  
- Tema oscuro moderno.  
- Persistencia automática en `data.json` (ignorado en el repositorio).  

---

## 🖥️ Capturas
<p align="center">
  <img src="docs/s1-timer.png" alt="Timer tab" width="75%"><br>
  <em>Timer por secciones y subdivisiones</em>
</p>

<p align="center">
  <img src="docs/s2-history.png" alt="History with filters" width="75%"><br>
  <em>Histórico con filtros y agrupación</em>
</p>

<p align="center">
  <img src="docs/s3-edit-dialog.png" alt="Edit session dialog" width="33%"><br>
  <em>Diálogo para editar una sesión</em>
</p>

---

## 📦 Requisitos
- Python **3.10+** (recomendado 3.10 o 3.11)  
- Dependencias:  
  ```txt
  PySide6>=6.5

---
## 🔧 Installation

```bash
# 1) (opcional) crear y activar entorno virtual en Windows
python -m venv .venv
.venv\Scripts\activate

# 2) instalar dependencias
pip install -r requirements.txt
```



