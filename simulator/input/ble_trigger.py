class InputTrigger:
    def poll(self) -> list[dict]:
        """
        Return a list of input events since last poll.
        Each event is a dict: { "source": "glove"|"ble", "event": "burst", "time": float }
        """
