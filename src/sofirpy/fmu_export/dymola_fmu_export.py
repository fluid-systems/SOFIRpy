"""This module allows to export a Dymola model as a fmu."""

import re
import subprocess
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Optional, Union

import fmpy

from sofirpy import utils
from sofirpy.fmu_export.fmu_export import FmuExport

ParameterValue = Union[str, int, float, list[Union[int, float, str, bool]], bool]


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

    def __init__(
        self,
        dymola_exe_path: Path,
        model_path: Path,
        model_name: str,
        parameters: Optional[dict[str, ParameterValue]] = None,
        model_modifiers: Optional[list[str]] = None,
        packages: Optional[list[Union[str, Path]]] = None,
    ) -> None:
        """Initialize the DymolaFmuExport object.

        Args:
            dymola_exe_path (Path): Path to the dymola executable.
            model_path (Path): Path to the modelica model that
                should be exported.
            model_name (str): Name of the model that should be exported. If the
                model that should be exported is inside a package, separate the
                package name and the model name with a '.'.
            parameters (dict[str, ParameterValue], optional):
                Dictionary of parameter names and values.
                Example:

                >>> parameters = {"Resistor.R" : "1",
                ...     "Resistor.useHeatPort": True}

                Defaults to None.
            model_modifiers (list[str]], optional): List of model modifiers.
                Example:

                >>> model_modifiers = [
                ...     "redeclare package Medium = "
                ...     "Modelica.Media.Water.ConstantPropertyLiquidWater"
                ... ]

                Defaults to None.
            packages (list[str], optional): List of model/package paths that
                need to be loaded as dependencies for the model.
        """

        self.model_name = model_name
        self._dump_directory = model_path.parent
        fmu_name = self.model_name.replace("_", "_0").replace(".", "_")
        fmu_path = self._dump_directory / f"{fmu_name}.fmu"

        super().__init__(model_path, fmu_path)

        self._dymola_exe_path = dymola_exe_path

        # add a time stamp to the mos file and log files
        time_stamp = datetime.now().strftime("%y%m%d%H%M%S")
        self.mos_file_path = (
            self.model_directory / f"export_script_{self.model_name}_{time_stamp}.mos"
        )
        self._simulator_log_path = (
            self.model_directory / f"log_{self.model_name}_{time_stamp}.txt"
        )
        self.error_log_path = (
            self.model_directory / f"errors_{self.model_name}_{time_stamp}.txt"
        )

        if not parameters:
            parameters = {}
        self.parameters = parameters

        if not model_modifiers:
            model_modifiers = []
        self.model_modifiers = model_modifiers

        if not packages:
            packages = []

        # converts paths to strings if paths are given as Path object
        self._packages = list(
            map(lambda path: utils.convert_str_to_path(path, "package_path"), packages)
        )

        self.paths_to_delete = list(
            map(
                lambda name: self.model_directory / name,
                DymolaFmuExport.files_to_delete,
            )
        )

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
            raise TypeError(
                f"'dymola_exe_path' is {type(dymola_exe_path)};  expected Path, str"
            )

        if isinstance(dymola_exe_path, str):
            dymola_exe_path = Path(dymola_exe_path)

        if not dymola_exe_path.exists():
            raise ValueError(f"{dymola_exe_path} does not exit")
        self._dymola_exe_path = dymola_exe_path

    @property
    def model_name(self) -> str:
        """Name of the model.

        Returns:
            str: Name of the model.
        """
        return self._model_name

    @model_name.setter
    def model_name(self, model_name: str) -> None:
        """Name of the model.

        Args:
            model_name (str): Name of the model.

        Raises:
            TypeError: type of model_name was invalid
        """
        if not isinstance(model_name, str):
            raise TypeError(f"'model_name' is {type(model_name)};  expected str")

        self._model_name = model_name

    @property
    def parameters(self) -> dict[str, ParameterValue]:
        """Dictionary of parameter names and values.

        Returns:
            dict[str, ParameterValue]: Dictionary of
            parameter names and values
        """
        return self._parameters

    @parameters.setter
    def parameters(self, parameters: dict[str, ParameterValue]) -> None:
        """Set dictionary of parameter names and values.

        Args:
            parameters (dict[str, ParameterValue]):
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
        for com_sym, value in parameters.items():
            if not isinstance(com_sym, str):
                raise TypeError(f"key of parameters is {type(com_sym)}; expected str")
            if not isinstance(value, (str, int, bool, float, list)):
                raise TypeError(
                    f"value of parameters is {type(value)}; expected str, int, float, bool or list"
                )
            self._parameters[com_sym] = value

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
            raise TypeError(
                f"'model_modifier' is {type(model_modifiers)}; expected list"
            )

        for modifier in model_modifiers:
            if not isinstance(modifier, str):
                raise TypeError(
                    f"element in 'model_modifier' is {type(modifier)}; expected str"
                )

        self._model_modifiers = list(
            map(lambda elm: re.sub(" +", " ", elm.strip()), model_modifiers)
        )

    def export_fmu(
        self,
        export_simulator_log: Optional[bool] = True,
        export_error_log: Optional[bool] = True,
    ) -> None:
        """Execute commands to export a fmu.

        Args:
            export_simulator_log (bool, optional): If True a simulator log file
                will be generated. Defaults to True.
            export_error_log (bool, optional): If True a error log file will be
                generated. Defaults to True.
        """
        mos_script = self.write_mos_script(export_simulator_log, export_error_log)
        self.create_mos_file(mos_script)

        cmd = [str(self._dymola_exe_path), str(self.mos_file_path), "/nowindow"]

        with subprocess.Popen(cmd) as process:
            process.wait()

    def write_mos_script(
        self,
        export_simulator_log: Optional[bool] = True,
        export_error_log: Optional[bool] = True,
    ) -> str:
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

        model_dir_str = str(self.model_directory).replace("\\", "/")
        model_path_str = str(self.model_path).replace("\\", "/")
        log_path_str = str(self._simulator_log_path).replace("\\", "/")

        mos_script = f'cd("{model_dir_str}");\n'

        if self._packages:
            for package in self._packages:
                package_path_str = str(package).replace("\\", "/")
                mos_script += f'openModel("{package_path_str}")\n'
        mos_script += f'openModel("{model_path_str}");\n'
        mos_script += f'modelInstance = "{self.model_name}(' + input_par + ')";\n'
        mos_script += (
            'translateModelFMU(modelInstance, false, "", "2", "all", false, 2);\n'
        )
        if export_simulator_log:
            mos_script += f'savelog("{log_path_str}");\n'
        if export_error_log:
            mos_script += "errors = getLastError();\n"
            mos_script += (
                f'Modelica.Utilities.Files.removeFile("{self.error_log_path.name}");\n'
            )
            mos_script += "Modelica.Utilities.Streams.print"
            mos_script += f'(errors, "{self.error_log_path.name}");\n'
        mos_script += "Modelica.Utilities.System.exit();"

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
        ...                          '"Resistor.useHeatPort" = "true"']

        Returns:
            list[str]: List of parameters.
        """

        def convert_to_modelica_value(value: ParameterValue) -> str:

            if isinstance(value, str):
                return value
            if isinstance(value, bool):
                return "true" if value else "false"
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, list):
                return (
                    "{"
                    + ", ".join(convert_to_modelica_value(element) for element in value)
                    + "}"
                )
            raise TypeError(
                f"value is {type(value)}; expected str, bool, float, int, list"
            )

        parameter_declaration = []
        for parameter_name, parameter_value in self.parameters.items():
            parameter_value = convert_to_modelica_value(parameter_value)
            parameter_declaration.append(f"{parameter_name} = {parameter_value}")

        return parameter_declaration

    def move_mos_script(self, target_directory: Path) -> None:
        """Move the mos script to a target directory.

        Args:
            target_directory (Path): Path to the target directory.
        """
        new_mos_path = target_directory / self.mos_file_path.name
        utils.move_file(self.mos_file_path, new_mos_path)
        self.mos_file_path = new_mos_path

    def move_log_file(self, target_directory: Path) -> None:
        """Move the log file to a target directory.

        Args:
            target_directory (Path): Path to the target directory.
        """
        new_log_path = target_directory / self._simulator_log_path.name
        utils.move_file(self._simulator_log_path, new_log_path)
        self._simulator_log_path = new_log_path


