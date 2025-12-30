# simulator/effects/__init__.py

from .oneshot import flash_effect, strobe_effect, pulse_effect, ripple_effect

EFFECT_MAP = {
    "Flash \u26a1": flash_effect,
    "Strobe \ud83d\udca1": strobe_effect,
    "Pulse \ud83d\udcfb": pulse_effect,
    "Ripple \ud83d\udcf6": ripple_effect,
}
