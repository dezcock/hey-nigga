import requests
import datetime

class EmergencyAlertDispatcher:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or "https://httpbin.org/post"
        self.alert_history = []

    def dispatch_critical_alert(self, simulation_state):
        if simulation_state.get("status") != "RED":
            return {"status": "SKIPPED"}
        payload = {
            "event": "CRITICAL_FLOOD_ALERT",
            "timestamp": datetime.datetime.now().isoformat(),
            "district": simulation_state.get("district"),
            "max_depth_m": simulation_state.get("max_depth_m")
        }
        self.alert_history.append(payload)
        try:
            res = requests.post(self.webhook_url, json=payload, timeout=3)
            return {"status": "DISPATCHED", "code": res.status_code}
        except Exception as e:
            return {"status": "LOGGED_OFFLINE", "error": str(e)}