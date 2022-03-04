from pathlib import Path
from typing import Union, Optional
import subprocess
from fair_sim.fmu_export.fmu_export import FmuExport
import fair_sim.utils as utils
from html import unescape
import fmpy
import re
from datetime import datetime

class DymolaFmuExport(FmuExport):
    """Object that performs the Dymola fmu export."""

    files_to_delete = [
        "dslog.txt",
        "fmiModelIdentifier.h",
        "dsmodel.c",
        "buildlog.txt",
        "dsmodel_fmuconf.h",
        "~FMUOutput",
        "dsin.txt",
        ]

    def __init__(self, dymola_exe_path: Union[Path, str], 
                 model_path: Union[Path, str], 
                 parameters: Optional[dict[str, Union[str, int, float, list, bool]]]= None,
                 model_modifiers: Optional[list[str]] = None) -> None:
        """Initialize the DymolaFmuExport object.

        Args:
            dymola_exe_path (Union[Path, str]): Path to the dymola executable.
            model_path (Union[Path, str]): Path to the modelica model that 
                should be exported.
            parameters (dict[str, Union[str, int, float, list, bool]], optional): 
                Dictionary of parameter names and values.
                Example:
                
                >>> paremeters = {"Resistor.R" : "1", 
                "Resistor.useHeatPort": True}

                Defaults to None.
            model_modifiers (list[str]], optional): List of model modifiers.
                Example:

                >>> model_modifiers = [
                "redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater"
                ]

                Defaults to None.
        """
        self.dump_directory = model_path.parent
        fmu_name = model_path.stem.replace("_", "_0")
        fmu_path = self.dump_directory / f'{fmu_name}.fmu'

        super().__init__(model_path, fmu_path)
        
        self.dymola_exe_path = dymola_exe_path

        # add a time stamp to the mos file
        time_stamp = datetime.now().strftime("%y%m%d%H%M%S") 
        self.mos_file_path = self.model_directory / f"export_script_{self.model_name}_{time_stamp}.mos"
        self.simulator_log_path = self.model_directory / f"log_{self.model_name}_{time_stamp}.txt"
        self.error_log_path =  self.model_directory / f"errors_{self.model_name}_{time_stamp}.txt"

        if not parameters:
            parameters = {}
        self.parameters = parameters

        if not model_modifiers:
            model_modifiers = []
        self.model_modifiers = model_modifiers

        self.files_to_move = [self.fmu_path, self.mos_file_path, self.simulator_log_path]
        self.paths_to_delete = map(lambda name: self.model_directory / name, DymolaFmuExport.files_to_delete)

    @property
    def dymola_exe_path(self) -> Path:
        """Path to the dymola executable.

        Returns:
            Path: Path to the dymola executable
        """
        return self._dymola_exe_path

    @dymola_exe_path.setter
    def dymola_exe_path(self, dymola_exe_path: Path) -> None:
        """Set the Path to the dymola executable.

        Args:
            dymola_exe_path (Path): Path to the dymola executable.

        Raises:
            TypeError: dymola_exe_path type was not 'Path'
            ValueError: File at dymola_exe_path doesn't exist
        """
        if not isinstance(dymola_exe_path, (Path, str)):
            raise TypeError(f"'dymola_exe_path' is {type(dymola_exe_path)};  expected Path, str")

        if isinstance(dymola_exe_path, str):
            dymola_exe_path = Path(dymola_exe_path)

        if not dymola_exe_path.exists():
            raise ValueError(f"{dymola_exe_path} does not exit")
        self._dymola_exe_path = dymola_exe_path

    @property
    def parameters(self) -> dict[str, Union[str, int, float, list, bool]]:
        """Dictionary of parameter names and values.

        Returns:
            dict[str, Union[str, int, float, list, bool]]: Dictionary of
            parameter names and values
        """
        return self._parameters

    @parameters.setter
    def parameters(self, parameters: dict[str, Union[str, int, float, list, bool]]) -> None:
        """Set dictionary of parameter names and values.

        Args:
            parameters (dict[str, Union[str, int, float, list, bool]]): 
                Dictionary of parameter names and values

        Raises:
            TypeError: 'parameters' type was not 'dict' 
            TypeError: type of key in dictionary was not 'str'
            TypeError: type of value in dictionary was not 
                'str', 'int', 'bool', 'float', 'list'
        """
        if not isinstance(parameters, dict):
            raise TypeError(f"'parameters' is {type(parameters)};  expected dict")

        self._parameters = {}
        for comsym, value in parameters.items():
            if not isinstance(comsym, str):
                raise TypeError(f"key of parameters is {type(comsym)}; expected str")
            if not isinstance(value, (str, int, bool, float, list)):
                raise TypeError(f"value of parameters is {type(value)}; expected str, int, float, bool or list")
            self._parameters[comsym] = value

    @property
    def model_modifiers(self) -> list[str]:
        """List of model modifiers.

        Returns:
            list[str]: List of model modifiers.
        """
        return self._model_modifiers

    @model_modifiers.setter
    def model_modifiers(self, model_modifiers: list[str]) -> None:
        """Set list of model modifiers.

        Args:
            model_modifiers (list[str]): List of model modifiers.

        Raises:
            TypeError: 'model_modifiers' type was not 'list' 
            TypeError: type of element in 'model_modifiers' was not 'str'
        """
        if not isinstance(model_modifiers, list):
            raise TypeError(f"'model_modifier' is {type(model_modifiers)}; expected list")

        for modifier in model_modifiers:
            if not isinstance(modifier, str):
                raise TypeError(f"element in 'model_modifier' is {type(modifier)}; expected str")

        self._model_modifiers = list(map(lambda elm: re.sub(" +", " ", elm.strip()), model_modifiers))
        
    def export_fmu(self, export_simulator_log: Optional[bool] = True, export_error_log: Optional[bool] = True) -> None:
        """Execute commands to export a fmu.

        Args:
            export_simulator_log (bool, optional): If True a simulator log file
                will be generated. Defaults to True.
            export_error_log (bool, optional): If True a error log file will be
                generated. Defaults to True.
        """
        mos_script = self.write_mos_script(export_simulator_log, export_error_log)
        self.create_mos_file(mos_script)

        cmd = [str(self.dymola_exe_path), str(self.mos_file_path), "/nowindow"]

        process = subprocess.Popen(cmd)
        process.wait()


    def write_mos_script(self, export_simulator_log: Optional[bool] = True, export_error_log: Optional[bool] = True) -> str:
        """Write the content for the mos file/script.
        
        The script contains the necessary instructions to import the specified
        parameters and model modifiers and export the model as a fmu.

        Args:
            export_simulator_log (bool, optional): If True a simulator log file 
                will be generated. Defaults to True.
            export_error_log (bool, optional): If True a error log file will be
                generated. Defaults to True.

        Returns:
            str: content for the mos script
        """
        parameters = self.format_parameters()
        input_par = ", ".join(parameters + self.model_modifiers)

        mos_script  = f'cd("{str(self.model_directory)}");\n'
        mos_script += f'openModel("{str(self.model_path)}");\n'
        mos_script += f'modelInstance = "{self.model_name}(' + input_par + ')";\n'
        mos_script += f'translateModelFMU(modelInstance, false, "", "2", "all", false, 2);\n'
        if export_simulator_log:
            mos_script += f'savelog("{str(self.simulator_log_path)}");\n'
        if export_error_log:
            mos_script += f'errors = getLastError();\n'
            mos_script += f'Modelica.Utilities.Files.removeFile("{self.error_log_path.name}");\n'
            mos_script += f'Modelica.Utilities.Streams.print(errors, "{self.error_log_path.name}");\n'
        mos_script += f'Modelica.Utilities.System.exit();'

        return mos_script

    def create_mos_file(self, mos_script: str) -> None:
        """Create the mos file with the specified content.

        Args:
            mos_script (str): The content for the mos file.
        """
        with open(str(self.mos_file_path), mode="w", encoding="utf-8") as mos_file:
            mos_file.write(mos_script)

    def format_parameters(self) -> list[str]:
        """Format parameter values.
        
        Format parameter values to adjust to dymola scripting syntax and 
        stores the parameter names and values in a list in the following format.

        >>> parameter_declaration = ['"Resistor.R" =  "1"',
        >>>                          '"Resistor.useHeatPort" = "true"']  

        Returns:
            list[str]: List of parameters. 
        """
        def convert_to_modelica_value(value: Union[list, str, int, float, bool]) -> str:
            
            if isinstance(value, str):
                return value
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, list):
                return "{" + ", ".join(convert_to_modelica_value(element) for element in value) + "}" #TODO check matrices exists in Dymola 
            
        parameter_declaration = []
        for parameter_name, parameter_value in self.parameters.items():
            parameter_value = convert_to_modelica_value(parameter_value)
            parameter_declaration.append(f"{parameter_name} = {parameter_value}")

        return parameter_declaration

