import os
import shutil
from OMPython import ModelicaSystem
from buildingspy.simulate.Simulator import Simulator
from abc import ABC, abstractmethod
import re
from typing import Union
import json




class ParameterImport:
    """Imports parameters and model modifiers for the fmu export."""
    
    def __init__(self, model_modifier_list: list = [], parameters_dict: dict = {}, datasheets: dict = {}, datasheet_directory: str = None) -> None:
        """ParameterImport Class Constructor to initialize the object.

        Args:
            datasheets (dict, optional): Name of datasheets as value and the corresponding component in the modeling environment as key.
                                         Example:
                                         >>>  datasheets = {"Resistor" : "Resistor_datasheet"}
                                         Defaults to {}.
            datasheet_directory (str, optional): Directory in which the datasheets are stored. Defaults to None.
        """
        self.parameters = parameters_dict
        self.model_modifiers = model_modifier_list
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
        if type(parameter_dict) != dict:
            raise TypeError("'parameter_dict' needs to be a dictionary")
        self._parameters = {}
        for comsym, value in parameter_dict.items():
            if '.' not in comsym: #TODO muss es das Format haben?
                raise ComponentSymbolFormatError(comsym, "The keys of the dictionary need to be in the following format: 'component_name.symbol_name'.")
            component, symbol = comsym.split('.',1)
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
        if type(model_modifier_list) is not list:
            raise TypeError("'model_modifier_list' has to be a list")

        r = re.compile('redeclare [A-Za-z]+ [A-Za-z0-9]+ = [A-Za-z0-9._]+$') 
        for i, modifier in enumerate(model_modifier_list): 
            modifier_striped = re.sub(' +',  ' ', modifier.strip())
            if not r.match(modifier_striped):
                raise ModelModifierFormatError(value =  modifier, message="The model modifiers need to be in the following format:e.g. 'redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater'")
            model_modifier_list[i] = modifier_striped
            
        self._model_modifiers = model_modifier_list    

    def read_datasheet(self) -> None: 
        """Reads datasheets, which are json files, and adds the data to the parameters variable.

        Raises:
            KeyError: If the datasheets are missing the key 'Parameters'
        """

        for component, sheet_name in self.datasheet_dict.items():
            with open(os.path.join(self.datasheet_directory, sheet_name + '.json')) as file:
                datasheet = json.load(file)
                if 'Parameters' not in datasheet.keys():
                    raise KeyError(f"The datasheet '{sheet_name}' in missing the key 'Parameters'.")
                parameters_from_datasheet = datasheet['Parameters']
                for parameter in parameters_from_datasheet:
                    symbol = parameter['symbol']
                    value = parameter['value']
                    if value != "":
                        self.add_parameter(component, symbol, value)


    def add_parameter(self, component: str, symbol: str, value: Union[str, int, float]) -> None:
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

        if type(component) != str:
            raise ComponentSymbolTypeError(component, "'Component' needs to be a string.")
        if type(symbol) != str:
            raise ComponentSymbolTypeError(symbol, "'Symbol' needs to be a string.")
        if type(value) not in (str, float, int):
            raise ValueTypeError(value, "'Value' needs to be a string, integer or float")
        
        self._parameters[f'{component}.{symbol}'] = value

