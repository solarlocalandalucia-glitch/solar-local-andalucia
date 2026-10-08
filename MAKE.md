# Cómo se conecta Make con la web (pendiente de probar)

Nada de esto está activado ni probado todavía. Lo que sigue es el diseño.

## Cómo funciona
1. La web vive en un repositorio de GitHub y se publica sola con GitHub Pages (gratis).
2. Cada vez que se añade un archivo `.md` a `src/posts/`, GitHub regenera la web en 1 o 2 minutos.
3. Make añade ese archivo una vez al día, a las 9:00.

## Pasos para ti (cuando yo lo diga)
1. Crear una cuenta en github.com con `solarlocalandalucia@gmail.com`.
2. Crear un repositorio llamado `solar-local-andalucia` y activar Pages (Settings > Pages > Source: GitHub Actions).
3. Subir la carpeta de la web (yo te la preparo).
4. En Make, conectar GitHub y Gmail con esa cuenta.

## Escenario de Make "Artículo diario"
Programación: todos los días a las 9:00.

| Módulo | Qué hace |
|---|---|
| Gmail: leer correos nuevos | Mira el buzón del proyecto |
| Filtro | Solo sigue si hay novedad real que publicar |
| Redacción | Genera el borrador. Necesita clave de API de pago por uso; mientras no exista, Claude deja el borrador y tú lo apruebas |
| HTTP: llamada a la API de GitHub (`PUT /repos/{usuario}/solar-local-andalucia/contents/src/posts/AAAA-MM-DD-titulo.md`) | Publica el artículo |

Comprobado en la página de Make del 8/10/2026: su módulo de GitHub no tiene "crear archivo", por eso se usa el módulo HTTP con la API de GitHub y una clave de acceso limitada a este repositorio.

## Reglas para que Google no penalice
- No publicar si no hay novedad. Mejor 2 artículos útiles a la semana que 7 de relleno.
- Cada artículo cita su fuente y dice cuándo se comprobó.
- Los artículos sobre cifras de una ordenanza se revisan por una persona hasta que el proceso demuestre que acierta.

## Créditos de Make (plan gratis, 1.000 al mes)
Un escenario diario de unos 5 módulos gasta unos 150 créditos al mes. Hay que confirmarlo en la página oficial de precios de Make.
