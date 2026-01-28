import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import streamlit as st

try:
    import requests
except Exception:
    requests = None


# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Habisolute | Painel Central",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LINKS_PATH = str(BASE_DIR / "links.json")


# =========================
# UI HELPERS (compat)
# =========================
def ui_toggle(label, value=False, **kwargs):
    if hasattr(st, "toggle"):
        return st.toggle(label, value=value, **kwargs)
    return st.checkbox(label, value=value, **kwargs)


# =========================
# CSS (Premium / SAP-like)
# =========================
def inject_css():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; padding-bottom: 2.2rem; max-width: 1400px; }

        /* Sidebar */
        [data-testid="stSidebar"]{
            border-right: 1px solid rgba(2,6,23,0.08);
            background: linear-gradient(180deg, rgba(249,115,22,0.06), rgba(249,115,22,0.00));
        }
        [data-testid="stSidebar"] .stMarkdown { opacity: .95; }

        /* Top header */
        .hb-top {
            display:flex; align-items:center; justify-content:space-between;
            gap: 12px;
            padding: 16px 18px;
            border-radius: 18px;
            background:
              radial-gradient(1200px 300px at 20% 0%, rgba(249,115,22,0.22), transparent 60%),
              linear-gradient(90deg, rgba(2,6,23,0.05), rgba(2,6,23,0.00));
            border: 1px solid rgba(2,6,23,0.08);
            box-shadow: 0 14px 40px rgba(2,6,23,0.06);
            margin-bottom: 14px;
        }
        .hb-title{ margin:0; font-size: 22px; font-weight: 800; letter-spacing: .2px;}
        .hb-sub{ margin-top: 4px; font-size: 13px; opacity: .78; }

        .hb-pills{ display:flex; flex-wrap:wrap; gap:8px; justify-content:flex-end;}
        .hb-pill{
            display:flex; gap:8px; align-items:center;
            padding: 7px 10px;
            border-radius: 999px;
            border: 1px solid rgba(2,6,23,0.10);
            background: rgba(255,255,255,0.70);
            font-size: 12px;
            backdrop-filter: blur(6px);
        }
        .dot{ width:8px; height:8px; border-radius:999px; display:inline-block; }
        .dot.on{ background: rgba(34,197,94,1); }
        .dot.off{ background: rgba(239,68,68,1); }
        .dot.maint{ background: rgba(234,179,8,1); }
        .dot.info{ background: rgba(59,130,246,1); }

        /* Clickable card link wrapper */
        .hb-card-link{
            text-decoration: none !important;
            color: inherit !important;
            display:block;
        }

        /* Card */
        .hb-card{
            position: relative;
            border-radius: 18px;
            padding: 14px 14px 14px 14px;
            border: 1px solid rgba(2,6,23,0.10);
            background:
              radial-gradient(900px 200px at 10% 0%, rgba(249,115,22,0.14), transparent 55%),
              linear-gradient(180deg, rgba(255,255,255,0.95), rgba(255,255,255,0.88));
            box-shadow: 0 14px 40px rgba(2,6,23,0.06);
            transition: transform .14s ease, box-shadow .14s ease, border-color .14s ease;
            height: 100%;
            cursor: pointer;
        }
        .hb-card:hover{
            transform: translateY(-2px);
            box-shadow: 0 22px 55px rgba(2,6,23,0.10);
            border-color: rgba(249,115,22,0.35);
        }

        .hb-row{ display:flex; justify-content:space-between; align-items:center; gap: 12px; }
        .hb-icon{
            font-size: 28px;
            width: 46px; height: 46px;
            display:flex; align-items:center; justify-content:center;
            border-radius: 14px;
            background: rgba(249,115,22,0.12);
            border: 1px solid rgba(249,115,22,0.18);
        }
        .hb-name{ margin:0; font-weight: 800; font-size: 15px; line-height: 1.2; }
        .hb-cat{ font-size: 12px; opacity:.70; margin-top: 4px; }

        .hb-badge{
            font-size: 11px;
            padding: 4px 9px;
            border-radius: 999px;
            border: 1px solid rgba(2,6,23,0.10);
            background: rgba(2,6,23,0.03);
            white-space: nowrap;
        }
        .hb-badge.online{ background: rgba(34,197,94,0.10); border-color: rgba(34,197,94,0.25); }
        .hb-badge.offline{ background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.24); }
        .hb-badge.manutencao{ background: rgba(234,179,8,0.14); border-color: rgba(234,179,8,0.28); }
        .hb-badge.info{ background: rgba(59,130,246,0.10); border-color: rgba(59,130,246,0.22); }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# DATA
