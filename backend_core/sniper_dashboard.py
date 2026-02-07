
import streamlit as st
import json
import pandas as pd
import time
import os
import plotly.express as px
from datetime import datetime

# Configuração da Página
st.set_page_config(
    page_title="SNIPER V3 CHIMERA - Command Center",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Título e Status ---
st.title(" SNIPER V3 CHIMERA - Neural Command Center")
st.markdown("### *Protocolo Antifrágil de Aprendizado por Reforço*")

# --- Carregamento de Dados ---
def load_status():
    try:
        if os.path.exists("sniper_status.json"):
            with open("sniper_status.json", "r") as f:
                return json.load(f)
    except:
        return None
    return None

def load_memory():
    try:
        if os.path.exists("trade_memory.json"):
            with open("trade_memory.json", "r") as f:
                return json.load(f)
    except:
        return []
    return []

def load_config():
    try:
        if os.path.exists("risk_config.json"):
            with open("risk_config.json", "r") as f:
                return json.load(f)
    except:
        return {}
    return {}

# --- Auto-Refresh (Hack para Streamlit) ---
if st.button(" Atualizar Dados"):
    st.rerun()

# --- Layout Principal ---
col1, col2 = st.columns([2, 1])

# --- Coluna 1: Status em Tempo Real (O Cérebro) ---
with col1:
    st.subheader(" Status Operacional (Live)")
    status = load_status()
    
    if status:
        # Estado Geral
        state = status.get("state", "UNKNOWN")
        symbol = status.get("symbol", "N/A")
        ts = status.get("human_time", "-")
        
        # Color Code do Estado
        state_color = "gray"
        if state == "SCANNING": state_color = "blue"
        elif state == "IN_POSITION": state_color = "green"
        elif state == "LOCKOUT": state_color = "orange"
        elif state == "ALIGNMENT_FOUND": state_color = "red"
        
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; background-color: rgba(255,255,255,0.05); border: 2px solid {state_color};">
            <h2 style="color: {state_color}; margin:0;">{state}</h2>
            <p style="margin:0;">Ativo: <strong>{symbol}</strong> | Última Atualização: {ts}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Dados da Última Checagem
        data = status.get("data", {})
        if state == "SCANNING" or state == "ALIGNMENT_FOUND":
            context = data.get("context", {})
            approved = data.get("approved", False)
            reason = data.get("reason", "")
            side = data.get("side", "-")
            price = data.get("price", 0)
            
            st.divider()
            st.markdown(f"####  Raio-X da Decisão ({side} @ ${price})")
            
            # Indicadores Chave
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("OBI (Fluxo)", f"{context.get('obi', 0):.2f}", delta_color="normal")
            with m2:
                st.metric("Spread", f"{context.get('spread', 0)*100:.4f}%")
            with m3:
                funding = context.get("funding_rate", 0)
                st.metric("Funding Rate", f"{funding*100:.4f}%", delta_color="inverse")
            with m4:
                vol = context.get("volume_24h", 0) / 1_000_000
                st.metric("Volume 24h", f"${vol:.1f}M")
            
            # Veredito
            if approved:
                st.success(f" APROVADO: {reason}")
            else:
                st.error(f" REJEITADO: {reason}")
                
        elif state == "IN_POSITION":
            st.success(f" POSIÇÃO ATIVA! Entrada: ${data.get('entry_price')}")
            st.info("Monitorando Zero Loss (Breakeven)...")
            
    else:
        st.warning("️ Sniper Offline ou Aguardando Dados...")

# --- Coluna 2: Configuração Dinâmica (O Aprendizado) ---
with col2:
    st.subheader(" Cérebro Evolutivo (Chimera)")
    config = load_config()
    
    if config:
        st.json(config)
        st.caption("Estes parâmetros são ajustados automaticamente pelo Learning Engine após cada erro.")
    else:
        st.info("Configuração Padrão Ativa.")

# --- Histórico e Aprendizado ---
st.divider()
st.subheader(" Diário de Bordo (Black Box Memory)")

memory = load_memory()
if memory:
    # Converter para DataFrame para melhor visualização
    df = pd.json_normalize(memory)
    
    # Selecionar colunas relevantes se existirem
    cols_to_show = ['human_time', 'symbol', 'side', 'result.pnl_percent', 'result.exit_reason', 'context.obi', 'context.spread']
    
    # Filtrar colunas que existem no df
    cols = [c for c in cols_to_show if c in df.columns]
    
    if not df.empty:
        # Ordenar por tempo (recente primeiro)
        df = df.sort_values(by='timestamp', ascending=False)
        
        # Colorir PnL
        def color_pnl(val):
            if pd.isna(val): return ''
            color = 'green' if val > 0 else 'red'
            return f'color: {color}'

        st.dataframe(df[cols].style.applymap(color_pnl, subset=['result.pnl_percent']), use_container_width=True)
else:
    st.info("Nenhum trade registrado na memória ainda.")

# --- Footer ---
st.divider()
st.markdown("*Sistema desenvolvido sob o Protocolo Omega V3 - DoubleGreen Capital*")
