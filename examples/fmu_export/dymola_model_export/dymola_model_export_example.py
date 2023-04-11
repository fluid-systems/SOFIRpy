from pathlib import Path

from sofirpy import export_dymola_model

dir_path = Path(__file__).parent
model_path = dir_path.parent / "DC_Motor.mo"
output_directory = dir_path
dymola_exe_path = r"C:\Program Files\Dymola 2018 FD01\bin64\Dymola.exe"
model_name = "DC_Motor"
fmu_path = export_dymola_model(
    dymola_exe_path, model_path, model_name, output_directory
)
