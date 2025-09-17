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

## 📦 Requisitos
- Python **3.10+** (recomendado 3.10 o 3.11)  
- Dependencias:  
  ```txt
  PySide6>=6.5
