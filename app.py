"""
TRIBUNA — Hollywood Cut
Um único arquivo. Treino diário de confiança, oratória, papo e charme,
com simulação de conversa e feedback de oratória via Groq.

Pra rodar:
    pip install streamlit groq
    streamlit run app.py

Configuração da chave Groq (uma das opções):
    - variável de ambiente GROQ_API_KEY
    - .streamlit/secrets.toml com GROQ_API_KEY = "..."
    - colar direto na barra lateral do app (fica só na sessão do navegador)
"""

import os
import json
from datetime import date, timedelta

import streamlit as st

try:
    from groq import Groq
except ImportError:
    Groq = None


# ==========================================================================
# 1. DADOS — banco de exercícios dos 4 pilares
# ==========================================================================
CATEGORIES = {
    "confianca": {
        "label": "Confiança",
        "trophy": "🏆",
        "color": "#d4af37",
        "items": [
            "Faça uma pose de poder por 2 minutos antes de sair de casa — ombros abertos, mãos na cintura.",
            "Grave um áudio de 60s contando algo bom que te aconteceu, sem pedir desculpa por nada.",
            "Puxe assunto com um estranho hoje — caixa do mercado, barista, motorista.",
            "Escreva 3 coisas que você fez bem essa semana, sem minimizar nenhuma.",
            "Ande com o queixo paralelo ao chão e ombros abertos por 10 minutos seguidos.",
            "Diga 'não' a um pedido pequeno hoje, sem se justificar depois.",
            "Olhe no espelho e fale em voz alta um elogio sincero pra você mesmo.",
            "Peça um desconto, uma troca ou um favor pequeno numa loja ou serviço hoje.",
            "Sente ocupando o espaço todo da cadeira, sem cruzar braços, numa reunião ou almoço.",
            "Inicie uma conversa numa fila ou elevador — só um comentário leve já vale.",
        ],
    },
    "oratoria": {
        "label": "Oratória",
        "trophy": "🎤",
        "color": "#8c1c1c",
        "items": [
            "Grave-se falando 2 minutos sobre um tema aleatório sem dizer 'é', 'tipo' ou 'né'.",
            "Leia um parágrafo em voz alta variando o ritmo: rápido, pausado, com uma pausa dramática.",
            "Pratique uma pausa de 3 segundos antes de responder algo importante hoje.",
            "Conte uma história curta de 30 a 60 segundos com início, conflito e final.",
            "Diga a mesma frase em 3 tons diferentes: sério, engraçado, misterioso.",
            "Explique um assunto complexo como se fosse pra uma criança de 8 anos.",
            "Grave um 'elevator pitch' de 30 segundos sobre você mesmo.",
            "Fale em pé, projetando a voz, como se estivesse num palco.",
            "Repita um trava-língua 5 vezes, cada vez mais rápido, sem embolar.",
            "Termine uma frase importante com uma pausa impactante em vez de completar tudo.",
        ],
    },
    "papo": {
        "label": "Papo",
        "trophy": "💬",
        "color": "#4f6f52",
        "items": [
            "Faça 3 perguntas abertas numa conversa hoje — que não dá pra responder só com sim ou não.",
            "Pratique escuta ativa: repita com suas palavras o que a pessoa disse antes de responder.",
            "Conte uma piada ou trocadilho pra alguém hoje.",
            "Puxe assunto sobre algo que você observou no ambiente — roupa, objeto, lugar.",
            "Quando alguém mencionar um detalhe, pergunte 'e então, como foi isso?' pra puxar mais.",
            "Faça uma pergunta 'e se...' pra puxar a imaginação numa conversa.",
            "Pratique o silêncio confortável — não preencha toda pausa com palavras.",
            "Conte uma história levemente embaraçosa sua pra quebrar o gelo.",
            "Mude de assunto suavemente com uma ponte tipo 'aliás, isso me lembra...'.",
            "Encerre uma conversa com um convite ou próximo passo claro, não só um 'tchau'.",
        ],
    },
    "charme": {
        "label": "Charme",
        "trophy": "✨",
        "color": "#7b5ea7",
        "items": [
            "Faça um elogio específico e genuíno pra alguém hoje — nada genérico.",
            "Sorria primeiro e sustente contato visual por 3-4 segundos numa conversa.",
            "Use humor auto-depreciativo leve uma vez hoje, sem se diminuir de verdade.",
            "Lembre de algo que a pessoa disse antes e traga de volta mais tarde na conversa.",
            "Mostre curiosidade genuína: pergunte 'por quê' ou 'como foi isso' sobre algo que importa pra ela.",
            "Brinque com leveza sobre algo que a pessoa disse, sem sarcasmo pesado.",
            "Incline o corpo levemente e aponte os pés na direção de quem está falando com você.",
            "Crie uma piada interna ou apelido carinhoso com alguém próximo.",
            "Convide alguém pra algo específico — dia, hora e lugar, não um 'a gente devia sair' vago.",
            "Termine uma conversa com algo memorável em vez de só um 'tchau' — um close de verdade.",
        ],
    },
}


