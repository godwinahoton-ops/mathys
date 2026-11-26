from datetime import datetime
import numpy as np
import pandas as pd
import requests
import yfinance as yf

# Paramètres Telegram
TELEGRAM_TOKEN = "9100690235:AAGxp14SDWOBAcDpj4HTu5tS4QZARuNGcrg"
TELEGRAM_CHAT_ID = "8875346326"


def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(
            f"Réponse Telegram - Code : {response.status_code}, "
            f"Texte : {response.text}"
        )
    except Exception as e:
        print(f"Erreur d'envoi Telegram : {e}")


def run_analysis():
    ticker = "GC=F"
    df = yf.download(ticker, period="1mo", interval="1h", progress=False)

    if df.empty or len(df) <= 105:
        print("Données insuffisantes pour l'analyse.")
        return

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    time_col = "Datetime" if "Datetime" in df.columns else "Date"
    df["time"] = pd.to_datetime(df[time_col])

    # Indicateurs
    df["ema100"] = df["Close"].ewm(span=100, adjust=False).mean()
    df["sma9"] = df["Close"].rolling(window=9).mean()
    df["sma20"] = df["Close"].rolling(window=20).mean()

    # ATR (14 périodes)
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    df["atr"] = ranges.max(axis=1).rolling(window=14).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    entry_price = float(last["Close"])
    atr_val = float(last["atr"])
    candle_time = last["time"].strftime("%Y-%m-%d %H:%M")

    bullish_trend = float(last["Close"]) > float(last["ema100"])
    bearish_trend = float(last["Close"]) < float(last["ema100"])
    buy_cross = (
        float(prev["sma9"]) <= float(prev["sma20"])
        and float(last["sma9"]) > float(last["sma20"])
    )
    sell_cross = (
        float(prev["sma9"]) >= float(prev["sma20"])
        and float(last["sma9"]) < float(last["sma20"])
    )

    if bullish_trend and buy_cross:
        signal = "ACHAT (BUY)"
    elif bearish_trend and sell_cross:
        signal = "VENTE (SELL)"
    else:
        signal = "NEUTRE (AUCUN SIGNAL)"

    message = (
        f"Analyse Or ({ticker}) - {candle_time}\n"
        f"Prix : {entry_price:.2f}\n"
        f"ATR (14) : {atr_val:.2f}\n"
        f"Signal : {signal}"
    )

    print(message)
    send_telegram_alert(message)


if __name__ == "__main__":
    run_analysis()
