ANEXO — INSTALACIÓN Y GUÍA DE USUARIO (MODIFICAR)
Traducción de referencia de la documentación del RTD SCADA Simulator v1.0.0
Descarga del software
El simulador se descarga desde el siguiente enlace (archivo comprimido .rar): [ pegar aquí el enlace de descarga ]
A.1 · Instalación
Requisitos. El software funciona únicamente en Windows.
1.	Descompriman por completo el archivo .rar en una carpeta (no ejecuten el .exe desde dentro del comprimido).
2.	Ejecuten RTD_SCADA_Simulator.exe.
3.	Si aparece la pantalla azul de Windows SmartScreen («Windows protegió tu PC»), es porque el programa no está firmado digitalmente, no porque sea peligroso. Hagan clic en «Más información» y luego en «Ejecutar de todas formas».
Si el programa no abre, verifiquen que descomprimieron el archivo completo y que están en Windows.
A.2 · Ejecutar un ensayo
Sobre el P&ID interactivo seleccionen la columna a ensayar y configuren la inyección: tipo (pulso o escalón), dosis o concentración de trazador y caudal. Pongan en marcha la corrida, dejen que la respuesta del fotocolorímetro se registre y detengan el ensayo para cargar los datos. Usen el control de velocidad para acelerar respecto del tiempo real y llegar antes al final de la cola.
Nota. Ajusten los nombres de los controles de esta sección a la interfaz final del simulador antes de distribuir la guía.
A.3 · Datos y exportación
Al detener la corrida, la serie temporal completa queda disponible como una tabla con una fila por muestra (tiempo, absorbancia/concentración de trazador a la salida, caudal). Expórtenla en formato CSV o Excel para procesarla en su herramienta de hoja de cálculo.

FLUJO DE TRABAJO TÍPICO
Seleccionen la columna y configuren la inyección → pongan en marcha → dejen correr hasta que la señal vuelva al ruido de base (acelérenla si hace falta) → detengan → exporten los datos → procesen en Excel: conversión, normalización, momentos, ajustes y contraste modelo–dato.