# =========================
@dataclass
class LinkItem:
    id: str
    name: str
    category: str
    description: str
    url: str
    icon: str = "🔗"
    tags: List[str] = None
    status: str = "info"
    favorite: bool = False


def load_links(path: str) -> Tuple[Dict[str, Any], List[LinkItem]]:
    p = Path(path)
    if not p.is_file():
        p2 = (BASE_DIR / path).resolve()
        if p2.is_file():
            p = p2
    if not p.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    raw = json.loads(p.read_text(encoding="utf-8"))

    items: List[LinkItem] = []
    for it in raw.get("items", []):
        items.append(
            LinkItem(
                id=str(it.get("id", "")),
                name=str(it.get("name", "Sem nome")),
                category=str(it.get("category", "Geral")),
                description=str(it.get("description", "")),
                url=str(it.get("url", "")),
                icon=str(it.get("icon", "🔗")),
                tags=list(it.get("tags", []) or []),
                status=str(it.get("status", "info")).lower(),
                favorite=bool(it.get("favorite", False)),
            )
        )
    return raw, items


def unique_sorted(values: List[str]) -> List[str]:
    return sorted(list({v for v in values if v and v.strip()}), key=lambda s: s.lower())


def status_label(status: str) -> str:
    s = (status or "info").lower()
    if s == "online":
        return "Online"
    if s == "offline":
        return "Offline"
    if s in ["manutencao", "manutenção", "maintenance"]:
        return "Manutenção"
    return "Info"


def ping_url(url: str, timeout: float = 2.5) -> Optional[Tuple[bool, int]]:
    if not requests:
        return None
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return (r.status_code < 500, r.status_code)
    except Exception:
        try:
            r = requests.get(url, timeout=timeout, allow_redirects=True)
            return (r.status_code < 500, r.status_code)
        except Exception:
            return (False, 0)


