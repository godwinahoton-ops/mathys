from datetime import datetime
import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import requests

# Paramètres Telegram
TELEGRAM_TOKEN = "9100690235:AAGxp14SDWOBAcDpj4HTu5tS4QZARuNGcrg"
TELEGRAM_CHAT_ID = "8875346326"


def send_telegram_alert(message):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
  try:
    response = requests.post(url, json=payload, timeout=10)
    print(
        f"Réponse Telegram - Code : {response.status_code}, Texte :"
        f" {response.text}"
    )
  except Exception as e:
    print(f"Erreur d'envoi Telegram : {e}")


def run_analysis():
  if not mt5.initialize():
    print("Erreur : impossible d'initialiser MetaTrader 5.")
    return

  symbol = "XAUUSD"
  rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 150)
  mt5.shutdown()

  if rates is None or len(rates) <= 105:
    print("Données insuffisantes pour l'analyse.")
    return

  df = pd.DataFrame(rates)
  df["time"] = pd.to_datetime(df["time"], unit="s")

  # Indicateurs
  df["ema100"] = df["close"].ewm(span=100, adjust=False).mean()
  df["sma9"] = df["close"].rolling(window=9).mean()
  df["sma20"] = df["close"].rolling(window=20).mean()

  # ATR (14 périodes)
  high_low = df["high"] - df["low"]
  high_close = np.abs(df["high"] - df["close"].shift())
  low_close = np.abs(df["low"] - df["close"].shift())
  ranges = pd.concat([high_low, high_close, low_close], axis=1)
  df["atr"] = ranges.max(axis=1).rolling(window=14).mean()

  last = df.iloc[-1]
  prev = df.iloc[-2]

  entry_price = float(last["close"])
  atr_val = float(last["atr"])
  candle_time = last["time"].strftime("%H:%M")

  bullish_trend = last["close"] > last["ema100"]
  bearish_trend = last["close"] < last["ema100"]
  buy_cross = prev["sma9"] <= prev["sma20"] and last["sma9"] > last["sma20"]
  sell_cross = prev["sma9"] >= prev["sma20"] and last["sma9"] < last["sma20"]

  # Calcul d'un score simple sur 100
  score = 40
  if bullish_trend or bearish_trend:
    score += 20
  if buy_cross or sell_cross:
    score += 25
  if not np.isnan(atr_val) and atr_val > 0:
    score += 15

  if bullish_trend and buy_cross:
    sl = entry_price - (1.5 * atr_val)
    tp = entry_price + (3.0 * atr_val)
    msg = (
        "🚨 SIGNAL BUY SUR L'OR 🚨\n\n"
        f"💰 Prix : {entry_price:.2f}\n"
        f"🛑 Stop Loss : {sl:.2f}\n"
        f"🎯 Take Profit : {tp:.2f}\n"
        f"🧠 Score : {score}/100\n"
        f"🕒 Bougie : {candle_time}\n\n"
        "👉 Ouvre MT5 et place ton trade !"
    )
  elif bearish_trend and sell_cross:
    sl = entry_price + (1.5 * atr_val)
    tp = entry_price - (3.0 * atr_val)
    msg = (
        "🚨 SIGNAL SELL SUR L'OR 🚨\n\n"
        f"💰 Prix : {entry_price:.2f}\n"
        f"🛑 Stop Loss : {sl:.2f}\n"
        f"🎯 Take Profit : {tp:.2f}\n"
        f"🧠 Score : {score}/100\n"
        f"🕒 Bougie : {candle_time}\n\n"
        "👉 Ouvre MT5 et place ton trade !"
    )
  else:
    tendance = "Haussière (> EMA100)" if bullish_trend else "Baissière (< EMA100)"
    msg = (
        "📊 ANALYSE XAUUSD (Pas de signal)\n\n"
        f"💰 Prix actuel : {entry_price:.2f}\n"
        f"📈 Tendance : {tendance}\n"
        f"🧠 Score : {score}/100\n"
        f"🕒 Bougie : {candle_time}\n\n"
        "⏳ Conditions non réunies pour le moment."
    )

  send_telegram_alert(msg)
  print("Analyse terminée.")


if __name__ == "__main__":
  run_analysis()