class _FmuExport(ABC):
    """Blueprint for class that export a fmu from a certain modeling environment."""

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
        if type(model_directory) != str:
            raise TypeError("'model_directory' needs to be a string.")
        if not os.path.exists(model_directory):
            raise DirectoryDoesNotExistError(model_directory, f"The directory '{model_directory}' does not exist.")
        self._model_directory = model_directory

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
        if type(model_name) != str:
            raise TypeError("'model_name' needs to be a string.")
        path = os.path.join(self.model_directory,model_name +".mo")
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

        
class DymolaFmuExport(_FmuExport, Simulator): #TODO _ wird zu _0 beim namen der fmu
    """Export a fmu from Dymola."""

    def __init__(self, model_name: str, model_directory: str, dymola_path: str, packages: list = []):
        """DymolaFmuExport Class Constructor to initialize the object.

        Args:
            model_name (str): Name of the Dymola model.
            model_directory (str): The directory in which the Dymola model is stored.
            dymola_path (str): Path to the Dymola executable.
            packages (list, optional): Modelica packages needed in the model. Defaults to [].
        """
        Simulator.__init__(self, model_name, 'dymola')
        _FmuExport.__init__(self, model_name, model_directory)
        self.packages = packages
        self.dymola_path = dymola_path
        self.files_to_delete = ['dslog.txt', 'fmiModelIdentifier.h', 'dsmodel.c', 'buildlog.txt',
                                'dsmodel_fmuconf.h', "~FMUOutput", "dsin.txt"]
        self.files_to_move = [f'{model_name}.fmu', 'simulator.log']
        self.additional_file_moves = []
        self.files_to_delete_no_success = ['simulator.log']

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

    def _get_dymola_commands(self, working_directory: str, log_file: str, model_instance: str, packages: list) -> str:
        s = """
// File autogenerated by _get_dymola_commands_customized\n"""
        
        # Command to open packages
        if packages:
            for pack in packages:
                s+= """openModel("{0}");\n""".format(pack)

        s += """//cd("{working_directory}");
cd("{model_directory}");
openModel("{model_path}");
OutputCPUtime:=true;
""".format(working_directory=working_directory,
           log_file=log_file, 
           model_directory = self.model_directory,
           model_path = os.path.join(self.model_directory, self.model_name + '.mo'))
        
        s += "modelInstance={0};\n".format(model_instance)
  
        s += """
translateModelFMU(modelInstance, false, "", "2", "all", false, 2);
"""

        s += """savelog("{0}");\n""".format(log_file)
        if self._exitSimulator:
            s += "Modelica.Utilities.System.exit();\n"
        return s

    def _declare_parameters(self) -> list:
        """ Declare list of parameters

        Arg:
            -
        
        Returns:
            dec (list): The model instance with all parameter values and the package redeclarations.
        """

        def to_modelica(arg):
            """ Convert to Modelica array.
            """
            # Check for strings and booleans
            if isinstance(arg, str):                                        
                return arg                                                  
            elif isinstance(arg, bool):                                     
                if arg is True:
                    return 'true'
                else:
                    return 'false'
            try:
                return '{' + ", ".join(to_modelica(x) for x in arg) + '}'
            except TypeError:
                return repr(arg)
        dec = list()

        for k, v in list(self._parameters_.items()):
            # Dymola requires vectors of parameters to be set in the format
            # p = {1, 2, 3} rather than in the format of python arrays, which
            # is p = [1, 2, 3].
            # Hence, we convert the value of the parameter if required.
            s = to_modelica(v)
            dec.append('{param}={value}'.format(param=k, value=s))

        return dec 


    def fmu_export(self) -> None:


        self.make_dymola_available()
        # function modified from buldingspy
        # Get directory name. This ensures for example that if the directory is called xx/Buildings
        # then the simulations will be done in tmp??/Buildings
        worDir = self._create_worDir()
        self._simulateDir_ = worDir
        self.additional_file_moves.append(os.path.join(worDir, "run.mos"))
        # Copy directory
        shutil.copytree(os.path.abspath(self._packagePath), worDir,
                        ignore=shutil.ignore_patterns('*.svn', '*.git'))        

        # Construct the model instance with all parameter values
        # and the package redeclarations
        dec = self._declare_parameters()
        dec.extend(self._modelModifiers_)
        self.custom_settings = dec.copy()
        mi = '"{mn}({dec})"'.format(mn=self.modelName, dec=','.join(dec))
        
        # Write the Modelica script
        runScriptName = os.path.join(worDir, "run.mos").replace("\\","/")
        with open(runScriptName, mode="w", encoding="utf-8") as fil:
            fil.write(self._get_dymola_commands(
                working_directory=worDir,
                log_file="simulator.log",
                model_instance=mi,
                packages = self.packages))
        # Run script
        self._runSimulation(runScriptName, self._simulator_.get('timeout'), worDir)

class OpenModelicaFmuExport(_FmuExport, ModelicaSystem):
    
    def __init__(self) -> None:
        super().__init__()

    def add_parameters(self) -> None:
        pass

    def add_model_modifiers(self):
        pass

    def fmu_export(self) -> None:
        pass

class FileManagement:
    
    def delete_unnecessary_files(self, files_to_delete: list, directory: str) -> None:

        for file in files_to_delete:
            path = os.path.join(directory, file)
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    os.remove(path)

    def move_files(self, files: list, target_dir: str, current_dir: str ,additional_file_moves: list[str] = None) -> None:

        def move_file(current_path, target_path):
            if os.path.exists(current_path):
                os.rename(current_path, target_path)

        for file in files: 
            current_path = os.path.join(current_dir, file)
            target_path = os.path.join(target_dir, file)
            move_file(current_path, target_path)
            
        for current_path in additional_file_moves:
            move_file(current_path, os.path.join(target_dir, os.path.basename(current_path)))

