from buildingspy.simulate.Simulator import Simulator
import json
import os
import shutil
import utils_Data as Data
import sys



class Dymolapy(Simulator):
    """Class to export a Dymola model as an FMU

    Attributes:
        model_name (string):                    The Name of the Modelica model.
        simulator (string):                     The simulation engine. Currently, the only supported value is ``dymola``.
        model_directory (string):               The path where the Modelica model is stored.
        datasheet_directory (string):           The path where the data sheets are stored.
        datasheets (dictionary):                The name of the dymola component and the corresponding data sheet name. 
        additional_parameters (dictionary):     Optional parameters that can be added.
        output_directory (string):              The path where the output files will be stored.
        dymola_path (string):                   The path where the dymola.exe is located.
        packages (list):                        Path to the packages used.

    Methods:
        make_dymola_available():                Makes the dymola.exe available.
        add_parameters():                       Extracts the relevant data from the data sheet and sets them as parameters.
        add_additional_parameters():            Reads the additional_parameters dictionary and adds the dymola symbols and values to a variable.
        fmu_export():                           Exports a FMU of the model.
        moves_files():                          Moves output files of the fmu export to the output directory.
        copy_model ():                          Copies the model and the custom elements to the output directory.
        checkFMUexport():                       Checks whether the FMU has been exported to the output directory.
        rename_files():                         Renames the essential output files to their PID.               
        read_log_gile():                        Reads the simulator.log file.
        delete_files():                         Deletes unnecessary output files of the fmu export
        _get_dymola_commands_customized():      Returns a string that contains all the commands required to export the model as a FMU.
        _declare_parameters_customized():       Declare list of parameters.
        
        
    """

    def __init__(self,model_name, simulator, model_directory,
                    datasheet_directory, datasheets, additional_parameters,
                    output_directory, dymola_path, packages):
        super().__init__(model_name, simulator, output_directory)
        self.model_directory = model_directory
        self.datasheet_directory = datasheet_directory
        self.datasheets = datasheets
        self.additional_parameters = additional_parameters
        self.PIDs = []
        self.dymola_path = dymola_path
        self.packages = packages


    def make_dymola_available(self):
        """Makes the dymola.exe available.

        Args:
            -

        Returns:
            -
            
        """

        os.environ["PATH"] += os.pathsep + self.dymola_path


    def add_parameters(self):
        """Extracts the relevant data from the data sheet and sets them as parameters.

        Args:
            -

        Returns:
            -
            
        """

        # lists of data-sheets and their associated fluid-system components
        components = list(self.datasheets.keys())
        data_sheet_names = list(self.datasheets.values())

        for component, sheet_name in zip(components, data_sheet_names):
            with open(f'{self.datasheet_directory}/{sheet_name}.json') as read_file:
                data_sheet = json.load(read_file)
            # extract list with paramaters from the data_sheet 
            dymola_params = data_sheet['Dymola parameters']
            # lists with values and symbols are extracted from the dictionary
            values = [sub['value'] for sub in dymola_params]
            symbols = [sub['symbol'] for sub in dymola_params]
            # the parameters are added 
            for value, symbol in zip(values, symbols):
                if value != "":
                    comp_sym = f'{component}.{symbol}'
                    self.addParameters({comp_sym: value})   # function inherited from Simulator
        
        print('Parameters from datasheets added')
    

    def add_additional_parameters(self):
        """Reads the additional_parameters dictionary and adds the dymola symbols and values to a variable.
        
        Args:
            -

        Returns:
            -

        """

        # extracts a list with the name of components and a list with values from the dictionary added_parameters
        component_symbols = list(self.additional_parameters.keys())
        values = list(self.additional_parameters.values())

        # add the parameters
        for comp_sym, value in zip(component_symbols, values):
            self.addParameters({comp_sym: value})
        print('Additional parameters added')


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
               


    def move_files (self):
        """Moves output files of the fmu export to the output directory.

        Arg:
            -

        Returns:
            -
        """

        print('Moving files...')
        filLis = ['simulator.log', 'dslog.txt', self.modelName+'.fmu',
        'fmiModelIdentifier.h', 'dsmodel.c', 'buildlog.txt',
        'dsmodel_fmuconf.h', "~FMUOutput"]
        for fil in filLis:
            srcFil = os.path.normpath(self.model_directory + fil)
            newFil = os.path.normpath(self._outputDir_ + fil)
            if os.path.exists(srcFil):
                os.rename(srcFil, newFil)
        os.rename(self._simulateDir_+"/run.mos", self._outputDir_+"/run.mos")


    def checkFMUexport(self):
        """Checks whether the FMU has been exported to the output directory.
        
        Arg:
            -

        Returns:
            -
        """

        outputDirectory = self._outputDir_
        fmu = outputDirectory + self.modelName + '.fmu'
        if os.path.exists(fmu):
            print('The FMU Export was successful!')
            return True
        else:
            log = self.read_log_file()
            print('The FMU was not exported!\n'
             'Possible faults:\n'
             'Model specific error.\n'
             'No active Dymola License.\n'
             'Parameters are imported that do not exist.\n'
             'The model name or model path is not correct.\n'
             'The model name was changed in the explorer, but not in Dymola\n'
             'Packages needed in the model are not imported.\n'
             'Custom Dymola models are not stored in the model path.\n'
             'Log:\n'
             f'{log}\n')
            return False


    def copy_model(self):
        """Copies the model and the custom elements to the output directory.

        Arg:
            -

        Returns:
            -
            
        """
        
        model_files = os.listdir(self.model_directory)
        for model in model_files:
            model_copy_path = f'{self.model_directory}{model}'
            model_paste_path = f'{self._outputDir_}{model}'
            shutil.copyfile(model_copy_path, model_paste_path)
        print('Model copied.')

    def rename_files (self,project_owner, project_number, run_name):
        """Renames the essential output files to their PID.
                
        Arg:
            project_owner (string):     Abbreviation for owner type    
            project_number (int):       Project number from FST Excel-sheet     
            run_name (string):          Name of the simulation run.        

        Returns:
            -
            
        """

        files = [self.modelName + '.mo', self.modelName + '.fmu', 'run.mos']
        type_PID = ["model", "fmu", "runscript"]
        
        for i, fil in enumerate(files):
            ending = '.' + fil.split('.')[1]
            run_PID = run_name.split("_")[1]
            PID = Data.create_PID(type_PID[i], project_owner, project_number, run_PID)
            oldfile = self._outputDir_ + fil
            newfile = self._outputDir_ + PID + ending
            if os.path.exists(oldfile):
                os.rename(oldfile, newfile)
            
            self.PIDs.append(PID)
        print('Files renamed.')
        
        
    def read_log_file(self):
        """Reads the simulator.log file.
        
        Arg:
            -

        Returns:
            simulator_log(string):  The text of the simulator.log file.

        """
        
        simulator_log_path = self._outputDir_ + 'simulator.log'

        with open(simulator_log_path, "r") as log_file:
            simulator_log = log_file.read()
        return simulator_log


    def delete_files (self):
        """Deletes unnecessary output files of the fmu export.

        Arg:
            -

        Returns:
            -
        """

        delete = ['simulator.log', 'dslog.txt',
        'fmiModelIdentifier.h', 'dsmodel.c', 'buildlog.txt',
        'dsmodel_fmuconf.h', "~FMUOutput"]

        for de in delete:
            srcFil = os.path.normpath(self._outputDir_ + de)
            if os.path.exists(srcFil):
                if de == "~FMUOutput":
                    shutil.rmtree(srcFil, ignore_errors=True)
                else:
                    os.remove(srcFil)
        print('Unnecessary files deleted.')
                

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