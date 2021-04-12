import numpy as np
import pandas as pd

def connect_MAS_to_FMU(agents, model_vars):
    """ Connects the Agents to the FMU by setting saving the FMU's reference numbers
    to the corresponding Agent's attributes

    This function has to be called after initializing the agents and the FMU!

    Args:
        agents (list):              List of agents (Agent)
        model_vars (dict):
            key (string):   Name of the FMU's port
            value (float):  Corresponding reference numbers

    Returns:
        -
    """
    for agent in agents:
        agent.u_refnum = model_vars[agent.u_name]
        agent.y_refnum = model_vars[agent.y_name]
    print('MAS connected to FMU')

################################################################################
#                                 Communication                                #
################################################################################
def agent_routine(agents,fmu, time_step, agent_step_size, step_size):
    """ Runs one action cycle of the multi agent system.
    Args:
        agents (list):              List of agents (Agent)
        fmu (FMU):                  fmu model of the physical system under control of the
                                    MAS
        time_step (float):          current simulation time step
        agent_step_size (float):    Step size between two agent cycles
        step_size (float):          Step size of the simulation. Must be a
                                    devider of agent_step_size

    
    Returns:
        -
    """
    # Agents measure the states of their components
    for agent in agents:
        agent.Get_system_output(fmu)
    # Agents communicate
    conversation(agents, time_step, agent_step_size, step_size)
    # Agents send their control-output to their components
    for agent in agents:
        agent.Send_u(fmu)


def conversation(agents, time_step, agent_step_size, step_size):
    """ Exchanges the relevant data among agents.
    Args:
        agents (list):              List of agents (Agent)
        time_step (float):          current simulation time step
        agent_step_size (float):    Step size between two agent cycles
        step_size (float):          Step size of the simulation. Must be a
                                    devider of agent_step_size

    
    Returns:
        -
    """
    if ((time_step % int(agent_step_size/step_size)) == 0) and (time_step > 1): # agents only intervent at every nth time step
        if not check_if_settled(agents, step_size):
            return
        Exchange_problems(agents)
        help_calls = Collect_help_calls(agents)
        proposals = Collect_proposals(help_calls, agents)
        commands = Collect_commands(proposals, agents)
        Execute_commands(commands, agents)

def check_if_settled(agents, step_size):
    """ Checks if system reached a stationary operating point.
    Args:
        agents (list):              List of agents (Agent)
        step_size (float):          Step size of the simulation. Must be a
                                    devider of agent_step_size

    
    Returns:
        True / False (boolean)      True if the system reached a stationary o.p.
    """
    for agent in agents:
        relative_change = (agent.y - agent.y_old) / agent.y
        rel_change_per_sec = relative_change / step_size
        if rel_change_per_sec >= 0.05:  #NOTE: Could choose different threshold
            print('System not settled - Agents not interfering')
            return False
        return True
            

def Exchange_problems(agents):
    """ Exchanges all agent problems among all agents

    The problems of the agents are calculated in their methods
    "Send_problem()" and saved in each agent by their method 
    "Recieve_problem(problems)".

    Args:
        agents (list):  List of agents (Agent)

    Returns:
        -   
    """
    
    for sending_agent in agents:
        problem = sending_agent.Send_problem()
        for receiving_agent in agents:
            receiving_agent.Receive_problem(problem)

def Collect_help_calls(agents):
    """ Collect the help calls of all agents.

    Args:
        agents (list):      List of agents (Agent)

    Returns:
        help_calls (dict):
                key (string):   Name of the calling agent
                value (float):  Value of the help call
    """
    help_calls = {}
    for agent in agents:
        help_call = agent.Call_for_help()
        help_calls[help_call[0]] = help_call[1]
    return help_calls

def Collect_proposals(help_calls, agents):
    """ Agents propose solution to help_calls

    Args:
        help_calls (dict):
                key (string):   Name of the calling agent
                value (float):  Value of the help-call

        agents (list):          List of agents (Agent)

    Returns:
        proposals (DataFrame):  Pandas DataFrame of proposals
                column1: proposal_from
                column2: proposal_to
                column3: value
    """

    column_names = ['proposal_from', 'proposal_to', 'value']
    proposals = pd.DataFrame(None, index= range(len(agents)),
                                                        columns= column_names)
    for i, agent in enumerate(agents):
        proposals.iloc[i] = agent.Send_proposal(help_calls)
    return proposals

