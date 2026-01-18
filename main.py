import os
import requests
import yfinance as yf
import pandas as pd

# --- 1. CONFIGURAÇÕES GERAIS ---
# A lista oficial de ativos (Cripto + Ouro Digital)
WATCHLIST = ["BTC-USD", "ETH-USD", "XRP-USD", "DOGE-USD", "PAXG-USD"]

# Configuração da Estratégia Campeã (H1 + Médias 40/60)
TIME_FRAME = "1h"  # Gráfico de 1 Hora
MA_FAST = 40       # Média Rápida
MA_SLOW = 60       # Média Lenta

# Credenciais do Telegram (Puxadas dos Secrets do GitHub)
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# --- 2. FUNÇÃO DE ENVIO PARA O TELEGRAM ---
def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

# --- 3. CÉREBRO DO ROBÔ (ANÁLISE TÉCNICA) ---
def analisar_mercado():
    print(f"🦅 J.A.R.V.I.S. Iniciando varredura no H1 ({MA_FAST}/{MA_SLOW})...")
    sinais_encontrados = 0

    for ativo in WATCHLIST:
        try:
            # Baixa os dados dos últimos 7 dias (suficiente para calcular média de 60h)
            df = yf.download(ativo, period="7d", interval=TIME_FRAME, progress=False)
            
            # Ajuste para garantir que temos dados suficientes
            if len(df) < MA_SLOW:
                print(f"⚠️ Dados insuficientes para {ativo}")
                continue

            # --- CÁLCULO DAS MÉDIAS MÓVEIS ---
            # Usa 'Close' para o cálculo. O yfinance às vezes retorna MultiIndex, garantimos o flatten.
            if isinstance(df.columns, pd.MultiIndex):
                close_prices = df["Close"].iloc[:, 0]
            else:
                close_prices = df["Close"]

            df['Fast'] = close_prices.rolling(window=MA_FAST).mean()
            df['Slow'] = close_prices.rolling(window=MA_SLOW).mean()

            # --- LEITURA DO MOMENTO ATUAL ---
            # Pegamos o último preço (atual) e o penúltimo (hora anterior)
            atual_fast = df['Fast'].iloc[-1]
            atual_slow = df['Slow'].iloc[-1]
            atual_price = float(close_prices.iloc[-1])
            
            prev_fast = df['Fast'].iloc[-2]
            prev_slow = df['Slow'].iloc[-2]

            # Nome bonitinho para o ativo (tira o -USD)
            nome_ativo = ativo.replace("-USD", "")
            if "PAXG" in nome_ativo: nome_ativo = "OURO (PAXG)"

            # --- LÓGICA DE SINAIS (CRUZAMENTOS) ---
            
            # 🟢 SINAL DE COMPRA (Golden Cross)
            # A rápida cruzou para CIMA da lenta
            if prev_fast <= prev_slow and atual_fast > atual_slow:
                msg = (
                    f"🚀 *SINAL DE COMPRA CONFIRMADO*\n\n"
                    f"💎 *Ativo:* {nome_ativo}\n"
                    f"💵 *Preço:* ${atual_price:.2f}\n"
                    f"📈 *Médias:* {atual_fast:.2f} (Rápida) cruzou acima de {atual_slow:.2f}\n\n"
                    f"⚡ *Ação:* Comprar Spot (20% da Banca)"
                )
                enviar_telegram(msg)
                print(f"🟢 SINAL ENVIADO: {ativo}")
                sinais_encontrados += 1

            # 🔴 SINAL DE VENDA/PROTEÇÃO (Death Cross)
            # A rápida cruzou para BAIXO da lenta
            elif prev_fast >= prev_slow and atual_fast < atual_slow:
                msg = (
                    f"🚨 *SINAL DE VENDA (PROTEÇÃO)*\n\n"
                    f"🔻 *Ativo:* {nome_ativo}\n"
                    f"💵 *Preço:* ${atual_price:.2f}\n"
                    f"📉 *Médias:* {atual_fast:.2f} (Rápida) cruzou abaixo de {atual_slow:.2f}\n\n"
                    f"🛡️ *Ação:* Vender tudo e ficar em Dólar (USDT)"
                )
                enviar_telegram(msg)
                print(f"🔴 SINAL ENVIADO: {ativo}")
                sinais_encontrados += 1
            
            else:
                # Apenas log no GitHub para sabermos que ele analisou
                tendencia = "ALTA" if atual_fast > atual_slow else "BAIXA"
                print(f"🔎 {ativo}: Sem mudanças. Tendência de {tendencia}.")

        except Exception as e:
            print(f"❌ Erro ao analisar {ativo}: {e}")

    # Mensagem final no log
    if sinais_encontrados == 0:
        print("✅ Varredura concluída. Nenhum cruzamento novo nesta hora.")
    else:
        print(f"✅ Varredura concluída. {sinais_encontrados} sinais enviados.")

# --- 4. EXECUÇÃO ---
if __name__ == "__main__":
    analisar_mercado()
