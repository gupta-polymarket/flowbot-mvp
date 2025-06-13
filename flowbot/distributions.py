import random
from typing import Sequence, Any, Dict, List

BUY = "BUY"
SELL = "SELL"


def _uniform(params: Dict[str, Any]) -> float:
    return random.uniform(params.get("min", 0), params.get("max", 1))


def sample_quantity(conf: Dict[str, Any]) -> float:
    q_conf = conf.get("quantity", {})
    if q_conf.get("type", "uniform") == "uniform":
        return round(_uniform(q_conf), 2)
    # fallback
    return 1.0


def sample_interval(conf: Dict[str, Any]) -> float:
    i_conf = conf.get("interval", {})
    if i_conf.get("type", "uniform") == "uniform":
        return _uniform(i_conf)
    return 5


def sample_side(conf: Dict[str, Any]) -> str:
    if random.random() < conf.get("p_buy", 0.5):
        return BUY
    return SELL


def sample_market(conf: Dict[str, Any], forced: str | None = None) -> str:
    """Return a tokenId.

    If *forced* is provided it is returned (after optional validity check).
    Otherwise a uniform-random choice is made from *conf["markets"]*.
    """
    if forced:
        return forced
    markets: List[str] = conf.get("markets", [])
    if not markets:
        raise ValueError("No markets defined in config or TOKEN_IDS env var")
    return random.choice(markets) 