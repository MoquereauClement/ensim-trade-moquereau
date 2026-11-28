import json, time
import math
from pathlib import Path
import requests

# Fill these in with the URLs the organizer gave you when they registered you:
MARKET_URL = "https://raw.githubusercontent.com/exofri/ensim-trade-center/refs/heads/main/docs/data/market.json"
HOLDINGS_URL = "https://raw.githubusercontent.com/exofri/ensim-trade-center/main/traders/clement/holdings.json"

MIN_MONEY_RESERVE = 50 # never let a buy signal spend below this much money
TARGET_TOLERANCE = 0.07  # Marge commune pour A, B et C, à l'achat et à la vente
TRADE_SIGNAL = 1.0  # 100 unités maximum par ordre
CYCLE_RULES = {
    "B": {"drop": 0.174, "rise": 0.349, "reversal": 0.05},
    "C": {"drop": 0.400, "rise": 0.565, "reversal": 0.10},
}
DECISION_PATH = Path(__file__).resolve().parents[1] / "decision.json"

def fetch_json(url):
    resp = requests.get(url, proxies={"http": None, "https": None}, timeout=(10, 20))
    resp.raise_for_status()
    return resp.json()

def cycle_references(prices, reversal):
    """Derniers sommet et creux confirmés par une variation significative.

    Parcours chronologique : une baisse de 5 % pour B (10 % pour C) confirme
    un sommet, une hausse équivalente confirme un creux. Cela filtre les petites
    fluctuations, sans confondre le dernier sommet avec le maximum historique.
    """
    if not prices:
        return None, None
    peak = trough = prices[0]
    last_peak = last_trough = None
    direction = 0
    for price in prices[1:]:
        if direction == 0:
            peak, trough = max(peak, price), min(trough, price)
            if price >= trough * (1 + reversal):
                last_trough, direction, peak = trough, 1, price
            elif price <= peak * (1 - reversal):
                last_peak, direction, trough = peak, -1, price
        elif direction == 1:
            peak = max(peak, price)
            if price <= peak * (1 - reversal):
                last_peak, direction, trough = peak, -1, price
        else:
            trough = min(trough, price)
            if price >= trough * (1 + reversal):
                last_trough, direction, peak = trough, 1, price
    return last_peak, last_trough


def signal_limits(prices, product):
    """Bornes utilisées pour le signal et affichées dans le tableau de bord."""
    if len(prices) < 3 or any(not math.isfinite(p) or p <= 0 for p in prices):
        return None, None
    if product == "A":
        low, high = min(prices), max(prices)
        if high == low:
            return None, None
        buy_target, sell_target = low, high
    elif product not in CYCLE_RULES:
        return None, None
    else:
        rule = CYCLE_RULES[product]
        peak, trough = cycle_references(prices, rule["reversal"])
        buy_target = peak * (1 - rule["drop"]) if peak is not None else None
        sell_target = trough * (1 + rule["rise"]) if trough is not None else None
    buy = buy_target * (1 + TARGET_TOLERANCE) if buy_target is not None else None
    sell = sell_target * (1 - TARGET_TOLERANCE) if sell_target is not None else None
    return buy, sell


def compute_signal(prices, product="A"):
    """Retournement sur trois prix, confirmé dans une zone d'achat ou de vente."""
    if len(prices) < 3:
        return 0.0
    buy_limit, sell_limit = signal_limits(prices, product)
    before, previous, current = prices[-3:]

    if buy_limit is not None and before > previous < current and current <= buy_limit:
        return TRADE_SIGNAL
    # Le prix précédent est le sommet. Le prix actuel confirme la baisse.
    if sell_limit is not None and before < previous > current and previous >= sell_limit:
        return -TRADE_SIGNAL
    return 0.0

def apply_budget_guard(raw_signal, money, price, reserve=MIN_MONEY_RESERVE):
    # A buy signal (positive) that would spend into the reserve gets scaled down,
    # not silently zeroed out -- you still act on the signal, just smaller. A sell
    # signal is never touched here: selling only ever adds money, never risks it.
    if raw_signal <= 0:
        return raw_signal
    if money <= reserve:
        return 0.0
    max_affordable_units = (money - reserve) / price
    desired_units = 100 * raw_signal
    if desired_units <= max_affordable_units:
        return raw_signal
    # Arrondir vers le bas pour ne pas dépenser au-delà de la réserve.
    return math.floor(max_affordable_units * 10) / 1000

def build_decision(market, holdings):
    products = market["products"]
    history = market["history"]

    decision = {}
    remaining_money = holdings["money"]
    for p in products:
        prices = [row[p] for row in history]
        raw = compute_signal(prices, p)
        current_price = prices[-1] if prices else 0
        if current_price <= 0:
            decision[p] = 0.0
            continue
        guarded = apply_budget_guard(raw, remaining_money, current_price)
        if guarded < 0:
            # Pas de vente de produits que l'on ne possède pas.
            available = max(0.0, holdings["products"][p])
            guarded = -min(abs(guarded), math.floor(available * 10) / 1000)
        decision[p] = round(guarded, 3)
        if decision[p] > 0:
            # Ordre A, B, C : les achats suivants utilisent le budget restant.
            # Les ventes ne financent pas les achats avant leur exécution.
            remaining_money -= 100 * decision[p] * current_price

    decision["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return decision


def main():
    decision = build_decision(fetch_json(MARKET_URL), fetch_json(HOLDINGS_URL))
    with DECISION_PATH.open("w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)
    print(f"Wrote decision.json: {decision}")

if __name__ == "__main__":
    main()
