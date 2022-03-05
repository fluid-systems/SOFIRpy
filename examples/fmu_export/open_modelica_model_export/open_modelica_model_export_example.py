from fair_sim import export_open_modelica_model
from pathlib import Path

dir_path = Path(__file__).parent.parent
model_path = dir_path / "DC_Motor.mo"
output_direcotry = dir_path

export_open_modelica_model(model_path, dir_path)