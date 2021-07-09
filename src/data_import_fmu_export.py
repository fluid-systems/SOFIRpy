# %%
from OMPython import ModelicaSystem
from OMPython import OMCSessionZMQ
from buildingspy.simulate.Simulator import Simulator
import json
import os
import shutil
import sys

class DataManagement():
    def __init__(self, model_name, model_directory, output_directory, 
                    datasheet_directory, datasheets ,additional_parameters):
                
        self.model_name = model_name
        self.model_directory = model_directory
        self.output_directory = output_directory
        self.datasheet_directory = datasheet_directory
        self.datasheets = datasheets
        self.data_sheet_names = list(self.datasheets.values())
        self.added_components = list(self.datasheets.keys())
        self.added_parameter_names = []
        self.added_parameter_values = []
        self.additional_component_symbols = list(additional_parameters.keys())
        self.additional_values = list(additional_parameters.values())
        self.components_in_model = []       
        self.model_vars = {}
        
        
    def read_datasheets(self):

        for component, sheet_name in zip(self.added_components, self.data_sheet_names):
            with open(f'{self.datasheet_directory}/{sheet_name}.json') as read_file:
                data_sheet = json.load(read_file)
            
            modelica_parameters = data_sheet["Dymola parameters"]
            _values = [sub['value'] for sub in modelica_parameters]
            _symbols = [sub['symbol'] for sub in modelica_parameters]
            for value, symbol in zip(_values, _symbols):
                if value != "":
                    self.added_parameter_names.append(f'{component}.{symbol}')
                    self.added_parameter_values.append(value)

    def check_fmu_export(self):
        
        fmu = self.model_directory + self.model_name + ".fmu"
        if os.path.exists(fmu):
            print('The FMU Export was successful!')
            return True
        else:
            print("The FMU was not exported.")
            return False

    def show_possible_faults(self):
        	
        if self.modeling_environment.lower().startswith("d"):
            
            dymola_simulator_log_path = self.model_directory + "simulator.log"
            with open(dymola_simulator_log_path, "r") as log_file:
                simulator_log = log_file.read() 
            
            print('The FMU was not exported!\n'
             'Possible faults:\n'
             'Model specific error.\n'
             'No active Dymola License.\n'
             'The model name or model path is not correct.\n'
             'The model name was changed in the explorer, but not in Dymola\n'
             'Packages needed in the model are not imported.\n'
             'Custom Dymola models are not stored in the model path.\n'
             'Log:\n'
             f'{simulator_log}\n')



    def delete_unnecessary_files(self):
        
        print("Deleting unnecessary files...")
        delete = ['dslog.txt', 'fmiModelIdentifier.h', 'dsmodel.c', 'buildlog.txt',
        'dsmodel_fmuconf.h', "~FMUOutput", "dsin.txt"]

        for de in delete:
            file_path = self.model_directory + de
            if os.path.exists(file_path):
                if de == "~FMUOutput":
                    shutil.rmtree(file_path, ignore_errors=True)
                else:
                    os.remove(file_path)

    def move_files_to_outputdirectory(self):
        
        print("Moving files to the output directory...")

        filLis = ["simulator.log", self.model_name+'.fmu']

        for fil in filLis:
            srcFil = os.path.normpath(self.model_directory + fil)
            newFil = os.path.normpath(self.output_directory + fil)
            if os.path.exists(srcFil):
                os.rename(srcFil, newFil)

        if self.modeling_environment.lower().startswith("d"):
            os.rename(self._simulateDir_+"/run.mos", self.output_directory+"/run.mos")

    
    def copy_modelica_models(self): #maybe move this funcion to another module --> data module
        
        model_files = os.listdir(self.model_directory)
        for model in model_files:
            if model.endswith("mo"):
                model_copy_path = f'{self.model_directory}{model}'
                model_paste_path = f'{self.output_directory}{model}'
                shutil.copyfile(model_copy_path, model_paste_path)

        print('Model copied.')

    def files_management(self):

        self.delete_unnecessary_files()
        self.move_files_to_outputdirectory()
        

