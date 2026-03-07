import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from sofirpy import export_dymola_model


def select_dymola_exe():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Dymola Executable",
        filetypes=[("Dymola Executable", "Dymola.exe")],
    )
    if not file_path:
        raise FileNotFoundError("No Dymola executable selected!")
    return Path(file_path)


dir_path = Path(__file__).parent
model_path = dir_path / "Building.mo"
package_custom_fittings = dir_path / "Custom_Fittings.mo"
package_custom_pump = dir_path / "Custom_Pump_V2.mo"
package_custom_pump = dir_path / "Custom_Pump.mo"
package_custom_sensors = dir_path / "Custom_Sensors.mo"
packages = [package_custom_fittings, package_custom_pump, package_custom_sensors]
output_directory = dir_path
dymola_exe_path = select_dymola_exe()
model_name = "Building"

# If many parameters have to be imported it is useful to store them in a JSON file.
json_path = dir_path / "parameters.json"

with json_path.open() as file:
    content: dict[str, dict] = json.load(file)
parameters = {}
for component_name, parameter_pairs in content.items():
    for parameter_name, parameter_value in parameter_pairs.items():
        parameters[f"{component_name}.{parameter_name}"] = parameter_value

model_modifiers = [
    "redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater"
]


export_dymola_model(
    dymola_exe_path=dymola_exe_path,
    model_path=model_path,
    model_name=model_name,
    output_directory=output_directory,
    parameters=parameters,
    model_modifiers=model_modifiers,
    packages=packages,
    keep_mos=True,
)
