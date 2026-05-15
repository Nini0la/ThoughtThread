from __future__ import annotations

from collections.abc import Callable

from pynput import keyboard


class HotkeyListener:
    def __init__(self, hotkey: str, on_activate: Callable[[], None]) -> None:
        self.hotkey = hotkey
        self.on_activate = on_activate
        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = keyboard.GlobalHotKeys({self.hotkey: self._safe_activate})
        self._listener.start()

    def join(self) -> None:
        if self._listener is not None:
            self._listener.join()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _safe_activate(self) -> None:
        try:
            self.on_activate()
        except Exception as exc:
            print(f"Hotkey action failed: {exc}")

