"""
Recolecta titulares recientes de medios de Sonora.
Todos se leen vía scraping simple del home (heurística por longitud de texto
y href) -- si un sitio cambia su diseño, ese scraper en particular puede dejar
de traer notas hasta que se ajuste; el resto sigue funcionando normal.

Facebook / Instagram no se incluyen: requieren login, no son accesibles vía
script (luis.a.medina.547, Noticiasonora, InfoSonMx, AaronTapiaPeriodista,
nahum.acosta.50 de la lista original quedan fuera por esta razón).

Salida: raw_items.json con una lista de {source, title, url, published}
"""

import json
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (panel-sonora-bot; +https://github.com/)"}

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


def fetch_html(source):
    items = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        seen = set()
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if len(text) < 25 or len(text) > 200:
                continue
            if href in seen:
                continue
            if not href.startswith("http"):
                if href.startswith("/"):
                    base = re.match(r"https?://[^/]+", source["url"]).group(0)
                    href = base + href
                else:
                    continue
            seen.add(href)
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


def main():
    all_items = []
    for s in HTML_SOURCES:
        all_items.extend(fetch_html(s))

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": all_items,
    }
    with open("raw_items.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Recolectadas {len(all_items)} notas de {len(HTML_SOURCES)} fuentes.")


if __name__ == "__main__":
    main()
