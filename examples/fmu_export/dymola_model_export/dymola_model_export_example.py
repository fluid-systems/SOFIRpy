from fair_sim import export_dymola_model
from pathlib import Path

dir_path = Path(__file__).parent
model_path = dir_path.parent / "DC_Motor.mo"
output_direcotry = dir_path
dymola_exe_path = r"C:\Program Files\Dymola 2018 FD01\bin64\Dymola.exe"

export_dymola_model(dymola_exe_path, model_path, output_direcotry)