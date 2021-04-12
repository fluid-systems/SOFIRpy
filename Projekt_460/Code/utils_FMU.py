from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave


def init_fmu(project_directory, run_name, PIDs):
    """ Load and initialize the fluid-model as fmu.
    
    Args:
        #TODO

    Returns:
        fmu (fmu): The initialized fluid model as fmu-instance
        model_vars (dict): dict of all model-variables with
            - key = variable-name
            - value = FMU-internal reference-number
        unzipdir: path to the unziped fmu
    """
    
    # get the file with fmu type from PIDs
    model_name = [PID for PID in PIDs if PID.split('_')[0] == 'fmu'][0]
    # read the model description
    model_description = read_model_description(f'{project_directory}/Runs/{run_name}/{model_name}.fmu')
    # collect the value references
    model_vars = {}
    for variable in model_description.modelVariables:
        model_vars[variable.name] = variable.valueReference
    # extract the FMU
    unzipdir = extract(f'{project_directory}/Runs/{run_name}/{model_name}.fmu')
    fmu = FMU2Slave(guid=model_description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=model_description.coSimulation.modelIdentifier,
                    instanceName='instance1')
                    # TODO: check if coSimulation works for modelExchange too
    # initialize
    fmu.instantiate()
    fmu.setupExperiment(startTime=0)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()
    print('FMU initialized.')
    return fmu, model_vars