import os
import shutil
import warnings
from OMPython import ModelicaSystem
from buildingspy.simulate.Simulator import Simulator
from abc import ABC, abstractmethod
import re
from typing import Union
import json


class ParameterImport:
    """Imports parameters and model modifiers for the fmu export."""

    def __init__(
        self,
        model_modifier_list: list = None,
        parameters_dict: dict = None,
        datasheets: dict = None,
        datasheet_directory: str = None,
    ) -> None:
        """ParameterImport Class Constructor to initialize the object.

        Args:
            datasheets (dict, optional): Name of datasheets as value and the corresponding component in the modeling environment as key.
                                         Example:
                                         >>>  datasheets = {"Resistor" : "Resistor_datasheet"}
                                         Defaults to {}.
            datasheet_directory (str, optional): Directory in which the datasheets are stored. Defaults to None.
        """
        if not parameters_dict:
            parameters_dict = {}
        self.parameters = parameters_dict
        if not model_modifier_list:
            model_modifier_list = []
        self.model_modifiers = model_modifier_list
        if not datasheet_directory:
            datasheets = {}
        self.datasheet_dict = datasheets
        self.datasheet_directory = datasheet_directory

    @property
    def parameters(self) -> dict:
        """Get the parameters."""
        return self._parameters

    @parameters.setter
    def parameters(self, parameter_dict: dict) -> None:
        """Set the parameters. The type of the argument 'parameter_dict' will be checked.
        Also the key and values are checked to ensure they are the right type and have the right format.

        Args:
            parameter_dict(dict): Dictionary in which the parameters and their values are stored.
                                  Example:
                                  >>> parameter_dict = {"Resistor.R" : "1", "Resistor.useHeatPort": "true"}

        Raises:
            TypeError: If the the argument 'parameter_dict' is not a dictionary.
            ComponentSymbolFormatError: If the keys or the values of the argument 'parameter_dict' have a wrong format.
        """
        if not isinstance(parameter_dict, dict):
            raise TypeError("'parameter_dict' needs to be a dictionary")
        self._parameters = {}
        for comsym, value in parameter_dict.items():
            if "." not in comsym:  # TODO muss es das Format haben?
                raise ComponentSymbolFormatError(
                    comsym,
                    "The keys of the dictionary need to be in the following format: 'component_name.symbol_name'.",
                )
            component, symbol = comsym.split(".", 1)
            self.add_parameter(component, symbol, value)

    @property
    def model_modifiers(self) -> list:
        """Get the model modifiers."""
        return self._model_modifiers

    @model_modifiers.setter
    def model_modifiers(self, model_modifier_list: list) -> None:
        """Sets the model modifiers and checks whether they have the right formart.

        Raises:
            TypeError: If the 'model_modifier_list' is not a list
            ModelModifierFormatError: If the model modifiers do not have the right format.
        """
        if not isinstance(model_modifier_list, list):
            raise TypeError("'model_modifier_list' has to be a list")

        r = re.compile("redeclare [A-Za-z]+ [A-Za-z0-9]+ = [A-Za-z0-9._]+$")
        for i, modifier in enumerate(model_modifier_list):
            modifier_striped = re.sub(" +", " ", modifier.strip())
            if not r.match(modifier_striped):
                raise ModelModifierFormatError(
                    value=modifier,
                    message="The model modifiers need to be in the following format:e.g. 'redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater'",
                )
            model_modifier_list[i] = modifier_striped

        self._model_modifiers = model_modifier_list

    def read_datasheet(self) -> None:
        """Reads datasheets, which are json files, and adds the data to the parameters variable.

        Raises:
            KeyError: If the datasheets are missing the key 'Parameters'
        """

        for component, sheet_name in self.datasheet_dict.items():
            with open(
                os.path.join(self.datasheet_directory, sheet_name + ".json")
            ) as file:
                datasheet = json.load(file)
                if "Parameters" not in datasheet.keys():
                    raise KeyError(
                        f"The datasheet '{sheet_name}' in missing the key 'Parameters'."
                    )
                parameters_from_datasheet = datasheet["Parameters"]
                for parameter in parameters_from_datasheet:
                    symbol = parameter["symbol"]
                    value = parameter["value"]
                    if value != "":
                        self.add_parameter(component, symbol, value)

    def add_parameter(
        self, component: str, symbol: str, value: Union[str, int, float]
    ) -> None:
        """Adds a variable and its value to the parameters.

        Args:
            component (str): The component name in the modelica model.
            symbol (str): The symbol name of a certain variable of a component.
            value (Union[str, int, float]): The value of a variable.

        Raises:
            ComponentSymbolTypeError: If 'component' is no a string.
            ComponentSymbolTypeError: If 'symbol' is not a string.
            ValueTypeError: If 'value' is not a string, integer or a float
        """

        if not isinstance(component, str):
            raise ComponentSymbolTypeError(
                component, "'Component' needs to be a string."
            )
        if not isinstance(symbol, str):
            raise ComponentSymbolTypeError(symbol, "'Symbol' needs to be a string.")
        if not isinstance(value, (str, float, int)):
            raise ValueTypeError(
                value, "'Value' needs to be a string, integer or float"
            )

        self._parameters[f"{component}.{symbol}"] = value