def export_dymola_model(
    dymola_exe_path: Union[Path, str], 
    model_path: Union[Path, str], 
    output_directory: Union[Path, str], 
    parameters: Optional[dict[str, Union[str, int, float, list, bool]]]= None,
    model_modifiers: Optional[list[str]] = None, 
    keep_log: Optional[bool] = True,
    keep_mos: Optional[bool] = True
) -> bool:
    """Export a dymola model as a fmu.

    The following steps are performed:
    1. Initializes the DymolaFmuExport object.
    2. Tries to export a dymola model as an fmu.
    3. When exporting, multiple unnecessary files will be generated. These 
    files will be deleted.
    4. If the export was successful, all generated files that are to be kept 
    are moved to the specified output directory.
    5. If the export was not successful the model is exported without imported 
    parameters.
    6. If the export without imported parameters was successful a list of 
    parameters is genereted that were tried to be imported but are not part of 
    the model.

    Args:
        dymola_exe_path (Union[Path, str]):  Path to the dymola executable.
        model_path (Union[Path, str]): Path to the dymola model that should be
            exported.
        output_directory (Union[Path, str]): Path to the output directory.
        parameters (dict[str, Union[str, int, float, list, bool]], optional): 
            Dictionary of parameter names and values.
            Example:

            >>> paremeters = {"Resistor.R" : "1", "Resistor.useHeatPort": True}

                                Defaults to None.
        model_modifiers (list[str]], optional): List of model modifiers.
            Example

            >>> model_modifiers = ["redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater"]

            Defaults to None.
        keep_log (Optional[bool], optional): If True the simulator log is kept
            else it will be deleted. Defaults to True.
        keep_mos (Optional[bool], optional): If True the mos script is kept
            else it will be deleted. Defaults to True.

    Returns:
        bool: True if export was successful else False
    """
    dymola_fmu_export = DymolaFmuExport(dymola_exe_path, model_path, parameters, model_modifiers)

    if not isinstance(output_directory, (Path, str)):
        raise TypeError(f"'output_directory' is {type(output_directory)};  expected Path, str")

    if isinstance(output_directory, str):
        output_directory = Path(output_directory)

    dymola_fmu_export.export_fmu(keep_log)

    # delete unnecessary files
    utils.delete_paths(dymola_fmu_export.paths_to_delete)

    if not keep_mos:
        dymola_fmu_export.mos_file_path.unlink()

    if dymola_fmu_export.fmu_path.exists():
        print("The FMU Export was successful.")
        utils.move_files(dymola_fmu_export.files_to_move, output_directory)
        dymola_fmu_export.error_log_path.unlink()
        return True
    else:
        print("The FMU Export was not successful")
        print("Dymola Error Message: ")
        print("======================")
        with open(dymola_fmu_export.error_log_path, "r") as error_log:
            print(unescape(error_log.read()))
        print("======================")
        dymola_fmu_export.error_log_path.unlink()
        if parameters: 
            print("Checking if added parameters exist in the model...")
            print("Exporting model without parameters and model modifiers...")

            # TODO export in temp instead of model dir
            dymola_fmu_export = DymolaFmuExport(dymola_exe_path, model_path)
            dymola_fmu_export.export_fmu(export_simulator_log = False, export_error_log = False)
            utils.delete_paths(dymola_fmu_export.paths_to_delete)
            if dymola_fmu_export.fmu_path.exists():
                print("FMU Export without added parameters and model modifiers was successfull.")
                parameters_in_model = read_model_parameters(dymola_fmu_export.fmu_path)
                not_valid_parameters = check_not_valid_parameters(list(parameters.keys()), parameters_in_model)
                print(f"Possible parameters that do not exist:\n{not_valid_parameters}")
                dymola_fmu_export.fmu_path.unlink()
            else:
                print("FMU Export without added parameters and model modifiers was not successfull.")
        return False

def read_model_parameters(fmu_path: Path) -> list[str]:
    """Read the models parameters of the given fmu.
    
    Args:
        fmu_path (Path): Path to a fmu.

    Returns:
        list[str]: List of parameters is the model.
    """
    model_description: fmpy.model_description.ModelDescription = fmpy.read_model_description(fmu_path)

    return [variable.name for variable in model_description.modelVariables]

def check_not_valid_parameters( imported_parameters: list[str], parameters_in_model: list[str]) -> list[str]:
    """Return parameters that were tried to be imported but were not part of the model.

    Args:
        imported_parameters (list[str]): Parameter names that were imported.
        parameters_in_model (list[str]): Parameters names in the model.

    Returns:
        list[str]: List of parameters names that are were tried to be imported but were not part of the model 
    """
    return [parameter for parameter in imported_parameters if parameter not in parameters_in_model]
