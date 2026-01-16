import os
import requests
import pandas as pd
import yfinance as yf
import warnings
import numpy as np

# --- CONFIGURAÇÃO SEGURA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

WATCHLIST = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"]

warnings.simplefilter(action='ignore', category=FutureWarning)

def enviar_telegram(mensagem):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, min_periods=period).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, min_periods=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analisar_ativo(symbol):
    try:
        df = yf.download(symbol, period="60d", interval="1h", progress=False)
        if df.empty or len(df) < 200: return None
        
        close = df['Close']
        sma200 = close.rolling(200).mean()
        sma50 = close.rolling(50).mean()
        rsi = calcular_rsi(close)
        
        curr_price = float(close.iloc[-1])
        curr_rsi = float(rsi.iloc[-1])
        curr_sma200 = float(sma200.iloc[-1])
        curr_sma50 = float(sma50.iloc[-1])

        trend_alta = curr_price > curr_sma200 and curr_sma50 > curr_sma200
        trend_baixa = curr_price < curr_sma200 and curr_sma50 < curr_sma200
        
        sinal = None
        if trend_alta:
            if curr_rsi <= 35: sinal = f"💎 COMPRA (RSI {curr_rsi:.0f})"
            elif 35 < curr_rsi <= 45: sinal = f"🦅 COMPRA (RSI {curr_rsi:.0f})"
        elif trend_baixa:
            if curr_rsi >= 65: sinal = f"🔴 VENDA (RSI {curr_rsi:.0f})"

        if sinal:
            return f"{sinal} *{symbol.replace('-USD','')}*\n💵 Px: {curr_price:.2f}"
        return None
    except: return None

if __name__ == "__main__":
    print("🚀 Verificando mercado...")
    msgs = []
    for symbol in WATCHLIST:
        res = analisar_ativo(symbol)
        if res: msgs.append(res)
    
    if msgs:
        full_msg = "⚡ *ALERTA H1 (GitHub)*\n\n" + "\n-------------------\n".join(msgs)
        enviar_telegram(full_msg)
        print("Sinais enviados.")
    else:
        print("Sem sinais agora.")