def Collect_commands(proposals, agents):
    """ Collect the commands of all agents.

    Args:
        proposals (DataFrame):  Pandas DataFrame of proposals
                column1: proposal_from
                column2: proposal_to
                column3: value
        agents (list):          List of agents (Agent)

    Returns:
        all_commands (DataFrame):   Pandas DataFrame of commands
                column1: command_from
                column2: command_to
                column3: command_value
    """
    all_commands = None
    for agent in agents:
        commands = agent.Send_command(proposals)
        if commands is not None:
            if all_commands is None:
                all_commands = commands
            else:
                all_commands.append(commands, ignore_index=True)
    return all_commands

def Execute_commands(commands, agents):
    """ Execution of the responds to proposals of agents

    The execution is defined in the agents method "Execute_proposal(relative_proposal)".
    Each agent is sent their specific respond (i.e. relative_proposal)

    Args:
        commands (DataFrame):       Pandas DataFrame of commands
                column1: command_from
                column2: command_to
                column3: command_value
        agents (list):              List of agents (Agent)
    
    Returns:
        -
    """
    if commands is not None:
        for agent in agents:
            agent.Execute_command(commands)

################################## Data Storing ################################
class Recorder():
    """ Class to centrally store simulation data during simulation

    Attributes:
        time_series (numpy array):          Simulation time of length [1 x n]
        u_series_valves (numpy array):      System input series of v valves [n x v]
        u_series_pumps (numpy array):       System input series of p pumps [n x p]
        w_series_user_valves (numpy array): User reference series of v valves [n x v]
        w_series_valves (numpy array):      Agents adapted reference series of v valves [n x v]
        y_series_valves (numpy array):      System output series of v valves [n x v]
        y_series_pumps (numpy array):       System output series of p pumps [n x p]
        valve_agents (list):                List of Agent, corresponding to valves agents
        pump_agents (list):                 List of Agent, corresponding to valves agents

    Methods:
        record_agents():                    Saves agents values at a certain time
        record_valve_agents():              Saves valve agents values at a certain time
        record_pump_agents():               Saves pump agents values at a certain time
        return_record():                    Returns all recorded values
    """
    def __init__(self, valve_agents, pump_agents, stop_time, step_size):
        self.time_series = np.arange(0, stop_time + step_size, step_size)
        self.u_series_valves = np.zeros((len(self.time_series), len(valve_agents)))
        self.u_series_pumps = np.zeros((len(self.time_series), len(pump_agents)))
        self.w_series_user_valves = np.zeros((len(self.time_series), len(valve_agents)))
        self.w_series_valves = np.zeros((len(self.time_series), len(valve_agents)))
        self.y_series_valves = np.zeros((len(self.time_series), len(valve_agents)))
        self.y_series_pumps = np.zeros((len(self.time_series), len(pump_agents)))
        self.valve_agents = valve_agents
        self.pump_agents = pump_agents
    
    def record_agents(self, time_step):
        """ Saves agents values at a certain time

        Args:
            time_step (float):  Time on which the samples are taken

        Returns:
            -
        """
        self.record_valve_agents(time_step)
        self.record_pump_agents(time_step)

    def record_valve_agents(self, time_step):
        """ Saves valve agents values at a certain time

        Args:
            time_step (float):  Time on which the samples are taken

        Returns:
            -
        """
        for i, agent in enumerate(self.valve_agents):
            self.u_series_valves[time_step, i] = agent.u
            self.w_series_user_valves[time_step, i] = agent.w_user
            self.w_series_valves[time_step, i] = agent.w
            self.y_series_valves[time_step, i] = agent.y
    
    def record_pump_agents(self, time_step):
        """ Saves pump agents values at a certain time

        Args:
            time_step (float):  Time on which the samples are taken

        Returns:
            -
        """
        for i, agent in enumerate(self.pump_agents):
            self.u_series_pumps[time_step, i] = agent.u
            self.y_series_pumps[time_step, i] = agent.y

    def return_record(self):
        """ Returns all recorded values

        Args:
            -

        Returns:
            record (dict):
                keys (string):  Names of the Recorder's attributes
                values ():      Corresponding values
        """
        record = {
            'valve_agent_names': [getattr(agent, '_name') for agent in self.valve_agents],
            'pump_agent_names': [getattr(agent, '_name') for agent in self.pump_agents],
            'time_series': self.time_series,
            'u_series_valves': self.u_series_valves,
            'u_series_pumps': self.u_series_pumps,
            'w_series_user_valves': self.w_series_user_valves,
            'w_series_valves': self.w_series_valves,
            'y_series_valves': self.y_series_valves,
            'y_series_pumps': self.y_series_pumps
        }
        return record