def export_dymola_model(
    dymola_exe_path: Union[Path, str],
    model_path: Union[Path, str],
    model_name: str,
    output_directory: Union[Path, str],
    parameters: Optional[dict[str, ParameterValue]] = None,
    model_modifiers: Optional[list[str]] = None,
    packages: Optional[list[Union[str, Path]]] = None,
    keep_log: bool = True,
    keep_mos: bool = True,
) -> Optional[DymolaFmuExport]:
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
    parameters is generated that were tried to be imported but are not part of
    the model.

    Args:
        dymola_exe_path (Union[Path, str]):  Path to the dymola executable.
        model_path (Union[Path, str]): Path to the dymola model that should be
            exported.
        model_name (str): Name of the model that should be exported. If the
            model that should be exported is inside a package, separate the
            package name and the model name with a '.'.
        output_directory (Union[Path, str]): Path to the output directory.
        parameters (dict[str, ParameterValue], optional):
            Dictionary of parameter names and values.
            Example:

            >>> parameters = {"Resistor.R" : "1", "Resistor.useHeatPort": True}

                                Defaults to None.
        model_modifiers (list[str]], optional): List of model modifiers.
            Example

            >>> model_modifiers = ["redeclare package Medium ="
            ...     "Modelica.Media.Water.ConstantPropertyLiquidWater"]

            Defaults to None.
        packages (Optional[list[Union[str, Path]]], optional): List of
            model/package paths that need to be loaded as dependencies for the
            model.
        keep_log (bool, optional): If True the simulator log is kept
            else it will be deleted. Defaults to True.
        keep_mos (bool, optional): If True the mos script is kept
            else it will be deleted. Defaults to True.

    Returns:
        Optional[DymolaFmuExport]: DymolaFmuExport object.
    """

    _dymola_exe_path = utils.convert_str_to_path(dymola_exe_path, "dymola_exe_path")
    _model_path = utils.convert_str_to_path(model_path, "model_path")

    dymola_fmu_export = DymolaFmuExport(
        _dymola_exe_path, _model_path, model_name, parameters, model_modifiers, packages
    )

    _output_directory = utils.convert_str_to_path(output_directory, "output_directory")

    dymola_fmu_export.export_fmu(keep_log)

    # delete unnecessary files
    utils.delete_paths(dymola_fmu_export.paths_to_delete)

    if not keep_mos:
        dymola_fmu_export.mos_file_path.unlink()

    if dymola_fmu_export.fmu_path.exists():
        print("The FMU Export was successful.")
        dymola_fmu_export.error_log_path.unlink()
        dymola_fmu_export.move_fmu(_output_directory)
        if keep_mos:
            dymola_fmu_export.move_mos_script(_output_directory)
        if keep_log:
            dymola_fmu_export.move_log_file(_output_directory)
        return dymola_fmu_export

    print("The FMU Export was not successful")
    print("Dymola Error Message: ")
    print("======================")
    with open(dymola_fmu_export.error_log_path, "r", encoding="utf-8") as error_log:
        print(unescape(error_log.read()))
    print("======================")
    dymola_fmu_export.error_log_path.unlink()
    if parameters:
        print("Checking if added parameters exist in the model...")
        print("Exporting model without parameters and model modifiers...")

        dymola_fmu_export = DymolaFmuExport(_dymola_exe_path, _model_path, model_name)
        dymola_fmu_export.export_fmu(export_simulator_log=False, export_error_log=False)
        dymola_fmu_export.mos_file_path.unlink()
        utils.delete_paths(dymola_fmu_export.paths_to_delete)
        if dymola_fmu_export.fmu_path.exists():
            print(
                "FMU Export without added parameters and model modifiers was successful."
            )
            parameters_in_model = read_model_parameters(dymola_fmu_export.fmu_path)
            not_valid_parameters = check_not_valid_parameters(
                list(parameters.keys()), parameters_in_model
            )
            print(f"Possible parameters that do not exist:\n{not_valid_parameters}")
            dymola_fmu_export.fmu_path.unlink()
        else:
            print(
                "FMU Export without added parameters and model modifiers was not successful."
            )

    return None


def read_model_parameters(fmu_path: Path) -> list[str]:
    """Read the models parameters of the given fmu.

    Args:
        fmu_path (Path): Path to a fmu.

    Returns:
        list[str]: List of parameters is the model.
    """
    model_description: fmpy.model_description.ModelDescription = (
        fmpy.read_model_description(fmu_path)
    )

    return [variable.name for variable in model_description.modelVariables]


def check_not_valid_parameters(
    imported_parameters: list[str], parameters_in_model: list[str]
) -> list[str]:
    """Return parameters that were tried to be imported but were not part of the model.

    Args:
        imported_parameters (list[str]): Parameter names that were imported.
        parameters_in_model (list[str]): Parameters names in the model.

    Returns:
        list[str]: List of parameters names that are were tried to be imported
        but were not part of the model
    """
    return [
        parameter
        for parameter in imported_parameters
        if parameter not in parameters_in_model
    ]