def _hash_str(s: str) -> int:
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return h


def pick_index(cat_key: str, date_str: str, offset: int = 0) -> int:
    items = CATEGORIES[cat_key]["items"]
    return _hash_str(f"{cat_key}{date_str}{offset}") % len(items)


# ==========================================================================
# 2. PERSISTÊNCIA — arquivo JSON local
# ==========================================================================
DATA_FILE = os.environ.get("TRIBUNA_DATA_FILE", "tribuna_progress.json")
DEFAULT_STATE = {
    "streak": 0,
    "last_complete_date": None,
    "totals": {"confianca": 0, "oratoria": 0, "papo": 0, "charme": 0},
    "days": {},
}


def load_state() -> dict:
    if not os.path.exists(DATA_FILE):
        return json.loads(json.dumps(DEFAULT_STATE))
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = json.loads(json.dumps(DEFAULT_STATE))
        merged.update(data)
        merged["totals"] = {**merged["totals"], **data.get("totals", {})}
        return merged
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(DEFAULT_STATE))


def save_state(state: dict) -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Aviso: não foi possível salvar o progresso ({e})")


def today_key() -> str:
    return date.today().isoformat()


def yesterday_key() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


# ==========================================================================
# 3. GROQ — cliente e chamada de chat
# ==========================================================================
def get_groq_client():
    if Groq is None:
        return None
    api_key = (
        st.session_state.get("groq_api_key")
        or os.environ.get("GROQ_API_KEY")
        or st.secrets.get("GROQ_API_KEY", None)
    )
    if not api_key:
        return None
    return Groq(api_key=api_key)


def groq_chat(messages, model, temperature=0.8, max_tokens=600):
    client = get_groq_client()
    if client is None:
        return None
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return resp.choices[0].message.content


# ==========================================================================
# 4. VISUAL — "Hollywood Cut": marquee dourada, veludo preto, holofote
# ==========================================================================
st.set_page_config(page_title="TRIBUNA — Hollywood Cut", page_icon="🎬", layout="centered")

