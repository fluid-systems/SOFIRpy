from pathlib import Path
import json
from fair_sim import export_dymola_model

dir_path = Path(__file__).parent
model_path = dir_path / "Building.mo"
package_custom_fittings = dir_path / "Custom_Fittings.mo"
package_custom_pump = dir_path / "Custom_Pump_V2.mo"
package_custom_sensors = dir_path / "Custom_Sensors.mo"
packages = [package_custom_fittings, package_custom_pump, package_custom_sensors]
output_direcotry = dir_path
dymola_exe_path = r"C:\Program Files\Dymola 2018 FD01\bin64\Dymola.exe"

# If many parameters have to be imported it is useful to store them in a JSON file.
json_path = dir_path / "parameters.json"
with open(json_path) as file:
    content: dict[str, dict] = json.load(file)
parameters = {}
for component_name, parameter_pairs in content.items():
    for parameter_name, parameter_value in parameter_pairs.items():
        parameters[f"{component_name}.{parameter_name}"] = parameter_value

model_modifiers = ['redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater']


export_dymola_model(
    dymola_exe_path,
    model_path,
    output_direcotry,
    parameters=parameters,
    model_modifiers=model_modifiers,
    packages = packages)