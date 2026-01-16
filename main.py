import os
import requests
import pandas as pd
import yfinance as yf
import warnings
import numpy as np

# --- CONFIGURAÇÃO SEGURA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Lista de ativos
WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", 
    "BNB-USD", "XRP-USD", "LINK-USD",
    "DOGE-USD", "ADA-USD"
]

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
        # Baixa dados (60 dias H1)
        df = yf.download(symbol, period="60d", interval="1h", progress=False, multi_level_index=False)
        df = df.dropna()
        if df.empty or len(df) < 200: return None

        # Dados Básicos
        close = df['Close']
        high = df['High']
        low = df['Low']

        # Médias e RSI
        sma200 = close.rolling(200).mean()
        sma50  = close.rolling(50).mean()
        rsi = calcular_rsi(close)

        # --- CÁLCULO DO ATR (Volatilidade) ---
        # ATR é essencial para calcular Stop/Alvo dinâmicos
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        # Pegando valores atuais
        curr_price = float(close.iloc[-1])
        curr_rsi = float(rsi.iloc[-1])
        curr_sma200 = float(sma200.iloc[-1])
        curr_sma50 = float(sma50.iloc[-1])
        curr_atr = float(atr.iloc[-1])

        # Lógica de Tendência
        trend_alta = curr_price > curr_sma200 and curr_sma50 > curr_sma200
        trend_baixa = curr_price < curr_sma200 and curr_sma50 < curr_sma200
        
        sinal, icone, direcao = None, "", ""

        # SETUP COMPRA
        if trend_alta:
            if curr_rsi <= 35: 
                sinal = "COMPRA (Sobrevendido)"
                icone = "💎"
                direcao = "LONG"
            elif 35 < curr_rsi <= 45: 
                sinal = "COMPRA (Pullback)"
                icone = "🦅"
                direcao = "LONG"
        
        # SETUP VENDA
        elif trend_baixa:
            if curr_rsi >= 65: 
                sinal = "VENDA (Topo)"
                icone = "🔴"
                direcao = "SHORT"

        if sinal:
            # --- CÁLCULO DE ALVOS (Math) ---
            stop_loss = 0.0
            take_profit = 0.0

            if direcao == "LONG":
                stop_loss = curr_price - (2.5 * curr_atr)
                take_profit = curr_price + (4.0 * curr_atr)
            else:
                stop_loss = curr_price + (2.5 * curr_atr)
                take_profit = curr_price - (4.0 * curr_atr)

            return (
                f"{icone} *{sinal}* | {symbol.replace('-USD','')}\n"
                f"💵 Entrada: {curr_price:.2f}\n"
                f"🛑 Stop: {stop_loss:.2f}\n"
                f"🎯 Alvo: {take_profit:.2f}\n"
                f"📊 RSI: {curr_rsi:.0f} | ATR: {curr_atr:.2f}"
            )
            
        return None

    except Exception: return None

if __name__ == "__main__":
    print("🚀 J.A.R.V.I.S. V147 - Analisando...")
    mensagens = []
    
    for symbol in WATCHLIST:
        res = analisar_ativo(symbol)
        if res: mensagens.append(res)

    if mensagens:
        full_msg = "⚡ *NOVOS SINAIS (H1)*\n\n" + "\n-------------------\n".join(mensagens)
        enviar_telegram(full_msg)
        print("Sinais enviados.")
    else:
        print("Sem oportunidades agora.")
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
