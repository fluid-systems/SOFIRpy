# %%
import os
import shutil
from OMPython import ModelicaSystem
from buildingspy.simulate.Simulator import Simulator
from abc import ABC, abstractmethod
import re
from typing import Union

def fmu_export( modeling_environment, model_name, model_directory, output_directory, 
                datasheet_directory, datasheets ,additional_parameters):
    pass

class FmuExport:
    
    def __init__(self, FmuExport, FileManagement, ParameterImport = None):

        fmu_export = FmuExport #class responsible for the export of the fmu
        parameter_import = ParameterImport #class responsible for import of Parameters
        file_management = FileManagement #class responsible for file Management


class ParameterImport:

    def __init__(self, model_modifier_list: list = [], parameters_dict: dict = {}) -> None:

        self.parameters = parameters_dict
        self.model_modifiers = model_modifier_list
    
    @property
    def parameters(self) -> dict:
        return self._parameters

    @parameters.setter
    def parameters(self, parameter_dict: dict) -> None:
        if type(parameter_dict) != dict:
            raise TypeError("'parameters' needs to be a dictonary")
        self._parameters = {}
        for comsym, value in parameter_dict.items():
            if '.' not in comsym: 
                raise ComponentSymbolFormatError(comsym, "The keys of the dictonary need to be in the following format: 'component_name.symbol_name'.")
            component, symbol = comsym.split('.',1)
            self.add_parameter(component, symbol, value)
    
    @property
    def model_modifiers(self) -> list:
        return self._model_modifiers

    @model_modifiers.setter
    def model_modifiers(self, model_modifier_list: list) -> None:
        if type(model_modifier_list) is not list:
            raise TypeError("'model_modifier_list' has to be a list")

        r = re.compile('redeclare [A-Za-z]+ [A-Za-z0-9]+ = [A-Za-z0-9.]+') #TODO check end of string
        for i, modifier in enumerate(model_modifier_list): #TODO maybe overwrite modifier
            modifier_striped = re.sub(' +',  ' ', modifier.strip())
            if not r.match(modifier_striped):
                raise ModelModifierFormatError(value =  modifier, message="The model modifiers need to be in the following format:e.g. 'redeclare package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater'")
            model_modifier_list[i] = modifier_striped
            
        self._model_modifiers = model_modifier_list    
    
    def read_datasheet(self, datasheet_directory: str, datasheet_dict: dict) -> None: #TODO what if datasheets all in different dir

        import json

        for component, sheet_name in datasheet_dict.items():
            with open(os.path.join(datasheet_directory, sheet_name + '.json')) as file:
                datasheet = json.load(file)
                try:
                    parameters = datasheet['Parameters']
                except KeyError:
                    print(f"The 'datasheet' {datasheet} in missing the key 'Parameters'.")
                for parameter in parameters:
                    symbol = parameter['symbol']
                    value = parameter['value']
                    if value != "":
                        self.add_parameter(component, symbol, value)

    def add_parameter(self, component: str, symbol: str, value: Union[str, int, float]) -> None:

        if type(component) != str:
            raise ComponentSymbolTypeError(component, "'Component' needs to be a string.")
        if type(symbol) != str:
            raise ComponentSymbolTypeError(symbol, "'Symbol' needs to be a string.")
        if type(value) not in (str, float, int):
            raise ValueTypeError(value, "'Value' needs to be a string, integer or float")
        
        self._parameters[f'{component}.{symbol}'] = value


class _FmuExport(ABC):

    @abstractmethod
    def add_parameters(self) -> None:
        pass
    
    @abstractmethod
    def fmu_export(self) -> None:
        pass

        
class DymolaFmuExport(_FmuExport, Simulator):
    
    def __init__(self, model_name,model_directory, dymola_path, output_directory, packages = []):
        Simulator.__init__(self, model_name, 'dymola', outputDirectory = output_directory)
        #ParameterImport.__init__(self, model_modifier_list=model_modifiers)
        
        self.packages = packages
        self.model_directory = model_directory
        self.dymola_path = dymola_path

    def make_dymola_available(self) -> None:
     
        os.environ["PATH"] += os.pathsep + self.dymola_path

    def add_parameters(self) -> None:
        for component_symbol, value in self.parameters.items():
            self.addParameters({component_symbol: value})

    def add_model_modifiers(self) -> None:

        for modifier in self.model_modifiers:
            self.addModelModifier(modifier) 

    def _get_dymola_commands(self, working_directory, log_file, model_instance, packages) -> str:
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
           model_path = f'{self.model_directory}{self.modelName}.mo')
        



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

        # function modified from buldingspy

        # Get directory name. This ensures for example that if the directory is called xx/Buildings
        # then the simulations will be done in tmp??/Buildings
        worDir = self._create_worDir()
        self._simulateDir_ = worDir
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
        print('Compiling...')
        self._runSimulation(runScriptName, self._simulator_.get('timeout'),
                                                                        worDir)

class OpenModelicaFmuExport(_FmuExport, ModelicaSystem):
    
    def fmu_export(self) -> None:
        pass

    def add_parameters(self) -> None:
        pass

class FileManagement:
    pass




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

#%%
# %%

# %%
