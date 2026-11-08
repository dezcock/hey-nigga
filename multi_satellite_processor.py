import numpy as np

class MultiSatelliteFusionProcessor:
    """
    Generates smooth, continuous elevation profiles and natural river channel basins 
    tailored to regional topography without random visual noise.
    """
    def __init__(self, rows=40, cols=40):
        self.rows = rows
        self.cols = cols

    def generate_pan_india_dem(self, bounds, district_name=""):
        sw_lat, sw_lon = bounds[0][0], bounds[0][1]
        ne_lat, ne_lon = bounds[1][0], bounds[1][1]
        center_lat = (sw_lat + ne_lat) / 2.0

        x = np.linspace(-3.0, 3.0, self.cols)
        y = np.linspace(-3.0, 3.0, self.rows)
        xx, yy = np.meshgrid(x, y)

        name_lower = district_name.lower()

        if "srinagar" in name_lower or "shimla" in name_lower:
            elevation = 50.0 + (xx**2) * 8.0 + np.abs(yy) * 4.0
        elif "chennai" in name_lower or "kolkata" in name_lower or "kochi" in name_lower:
            elevation = 10.0 + yy * 2.5 + (xx**2) * 0.8
        elif "mumbai" in name_lower:
            elevation = 15.0 + (xx**2 + yy**2) * 1.2
        else:
            elevation = 20.0 + (xx**2) * 1.5 + (yy**2) * 1.5

        # Smooth natural river channel excavation
        river_channel = -12.0 * np.exp(-0.8 * (xx + 0.3 * yy)**2)
        elevation += river_channel

        return elevation.astype(np.float32)

    def fuse_constellations(self, bounds, dem_grid, district_name=""):
        x = np.linspace(-3.0, 3.0, self.cols)
        y = np.linspace(-3.0, 3.0, self.rows)
        xx, yy = np.meshgrid(x, y)

        smooth_moisture = np.exp(-0.5 * (xx + 0.3 * yy)**2)
        lowest_threshold = np.percentile(dem_grid, 25)
        dem_water_priors = (dem_grid <= lowest_threshold).astype(np.float32)

        final_calibration = np.maximum(smooth_moisture * 0.4, dem_water_priors * 0.5)
        return final_calibration.astype(np.float32)