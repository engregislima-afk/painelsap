import json
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

import streamlit as st

try:
    import requests
except Exception:
    requests = None


# -----------------------------
# Config
# -----------------------------
st.set_page_config(
    page_title="Painel Central",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_LINKS_PATH = "links.json"


# -----------------------------
# UI (CSS)
# -----------------------------
def inject_css():
    st.markdown(
        """
        <style>
        /* Layout geral */
        .block-container { padding-top: 1.0rem; padding-bottom: 2.0rem; }
        [data-testid="stSidebar"] { border-right: 1px solid rgba(0,0,0,0.06); }

        /* Top bar */
        .topbar {
            display:flex; align-items:center; justify-content:space-between;
            padding: 14px 18px; border-radius: 16px;
            background: linear-gradient(90deg, rgba(249,115,22,0.18), rgba(249,115,22,0.04));
            border: 1px solid rgba(0,0,0,0.06);
            margin-bottom: 14px;
        }
        .topbar h1 { font-size: 20px; margin: 0; line-height: 1.1; }
        .topbar .sub { opacity: 0.72; font-size: 13px; margin-top: 2px; }
        .pill {
            padding: 6px 10px; border-radius: 999px;
            border: 1px solid rgba(0,0,0,0.08);
            background: rgba(255,255,255,0.6);
            font-size: 12px;
        }

        /* Cards */
        .card {
            border-radius: 16px;
            padding: 14px 14px 12px 14px;
            border: 1px solid rgba(0,0,0,0.08);
            background: #ffffff;
            box-shadow: 0 6px 22px rgba(15, 23, 42, 0.06);
            height: 100%;
        }
        .cardhead {
            display:flex; align-items:flex-start; justify-content:space-between;
            gap: 10px;
        }
        .title {
            font-weight: 700; font-size: 15px; margin: 0;
        }
        .desc {
            margin: 6px 0 10px 0;
            font-size: 12.5px; opacity: 0.78;
            min-height: 34px;
        }
        .meta {
            display:flex; flex-wrap:wrap; gap: 6px;
            margin: 6px 0 10px 0;
        }
        .tag {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 999px;
            border: 1px solid rgba(0,0,0,0.08);
            background: rgba(2,6,23,0.02);
            opacity: 0.9;
        }
        .badge {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 999px;
            border: 1px solid rgba(0,0,0,0.08);
            background: rgba(2,6,23,0.02);
        }
        .badge.online { background: rgba(34,197,94,0.12); border-color: rgba(34,197,94,0.25); }
        .badge.offline { background: rgba(239,68,68,0.10); border-color: rgba(239,68,68,0.25); }
        .badge.manutencao { background: rgba(234,179,8,0.16); border-color: rgba(234,179,8,0.28); }

        /* Botões */
        div.stButton > button, a.stLinkButton {
            border-radius: 12px !important;
        }

        /* Pequena “grade” tipo Fiori */
        .gridhint {
            opacity: 0.65;
            font-size: 12px;
            margin: 2px 0 0 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Data model
# -----------------------------
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
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    items = []
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
    """Tenta um HEAD/GET rápido só pra ver se responde."""
    if not requests:
        return None
    try:
        # HEAD às vezes é bloqueado; tenta GET se falhar
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        return (r.status_code < 500, r.status_code)
    except Exception:
        try:
            r = requests.get(url, timeout=timeout, allow_redirects=True)
            return (r.status_code < 500, r.status_code)
        except Exception:
            return (False, 0)


# -----------------------------
# Render
# -----------------------------
def render_topbar(meta: Dict[str, Any], total: int, shown: int):
    app_name = meta.get("app_name", "Painel Central")
    subtitle = meta.get("subtitle", "")
    owner = meta.get("owner", "")

    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <h1>{app_name}</h1>
                <div class="sub">{subtitle} • {owner}</div>
            </div>
            <div class="pill">Apps: {shown}/{total}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_card(item: LinkItem, do_healthcheck: bool = False):
    # Badge status
    badge_class = item.status if item.status in ["online", "offline", "manutencao"] else ""
    badge_text = status_label(item.status)

    # Health check (opcional)
    hc_text = ""
    if do_healthcheck and item.url and item.url.startswith("http"):
        res = ping_url(item.url)
        if res is None:
            hc_text = ""
        else:
            ok, code = res
            if ok:
                hc_text = f"• HTTP {code}"
            else:
                hc_text = "• Sem resposta"

    tags_html = ""
    for t in (item.tags or [])[:8]:
        tags_html += f'<span class="tag">{t}</span>'

    st.markdown(
        f"""
        <div class="card">
            <div class="cardhead">
                <div>
                    <div class="title">{item.icon} {item.name}</div>
                    <div class="gridhint">{item.category}</div>
                </div>
                <div class="badge {badge_class}">{badge_text} {hc_text}</div>
            </div>
            <div class="desc">{item.description}</div>
            <div class="meta">{tags_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Botões (fora do HTML pra manter click seguro)
    c1, c2 = st.columns([1, 1])
    with c1:
        if item.url:
            st.link_button("Abrir", item.url, use_container_width=True)
        else:
            st.button("Sem link", disabled=True, use_container_width=True)
    with c2:
        # Copiar link (simples)
        if item.url:
            st.code(item.url, language=None)
        else:
            st.caption("Cadastre a URL no links.json")


def main():
    inject_css()

    # Sidebar
    st.sidebar.markdown("### 🧭 Navegação")
    st.sidebar.caption("Edite o arquivo `links.json` no GitHub para adicionar/remover sistemas.")

    links_path = st.sidebar.text_input("Arquivo de links", value=DEFAULT_LINKS_PATH)
    do_healthcheck = st.sidebar.toggle("Checar disponibilidade (rápido)", value=False, help="Faz um ping HTTP simples. Pode falhar em links bloqueados.")
    only_favorites = st.sidebar.toggle("Somente favoritos", value=False)

    # Load data
    try:
        meta, items = load_links(links_path)
    except Exception as e:
        st.error(f"Não consegui ler o arquivo `{links_path}`. Erro: {e}")
        st.stop()

    categories = unique_sorted([i.category for i in items])
    category = st.sidebar.selectbox("Categoria", options=["Todas"] + categories, index=0)

    # Search & filters
    colA, colB, colC = st.columns([2.2, 1.2, 1.2])
    with colA:
        q = st.text_input("🔎 Buscar (nome, descrição, tags)", placeholder="Ex.: concreto, OS, financeiro, CP, FCK...")
    with colB:
        status_filter = st.selectbox("Status", options=["Todos", "Online", "Manutenção", "Offline", "Info"], index=0)
    with colC:
        sort_mode = st.selectbox("Ordenar", options=["Categoria > Nome", "Nome", "Favoritos primeiro"], index=0)

    # Apply filters
    def match(item: LinkItem) -> bool:
        if only_favorites and not item.favorite:
            return False
        if category != "Todas" and item.category != category:
            return False

        if status_filter != "Todos":
            wanted = status_filter.lower()
            if wanted == "manutenção":
                wanted = "manutencao"
            # "Info" pega tudo que não é online/offline/manutencao
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
                    item.description or "",
                    item.category or "",
                    " ".join(item.tags or []),
                ]
            ).lower()
            return s in blob

        return True

    filtered = [i for i in items if match(i)]

    # Sort
    if sort_mode == "Nome":
        filtered.sort(key=lambda x: (x.name or "").lower())
    elif sort_mode == "Favoritos primeiro":
        filtered.sort(key=lambda x: (0 if x.favorite else 1, (x.category or "").lower(), (x.name or "").lower()))
    else:
        filtered.sort(key=lambda x: ((x.category or "").lower(), (x.name or "").lower()))

    render_topbar(meta, total=len(items), shown=len(filtered))

    # Summary row
    s_online = sum(1 for i in filtered if i.status == "online")
    s_man = sum(1 for i in filtered if i.status == "manutencao")
    s_off = sum(1 for i in filtered if i.status == "offline")
    st.caption(f"Exibindo **{len(filtered)}** apps • Online: **{s_online}** • Manutenção: **{s_man}** • Offline: **{s_off}**")

    # Grid
    if not filtered:
        st.info("Nenhum app encontrado com esses filtros. Ajuste a busca/categoria/status ou edite o links.json.")
        st.stop()

    # Cards em colunas responsivas
    cols = st.columns(3)
    for idx, item in enumerate(filtered):
        with cols[idx % 3]:
            render_card(item, do_healthcheck=do_healthcheck)
            st.write("")  # espaço

    # Rodapé
    st.divider()
    st.caption("📌 Dica: Você pode manter esse painel como “home” e apontar para todos os seus sistemas (Streamlit/Render/Sites).")


if __name__ == "__main__":
    main()

