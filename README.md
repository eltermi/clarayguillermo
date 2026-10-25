# Clara y Guillermo · Menuda fiesta

Web para la boda del 24 de octubre de 2026 en Avilés. Incluye galería de fotos y vídeos, filtros, visor y solicitud de archivos de Dropbox para recibir aportaciones.

## Sincronización de Dropbox

El workflow `Actualizar galería desde Dropbox` comprueba la carpeta aproximadamente cada 10 minutos. GitHub puede retrasar los trabajos programados. Cuando cambia el tamaño del ZIP de la carpeta, importa los archivos nuevos, convierte fotos y vídeos para móvil y publica la galería en `main`. Una comprobación completa diaria detecta también reemplazos que no cambien el tamaño total. Los errores de conversión se registran en Actions y se reintentan; las importaciones correctas se conservan.

El enlace de lectura de la carpeta se configura mediante el secreto de repositorio `DROPBOX_SHARED_LINK`. La solicitud de archivos debe guardar las aportaciones en esa misma carpeta. La integración utiliza la descarga pública oficial del ZIP de Dropbox; no necesita un token de usuario. Solo se importan formatos de imagen y vídeo compatibles. No se eliminan automáticamente las fotos ya publicadas.

La web consulta `live-media.json` en este repositorio cada minuto mientras está abierta, por lo que puede mostrar nuevas aportaciones aunque OVH conserve una copia anterior de los archivos de la galería. Hace falta desplegar una vez la versión de `app.js` que incluye esta consulta.

## Publicación

La web no requiere compilación. `index.html` debe quedar en la raíz del directorio de destino, junto a `app.js`, `style.css`, `media.js`, `live-media.json` y `assets`.

`descargar.html` permite preparar un ZIP de los archivos de la web desde el navegador.
