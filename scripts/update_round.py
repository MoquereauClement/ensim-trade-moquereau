"""Publie le tableau de bord et l’ordre établi sur le dernier tour."""

import json
from datetime import datetime, timezone
from pathlib import Path

import algorithm


LEADERBOARD_URL = "https://raw.githubusercontent.com/exofri/ensim-trade-center/main/docs/data/leaderboard.json"
TRADERS = ("clement", "random_trader", "random_buyer", "random_seller")
DATA_PATH = Path(__file__).resolve().parents[1] / "docs" / "data" / "observations.json"


def describe_order(prices, product, signal):
    buy, sell = algorithm.signal_limits(prices, product)
    current = prices[-1]
    reason = "Historique insuffisant pour établir un seuil."
    if signal > 0:
        reason = "Rebond dans la zone d’achat."
    elif signal < 0:
        reason = "Sommet au-dessus du seuil de vente, puis baisse confirmée."
    elif algorithm.compute_signal(prices, product):
        reason = "Ordre ramené à zéro par le budget ou le stock."
    elif buy is not None or sell is not None:
        before, previous, current = prices[-3:]
        if before > previous < current:
            reason = "Rebond au-dessus du seuil d’achat." if buy is not None else "Rebond sans seuil d’achat disponible."
        elif before < previous > current:
            reason = "Sommet sous le seuil de vente." if sell is not None else "Retournement sans seuil de vente disponible."
        else:
            reason = "Aucun retournement sur les trois derniers prix."
    return {"price": current, "signal": signal, "buy_limit": buy, "sell_limit": sell, "reason": reason}


def performance_point(row, leaderboard):
    values = {entry["id"]: entry["total_value"] for entry in leaderboard["leaderboard"]}
    return {
        "turn": row["t"],
        "at": row["timestamp"],
        "values": {name: values[name] for name in TRADERS if name in values},
    }


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def update_round(market, holdings, leaderboard, data_path=DATA_PATH, decision_path=algorithm.DECISION_PATH):
    history = market["history"]
    if not history:
        raise ValueError("Historique du marché vide.")
    market_time, ranking_time = (
        datetime.fromisoformat(feed["generated_at"]).astimezone(timezone.utc)
        for feed in (market, leaderboard)
    )
    if abs((market_time - ranking_time).total_seconds()) > 5:
        raise ValueError("Le marché et le classement ne correspondent pas au même relevé.")

    data = json.loads(data_path.read_text(encoding="utf-8")) if data_path.exists() else {"performance": [], "decisions": []}
    row = history[-1]
    turn = row["t"]
    last_decision = data["decisions"][-1] if data["decisions"] else None
    if last_decision and turn < last_decision["turn"]:
        return False
    if data["performance"] and turn < data["performance"][-1]["turn"]:
        raise ValueError("Le tour reçu est antérieur au dernier classement déjà enregistré.")

    product_names = market["products"]
    snapshot = {
        "turn": turn,
        "cash": holdings["money"],
        "stocks": {name: holdings["products"][name] for name in product_names},
        "prices": [{"turn": entry["t"], **{name: entry[name] for name in product_names}} for entry in history],
    }
    ranking = {
        "turn": turn,
        "at": row["timestamp"],
        "rows": [
            {
                "id": entry["id"],
                "name": entry.get("name", entry["id"]),
                "total_value": entry["total_value"],
                "baseline": bool(entry.get("baseline", False)),
            }
            for entry in leaderboard["leaderboard"]
        ],
    }
    decision = algorithm.build_decision(market, holdings)
    products = {
        name: describe_order([entry[name] for entry in history], name, decision[name])
        for name in product_names
    }
    same_turn = last_decision is not None and turn == last_decision["turn"]
    if same_turn and last_decision["products"] == products:
        if data.get("market") == snapshot and data.get("leaderboard") == ranking:
            return False
        data["market"] = snapshot
        data["leaderboard"] = ranking
        write_json(data_path, data)
        return True

    data["market"] = snapshot
    data["leaderboard"] = ranking
    point = performance_point(row, leaderboard)
    if data["performance"] and data["performance"][-1]["turn"] == turn:
        data["performance"][-1] = point
    else:
        data["performance"].append(point)
    entry = {"turn": turn, "at": decision["updated_at"], "products": products}
    # Un réglage peut changer l’ordre à envoyer avant le prochain tour.
    if same_turn:
        data["decisions"][-1] = entry
    else:
        data["decisions"].append(entry)
    write_json(decision_path, decision)
    write_json(data_path, data)
    return True


def main():
    changed = update_round(
        algorithm.fetch_json(algorithm.MARKET_URL),
        algorithm.fetch_json(algorithm.HOLDINGS_URL),
        algorithm.fetch_json(LEADERBOARD_URL),
    )
    print("Données du marché et du portefeuille actualisées." if changed else "Aucun nouveau tour à traiter.")


if __name__ == "__main__":
    main()