class Dymola(Simulator, DataManagement):
 
    def __init__(self, model_name,dymola_path, model_directory, output_directory ,
                    datasheet_directory, datasheets, additional_parameters, packages):

        Simulator.__init__(self, model_name, "dymola", output_directory)
        DataManagement.__init__(self, model_name, model_directory, output_directory, datasheet_directory, datasheets ,additional_parameters)
        self.dymola_path = dymola_path
        self.packages = packages
        self.modeling_environment = "dymola"


    def make_dymola_available(self):
        """Makes the dymola.exe available.

        Args:
            -

        Returns:
            -
            
        """

        os.environ["PATH"] += os.pathsep + self.dymola_path


    def add_parameters(self):
        
        self.read_datasheets()

       

        for value, component_symbol in zip(self.added_parameter_values, self.added_parameter_names):
            self.addParameters({component_symbol: value})   # function inherited from Simulator
        

        print('Parameters from datasheets added')
    

    def add_additional_parameters(self):
        """Reads the additional_parameters dictionary and adds the dymola symbols and values to a variable.
        
        Args:
            -

        Returns:
            -

        """

        if self.additional_component_symbols:
            for comp_sym, value in zip(self.additional_component_symbols, self.additional_values):
                self.addParameters({comp_sym: value})
            print('Additional parameters added')
        
        else: 
            print('No additional parameters added')

    def fmu_export(self):
        """Exports an FMU of the model.

        This method
            1. Writes a Modelica script to the temporary directory.
            2. Starts the Modelica simulation environment from the temporary directory.
            3. Exports a FMU of the model.
            4. Closes the Modelica simulation environment.
            

        This method requires that the directory that contains the executable *dymola*
        is on the system PATH variable. If it is not found, the function returns with
        an error message.

        Args:
            -

        Returns:
            -

        """

        # Get directory name. This ensures for example that if the directory is called xx/Buildings
        # then the simulations will be done in tmp??/Buildings
        worDir = self._create_worDir()
        self._simulateDir_ = worDir
        # Copy directory
        shutil.copytree(os.path.abspath(self._packagePath), worDir,
                        ignore=shutil.ignore_patterns('*.svn', '*.git'))        

        # Construct the model instance with all parameter values
        # and the package redeclarations
        dec = self._declare_parameters_customized()
        dec.extend(self._modelModifiers_)
        self.custom_settings = dec.copy()
        mi = '"{mn}({dec})"'.format(mn=self.modelName, dec=','.join(dec))
        
        # Write the Modelica script
        runScriptName = os.path.join(worDir, "run.mos").replace("\\","/")
        with open(runScriptName, mode="w", encoding="utf-8") as fil:
            fil.write(self._get_dymola_commands_customized(
                working_directory=worDir,
                log_file="simulator.log",
                model_instance=mi,
                packages = self.packages))
        # Run script
        print('Compiling...')
        self._runSimulation(runScriptName, self._simulator_.get('timeout'),
                                                                        worDir)
               

    def _get_dymola_commands_customized(self, working_directory, log_file, model_instance, packages):
        """ Returns a string that contains all the commands required
            to export the model as a FMU.

        Args: 
            working_directory (string):     The working directory for the FMU export.
            log_file (string):              The name of the log file that will be written by Dymola.
            model_instance (string):        Contains the model name and model parameters for the .mos script.  
            packages (list):                Path to the packages used.

        Returns:
            s  (string):                The commands for the .mos script. 
        """

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
        # Pre-processing commands
        for prePro in self._preProcessing_:
            s += prePro + '\n'



        s += "modelInstance={0};\n".format(model_instance)
  
        s += """
translateModelFMU(modelInstance, false, "", "2", "all", false, 2);
"""

        s += """savelog("{0}");\n""".format(log_file)
        if self._exitSimulator:
            s += "Modelica.Utilities.System.exit();\n"
        return s


    def _declare_parameters_customized(self):
            """ Declare list of parameters

            Arg:
                -
            
            Returns:
                dec (string): The model instance with all parameter values and the package redeclarations.
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


    def export_model_without_added_parameters(self):

        print("Exporting FMU without added parameters to check if parameters in datasheets exist in the model")

        worDir = self._create_worDir()
        self._simulateDir_ = worDir
        
        shutil.copytree(os.path.abspath(self._packagePath), worDir,
                        ignore=shutil.ignore_patterns('*.svn', '*.git'))        

        
        
        mi = '"{mn}"'.format(mn=self.modelName)
        
        # Write the Modelica script
        runScriptName = os.path.join(worDir, "run.mos").replace("\\","/")
        with open(runScriptName, mode="w", encoding="utf-8") as fil:
            fil.write(self._get_dymola_commands_customized(
                working_directory=worDir,
                log_file="_simulator.log",
                model_instance=mi,
                packages = self.packages))
        # Run script
        print('Compiling...')
        self._runSimulation(runScriptName, self._simulator_.get('timeout'),
                                                                        worDir)

        # deleting files

        success = self.check_fmu_export()

      
        simulator_path = self.model_directory + "_simulator.log"
        if os.path.exists(simulator_path):
            os.remove(simulator_path)
        run_path = self._simulateDir_+"/run.mos"
        if os.path.exists(run_path):
            os.remove(run_path)      
    
        self.delete_unnecessary_files()

        return success

    def get_model_parameters(self):

        from fmpy import read_model_description
        

        fmu_path = self.model_directory + self.model_name + ".fmu"
        model_description = read_model_description(fmu_path)

        for variable in model_description.modelVariables:
            self.model_vars[variable.name] = variable.valueReference

        
        
        
    def check_if_parameters_exist(self, added_parameters):

        print("Checking...")
        
        
        for par in added_parameters:
            if par[0] not in self.model_vars:
                print(f'Make sure the parameter {par[0]} can be added to the model')
        if os.path.exists(self.model_directory + self.model_name +".fmu"):
            os.remove(self.model_directory + self.model_name +".fmu")
                


     

class OpenModelica(ModelicaSystem, DataManagement):

    def __init__(self, model_name, model_directory,datasheet_directory, datasheets, additional_parameters, output_directory ,packages):
        ModelicaSystem.__init__(self, model_directory, model_name)  #TODO Model path
        DataManagement.__init__(model_name, model_directory, datasheet_directory, datasheets, additional_parameters, output_directory)
        self.packages = packages
        self.modeling_environment = "openModelica"
    def fmu_export(self):
        self.sendExpression(f'translateModelFMU({self.model_name})')