class _FmuExport(ABC):
    """Blueprint for class that exports a fmu from a certain modeling environment."""

    def __init__(self, model_name: str, model_directory: str) -> None:
        """_FmuExport Class Constructor to initialize the object."""

        self.model_directory = model_directory
        self.model_name = model_name

    @property
    def model_directory(self) -> str:
        """Get the model direcotry"""
        return self._model_directory

    @model_directory.setter
    def model_directory(self, model_directory: str) -> None:
        """Set the model direcotry.

        Args:
            model_directory (str): The directory in which the model is stored.

        Raises:
            TypeError: If the model directory is not a string.
            DirectoryDoesNotExistError: If the directory does not exist.
        """
        if not isinstance(model_directory, str):
            raise TypeError("'model_directory' needs to be a string.")
        if not os.path.exists(model_directory):
            raise DirectoryDoesNotExistError(
                model_directory, f"The directory '{model_directory}' does not exist."
            )

        self._model_directory = os.path.normpath(model_directory)

    @property
    def model_name(self) -> str:
        """Get the model name"""
        return self._model_name

    @model_name.setter
    def model_name(self, model_name: str) -> None:
        """Set the model name.

        Args:
            model_name (str): The name of the model.

        Raises:
            TypeError: If the model name is not a string.
            FileNotFoundError: If the file does not exist.
        """
        if not isinstance(model_name, str):
            raise TypeError("'model_name' needs to be a string.")
        path = os.path.join(self.model_directory, model_name + ".mo")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path '{path}' does not exist.")
        self._model_name = model_name

    @abstractmethod
    def add_parameters(self) -> None:
        """This methode should implement how to add parameters to the modeling environemt."""
        pass

    @abstractmethod
    def add_model_modifiers(self):
        """This methode should implement how to add model modifiers to the modeling environemt."""
        pass

    @abstractmethod
    def fmu_export(self) -> None:
        """This methode should implement how to export a fmu from the modeling environemt."""
        pass


