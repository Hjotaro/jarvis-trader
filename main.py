import os
import requests
import pandas as pd
import yfinance as yf
import warnings
import numpy as np

# --- CONFIGURAÇÃO ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ATIVOS = ["BTC-USD", "ETH-USD", "XRP-USD", "DOGE-USD", "PAXG-USD"]

# PARÂMETROS CAMPEÕES (V15 - Otimizado 40/60)
MA_FAST = 40
MA_SLOW = 60

warnings.simplefilter(action='ignore', category=FutureWarning)

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def analisar_ativo(symbol):
    try:
        # Baixa dados (H1)
        df = yf.download(symbol, period="1mo", interval="1h", progress=False, multi_level_index=False)
        df = df.dropna()
        if len(df) < 100: return None

        # Dados
        close = df['Close']
        high = df['High']
        low = df['Low']

        # --- CÁLCULO DA ESTRATÉGIA ---
        sma_fast = close.rolling(window=MA_FAST).mean()
        sma_slow = close.rolling(window=MA_SLOW).mean()

        # ATR (Volatilidade para Stop)
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        # Valores atuais
        curr_price = float(close.iloc[-1])
        curr_fast = float(sma_fast.iloc[-1])
        curr_slow = float(sma_slow.iloc[-1])
        curr_atr = float(atr.iloc[-1])
        
        # Valores anteriores
        prev_fast = float(sma_fast.iloc[-2])
        prev_slow = float(sma_slow.iloc[-2])

        sinal, icone, direcao = None, "", ""

        # --- GATILHOS ---
        # Cruzou para CIMA
        if curr_fast > curr_slow and prev_fast <= prev_slow:
            sinal = f"COMPRA (Golden {MA_FAST}/{MA_SLOW})"
            icone = "🟢"
            direcao = "LONG"
            
        # Cruzou para BAIXO
        elif curr_fast < curr_slow and prev_fast >= prev_slow:
            sinal = f"VENDA (Death {MA_FAST}/{MA_SLOW})"
            icone = "🔴"
            direcao = "SHORT"

        if sinal:
            # Stop Loss (3x ATR)
            stop_dist = 3.0 * curr_atr
            stop_loss = curr_price - stop_dist if direcao == "LONG" else curr_price + stop_dist

            return (
                f"{icone} *{sinal}* | {symbol.replace('-USD','')}\n"
                f"💵 Preço: {curr_price:.2f}\n"
                f"📈 Médias: {curr_fast:.2f} / {curr_slow:.2f}\n"
                f"🛡️ Stop: {stop_loss:.2f}\n"
                f"🚀 Alvo: Aberto (Tendência)"
            )
            
        return None

    except Exception as e: 
        print(f"Erro ao analisar {symbol}: {e}")
        return None

if __name__ == "__main__":
    print(f"🦅 J.A.R.V.I.S. V15 (Elite) | Setup: {MA_FAST}/{MA_SLOW}")
    mensagens = []
    
    for symbol in WATCHLIST:
        res = analisar_ativo(symbol)
        if res: mensagens.append(res)

    if mensagens:
        full_msg = "🚨 *SINAL CONFIRMADO (H1)*\n\n" + "\n-------------------\n".join(mensagens)
        enviar_telegram(full_msg)
    else:
        print("Monitorando... Sem sinais agora.")
