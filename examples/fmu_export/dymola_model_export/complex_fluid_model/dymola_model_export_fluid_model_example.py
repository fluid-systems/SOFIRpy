from fair_sim import export_dymola_model

from fair_sim import export_dymola_model
from pathlib import Path

dir_path = Path(__file__).parent
model_path = dir_path / "Building.mo"
package_custom_fittings = dir_path / "Custom_Fittings.mo"
package_custom_pump = dir_path / "Custom_Pump_V2.mo"
package_custom_sensors = dir_path / "Custom_Sensors.mo"
packages = [package_custom_fittings, package_custom_pump, package_custom_sensors]
output_direcotry = dir_path
dymola_exe_path = r"C:\Program Files\Dymola 2018 FD01\bin64\Dymola.exe"

# To import paramater define the parameters and their values in a dictionary as
# follows:

parameters = {}
model_modifiers = ['redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater']
# Note: The values can also be strings, but then they must correspond to the
# Modelica syntax: 
# >>> parameters = {"damper.d": "0.1", "damper.useHeatPort": "false"} 

export_dymola_model(
    dymola_exe_path,
    model_path,
    output_direcotry,
    parameters=parameters,
    model_modifiers=model_modifiers,
    packages = packages)