class DymolaFmuExport(_FmuExport, Simulator):
    """Export a fmu from Dymola."""

    def __init__(
        self,
        model_name: str,
        model_directory: str,
        dymola_path: str,
        packages: list = [],
        keep_log=True,
        keep_run=True,
    ):
        """DymolaFmuExport Class Constructor to initialize the object.

        Args:
            model_name (str): Name of the Dymola model.
            model_directory (str): The directory in which the Dymola model is stored.
            dymola_path (str): Path to the Dymola executable.
            packages (list, optional): Modelica packages needed in the model. Defaults to [].
        """
        Simulator.__init__(self, model_name, "dymola")
        _FmuExport.__init__(self, model_name, model_directory)
        self._model_directory = self.model_directory.replace("\\", "/") + "/"
        self.packages = packages
        self.dymola_path = dymola_path
        self.dump_directory = self.model_directory
        self.fmu_name = self.model_name.replace("_", "_0")
        self.files_to_delete = [
            "dslog.txt",
            "fmiModelIdentifier.h",
            "dsmodel.c",
            "buildlog.txt",
            "dsmodel_fmuconf.h",
            "~FMUOutput",
            "dsin.txt",
        ]
        if not keep_log:
            self.files_to_delete += [f"simulator_{self.model_name}.log"]
            self.files_to_move = [f"{self.fmu_name}.fmu"]
        else:
            self.files_to_move = [
                f"{self.fmu_name}.fmu",
                f"simulator_{self.model_name}.log",
            ]
        self.keep_run = keep_run
        self.additional_file_moves = []
        self.files_to_delete_no_success = [f"simulator_{self.model_name}.log"]

    def make_dymola_available(self) -> None:
        """Adds Dymola executable path to the environment variables."""

        os.environ["PATH"] += os.pathsep + self.dymola_path

    def add_parameters(self, parameters: dict) -> None:
        """Adds the parameters to the simulator.

        Args:
            parameters (dict): [description]
        """

        for component_symbol, value in parameters.items():
            self.addParameters({component_symbol: value})

    def add_model_modifiers(self, model_modifiers) -> None:

        for modifier in model_modifiers:
            self.addModelModifier(modifier)

    def _get_dymola_commands(
        self, working_directory: str, log_file: str, model_instance: str, packages: list
    ) -> str:
        s = """
// File autogenerated by _get_dymola_commands_customized\n"""

        # Command to open packages
        if packages:
            for pack in packages:
                s += """openModel("{0}");\n""".format(pack)

        s += """//cd("{working_directory}");
cd("{model_directory}");
openModel("{model_path}");
OutputCPUtime:=true;
""".format(
            working_directory=working_directory,
            log_file=log_file,
            model_directory=self.model_directory,
            model_path=os.path.join(self.model_directory, self.model_name + ".mo"),
        )

        s += "modelInstance={0};\n".format(model_instance)

        s += """
translateModelFMU(modelInstance, false, "", "2", "all", false, 2);
"""

        s += """savelog("{0}");\n""".format(log_file)
        if self._exitSimulator:
            s += "Modelica.Utilities.System.exit();\n"
        return s

    def _declare_parameters(self) -> list:
        """Declare list of parameters

        Arg:
            -

        Returns:
            dec (list): The model instance with all parameter values and the package redeclarations.
        """

        def to_modelica(arg):
            """Convert to Modelica array."""
            # Check for strings and booleans
            if isinstance(arg, str):
                return arg
            elif isinstance(arg, bool):
                if arg is True:
                    return "true"
                else:
                    return "false"
            try:
                return "{" + ", ".join(to_modelica(x) for x in arg) + "}"
            except TypeError:
                return repr(arg)

        dec = list()

        for k, v in list(self._parameters_.items()):
            # Dymola requires vectors of parameters to be set in the format
            # p = {1, 2, 3} rather than in the format of python arrays, which
            # is p = [1, 2, 3].
            # Hence, we convert the value of the parameter if required.
            s = to_modelica(v)
            dec.append("{param}={value}".format(param=k, value=s))

        return dec

    def fmu_export(self) -> None:

        self.make_dymola_available()
        # function modified from buldingspy
        # Get directory name. This ensures for example that if the directory is called xx/Buildings
        # then the simulations will be done in tmp??/Buildings
        worDir = self._create_worDir()
        self._simulateDir_ = worDir
        if self.keep_run:
            self.additional_file_moves.append(
                os.path.join(worDir, f"run_{self.model_name}.mos")
            )
        # Copy directory
        shutil.copytree(
            os.path.abspath(self._packagePath),
            worDir,
            ignore=shutil.ignore_patterns("*.svn", "*.git"),
        )

        # Construct the model instance with all parameter values
        # and the package redeclarations
        dec = self._declare_parameters()
        dec.extend(self._modelModifiers_)
        self.custom_settings = dec.copy()
        mi = '"{mn}({dec})"'.format(mn=self.modelName, dec=",".join(dec))

        # Write the Modelica script
        runScriptName = os.path.join(worDir, f"run_{self.model_name}.mos").replace(
            "\\", "/"
        )
        with open(runScriptName, mode="w", encoding="utf-8") as fil:
            fil.write(
                self._get_dymola_commands(
                    working_directory=worDir,
                    log_file=f"simulator_{self.model_name}.log",
                    model_instance=mi,
                    packages=self.packages,
                )
            )
        # Run script
        self._runSimulation(runScriptName, self._simulator_.get("timeout"), worDir)


