import numpy as np

class HistoricalReplayEngine:
    def __init__(self, rows=40, cols=40):
        self.rows = rows
        self.cols = cols
        self.events = {
            "chennai_2015": {"name": "Chennai 2015 (Adyar River Breach)", "bounds": [[12.95, 80.15], [13.10, 80.30]], "max_ticks": 12, "peak_tick": 7},
            "assam_2022": {"name": "Assam 2022 (Brahmaputra Flood)", "bounds": [[26.12, 91.70], [26.20, 91.82]], "max_ticks": 12, "peak_tick": 9},
            "mumbai_2005": {"name": "Mumbai 2005 (Mithi Deluge)", "bounds": [[19.05, 72.80], [19.18, 72.95]], "max_ticks": 12, "peak_tick": 8},
            "kerala_2018": {"name": "Kerala 2018 (Idukki Release)", "bounds": [[9.90, 76.25], [10.05, 76.40]], "max_ticks": 12, "peak_tick": 6}
        }

    def get_event_timeline_frame(self, event_key, tick_index):
        if event_key not in self.events:
            event_key = "chennai_2015"
        evt = self.events[event_key]
        tick = max(0, min(int(tick_index), evt["max_ticks"]))
        
        peak = evt["peak_tick"]
        intensity = (tick / float(peak)) ** 1.8 if tick <= peak else max(0.2, 1.0 - ((tick - peak) / float(evt["max_ticks"] - peak)) * 0.7)

        x = np.linspace(-2, 2, self.cols)
        y = np.linspace(-2, 2, self.rows)
        xx, yy = np.meshgrid(x, y)
        
        base_depth = (np.sin(xx * 1.5) * np.cos(yy * 1.5) + 1.2) * 0.45 * intensity
        water_grid = np.clip(base_depth, 0.0, 2.2).astype(np.float32)

        return {
            "event_name": evt["name"],
            "current_tick": tick,
            "max_ticks": evt["max_ticks"],
            "bounds": evt["bounds"],
            "max_depth_m": round(float(np.max(water_grid)), 2),
            "water_grid": water_grid.tolist()
        }