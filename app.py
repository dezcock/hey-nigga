import os
import io
import json
import numpy as np
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

from grid_engine import GridSimulator
from audio_engine import AcousticDrainProcessor
from cctv_engine import OpticalFlowVelocityProcessor
from historical_engine import HistoricalReplayEngine
from alert_engine import EmergencyAlertDispatcher

app = Flask(__name__)
CORS(app)

sim_primary = GridSimulator(district_name="Guwahati (Zoo Road Basin)")
sim_secondary = GridSimulator(district_name="Chennai (Adyar Basin)")

audio_processor = AcousticDrainProcessor()
cctv_processor = OpticalFlowVelocityProcessor()
replay_engine = HistoricalReplayEngine()
alert_dispatcher = EmergencyAlertDispatcher()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/simulation/step", methods=["POST"])
def simulation_step():
    data = request.get_json() or {}
    rainfall_mm = data.get("rainfall_mm", 120.0)
    target = data.get("target", "primary")
    sim = sim_secondary if target == "secondary" else sim_primary
    sim.add_rainfall(rainfall_mm)
    sim.step_cellular_automata(iterations=3)
    state = sim.get_inundation_state()
    if state["status"] == "RED":
        alert_dispatcher.dispatch_critical_alert(state)
    return jsonify(state)

@app.route("/api/simulation/reset", methods=["POST"])
def simulation_reset():
    data = request.get_json() or {}
    district = data.get("district", "Guwahati (Zoo Road Basin)")
    target = data.get("target", "primary")
    sim = sim_secondary if target == "secondary" else sim_primary
    sim.set_district(district)
    return jsonify(sim.get_inundation_state())

@app.route("/api/simulation/set-district", methods=["POST"])
def set_district():
    data = request.get_json() or {}
    district = data.get("district")
    target = data.get("target", "primary")
    sim = sim_secondary if target == "secondary" else sim_primary
    if district:
        sim.set_district(district)
    return jsonify(sim.get_inundation_state())

@app.route("/api/simulation/set-boundary", methods=["POST"])
def set_boundary():
    data = request.get_json() or {}
    sw_lat, sw_lon = data.get("sw_lat"), data.get("sw_lon")
    ne_lat, ne_lon = data.get("ne_lat"), data.get("ne_lon")
    target = data.get("target", "primary")
    sim = sim_secondary if target == "secondary" else sim_primary
    if all([sw_lat, sw_lon, ne_lat, ne_lon]):
        sim.set_custom_boundary(sw_lat, sw_lon, ne_lat, ne_lon)
    return jsonify(sim.get_inundation_state())

@app.route("/api/satellites/toggle", methods=["POST"])
def toggle_satellites():
    data = request.get_json() or {}
    enabled = data.get("enabled", True)
    sim_primary.multi_sat_active = enabled
    sim_secondary.multi_sat_active = enabled
    return jsonify({"status": "success", "multi_satellite_active": enabled})

@app.route("/api/historical/load-frame", methods=["POST"])
def load_historical_frame():
    data = request.get_json() or {}
    return jsonify(replay_engine.get_event_timeline_frame(data.get("event_key", "chennai_2015"), data.get("tick_index", 0)))

@app.route("/api/audio/analyze", methods=["POST"])
def analyze_audio():
    audio_file = request.files.get("audio")
    return jsonify(audio_processor.classify_drain_audio(audio_file.read())) if audio_file else jsonify({"error": "No audio"}), 400

@app.route("/api/cctv/analyze", methods=["POST"])
def analyze_cctv():
    cctv_file = request.files.get("cctv")
    return jsonify(cctv_processor.estimate_surface_velocity(cctv_file.read())) if cctv_file else jsonify({"error": "No CCTV"}), 400

@app.route("/api/unified/analyze-event", methods=["POST"])
def analyze_unified_event():
    rainfall_mm = float(request.form.get("rainfall_mm", 120.0))
    audio_file = request.files.get("audio")
    cctv_file = request.files.get("cctv")

    audio_res = audio_processor.classify_drain_audio(audio_file.read()) if audio_file else {"classification": "Normal Flow", "confidence": 0.94}
    cctv_res = cctv_processor.estimate_surface_velocity(cctv_file.read()) if cctv_file else {"estimated_velocity_ms": 1.85, "hazard_level": "NOMINAL"}

    sim_primary.add_rainfall(rainfall_mm)
    sim_primary.step_cellular_automata(iterations=3)
    state = sim_primary.get_inundation_state()
    return jsonify({"status": "success", "audio_analysis": audio_res, "cctv_analysis": cctv_res, "simulation": state})

@app.route("/api/export/pdf-briefing", methods=["GET"])
def export_pdf_briefing():
    state = sim_primary.get_inundation_state()
    return f"""<html><body><h1>Executive Briefing</h1><p>Sector: {state['district']}</p><p>Status: {state['status']}</p><script>window.print();</script></body></html>"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)