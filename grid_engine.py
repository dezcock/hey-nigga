import numpy as np
import datetime
from multi_satellite_processor import MultiSatelliteFusionProcessor

class GridSimulator:
    def __init__(self, district_name="Guwahati (Zoo Road Basin)", rows=40, cols=40):
        self.rows = rows
        self.cols = cols
        self.district_name = district_name
        self.water_grid = np.zeros((rows, cols), dtype=np.float32)
        
        self.sat_processor = MultiSatelliteFusionProcessor(rows, cols)
        self.bounds = [[26.12, 91.70], [26.20, 91.82]]
        self.elevation_grid = self.sat_processor.generate_pan_india_dem(self.bounds, self.district_name)
        
        self.sim_time = datetime.datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        self.step_count = 0
        self.multi_sat_active = True
        self.sar_fusion_enabled = True

        self.presets = {
            "Guwahati (Zoo Road Basin)": [[26.12, 91.70], [26.20, 91.82]],
            "Chennai (Adyar Basin)": [[12.95, 80.15], [13.10, 80.30]],
            "Mumbai (Mithi River Sector)": [[19.05, 72.80], [19.18, 72.95]],
            "Delhi (Yamuna Basin)": [[28.60, 77.15], [28.75, 77.30]],
            "Kolkata (Hooghly Delta)": [[22.50, 88.30], [22.65, 88.45]],
            "Srinagar (Jhelum Basin)": [[34.00, 74.75], [34.15, 74.90]],
            "Bengaluru (Bellandur Catchment)": [[12.88, 77.58], [13.00, 77.72]],
            "Hyderabad (Hussain Sagar Basin)": [[17.38, 78.40], [17.50, 78.52]]
        }

    def set_district(self, district_name):
        self.district_name = district_name
        if district_name in self.presets:
            self.bounds = self.presets[district_name]
        else:
            self.bounds = [[13.0, 80.0], [13.1, 80.1]] 
        self.water_grid = np.zeros((self.rows, self.cols), dtype=np.float32)
        self.elevation_grid = self.sat_processor.generate_pan_india_dem(self.bounds, self.district_name)

    def set_custom_boundary(self, sw_lat, sw_lon, ne_lat, ne_lon):
        self.bounds = [[float(sw_lat), float(sw_lon)], [float(ne_lat), float(ne_lon)]]
        self.district_name = f"Custom AOI [{float(sw_lat):.2f}N, {float(sw_lon):.2f}E]"
        self.water_grid = np.zeros((self.rows, self.cols), dtype=np.float32)
        self.elevation_grid = self.sat_processor.generate_pan_india_dem(self.bounds, self.district_name)

    def add_rainfall(self, rainfall_mm_per_hr):
        # Properly scale down mm/hr to a 15-minute simulation step increment (capped realistically)
        clamped_rain = max(0.0, min(float(rainfall_mm_per_hr), 300.0))
        depth_increment = (clamped_rain / 1000.0) * (15.0 / 60.0) * 0.15 
        
        max_elev = np.max(self.elevation_grid)
        min_elev = np.min(self.elevation_grid)
        topo_slope_factor = (max_elev - self.elevation_grid) / (max_elev - min_elev + 1e-5)
        
        # Add rainfall with a physical absorption/drainage cap of 1.8 meters max depth
        self.water_grid += depth_increment * np.clip(topo_slope_factor, 0.05, 1.0)
        self.water_grid = np.clip(self.water_grid, 0.0, 1.8)

    def step_cellular_automata(self, iterations=3):
        for _ in range(iterations):
            # Apply natural runoff drainage & evaporation loss per step
            self.water_grid *= 0.985 
            
            for r in range(self.rows):
                for c in range(self.cols):
                    current_water = self.water_grid[r, c]
                    current_elev = self.elevation_grid[r, c]
                    neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                    for nr, nc in neighbors:
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            n_elev = self.elevation_grid[nr, nc]
                            n_water = self.water_grid[nr, nc]
                            if (current_elev + current_water) > (n_elev + n_water):
                                flow = 0.05 * ((current_elev + current_water) - (n_elev + n_water))
                                self.water_grid[r, c] = max(0.0, current_water - flow)
                                self.water_grid[nr, nc] += flow

        # Controlled Satellite Calibration (No artificial flooding inflation)
        if self.multi_sat_active and self.sar_fusion_enabled:
            sat_mask = self.sat_processor.fuse_constellations(self.bounds, self.elevation_grid, self.district_name)
            self.water_grid = np.where((sat_mask > 0.5) & (self.water_grid < 0.1), 0.12, self.water_grid)

        self.sim_time += datetime.timedelta(minutes=15)
        self.step_count += 1

    def get_inundation_state(self):
        max_depth = float(np.max(self.water_grid))
        critical_cells = int(np.sum(self.water_grid >= 0.5))
        
        status = "GREEN"
        action_command = f"Sector {self.district_name} stable. Drainage systems nominal."
        
        if max_depth > 0.6 or critical_cells > 120:
            status = "RED"
            action_command = f"CRITICAL ALERT [{self.sim_time.strftime('%H:%M')}]: Severe flooding confirmed in {self.district_name}. Deploy pumps."
        elif max_depth > 0.3 or critical_cells > 30:
            status = "YELLOW"
            action_command = f"WARNING [{self.sim_time.strftime('%H:%M')}]: Water accumulation building in low basins of {self.district_name}."

        def evaluate_risk(depth):
            if depth >= 0.5: return "CRITICAL"
            elif depth >= 0.25: return "MODERATE"
            return "LOW"

        mid_r, mid_c = self.rows // 2, self.cols // 2
        z1 = float(np.mean(self.water_grid[:mid_r, :mid_c]))
        z2 = float(np.mean(self.water_grid[:mid_r, mid_c:]))
        z3 = float(np.max(self.water_grid[mid_r:, :mid_c]))
        z4 = float(np.max(self.water_grid[mid_r:, mid_c:]))

        ward_predictions = [
            {"ward": f"{self.district_name} - Zone A", "max_depth_m": round(z1, 2), "risk": evaluate_risk(z1), "estimated_peak_time": (self.sim_time + datetime.timedelta(minutes=30)).strftime('%H:%M')},
            {"ward": f"{self.district_name} - Zone B", "max_depth_m": round(z2, 2), "risk": evaluate_risk(z2), "estimated_peak_time": (self.sim_time + datetime.timedelta(minutes=15)).strftime('%H:%M')},
            {"ward": f"{self.district_name} - Zone C", "max_depth_m": round(z3, 2), "risk": evaluate_risk(z3), "estimated_peak_time": self.sim_time.strftime('%H:%M')},
            {"ward": f"{self.district_name} - Zone D", "max_depth_m": round(z4, 2), "risk": evaluate_risk(z4), "estimated_peak_time": (self.sim_time + datetime.timedelta(minutes=45)).strftime('%H:%M')}
        ]

        return {
            "status": status,
            "district": self.district_name,
            "max_depth_m": round(max_depth, 2),
            "critical_cell_count": critical_cells,
            "action_command": action_command,
            "simulation_time": self.sim_time.strftime('%Y-%m-%d %H:%M:%S'),
            "bounds": self.bounds,
            "multi_satellite_active": self.multi_sat_active,
            "ward_predictions": ward_predictions,
            "water_grid": self.water_grid.tolist()
        }