st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;900&family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

      .stApp {
        background:
          radial-gradient(ellipse at 50% -10%, rgba(212,175,55,0.10), transparent 60%),
          #0b0b0c;
        color: #f2ead9;
      }

      /* marquee header */
      .marquee-wrap{
        position:relative;
        border:2px solid #d4af37;
        border-radius:6px;
        padding:26px 20px 20px;
        margin-bottom:28px;
        text-align:center;
        background:linear-gradient(180deg, rgba(212,175,55,0.06), transparent 70%);
        overflow:hidden;
      }
      .marquee-wrap::before, .marquee-wrap::after{
        content:"";
        position:absolute; left:10px; right:10px; height:1px;
        background:repeating-linear-gradient(90deg, #d4af37 0 6px, transparent 6px 14px);
        opacity:0.55;
      }
      .marquee-wrap::before{ top:6px; }
      .marquee-wrap::after{ bottom:6px; }
      .marquee-eyebrow{
        font-family:'Bebas Neue', sans-serif;
        letter-spacing:4px;
        color:#8c1c1c;
        background:#f2ead9;
        display:inline-block;
        padding:2px 14px;
        border-radius:2px;
        font-size:13px;
        margin-bottom:10px;
      }
      .marquee-title{
        font-family:'Cinzel', serif;
        font-weight:900;
        font-size:clamp(38px, 8vw, 58px);
        letter-spacing:3px;
        color:#f2ead9;
        text-shadow: 0 0 18px rgba(212,175,55,0.35);
        margin:0;
        line-height:1;
      }
      .marquee-sub{
        font-family:'Bebas Neue', sans-serif;
        letter-spacing:2px;
        color:#d4af37;
        font-size:14px;
        margin-top:6px;
      }

      /* filmstrip divider */
      .filmstrip{
        height:14px;
        margin:22px 0 18px;
        background:
          repeating-linear-gradient(90deg, #0b0b0c 0 10px, transparent 10px 22px),
          linear-gradient(#1a1a1a,#1a1a1a);
        border-top:1px solid #333; border-bottom:1px solid #333;
      }

      /* award category card */
      .award-badge{
        display:inline-block;
        font-family:'Bebas Neue', sans-serif;
        letter-spacing:1.5px;
        font-size:13px;
        padding:3px 12px;
        border-radius:20px;
        margin-bottom:8px;
      }

      /* sidebar */
      section[data-testid="stSidebar"]{
        background:#131010;
        border-right:1px solid rgba(212,175,55,0.25);
      }

      /* buttons */
      .stButton>button{
        border:1px solid #d4af37;
        color:#d4af37;
        background:transparent;
        font-family:'Bebas Neue', sans-serif;
        letter-spacing:1px;
      }
      .stButton>button:hover{
        background:#d4af37;
        color:#0b0b0c;
        border-color:#d4af37;
      }

      div[data-testid="stMetric"]{
        background:rgba(212,175,55,0.06);
        border:1px solid rgba(212,175,55,0.25);
        border-radius:8px;
        padding:10px 14px;
      }

      @media (prefers-reduced-motion: reduce){ * { animation:none !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def marquee(title, eyebrow, sub):
    st.markdown(
        f"""
        <div class="marquee-wrap">
          <span class="marquee-eyebrow">{eyebrow}</span>
          <div class="marquee-title">{title}</div>
          <div class="marquee-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def filmstrip():
    st.markdown('<div class="filmstrip"></div>', unsafe_allow_html=True)


# ==========================================================================
# 5. ESTADO
# ==========================================================================
if "state" not in st.session_state:
    st.session_state.state = load_state()
state = st.session_state.state
tk = today_key()

if tk not in state["days"]:
    state["days"][tk] = {
        cat: {"index": pick_index(cat, tk, 0), "offset": 0, "done": False}
        for cat in CATEGORIES
    }
    save_state(state)
day = state["days"][tk]


def all_done_today():
    return all(day[c]["done"] for c in CATEGORIES)


def toggle_done(cat):
    was_done = day[cat]["done"]
    day[cat]["done"] = not was_done
    state["totals"][cat] = max(0, state["totals"].get(cat, 0) + (1 if not was_done else -1))

    if not was_done and all_done_today():
        if state["last_complete_date"] != tk:
            state["streak"] = state["streak"] + 1 if state["last_complete_date"] == yesterday_key() else 1
            state["last_complete_date"] = tk
            st.toast(f"Sessão no ar — sequência de {state['streak']} noites 🎬")
    elif was_done and state["last_complete_date"] == tk and not all_done_today():
        state["last_complete_date"] = None
        state["streak"] = max(0, state["streak"] - 1)
    save_state(state)


def refresh_card(cat):
    day[cat]["offset"] += 1
    day[cat]["index"] = pick_index(cat, tk, day[cat]["offset"])
    save_state(state)


# ==========================================================================
# 6. SIDEBAR
# ==========================================================================
with st.sidebar:
    st.markdown("### 🎬 TRIBUNA")
    st.caption("Hollywood Cut")
    page = st.radio(
        "Navegação",
        ["🎟️ Treino diário", "🎭 Simulador de papo", "🎙️ Feedback de oratória", "🏆 Sala de troféus"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Groq API**")
    has_env_key = bool(os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", None))
    if has_env_key:
        st.caption("Chave carregada do ambiente/secrets ✓")
    else:
        st.session_state["groq_api_key"] = st.text_input(
            "Cole sua GROQ_API_KEY", type="password", value=st.session_state.get("groq_api_key", "")
        )
        st.caption("Chave grátis em console.groq.com")
    st.session_state["model"] = st.selectbox(
        "Modelo", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"], index=0
    )


# ==========================================================================
# 7. PÁGINA: TREINO DIÁRIO
# ==========================================================================
if page == "🎟️ Treino diário":
    marquee("TRIBUNA", "AGORA EM CARTAZ", "o treino diário de confiança, oratória, papo e charme")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Noites seguidas", f"{state['streak']} 🔥")
    with c2:
        st.metric("Sessões no total", sum(state["totals"].values()))

    st.progress(sum(1 for c in CATEGORIES if day[c]["done"]) / len(CATEGORIES))
    st.caption("Complete as 4 cenas de hoje pra manter o show no ar.")
    filmstrip()

    for cat, meta in CATEGORIES.items():
        idx = day[cat]["index"]
        text = meta["items"][idx]
        done = day[cat]["done"]
        with st.container(border=True):
            st.markdown(
                f'<span class="award-badge" style="background:{meta["color"]}22; color:{meta["color"]}">'
                f'{meta["trophy"]} MELHOR CENA — {meta["label"].upper()}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(f"~~{text}~~" if done else f"**{text}**")
            b1, b2, _ = st.columns([1, 1, 3])
            with b1:
                if st.button("✓ Feito" if done else "Marcar feito", key=f"done_{cat}"):
                    toggle_done(cat)
                    st.rerun()
            with b2:
                if st.button("⟳ Trocar cena", key=f"refresh_{cat}"):
                    refresh_card(cat)
                    st.rerun()

    filmstrip()
    st.markdown("##### Bastidores — progresso por categoria")
    for cat, meta in CATEGORIES.items():
        st.write(f"{meta['trophy']} {meta['label']}")
        st.progress(min(state["totals"].get(cat, 0) / 20, 1.0))


# ==========================================================================
# 8. PÁGINA: SIMULADOR DE PAPO
# ==========================================================================
elif page == "🎭 Simulador de papo":
    marquee("TESTE DE ELENCO", "AUDIÇÃO AO VIVO", "pratique a cena com uma persona de IA")

    st.caption(
        "Treino de conversação com um parceiro de cena de IA. Tom sempre leve, "
        "respeitoso e apropriado — o objetivo é treinar charme e presença, não gerar "
        "conteúdo explícito."
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    scene = st.selectbox(
        "Escolha a cena",
        [
            "Conhecendo alguém numa festa",
            "Papo leve com um colega de trabalho no café",
            "Conversa numa primeira saída",
            "Reencontro com alguém que você não vê há um tempo",
        ],
    )

    if st.button("🎬 Novo take (reiniciar)"):
        st.session_state.chat_history = []
        st.rerun()

    scene_prompts = {
        "Conhecendo alguém numa festa": "Você é alguém simpático e espontâneo numa festa, puxando papo com o usuário pela primeira vez.",
        "Papo leve com um colega de trabalho no café": "Você é um colega de trabalho numa pausa pro café, num tom leve e profissionalmente apropriado.",
        "Conversa numa primeira saída": "Você está numa primeira saída com o usuário, curioso(a) e um pouco tímido(a), mas aberto(a).",
        "Reencontro com alguém que você não vê há um tempo": "Você reencontrou o usuário depois de um tempo, com curiosidade genuína sobre a vida dele(a).",
    }
    system_prompt = (
        f"{scene_prompts[scene]} Responda sempre em português, em 1 a 3 frases, de forma "
        "natural e humana — nunca robótica. Mantenha o tom leve, respeitoso e apropriado; "
        "nunca gere conteúdo sexual ou explícito. O objetivo é treinar conversação, charme "
        "e confiança social do usuário."
    )

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_msg = st.chat_input("Sua fala...")
    if user_msg:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.write(user_msg)
        messages = [{"role": "system", "content": system_prompt}] + st.session_state.chat_history
        with st.chat_message("assistant"):
            with st.spinner("gravando a cena..."):
                reply = groq_chat(messages, st.session_state.get("model", "llama-3.3-70b-versatile"))
            if reply is None:
                st.warning("Adicione sua GROQ_API_KEY na barra lateral pra ativar o teste de elenco.")
            else:
                st.write(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

    if len(st.session_state.chat_history) >= 4 and st.button("🎥 Pedir corte do diretor (feedback)"):
        transcript = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.chat_history)
        coach_prompt = (
            "Você é um coach de comunicação e carisma, com tom de diretor de cinema dando "
            "notas depois de um take. Analise a conversa abaixo do ponto de vista do usuário "
            "(role 'user') e dê um feedback curto em português, em tópicos: o que funcionou "
            "bem, um ponto pra melhorar, e uma sugestão prática pro próximo take. Direto, "
            "construtivo e encorajador.\n\n" + transcript
        )
        with st.spinner("o diretor está assistindo o replay..."):
            feedback = groq_chat(
                [{"role": "user", "content": coach_prompt}],
                st.session_state.get("model", "llama-3.3-70b-versatile"),
                temperature=0.5,
            )
        st.info(feedback) if feedback else st.warning("Adicione sua GROQ_API_KEY na barra lateral.")


# ==========================================================================
# 9. PÁGINA: FEEDBACK DE ORATÓRIA
# ==========================================================================
elif page == "🎙️ Feedback de oratória":
    marquee("LEITURA DE MESA", "SESSÃO DE ENSAIO", "cole sua fala e receba a nota do diretor")

    speech = st.text_area(
        "Seu texto ou transcrição", height=200,
        placeholder="Cole aqui o que você falou ou pretende falar..."
    )

    if st.button("🎬 Rodar análise"):
        if not speech.strip():
            st.warning("Cole algum texto primeiro.")
        else:
            prompt = (
                "Você é um coach de oratória com tom de diretor de cinema revisando uma leitura "
                "de mesa. Analise o texto abaixo e dê feedback em português, cobrindo: clareza, "
                "ritmo/estrutura, muletas de linguagem (tipo 'é', 'tipo', 'né'), confiança "
                "percebida no tom, e uma sugestão prática de melhoria. Direto e construtivo, "
                f"em no máximo 200 palavras.\n\nTexto: {speech}"
            )
            with st.spinner("o diretor está anotando..."):
                feedback = groq_chat(
                    [{"role": "user", "content": prompt}],
                    st.session_state.get("model", "llama-3.3-70b-versatile"),
                    temperature=0.4,
                )
            if feedback:
                st.success("Nota do diretor:")
                st.write(feedback)
            else:
                st.warning("Adicione sua GROQ_API_KEY na barra lateral pra ativar a análise.")


# ==========================================================================
# 10. PÁGINA: SALA DE TROFÉUS (progresso)
# ==========================================================================
elif page == "🏆 Sala de troféus":
    marquee("SALA DE TROFÉUS", "NOITE DE PREMIAÇÃO", "seu histórico de sessões, categoria por categoria")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Sequência atual", f"{state['streak']} noites")
    with c2:
        st.metric("Sessões totais", sum(state["totals"].values()))

    filmstrip()
    st.markdown("##### Estatuetas por categoria")
    st.bar_chart(state["totals"])

    filmstrip()
    st.caption(f"Progresso salvo localmente. Hoje é {date.today().strftime('%d/%m/%Y')}.")
