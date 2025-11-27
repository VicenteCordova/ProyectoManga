import os
from pdf2image import convert_from_path, convert_from_bytes
from django.core.files.base import ContentFile
from io import BytesIO
from .models import Panel

def process_chapter_files(chapter, uploaded_files):
    """
    Procesa una lista de archivos (Imágenes o PDFs).
    Si es imagen: La guarda directamente.
    Si es PDF: Lo convierte a imágenes y guarda cada página como un Panel.
    """
    # Calculamos la página de inicio para no sobrescribir si ya hay paneles
    start_page = chapter.panels.count() + 1
    
    for file in uploaded_files:
        filename = file.name.lower()
        
        # CASO 1: Es un PDF
        if filename.endswith('.pdf'):
            try:
                # Convertimos el PDF a imágenes en memoria
                images = convert_from_bytes(file.read())
                
                for i, image in enumerate(images):
                    # Convertir imagen PIL a bytes para que Django la entienda
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format='JPEG', quality=85)
                    
                    # Nombre único para cada página
                    file_name = f"pdf_page_{start_page + i}.jpg"
                    
                    # Crear el objeto Panel
                    Panel.objects.create(
                        chapter=chapter,
                        page_number=start_page + i,
                        image=ContentFile(img_byte_arr.getvalue(), name=file_name)
                    )
                # Actualizamos el contador de páginas
                start_page += len(images)
                
            except Exception as e:
                print(f"Error procesando PDF: {e}")
                # Aquí podrías agregar un log o lanzar una excepción controlada
                
        # CASO 2: Es una Imagen normal (JPG, PNG, etc.)
        else:
            Panel.objects.create(
                chapter=chapter,
                page_number=start_page,
                image=file
            )
            start_page += 1