"""OBS WebSockets integration — show/hide agent sources while they speak.

Adapted from Babagaboosh/obs_websockets.py (DougDoug).
Requires: pip install obs-websocket-py==1.0.1
OBS: Tools → WebSocket Server Settings → Enable, note port + password.
"""

import config

try:
    from obswebsocket import obsws, requests as obsrequests
    _LIB_AVAILABLE = True
except ImportError:
    _LIB_AVAILABLE = False

# Maps agent name → OBS source name (set in config.py)
_AGENT_SOURCES: dict[str, str] = {}

# Module-level singleton
_obs_manager: "OBSManager | None" = None


class OBSManager:
    def __init__(self) -> None:
        self._ws = obsws(config.OBS_HOST, config.OBS_PORT, config.OBS_PASSWORD)
        self._ws.connect()
        print(f"  [OBS] Connected to {config.OBS_HOST}:{config.OBS_PORT}")

    def disconnect(self) -> None:
        self._ws.disconnect()

    def set_source_visibility(self, scene: str, source: str, visible: bool) -> None:
        response = self._ws.call(obsrequests.GetSceneItemId(sceneName=scene, sourceName=source))
        item_id = response.datain["sceneItemId"]
        self._ws.call(obsrequests.SetSceneItemEnabled(
            sceneName=scene, sceneItemId=item_id, sceneItemEnabled=visible
        ))

    def show_agent(self, agent_name: str) -> None:
        source = _AGENT_SOURCES.get(agent_name.upper())
        if source:
            self.set_source_visibility(config.OBS_SCENE, source, True)

    def hide_agent(self, agent_name: str) -> None:
        source = _AGENT_SOURCES.get(agent_name.upper())
        if source:
            self.set_source_visibility(config.OBS_SCENE, source, False)


def init_obs_manager() -> "OBSManager | None":
    global _obs_manager, _AGENT_SOURCES

    if not _LIB_AVAILABLE:
        print("  [OBS] obs-websocket-py not installed. Run: pip install obs-websocket-py==1.0.1")
        return None

    _AGENT_SOURCES = {
        "EDGEWORTH": config.EDGEWORTH_OBS_SOURCE,
        "LIGHT":     config.LIGHT_OBS_SOURCE,
        "INTERN":    config.INTERN_OBS_SOURCE,
    }

    try:
        _obs_manager = OBSManager()
    except Exception as e:
        print(f"  [OBS] Could not connect — is OBS open with WebSocket server enabled? ({e})")
        _obs_manager = None

    return _obs_manager


def get_obs_manager() -> "OBSManager | None":
    return _obs_manager
