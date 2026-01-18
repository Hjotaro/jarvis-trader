import os
import requests
import yfinance as yf
import pandas as pd
import ccxt
import time

# --- 1. CONFIGURAÇÕES ---
# Mapeamento: O nome no Yahoo Finance -> O nome na Binance
ASSET_MAP = {
    "BTC-USD": "BTC/USDT",
    "ETH-USD": "ETH/USDT",
    "XRP-USD": "XRP/USDT",
    "DOGE-USD": "DOGE/USDT",
    "PAXG-USD": "PAXG/USDT"
}

WATCHLIST = list(ASSET_MAP.keys())
TIME_FRAME = "1h"
MA_FAST = 40
MA_SLOW = 60

# Configuração de Risco: Quanto da banca usar por trade?
PCT_BANCA = 0.20  # 20% do saldo livre em USDT

# Credenciais
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
API_KEY = os.environ["BINANCE_API_KEY"]
SECRET_KEY = os.environ["BINANCE_SECRET_KEY"]

# Conexão com a Binance via CCXT
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

# --- 2. FUNÇÕES AUXILIARES ---

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def executar_ordem(symbol, lado, preco_atual):
    try:
        # Carrega saldo atualizado
        balance = exchange.fetch_balance()
        usdt_livre = balance['USDT']['free']
        
        # Separa o símbolo da moeda (ex: BTC/USDT -> BTC)
        moeda_base = symbol.split('/')[0]
        qtd_moeda = balance[moeda_base]['free']

        if lado == 'buy':
            # Regra: Só compra se tiver USDT suficiente
            custo_estimado = usdt_livre * PCT_BANCA
            
            # Trava de segurança: Mínimo $6 USD (Binance pede min $5)
            if custo_estimado < 6.0:
                print(f"⚠️ Saldo USDT insuficiente (${usdt_livre:.2f}) para operar {symbol}.")
                return False

            # Calcula quantidade
            quantidade = custo_estimado / preco_atual
            
            # Ajusta precisão da Binance (MUITO IMPORTANTE)
            amount = exchange.amount_to_precision(symbol, quantidade)
            
            # Envia Ordem
            order = exchange.create_market_buy_order(symbol, amount)
            msg = f"🚀 *ORDEM EXECUTADA (COMPRA)*\n\n✅ Comprei: {amount} {moeda_base}\n💵 Valor: ${custo_estimado:.2f}"
            enviar_telegram(msg)
            return True

        elif lado == 'sell':
            # Regra: Vende tudo o que tem da moeda
            amount = exchange.amount_to_precision(symbol, qtd_moeda)
            
            # Valor nocional (Qtd * Preço) deve ser > $5
            if (float(amount) * preco_atual) < 5.5:
                print(f"⚠️ Quantidade de {moeda_base} muito pequena para vender.")
                return False
                
            order = exchange.create_market_sell_order(symbol, amount)
            msg = f"🛡️ *ORDEM EXECUTADA (VENDA)*\n\n✅ Vendi: {amount} {moeda_base}\n💵 Voltamos para USDT."
            enviar_telegram(msg)
            return True

    except Exception as e:
        print(f"❌ ERRO CRÍTICO NA BINANCE: {e}")
        enviar_telegram(f"⚠️ *ERRO DE EXECUÇÃO*\n\nNão consegui operar {symbol}.\nErro: {e}")
        return False

# --- 3. CÉREBRO (ANÁLISE) ---
def analisar_mercado():
    print(f"🦅 J.A.R.V.I.S. V16 (Executor) | Setup: {MA_FAST}/{MA_SLOW}")
    
    for yf_symbol in WATCHLIST:
        binance_symbol = ASSET_MAP[yf_symbol] # Converte nome para Binance
        
        try:
            # Baixa dados do Yahoo (Para não gastar API da Binance com histórico)
            df = yf.download(yf_symbol, period="7d", interval=TIME_FRAME, progress=False)
            
            if len(df) < MA_SLOW: continue

            # Tratamento de dados
            if isinstance(df.columns, pd.MultiIndex):
                close = df["Close"].iloc[:, 0]
            else:
                close = df["Close"]

            df['Fast'] = close.rolling(window=MA_FAST).mean()
            df['Slow'] = close.rolling(window=MA_SLOW).mean()

            # Dados Atuais
            atual_fast = df['Fast'].iloc[-1]
            atual_slow = df['Slow'].iloc[-1]
            prev_fast = df['Fast'].iloc[-2]
            prev_slow = df['Slow'].iloc[-2]
            preco_atual = float(close.iloc[-1])

            # --- LÓGICA DE EXECUÇÃO ---
            
            # 🟢 COMPRA
            if prev_fast <= prev_slow and atual_fast > atual_slow:
                print(f"🚀 SINAL DE COMPRA: {binance_symbol}")
                executar_ordem(binance_symbol, 'buy', preco_atual)

            # 🔴 VENDA
            elif prev_fast >= prev_slow and atual_fast < atual_slow:
                print(f"🚨 SINAL DE VENDA: {binance_symbol}")
                executar_ordem(binance_symbol, 'sell', preco_atual)
            
            else:
                print(f"💤 {binance_symbol}: Neutro. (${preco_atual:.2f})")

        except Exception as e:
            print(f"Erro em {yf_symbol}: {e}")

if __name__ == "__main__":
    analisar_mercado()
            
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
