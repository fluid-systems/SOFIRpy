from pathlib import Path

from sofirpy import export_dymola_model

dir_path = Path(__file__).parent
model_path = dir_path.parent / "DC_Motor.mo"
output_direcotry = dir_path
dymola_exe_path = r"C:\Program Files\Dymola 2018 FD01\bin64\Dymola.exe"
model_name = "DC_Motor"
# To import paramater define the parameters and their values in a dictionary as
# follows:

parameters = {"damper.d": 0.1, "damper.useHeatPort": False}

# Note: The values can also be strings, but then they must correspond to the
# Modelica syntax:
# >>> parameters = {"damper.d": "0.1", "damper.useHeatPort": "false"}

export_dymola_model(
    dymola_exe_path,
    model_path,
    model_name,
    output_direcotry,
    parameters=parameters,
    keep_mos=False,
)