# =========================
# RENDER
# =========================
def render_top(meta: Dict[str, Any], total: int, shown: int, s_online: int, s_man: int, s_off: int):
    app_name = meta.get("app_name", "Painel Central")
    subtitle = meta.get("subtitle", "")
    owner = meta.get("owner", "")

    st.markdown(
        f"""
        <div class="hb-top">
            <div>
                <div class="hb-title">{app_name}</div>
                <div class="hb-sub">{subtitle} • {owner}</div>
            </div>
            <div class="hb-pills">
                <div class="hb-pill"><span class="dot info"></span> Apps: <b>{shown}/{total}</b></div>
                <div class="hb-pill"><span class="dot on"></span> Online: <b>{s_online}</b></div>
                <div class="hb-pill"><span class="dot maint"></span> Manutenção: <b>{s_man}</b></div>
                <div class="hb-pill"><span class="dot off"></span> Offline: <b>{s_off}</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ✅ CARD: clicável, clean (sem botão / sem código aparecendo)
def render_card(item: LinkItem, do_healthcheck: bool = False):
    badge_class = item.status if item.status in ["online", "offline", "manutencao"] else "info"
    badge_text = status_label(item.status)

    hc_text = ""
    if do_healthcheck and item.url and item.url.startswith("http"):
        res = ping_url(item.url)
        if res is not None:
            ok, code = res
            hc_text = f" • HTTP {code}" if ok else " • sem resposta"

    href_open = item.url if (item.url and item.url.startswith("http")) else None
    if href_open:
        open_tag = f'<a class="hb-card-link" href="{href_open}" target="_blank" rel="noopener noreferrer">'
        close_tag = "</a>"
    else:
        open_tag = '<div class="hb-card-link">'
        close_tag = "</div>"

    st.markdown(
        f"""{open_tag}
<div class="hb-card">
  <div class="hb-row">
    <div style="display:flex; gap:12px; align-items:center;">
      <div class="hb-icon">{item.icon}</div>
      <div>
        <div class="hb-name">{item.name}</div>
        <div class="hb-cat">{item.category}</div>
      </div>
    </div>
    <div class="hb-badge {badge_class}">{badge_text}{hc_text}</div>
  </div>
</div>
{close_tag}""",
        unsafe_allow_html=True,
    )

    st.write("")


def main():
    inject_css()

    # Sidebar
    st.sidebar.markdown("## 🧭 Navegação")
    st.sidebar.caption("Edite o arquivo links.json no GitHub para adicionar/remover sistemas.")

    links_path = st.sidebar.text_input("Arquivo de links", value="links.json")
    only_favorites = ui_toggle("Somente favoritos", value=False)

    # Load
    try:
        meta, items = load_links(links_path)
    except Exception as e:
        st.error(f"Não consegui ler o arquivo `{links_path}`. Erro: {e}")
        st.stop()

    categories = unique_sorted([i.category for i in items])
    category = st.sidebar.selectbox("Categoria", options=["Todas"] + categories, index=0)

    # Filters row
    colA, colB, colC = st.columns([2.2, 1.1, 1.1])
    with colA:
        q = st.text_input("🔎 Buscar", placeholder="Ex.: CP, OS, Financeiro, Argamassa...")
    with colB:
        status_filter = st.selectbox("Status", options=["Todos", "Online", "Manutenção", "Offline", "Info"], index=0)
    with colC:
        sort_mode = st.selectbox("Ordenar", options=["Favoritos primeiro", "Categoria > Nome", "Nome"], index=0)

    def match(item: LinkItem) -> bool:
        if only_favorites and not item.favorite:
            return False
        if category != "Todas" and item.category != category:
            return False

        if status_filter != "Todos":
            wanted = status_filter.lower()
            if wanted == "manutenção":
                wanted = "manutencao"
            if wanted == "info":
                if item.status in ["online", "offline", "manutencao"]:
                    return False
            else:
                if item.status != wanted:
                    return False

        if q and q.strip():
            s = q.strip().lower()
            blob = " ".join(
                [
                    item.name or "",
                    item.category or "",
                    item.description or "",
                    " ".join(item.tags or []),
                ]
            ).lower()
            return s in blob

        return True

    filtered = [i for i in items if match(i)]

    if sort_mode == "Nome":
        filtered.sort(key=lambda x: (x.name or "").lower())
    elif sort_mode == "Categoria > Nome":
        filtered.sort(key=lambda x: ((x.category or "").lower(), (x.name or "").lower()))
    else:
        filtered.sort(key=lambda x: (0 if x.favorite else 1, (x.category or "").lower(), (x.name or "").lower()))

    s_online = sum(1 for i in filtered if i.status == "online")
    s_man = sum(1 for i in filtered if i.status == "manutencao")
    s_off = sum(1 for i in filtered if i.status == "offline")

    render_top(meta, total=len(items), shown=len(filtered), s_online=s_online, s_man=s_man, s_off=s_off)

    if not filtered:
        st.info("Nenhum sistema encontrado com os filtros atuais.")
        st.stop()

    cols = st.columns(4)
    for idx, item in enumerate(filtered):
        with cols[idx % 4]:
            render_card(item)

    st.divider()
    st.caption("Habisolute • Painel Central")


if __name__ == "__main__":
    main()
