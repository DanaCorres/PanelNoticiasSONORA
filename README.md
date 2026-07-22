# Panel de noticias — Sonora

Dashboard que muestra las noticias más relevantes de Sonora, organizadas por
Seguridad, Política, Economía y Sociedad/deportes. Se actualiza solo cada 3
horas y acumula las notas del día (se reinicia a medianoche, hora de Sonora).

## 1. Crea el repositorio en GitHub

1. Ve a github.com, inicia sesión.
2. Botón "+" (arriba a la derecha) -> New repository.
3. Nombre sugerido: Panel-Sonora
4. Público, sin agregar README (vamos a subir el nuestro).
5. Create repository.

## 2. Sube estos archivos

Estructura completa que debes subir (respetando las carpetas):

panel-sonora/
├── .github/workflows/update.yml
├── data/today.json
├── scripts/fetch_news.py
├── scripts/curate_and_render.py
├── templates/index_template.html
├── index.html          (se regenera solo, pero sube uno inicial vacío o cópialo del de BC)
├── README.md
└── requirements.txt

TIP aprendido con el panel de Baja California: al arrastrar carpetas a GitHub
("Add file" -> "Upload files"), la carpeta .github puede dar error de "file is
hidden" porque empieza con un punto. Si te pasa:
1. Sube primero todo lo demás (data, scripts, templates, index.html, README,
   requirements.txt) arrastrando las carpetas normales.
2. Para el workflow, entra a tu repo -> "Add file" -> "Create new file" -> en
   el nombre escribe exactamente: .github/workflows/update.yml (GitHub crea
   las carpetas solo al ver el "/"). Pega el contenido del archivo ahí.

## 3. Activa GitHub Pages

Settings -> Pages -> Source: "Deploy from a branch" -> Branch: main,
carpeta / (root) -> Save. Tu panel queda en:
https://TU_USUARIO.github.io/Panel-Sonora/

## 4. Configura la API key de Claude

Puedes reutilizar la misma cuenta/API key que ya tienes de console.anthropic.com
(el gasto es independiente por proyecto, pero la key es la misma).

1. Repo -> Settings -> Secrets and variables -> Actions -> New repository secret.
2. Name: ANTHROPIC_API_KEY
3. Secret: tu API key.
4. Add secret.

## 5. Da permiso de escritura al Action

Settings -> Actions -> General -> baja hasta "Workflow permissions" ->
elige "Read and write permissions" -> Save.

## 6. Pruébalo

Pestaña Actions -> workflow "Actualizar panel de noticias" -> Run workflow.
Espera y revisa si sale verde (éxito) o rojo (falla, revisa los logs del
paso que falló).

## Fuentes incluidas

El Imparcial, Proyecto Puente, Expreso, Tribuna, Diario del Yaqui, El Sol de
Hermosillo, Radio Sonora, El Diario de Sonora, Despierta Sonora, Nuevo Día,
Tribuna de San Luis, Telemax, Opinión Sonora, Uniradio Sonora, Radar Sonora,
Entorno Informativo, Sonora Presente, Medios OBSON. (18 fuentes en total)

## Pendiente

- "La I Noticias" (laiparati.com.mx): la URL que se dio originalmente era un
  link de búsqueda de Google, no la URL directa del sitio. Cuando se tenga la
  URL correcta, se agrega a HTML_SOURCES en scripts/fetch_news.py.
- Las páginas de Facebook de la lista original (luis.a.medina.547,
  Noticiasonora, InfoSonMx, AaronTapiaPeriodista, nahum.acosta.50) no están
  incluidas: requieren inicio de sesión y no son accesibles por script.
- El scraping es frágil: si algún sitio rediseña su página, ese scraper en
  particular puede dejar de traer notas hasta que se ajuste el código
  (revisa los logs del Action de vez en cuando).
