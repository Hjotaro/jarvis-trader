import os
import requests
import yfinance as yf
import pandas as pd

# --- CONFIGURAÇÕES ---
# Lista de ativos para vigiar
WATCHLIST = ["BTC-USD", "ETH-USD", "XRP-USD", "DOGE-USD", "PAXG-USD"]

# Setup: Gráfico de 1 Hora (H1) com Médias 40 e 60
TIME_FRAME = "1h"
MA_FAST = 40
MA_SLOW = 60

# --- CREDENCIAIS ---
# Apenas Telegram (Não precisa de Binance aqui)
try:
    TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
    TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
except KeyError:
    print("Erro: Tokens do Telegram não encontrados.")
    exit()

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Erro no Telegram: {e}")

def analisar_mercado():
    print(f"🦅 J.A.R.V.I.S. Sentinela | Monitorando {len(WATCHLIST)} ativos...")
    
    for ativo in WATCHLIST:
        try:
            # Baixa dados do Yahoo Finance (Sem bloqueio de IP)
            df = yf.download(ativo, period="7d", interval=TIME_FRAME, progress=False)
            
            if len(df) < MA_SLOW: continue

            # Tratamento de dados
            if isinstance(df.columns, pd.MultiIndex):
                close = df["Close"].iloc[:, 0]
            else:
                close = df["Close"]

            # Calcula as Médias Móveis
            df['Fast'] = close.rolling(window=MA_FAST).mean()
            df['Slow'] = close.rolling(window=MA_SLOW).mean()

            # Pega os últimos valores
            atual_fast = df['Fast'].iloc[-1]
            atual_slow = df['Slow'].iloc[-1]
            prev_fast = df['Fast'].iloc[-2]
            prev_slow = df['Slow'].iloc[-2]
            preco_atual = float(close.iloc[-1])
            
            nome_limpo = ativo.replace("-USD", "")

            # --- LÓGICA DE ALERTA ---
            
            # Cruzamento para CIMA (Compra)
            if prev_fast <= prev_slow and atual_fast > atual_slow:
                msg = (
                    f"🚀 *SINAL DE COMPRA DETECTADO*\n\n"
                    f"💎 *Ativo:* {nome_limpo}\n"
                    f"💵 *Preço:* ${preco_atual:.2f}\n"
                    f"📈 *Sinal:* Média {MA_FAST} cruzou ACIMA da {MA_SLOW}\n\n"
                    f"⚡ *Ação:* Verifique o gráfico e COMPRE se confirmar!"
                )
                enviar_telegram(msg)
                print(f"🚀 Alerta de COMPRA enviado para {ativo}")

            # Cruzamento para BAIXO (Venda)
            elif prev_fast >= prev_slow and atual_fast < atual_slow:
                msg = (
                    f"🚨 *SINAL DE VENDA DETECTADO*\n\n"
                    f"🔻 *Ativo:* {nome_limpo}\n"
                    f"💵 *Preço:* ${preco_atual:.2f}\n"
                    f"📉 *Sinal:* Média {MA_FAST} cruzou ABAIXO da {MA_SLOW}\n\n"
                    f"🛡️ *Ação:* Hora de realizar lucro ou proteger capital!"
                )
                enviar_telegram(msg)
                print(f"🚨 Alerta de VENDA enviado para {ativo}")
            
            else:
                print(f"💤 {ativo}: Neutro. (${preco_atual:.2f})")

        except Exception as e:
            print(f"Erro ao analisar {ativo}: {e}")

if __name__ == "__main__":
    analisar_mercado()
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
            # Baixa dados do Yahoo
            df = yf.download(yf_symbol, period="7d", interval=TIME_FRAME, progress=False)
            
            # Se não tiver dados suficientes, pula
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
            
