# 🎌 MangaVerse - Plataforma de Gestión de Manga (Cyberpunk Edition)

**MangaVerse** es una aplicación web moderna ("Full-Stack") desarrollada como Evaluación Final de Integración de Programación. Permite a los usuarios subir, gestionar y leer mangas online con una experiencia de usuario fluida y una estética inmersiva.

## Integrantes (Guild CloudCode)
* **Vicente Córdova**
* **José González** 
* **Pedro Luengo** 
---

## Valor Agregado e Innovación
Este proyecto supera los requisitos básicos de un CRUD, implementando tecnologías avanzadas:

### 1.  Experiencia de Usuario (UX/UI) "Nivel Dios"
* **Diseño Cyberpunk/Neon:** Interfaz oscura con efectos de brillo (Glow), tarjetas con desenfoque (Glassmorphism) y animaciones CSS suaves.
* **Fondo Animado:** Implementación de Canvas JS para un fondo de partículas estelar que no afecta el rendimiento.
* **Responsive Design:** Adaptable a móviles y escritorio.

### 2.  Funcionalidades Avanzadas
* **Dashboard de Creador:** Perfil de usuario con **Gráficos en tiempo real (Chart.js)** que comparan el rendimiento de las obras (Likes vs Capítulos).
* **Subida Híbrida Inteligente:** Sistema de carga de capítulos mediante **Arrastrar y Soltar (Dropzone.js)** con soporte AJAX.
* **Soporte PDF Nativo:** Integración con `pdf2image` para descomponer automáticamente archivos `.pdf` en imágenes individuales para el lector web.
* **Sistema de Favoritos Asíncrono:** Permite dar "Like" y agregar a la biblioteca sin recargar la página (Fetch API).
* **Buscador en Tiempo Real:** Filtrado instantáneo de obras en el perfil del creador.

---

## Stack Tecnológico
* **Backend:** Python 3.10+ / Django 5.x
* **Base de Datos:** **MariaDB** (vía XAMPP).
    * *Justificación:* Se eligió MariaDB para garantizar la compatibilidad con el entorno de desarrollo local y simular un despliegue en servidor clásico LAMP/WAMP.
* **Frontend:** Bootstrap 5 + CSS3 Custom Properties + JavaScript Vanilla.
* **Librerías Clave:**
    * `pdf2image`: Procesamiento de archivos PDF.
    * `mysqlclient`: Conector de base de datos optimizado.
    * `Chart.js`: Visualización de datos.
    * `Dropzone`: Carga de archivos moderna.

---

## Guía de Instalación y Ejecución (Comandos de Consola)

Sigue estos pasos estrictos en tu terminal para levantar el proyecto.

### Prerrequisitos
1.  Python 3.10 o superior instalado.
2.  **XAMPP** instalado y corriendo (Asegúrate de que Apache y MySQL estén en verde/Start).
3.  **Poppler** instalado (Requerido para procesar PDFs en Windows).
    * *Descargar y agregar la carpeta `bin` al PATH del sistema.*

### Paso 1: Clonar el Repositorio
Abre tu terminal (CMD, PowerShell o Git Bash) y ejecuta:
```bash
git clone <URL_DEL_REPOSITORIO>
cd mangaverse