class OpenModelicaFmuExport(_FmuExport, ModelicaSystem):
    def __init__(self, model_name, model_directory) -> None:
        _FmuExport.__init__(self, model_name, model_directory)
        self._model_directory = self.model_directory.replace("\\", "//")
        model_path = os.path.join(self.model_directory, model_name + ".mo")
        ModelicaSystem.__init__(self, model_path, model_name)
        self.fmu_name = self.model_name
        self.dump_directory = os.getcwd()
        self.files_to_move = [f"{self.fmu_name}.fmu"]
        self.files_to_delete = [
            f"{self.model_name}.c",
            f"{self.model_name}.exe",
            f"{self.model_name}.libs",
            f"{self.model_name}.log",
            f"{self.model_name}.makefile",
            f"{self.model_name}.o",
            f"{self.model_name}_01exo.c",
            f"{self.model_name}_01exo.o",
            f"{self.model_name}_02nls.c",
            f"{self.model_name}_02nls.o",
            f"{self.model_name}_03lsy.c",
            f"{self.model_name}_03lsy.o",
            f"{self.model_name}_04set.c",
            f"{self.model_name}_04set.o",
            f"{self.model_name}_05evt.c",
            f"{self.model_name}_05evt.o",
            f"{self.model_name}_06inz.c",
            f"{self.model_name}_06inz.o",
            f"{self.model_name}_07dly.c",
            f"{self.model_name}_07dly.o",
            f"{self.model_name}_08bnd.c",
            f"{self.model_name}_08bnd.o",
            f"{self.model_name}_09alg.c",
            f"{self.model_name}_09alg.o",
            f"{self.model_name}_10asr.c",
            f"{self.model_name}_10asr.o",
            f"{self.model_name}_11mix.c",
            f"{self.model_name}_11mix.h",
            f"{self.model_name}_11mix.o",
            f"{self.model_name}_12jac.c",
            f"{self.model_name}_12jac.h",
            f"{self.model_name}_12jac.o",
            f"{self.model_name}_13opt.c",
            f"{self.model_name}_13opt.h",
            f"{self.model_name}_13opt.o",
            f"{self.model_name}_14lnz.c",
            f"{self.model_name}_14lnz.o",
            f"{self.model_name}_15syn.c",
            f"{self.model_name}_15syn.o",
            f"{self.model_name}_16dae.c",
            f"{self.model_name}_16dae.h",
            f"{self.model_name}_16dae.o",
            f"{self.model_name}_17inl.c",
            f"{self.model_name}_17inl.o",
            f"{self.model_name}_functions.c",
            f"{self.model_name}_functions.h",
            f"{self.model_name}_functions.o",
            f"{self.model_name}_includes.h",
            f"{self.model_name}_info.json",
            f"{self.model_name}_init.xml",
            f"{self.model_name}_literals.h",
            f"{self.model_name}_model.h",
            f"{self.model_name}_records.c",
            f"{self.model_name}_records.o",
            f"{self.model_name}_FMU.libs",
            f"{self.model_name}_FMU.log",
            f"{self.model_name}_FMU.makefile",
        ]
        self.additional_file_moves = None
        self.files_to_delete_no_success = self.files_to_delete

    def add_parameters(self) -> None:
        pass

    def add_model_modifiers(self):
        pass

    def fmu_export(self) -> None:
        self.convertMo2Fmu()


class FileManagement:
    """Moves and deletes files"""

    def delete_unnecessary_files(self, files_to_delete: list, directory: str) -> None:
        """Deletes unnecessary files"

        Args:
            files_to_delete (list): Name of the files to be deleted.
            directory (str): Direcotry in which the files are located.
        """

        for file in files_to_delete:
            path = os.path.join(directory, file)
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)

    def move_files(
        self,
        files: list,
        target_dir: str,
        source_dir: str,
        additional_file_moves: list = None,
    ) -> None:
        """Moves files from a source directory to a target directory.

        Args:
            files (list): Name of the files to be moved.
            target_dir (str): Name of the target directory.
            source_dir (str): Name of the source directory.
            additional_file_moves (list, optional): Path of the files to be moved. Defaults to None.
        """

        def move_file(source_path, target_path):
            if os.path.exists(source_path):
                src_path = os.path.normpath(source_path)
                tar_path = os.path.normpath(target_path)
                if not src_path == tar_path:
                    try:
                        os.rename(src_path, tar_path)
                    except FileExistsError as e:
                        while True:
                            overwrite = input(
                                f"The path {tar_path} already exists. Overwrite? [y/n]"
                            )
                            if overwrite == "y" or overwrite == "n":
                                if overwrite == "y":
                                    break
                                elif overwrite == "n":
                                    raise e
                                else:
                                    print("Enter 'y' or 'n'.")
                        os.replace(src_path, tar_path)

        for file in files:
            source_path = os.path.join(source_dir, file)
            target_path = os.path.join(target_dir, file)
            move_file(source_path, target_path)

        if additional_file_moves:
            for source_path in additional_file_moves:
                move_file(
                    source_path,
                    os.path.join(target_dir, os.path.basename(source_path)),
                )


