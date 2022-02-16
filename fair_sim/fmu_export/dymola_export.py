from pathlib import Path
from typing import Any, Union, Optional
import subprocess
from export import FmuExport
from ..utils import move_files, delete_paths
from html import unescape
import fmpy
import re


class DymolaFmuExport(FmuExport):

    files_to_delete = [
        "dslog.txt",
        "fmiModelIdentifier.h",
        "dsmodel.c",
        "buildlog.txt",
        "dsmodel_fmuconf.h",
        "~FMUOutput",
        "dsin.txt",
        ]

    def __init__(self, dymola_exe_path: Path, 
                 model_path: Path, 
                 parameters: Optional[dict[str, Union[str, int, float, list, bool]]]= None,
                 model_modifiers: Optional[list[str]] = None) -> None:
        
        self.dump_directory = model_path.parent
        fmu_name = model_path.stem.replace("_", "_0")
        fmu_path = self.dump_directory / f'{fmu_name}.fmu'

        super().__init__(model_path, fmu_path)
        
        self.dymola_exe_path = dymola_exe_path

        self.mos_file_path = self.model_directory / f"export_script_{self.model_name}.mos"
        self.simulator_log_path = self.model_directory / f"simulator_{self.model_name}.txt"
        self.error_log_path =  self.model_directory / f"errors_{self.model_name}.txt"

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
        return self._dymola_exe_path

    @dymola_exe_path.setter
    def dymola_exe_path(self, dymola_exe_path: Path) -> None:

        if not isinstance(dymola_exe_path, Path):
            raise TypeError(f"'dymola_exe_path' is {type(dymola_exe_path)};  expected Path")
        self._dymola_exe_path = dymola_exe_path

    @property
    def parameters(self) -> dict[str, Union[str, int, float, list, bool]]:
        return self._parameters

    @parameters.setter
    def parameters(self, parameters: dict[str, Union[str, int, float, list, bool]]) -> None:

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
        return self._model_modifiers

    @model_modifiers.setter
    def model_modifiers(self, model_modifiers: list[str]) -> None:

        if not isinstance(model_modifiers, list):
            raise TypeError(f"'model_modifier' is {type(model_modifiers)}; expected list")

        self._model_modifiers = list(map(lambda elm: re.sub(" +", " ", elm.strip()), model_modifiers))
        
    def export_fmu(self, export_simulator_log: bool = True, export_error_log: bool = True) -> None:
        """Executes the mos script.
        """
        mos_script = self.write_mos_script(export_simulator_log, export_error_log)
        self.create_mos_file(mos_script)

        cmd = [str(self.dymola_exe_path), str(self.mos_file_path), "/nowindow"]
       # cmd = [str(self.dymola_exe_path), str(self.mos_file_path)]

        process = subprocess.Popen(cmd)
        process.wait()


    def write_mos_script(self, export_simulator_log: Optional[bool] = True, export_error_log: Optional[bool] = True) -> str:
        """Write the content for the mos file/script. The script contains the necessary instructions to 
           import the specified parameters and model modifiers and export the model as a fmu.

        Returns:
            str: content for the mos script
        """

        parameters = self.format_parameters()
        input = ", ".join(parameters + self.model_modifiers)

        mos_script  = f'cd("{str(self.model_directory)}");\n'
        mos_script += f'openModel("{str(self.model_path)}");\n'
        mos_script += f'modelInstance = "{self.model_name}(' + input + ')";\n'
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
        """Creates the mos file with the specified content.

        Args:
            mos_script (str): The content for the mos file.
        """
        with open(str(self.mos_file_path), mode="w", encoding="utf-8") as mos_file:
            mos_file.write(mos_script)

    def format_parameters(self) -> list[str]:

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

def export_dymola_fmu(dymola_exe_path: Path, model_path: Path, output_directory: Path, 
                        parameters: Optional[dict[str, Union[str, int, float, list, bool]]]= None,
                        model_modifiers: Optional[list[str]] = None, 
                        keep_log: Optional[bool] = True,
                        keep_mos: Optional[bool] = True) -> bool:

    dymola_fmu_export = DymolaFmuExport(dymola_exe_path, model_path, parameters, model_modifiers)
    dymola_fmu_export.export_fmu(keep_log)

    # delete unnecessary files
    delete_paths(dymola_fmu_export.paths_to_delete)

    if not keep_mos:
        dymola_fmu_export.mos_file_path.unlink()

    if dymola_fmu_export.fmu_path.exists():
        print("The FMU Export was successful.")
        move_files(dymola_fmu_export.files_to_move, output_directory)
        dymola_fmu_export.error_log_path.unlink()
        return True
    else:
        print("The FMU Export was not successful")
        print("Dymola Error Message: ")
        with open(dymola_fmu_export.error_log_path, "r") as error_log:
            print(unescape(extract_error_message(error_log.read())))
        dymola_fmu_export.error_log_path.unlink()

        print("Checking if added parameters exist in the model...")
        print("Exporting model without parameters and model modifiers...")

        # TODO export in temp instead of model dir
        dymola_fmu_export = DymolaFmuExport(dymola_exe_path, model_path)
        dymola_fmu_export.export_fmu(export_simulator_log = False, export_error_log = False)
        delete_paths(dymola_fmu_export.paths_to_delete)
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

    model_description: fmpy.model_description.ModelDescription = fmpy.read_model_description(fmu_path)

    return [variable.name for variable in model_description.modelVariables]

def check_not_valid_parameters( imported_parameters: list[str], parameters_in_model: list[str]) -> list[str]:

    return [parameter for parameter in imported_parameters if parameter not in parameters_in_model]

def extract_error_message(error_log: str) -> str:

    error_log = error_log.split("Error: ", 1)
    if len(error_log) == 1: # in case dymola doesn't throw an error
        error_log = "No Dymola errors thrown."
    else:
        error_log = error_log[1]
        error_log = error_log.split("Error: ERRORS have been issued.", 1)[0]
    return error_log

if __name__ == "__main__":

    export_dymola_fmu(Path(r"C:\Program Files\Dymola 2018 FD01\bin64\Dymola.exe"), Path(r'C:\Users\Daniele\Desktop\export_test\test.mo'),
       Path(r'C:\Users\Daniele\Desktop\export_test_out'))#, parameters= {"av":1, "asf":3}) #, model_modifiers=["redeclare package = bla"])    