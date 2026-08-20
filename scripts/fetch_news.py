"""
Recolecta titulares recientes de medios de Sonora.
Todos se leen vía scraping simple del home (heurística por longitud de texto
y href) -- si un sitio cambia su diseño, ese scraper en particular puede dejar
de traer notas hasta que se ajuste; el resto sigue funcionando normal.
Facebook / Instagram no se incluyen: requieren login, no son accesibles vía
script (luis.a.medina.547, Noticiasonora, InfoSonMx, AaronTapiaPeriodista,
nahum.acosta.50 de la lista original quedan fuera por esta razón).

Salida: raw_items.json con una lista de {source, title, url, published}

IMPORTANTE sobre el orden de la salida: curate_and_render.py se queda con los
primeros titulares del archivo. Si aquí se escribieran uno tras otro, fuente por
fuente, las primeras tres (15 notas cada una) llenarían el cupo y los otros
quince medios nunca llegarían al modelo: se recolectaban para nada. Por eso la
lista se entrega intercalada, una nota de cada fuente por turnos, de modo que el
recorte se reparta entre todas.
"""

import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (panel-bc-bot; +https://github.com/)"}

HTML_SOURCES = [
    {"name": "El Imparcial", "url": "https://www.elimparcial.com/sonora"},
    {"name": "Proyecto Puente", "url": "https://proyectopuente.com.mx/"},
    {"name": "Expreso", "url": "https://www.expreso.com.mx/noticias/sonora"},
    {"name": "Tribuna", "url": "https://tribuna.com.mx/seccion/sonora/"},
    {"name": "Diario del Yaqui", "url": "https://diariodelyaqui.mx/"},
    {"name": "El Sol de Hermosillo", "url": "https://www.elsoldehermosillo.com.mx/"},
    {"name": "Radio Sonora", "url": "https://www.radiosonora.com.mx/"},
    {"name": "El Diario de Sonora", "url": "https://www.eldiariodesonora.com.mx/"},
    {"name": "Despierta Sonora", "url": "https://despiertasonora.com/"},
    {"name": "Nuevo Día", "url": "https://nuevodia.mx/"},
    {"name": "Tribuna de San Luis", "url": "https://www.tribunadesanluis.com.mx/"},
    {"name": "Telemax", "url": "https://www.telemax.com.mx/"},
    {"name": "Opinión Sonora", "url": "https://www.opinionsonora.com/"},
    {"name": "Uniradio Sonora", "url": "https://www.uniradiosonora.com/"},
    {"name": "Radar Sonora", "url": "https://www.radarsonora.com/"},
    {"name": "Entorno Informativo", "url": "https://entornoinformativo.com.mx/"},
    {"name": "Sonora Presente", "url": "https://sonorapresente.com/sonora/"},
    {"name": "Medios OBSON", "url": "https://mediosobson.com/"},
    # Pendiente de agregar cuando se tenga la URL directa (no de búsqueda):
    # "La I Noticias" (laiparati.com.mx)
]

MAX_PER_SOURCE = 15

# Baja California sí cambia de horario de verano.
LOCAL_TZ = ZoneInfo("America/Tijuana")

# Enlaces del home que no son notas. Al scrapear un menú se cuelan secciones,
# avisos legales y llamados a suscribirse; antes daba igual porque estas
# fuentes nunca llegaban al modelo, ahora sí llegan.
BASURA = re.compile(
    r"aviso de privacidad|t[eé]rminos y condiciones|pol[ií]tica de (privacidad|cookies)|"
    r"suscr[ií]b|reg[ií]strate|inicia sesi[oó]n|contacto|qui[eé]nes somos|directorio|"
    r"publicidad|newsletter|todos los derechos|men[uú] principal|ver m[aá]s|"
    r"lee tambi[eé]n|leer m[aá]s",
    re.IGNORECASE)


def parece_nota(texto: str) -> bool:
    """Filtro mínimo: descarta enlaces de navegación y avisos legales."""
    if not 25 <= len(texto) <= 200:
        return False
    if BASURA.search(texto):
        return False
    # Un titular casi siempre trae varias palabras y un verbo; las secciones
    # del menú suelen ser dos o tres palabras en mayúsculas.
    if len(texto.split()) < 5:
        return False
    if texto.isupper():
        return False
    return True


def fetch_html(source):
    items = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        seen = set()
        vistos_titulos = set()
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not parece_nota(text):
                continue
            if href in seen or text.lower() in vistos_titulos:
                continue
            if not href.startswith("http"):
                if href.startswith("/"):
                    base = re.match(r"https?://[^/]+", source["url"]).group(0)
                    href = base + href
                else:
                    continue
            seen.add(href)
            vistos_titulos.add(text.lower())
            items.append({
                "source": source["name"],
                "title": text,
                "url": href,
                "published": "",
            })
            if len(items) >= MAX_PER_SOURCE:
                break
    except Exception as e:
        print(f"[aviso] scraping falló para {source['name']}: {e}")
    return items


# --------------------------------------------------------------------------
# Que solo entren notas de hoy
# --------------------------------------------------------------------------
# Tres filtros, de más a menos confiable:
#   1. La fecha del RSS, cuando la fuente la manda.
#   2. La fecha metida en la URL: casi todos los medios usan /2026/08/20/ o
#      -20-08-2026 en la dirección de sus notas.
#   3. El historial: si una URL ya estaba en la portada en días anteriores,
#      no es nueva hoy aunque el medio la siga mostrando.
# Lo que no cae en ninguno de los tres se deja pasar: más vale una nota vieja
# colada que perder una buena por falta de datos.

HISTORIAL = "data/urls_vistas.json"
DIAS_QUE_RECUERDA = 4

FECHA_EN_URL = [
    re.compile(r"/(20\d{2})/(\d{1,2})/(\d{1,2})/"),        # /2026/08/20/
    re.compile(r"/(20\d{2})-(\d{1,2})-(\d{1,2})"),          # /2026-08-20
    re.compile(r"[-_](\d{1,2})[-_](\d{1,2})[-_](20\d{2})"),  # -20-08-2026
]


def fecha_de_url(url):
    """Fecha escrita en la dirección de la nota, o None si no trae."""
    for i, patron in enumerate(FECHA_EN_URL):
        m = patron.search(url or "")
        if not m:
            continue
        try:
            a, b, c = (int(x) for x in m.groups())
            anio, mes, dia = (c, b, a) if i == 2 else (a, b, c)
            return date(anio, mes, dia)
        except ValueError:
            return None
    return None


def fecha_de_rss(publicado):
    """Fecha del campo published de un feed."""
    if not publicado:
        return None
    try:
        t = parsedate_to_datetime(publicado)
        return t.astimezone(LOCAL_TZ).date()
    except (TypeError, ValueError):
        return None


def cargar_historial():
    try:
        with open(HISTORIAL, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def guardar_historial(historial, hoy):
    """Guarda las URLs vistas y olvida las de hace más de unos días."""
    limite = (hoy - timedelta(days=DIAS_QUE_RECUERDA)).isoformat()
    vigentes = {u: d for u, d in historial.items() if d >= limite}
    try:
        os.makedirs(os.path.dirname(HISTORIAL), exist_ok=True)
        with open(HISTORIAL, "w", encoding="utf-8") as f:
            json.dump(vigentes, f, ensure_ascii=False, indent=1)
    except OSError as e:
        print(f"[aviso] no pude guardar el historial de URLs: {e}")


def filtrar_de_hoy(items, historial, hoy):
    """Deja solo lo que se puede dar por publicado hoy."""
    de_hoy, viejas, sin_fecha = [], 0, 0
    for it in items:
        fecha = fecha_de_rss(it.get("published")) or fecha_de_url(it.get("url"))

        if fecha is not None:
            if fecha == hoy:
                de_hoy.append(it)
            else:
                viejas += 1
            continue

        # Sin fecha: vale el historial. Si ya la habíamos visto otro día, fuera.
        primera_vez = historial.get(it["url"])
        if primera_vez and primera_vez < hoy.isoformat():
            viejas += 1
            continue
        sin_fecha += 1
        de_hoy.append(it)

    print(f"  filtro de fecha: {len(de_hoy)} de hoy, {viejas} descartadas por "
          f"viejas ({sin_fecha} pasaron sin fecha, por historial)")
    return de_hoy


def intercalar(por_fuente):
    """Une las listas por turnos: una nota de cada fuente, luego la siguiente.

    Así, al recortar la lista más adelante, el recorte se reparte entre todos
    los medios en vez de quedarse con los primeros dos o tres.
    """
    mezclado = []
    vueltas = max((len(v) for v in por_fuente.values()), default=0)
    for i in range(vueltas):
        for nombre in por_fuente:
            if i < len(por_fuente[nombre]):
                mezclado.append(por_fuente[nombre][i])
    return mezclado


def main():
    por_fuente = {}
    for s in HTML_SOURCES:
        por_fuente[s["name"]] = fetch_html(s)

    all_items = intercalar(por_fuente)

    hoy = datetime.now(LOCAL_TZ).date()
    historial = cargar_historial()
    all_items = filtrar_de_hoy(all_items, historial, hoy)
    for it in all_items:
        historial.setdefault(it["url"], hoy.isoformat())
    guardar_historial(historial, hoy)

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": all_items,
    }
    with open("raw_items.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    for nombre, notas in por_fuente.items():
        marca = "✓" if notas else "✗"
        print(f"  {marca} {nombre}: {len(notas)} notas")

    vivas = sum(1 for v in por_fuente.values() if v)
    print(f"Recolectadas {len(all_items)} notas de {vivas} fuentes vivas "
          f"(de {len(por_fuente)}).")
    print(f"Las primeras 72 —las que verá el modelo— cubren "
          f"{len({n['source'] for n in all_items[:72]})} fuentes distintas.")


if __name__ == "__main__":
    main()