class FmuExport:
    """Imports Parameters, exports a fmu and does the file management."""

    def __init__(
        self,
        output_directory: str,
        FmuExport: _FmuExport,
        FileManagement: FileManagement,
        ParameterImport: ParameterImport = None,
    ) -> None:
        """
        Args:
            output_directory (str): Target directory for the generated files.
            FmuExport (_FmuExport): FmuExport class
            FileManagement (FileManagement): File management class
            ParameterImport (ParameterImport, optional): Parameter import class. Defaults to None.
        """

        self.modeling_env = FmuExport  # class responsible for the export of the fmu
        self.parameter_import = (
            ParameterImport  # class responsible for import of Parameters
        )
        self._file_management = FileManagement  # class responsible for file Management
        self.output_directory = output_directory
        self.fmu_path = os.path.join(
            self.modeling_env.dump_directory, self.modeling_env.fmu_name + ".fmu"
        )

    @property
    def fmu_path(self) -> str:
        return self._fmu_path

    @fmu_path.setter
    def fmu_path(self, fmu_path: str):
        """Sets the fmu path and checks if the path already exists.

        Args:
            fmu_path (str): Path to the generated fmu.

        Raises:
            FmuAlreadyExistsError: If a fmu with the same path already exists.
        """

        if os.path.exists(fmu_path):
            while True:
                overwrite = input(
                    "The new fmu will have the same path as an existing fmu. Overwrite? [y/n]"
                )
                if overwrite == "y" or overwrite == "n":
                    if overwrite == "y":
                        break
                    elif overwrite == "n":
                        raise FmuAlreadyExistsError("Stopping execution.")
                    else:
                        print("Enter 'y' or 'n'")
        self._fmu_path = os.path.normpath(fmu_path)

    def import_parameters(self) -> None:
        """Calls the functions from the ParameterImport class"""

        if self.parameter_import:
            self.parameter_import.read_datasheet()
            self.modeling_env.add_parameters(self.parameter_import.parameters)
            self.modeling_env.add_model_modifiers(self.parameter_import.model_modifiers)

    def fmu_export(self) -> bool:
        """Exports a fmu.

        Returns:
            bool: If the export was successful returns true else false.
        """

        self.modeling_env.fmu_export()
        return self.check_fmu_export()

    def check_fmu_export(self) -> bool:
        """Checks if the fmu export was successful.

        Returns:
            bool: If the export was successful returns true else false
        """

        if os.path.exists(self.fmu_path):
            return True
        else:
            return False

    def file_management(
        self,
        files_to_delete: list,
        files_to_move: list = [],
        additional_file_moves: list = [],
    ) -> None:

        self._file_management.delete_unnecessary_files(
            files_to_delete, self.modeling_env.dump_directory
        )
        self._file_management.move_files(
            files_to_move,
            self.output_directory,
            self.modeling_env.dump_directory,
            additional_file_moves,
        )
        self._fmu_path = os.path.normpath(
            os.path.join(self.output_directory, self.modeling_env.fmu_name + ".fmu")
        )


def _initialize(
    modeling_environment: str,
    model_name: str,
    model_directory: str,
    output_directory: str,
    env_path: str = None,
    datasheet_directory: str = None,
    datasheets: dict = None,
    parameters: dict = None,
    model_modifiers: list = None,
    packages: list = None,
    keep_log: bool = True,
    keep_run: bool = True,
) -> FmuExport:

    if modeling_environment.lower().startswith("d"):
        if not env_path:
            raise TypeError("'env_path' needs to be defined.")
        modeling_env = DymolaFmuExport(
            model_name,
            model_directory,
            env_path,
            packages=packages,
            keep_run=keep_run,
            keep_log=keep_log,
        )
    elif modeling_environment.lower().startswith("o"):
        modeling_env = OpenModelicaFmuExport(model_name, model_directory)
        if parameters or datasheets or datasheets or model_modifiers:
            warnings.warn("Parameter for importing are specified, but the parameter import for OpenModelica is not supported.")
    else:
        raise ModelEnvironmentArgumentError(
            "Enter either d for Dymola or o for OpenModelica as the 'modeling_environment'."
        )

    if (
        (datasheet_directory and datasheets) or parameters or model_modifiers
    ) and modeling_environment.lower().startswith("d"):
        parameter_import = ParameterImport(
            model_modifiers, parameters, datasheets, datasheet_directory
        )
    else:
        parameter_import = None

    _file_management = FileManagement()

    fmu_export = FmuExport(
        output_directory, modeling_env, _file_management, parameter_import
    )

    return fmu_export