class FmuExport:
    
    def __init__(self,output_directory, FmuExport: _FmuExport, FileManagement: FileManagement, ParameterImport: ParameterImport = None) -> None:

        self.modeling_env = FmuExport #class responsible for the export of the fmu
        self.parameter_import = ParameterImport #class responsible for import of Parameters
        self._file_management = FileManagement #class responsible for file Management
        self.output_directory = output_directory

    def import_parameters(self) -> None:
        
        if self.parameter_import:
            self.parameter_import.read_datasheet() 
            self.modeling_env.add_parameters(self.parameter_import.parameters)
            self.modeling_env.add_model_modifiers(self.parameter_import.model_modifiers)

    def fmu_export(self) -> bool:
        
        self.modeling_env.fmu_export()
        return self.check_fmu_export()
        
    def check_fmu_export(self) -> bool:

        fmu_path = os.path.join(self.modeling_env.model_directory, self.modeling_env.model_name + ".fmu")

        if os.path.exists(fmu_path):
            return True
        else:
            return False

    def file_management(self, files_to_delete: list, files_to_move: list = [], additional_file_moves:list = []) -> None:

        self._file_management.delete_unnecessary_files(files_to_delete, self.modeling_env.model_directory)
        self._file_management.move_files(files_to_move,self.output_directory,self.modeling_env.model_directory ,additional_file_moves)

def _initialize( modeling_environment: str, model_name:str, model_directory:str,env_path, output_directory, 
                _datasheet_directory = None, _datasheets = {} ,parameters = {}, model_modifiers = []) -> FmuExport:

    if modeling_environment.lower().startswith("d"):
        modeling_env = DymolaFmuExport(model_name, model_directory, env_path)
    elif modeling_environment.lower().startswith("o"):
        modeling_env = OpenModelicaFmuExport()
    else:
        raise ModelEnvironmentArgumentError("Enter either d for Dymola or o for OpenModelica as the 'modeling_environment'.")

    if (_datasheet_directory and _datasheets) or parameters or model_modifiers:
        parameter_import = ParameterImport( model_modifiers, parameters,_datasheets, _datasheet_directory)
    else:
        parameter_import = None

    _file_management = FileManagement()
    
    fmu_export = FmuExport(output_directory,modeling_env, _file_management, parameter_import)

    return fmu_export
        
def export_fmu( modeling_environment: str, model_name:str, model_directory:str,env_path, output_directory, 
                datasheet_directory = None, datasheets = {} ,additional_parameters = {}, model_modifiers = []) -> FmuExport:
    
    fmu_export = _initialize(modeling_environment, model_name, model_directory, env_path, output_directory, 
                datasheet_directory, datasheets, additional_parameters, model_modifiers)

    fmu_export.import_parameters()
    success = fmu_export.fmu_export()

    if success:
        fmu_export.file_management(fmu_export.modeling_env.files_to_delete, fmu_export.modeling_env.files_to_move, fmu_export.modeling_env.additional_file_moves)
        print("The FMU Export was successful.")
    else:
        print("The FMU Export was not successful. Checking if parameters were added that do not exist...")
        fmu_export.file_management(fmu_export.modeling_env.files_to_delete_no_success)
        # check if parameter where imported that do not exist
        # try fmu export without added parameters
        _fmu_export = _initialize(modeling_environment, model_name, model_directory, env_path, output_directory)
        success = _fmu_export.fmu_export()
        if success:
            check_paremeters_exist = CheckParametersExist()
            check_paremeters_exist.read_model_parameters(model_directory, model_name)
            possibly_non_existing_parameters = check_paremeters_exist.check(list(fmu_export.parameter_import.parameters.keys()))
            # files that need to be moved if fmu export was successful the first time now need to be deleted as well
            files_to_delete = _fmu_export.modeling_env.files_to_delete + _fmu_export.modeling_env.files_to_move
            _fmu_export.file_management(files_to_delete)
            print("The FMU Export without added parameters was successful.")
            print("Check if model_modifiers and added parameters exist in the model. ")
            print(f"Possible parameters that do not exist:\n{possibly_non_existing_parameters}")
            print("Check if values of added parameters are valid.")
            if model_modifiers:
                print("Check if model modifiers are valid.")

        else:
            print('The FMU Export without added parameters was not successful.')
            if modeling_environment == 'd':
                print('Check if Dymola license is active.')
            _fmu_export.file_management(_fmu_export.modeling_env.files_to_delete_no_success)

    return fmu_export

class CheckParametersExist:
    
    def read_model_parameters(self, model_directory: str, model_name: str) -> None:

        from fmpy import read_model_description
        
        fmu_path = os.path.join(model_directory, model_name + ".fmu")
        model_description = read_model_description(fmu_path)

        self.variables =  [variable.name for variable in model_description.modelVariables]

    def check(self, parameters: list) -> list:

        return [parameter for parameter in parameters if parameter not in self.variables]
      
class ModelModifierFormatError(Exception):
    """Custom error that is raised when the 'model modifier' doesn't have the right format."""

    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(message)

class ComponentSymbolTypeError(Exception):
    """ Custom error that is raised when the component symbol name that is added is not a string."""

    def __init__(self, value, message):
        self.value = value
        self.message = message
        super().__init__(message)

class ValueTypeError(Exception):
    """ Custom error that is raised when the value that is added is not a string a int or a float."""

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
