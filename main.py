import os
import requests
import pandas as pd
import yfinance as yf
import warnings
import numpy as np

# --- CONFIGURAÇÃO ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Lista de ativos
WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", 
    "BNB-USD", "XRP-USD", "DOGE-USD"
]

# PARÂMETROS CAMPEÕES (Validado via Grid Search: +163% de Lucro)
MA_FAST = 40
MA_SLOW = 70

warnings.simplefilter(action='ignore', category=FutureWarning)

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def analisar_ativo(symbol):
    try:
        # Baixa dados suficientes para calcular a média de 70 períodos
        df = yf.download(symbol, period="1mo", interval="1h", progress=False, multi_level_index=False)
        df = df.dropna()
        if len(df) < 100: return None

        # Dados Básicos
        close = df['Close']
        high = df['High']
        low = df['Low']

        # --- A ESTRATÉGIA CAMPEÃ (SMA 40/70) ---
        sma_fast = close.rolling(window=MA_FAST).mean()
        sma_slow = close.rolling(window=MA_SLOW).mean()

        # ATR para Stop de Segurança
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        # Valores atuais e anteriores
        curr_price = float(close.iloc[-1])
        curr_fast = float(sma_fast.iloc[-1])
        curr_slow = float(sma_slow.iloc[-1])
        curr_atr = float(atr.iloc[-1])
        
        prev_fast = float(sma_fast.iloc[-2])
        prev_slow = float(sma_slow.iloc[-2])

        sinal, icone, direcao = None, "", ""

        # --- LÓGICA DE CRUZAMENTO ---
        
        # Cruzou para CIMA (Compra)
        if curr_fast > curr_slow and prev_fast <= prev_slow:
            sinal = "COMPRA (Golden 40/70)"
            icone = "🟢"
            direcao = "LONG"
            
        # Cruzou para BAIXO (Venda)
        elif curr_fast < curr_slow and prev_fast >= prev_slow:
            sinal = "VENDA (Death 40/70)"
            icone = "🔴"
            direcao = "SHORT"

        if sinal:
            # Stop Loss de segurança (3x ATR)
            stop_loss = 0.0
            
            if direcao == "LONG":
                stop_loss = curr_price - (3.0 * curr_atr)
            else:
                stop_loss = curr_price + (3.0 * curr_atr)

            return (
                f"{icone} *{sinal}* | {symbol.replace('-USD','')}\n"
                f"💵 Preço: {curr_price:.2f}\n"
                f"📈 Média Rápida ({MA_FAST}): {curr_fast:.2f}\n"
                f"📉 Média Lenta ({MA_SLOW}): {curr_slow:.2f}\n"
                f"🛑 Stop Sugerido: {stop_loss:.2f}\n"
                f"🎯 Alvo: Aberto (Seguir Tendência)"
            )
            
        return None

    except Exception as e: 
        print(f"Erro em {symbol}: {e}")
        return None

if __name__ == "__main__":
    print(f"🚀 J.A.R.V.I.S. V12 - Monitorando Médias {MA_FAST}/{MA_SLOW}...")
    mensagens = []
    
    for symbol in WATCHLIST:
        res = analisar_ativo(symbol)
        if res: mensagens.append(res)

    if mensagens:
        full_msg = "🏆 *SINAL CONFIRMADO (H1)*\n\n" + "\n-------------------\n".join(mensagens)
        enviar_telegram(full_msg)
        print("Sinais enviados.")
    else:
        print("Sem cruzamentos novos. Tendência mantida.")