def export_fmu(
    modeling_environment: str,
    model_name: str,
    model_directory: str,
    output_directory,
    env_path=None,
    datasheet_directory=None,
    datasheets={},
    additional_parameters={},
    model_modifiers=[],
    packages=[],
    keep_log=True,
    keep_run=True,
) -> FmuExport:

    fmu_export = _initialize(
        modeling_environment,
        model_name,
        model_directory,
        output_directory,
        env_path,
        datasheet_directory=datasheet_directory,
        datasheets=datasheets,
        parameters=additional_parameters,
        model_modifiers=model_modifiers,
        packages=packages,
        keep_log=keep_log,
        keep_run=keep_run,
    )

    fmu_export.import_parameters()
    success = fmu_export.fmu_export()

    if success:
        fmu_export.file_management(
            fmu_export.modeling_env.files_to_delete,
            fmu_export.modeling_env.files_to_move,
            fmu_export.modeling_env.additional_file_moves,
        )
        print("The FMU Export was successful.")
    else:
        print("The FMU Export was not successful.")
        fmu_export.file_management(fmu_export.modeling_env.files_to_delete_no_success)
        # check if parameter where imported that do not exist
        # try fmu export without added parameters
        if modeling_environment.lower().startswith("d"):
            print("Exporting fmu without added parameters.")
            _fmu_export = _initialize(
                modeling_environment,
                model_name,
                model_directory,
                output_directory,
                env_path,
            )
            success = _fmu_export.fmu_export()
            if success:
                check_paremeters_exist = CheckParametersExist()
                check_paremeters_exist.read_model_parameters(
                    _fmu_export.modeling_env.dump_directory,
                    _fmu_export.modeling_env.fmu_name,
                )
                possibly_non_existing_parameters = check_paremeters_exist.check(
                    list(fmu_export.parameter_import.parameters.keys())
                )
                # files that need to be moved if fmu export was successful the first time now need to be deleted as well
                files_to_delete = (
                    _fmu_export.modeling_env.files_to_delete
                    + _fmu_export.modeling_env.files_to_move
                )
                _fmu_export.file_management(files_to_delete)
                print("The FMU Export without added parameters was successful.")
                print(
                    "Check if model_modifiers and added parameters exist in the model. "
                )
                print(
                    f"Possible parameters that do not exist:\n{possibly_non_existing_parameters}"
                )
                print("Check if values of added parameters are valid.")
                if model_modifiers:
                    print("Check if model modifiers are valid.")

            else:
                print("The FMU Export without added parameters was not successful.")
                print("Check if Dymola license is active.")
                _fmu_export.file_management(
                    _fmu_export.modeling_env.files_to_delete_no_success
                )
            raise FmuExportError("The FMU Export was not successful")
        else:
            raise FmuExportError("The FMU Export was not successful")

    return fmu_export


class CheckParametersExist:
    def read_model_parameters(self, model_directory: str, fmu_name: str) -> None:

        from fmpy import read_model_description

        fmu_path = os.path.join(model_directory, fmu_name + ".fmu")
        model_description = read_model_description(fmu_path)

        self.variables = [
            variable.name for variable in model_description.modelVariables
        ]

    def check(self, parameters: list) -> list:

        return [
            parameter for parameter in parameters if parameter not in self.variables
        ]


class ModelModifierFormatError(Exception):
    """Custom error that is raised when the 'model modifier' doesn't have the right format."""

    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(message)


class ComponentSymbolTypeError(Exception):
    """Custom error that is raised when the component symbol name that is added is not a string."""

    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(message)


class ValueTypeError(Exception):
    """Custom error that is raised when the value that is added is not a string a int or a float."""

    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(message)


class ComponentSymbolFormatError(Exception):
    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(message)


class DirectoryDoesNotExistError(Exception):
    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(message)


class ModelEnvironmentArgumentError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class FmuAlreadyExistsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class FmuExportError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)
