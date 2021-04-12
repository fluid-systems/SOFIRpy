import numpy as np
import pandas as pd
################################################################################
#                               Agent Definition                               #
################################################################################
class Agent():
    """Super Class for all types of agents

    Remark: 'input' and 'output' refer to the fluid-system-input / -output

    Attributes:
        _name (string):         Name of the agent - should be same as variable name
        u_name (string):        Name of the FMU input the agent can control
        u_refnum (int):         FMU-internal reference number. Caution! This 
                                attribute has to be set externally via 
                                "connect_MAS_to_FMU" as defined in "utils_MAS"                 
        y_name (string):        Name of the FMU input the agent can control
        y_refnum (int):         FMU-internal reference number.  Caution! This 
                                attribute has to be set externally via 
                                "connect_MAS_to_FMU" as defined in "utils_MAS"                   
        problems (dict):        Dictionary of the problems of all agents
        problem_series (list):  Time series of current and past problem of the agent (problem ~ w-y)

    Methods:
        Get_system_output():    Read system outputs from fmu
        Send_problem():         Returns problem of Agent
        Receive_problems():     Receive problems of other agents
        Call_for_help():        Returns Agent's help call
        Send_proposal():        Respond to incoming help calls by making a proposal.
        Send_command():         Return commands to the agents who offered help.
        Send_u():               Returns system input and send it to fmu

    """
    def __init__(self, name, u_name, y_name, memory_time, agent_step_size,
                                                                    u_bounds):
        self._name = name
        self.u_name = u_name
        self.y_name = y_name
        self.problems = {}
        self.u_bounds = u_bounds
        self.memory_time = memory_time
        self.agent_step_size = agent_step_size
        if (int(memory_time/agent_step_size)) > 0:
            self.problem_series = np.zeros((int(memory_time/agent_step_size)))
        else:
            self.problem_series = np.zeros((1))
        print(f'Agent "{name}" created')

    def Get_system_output(self, fmu):
        """ Read system outputs from fmu.
        
        Args:
            fmu (fmu):  Fluid model

        Returns:
            -
        """
        self.y_old = self.y
        self.y = fmu.getReal([self.y_refnum])[0]



    def Send_problem(self):
        """ Returns problem of Agent

        Args:
            -
        
        Returns:
            problem (tuple):    Problem consisting of the sending agent's name and problem
        """
        problem = self._name, self.Calculate_problem()
        return problem


    def Receive_problem(self, problem):
        """ Receive problem of other agent.
        
        Args:
            problem (tuple):    Problem consisting of the sending agent's name and problem
        
        Returns:
            -
        """
        self.problems[problem[0]] = problem[1]
    
    
    def Call_for_help(self):
        """ Returns Agent's help call

        Args:
            -
        
        Returns:
            help_call (tuple):  Help-call consisting of the calling agent's name and help-call-value
        """
        help_call = self._name, self.Calculate_help_call()
        return help_call


    def Send_proposal(self, help_calls):
        """ Respond to incoming help calls by making a proposal.
        
        Args:
            help_calls (dict):
                key (string):   Name of the calling agent
                value (float):  Value of the help call
        Returns:
            proposal (tuple):
                [0] (string):   Name of agent that makes a proposal
                [1] (string):   Name of agent that proposal is for
                [2] (float):    Value of the proposal
        """
        proposal = self._name, self.Calculate_proposal(help_calls)[0], self.Calculate_proposal(help_calls)[1]
        return proposal


    def Send_command(self, proposals):
        """ Return commands to the agents who offered help.
        
        Args:
            proposals (DataFrame):  Pandas DataFrame of proposals
                column1: proposal_from
                column2: proposal_to
                column3: value
        
        Returns:
            relative_proposals (dict):
                    key (string):       Name of agent that should execute the command
                    value (float):      Value of the command 
        """
        command = self.Calculate_command(proposals)
        return command

    def Send_u(self, fmu):
        """ Returns system input and send it to fmu

        Args:
            fmu (fmu):  Fluid model

        Returns:
            u (float):  Control output
        """

        u = self.Calculate_u()
        self.u = u
        fmu.setReal([self.u_refnum], [u])
        return u


################################################################################
#                             Valve Agent Definition                           #
################################################################################
class Valve_Agent(Agent):
    """Sub Class of Agent for valve agents

    Attributes:
        u (float):                  System input
        w (float):                  Reference value
        w_user (float):             Reference value as wished by user
        y (float):                  System output
        y_old (float):              System output of previous step
        min_state (float):          Min value for w and y
        max_state (float):          Max value for w and y
        k_p (float):                Proportional gain of controller
        k_i (float):                Integral gain of controller
        step_size (float):          Step size of fmu (=sample step of control)
        controller (PI_Control):    Local PI-Controller
        threshold (float):          Deviations smaller than this value are not classified as problems
        old_help_value (float): Amount of the proposal value at last step

    Methods:
        Calculate_u():              Calculates the system input
        Calculate_problem():        Calculate problem series and problem
        Calculate_help_call():      Calculates value of help call
        Calculate_proposal():       Calculates the proposal to make
        Calculate_command():        Calculates the command to make
        Execute_command():          Executes incoming commands

    """

    def __init__(self, name, u_name, y_name, memory_time, 
                    agent_step_size, u_bounds, step_size, 
                    k_p, k_i, threshold, w_user,
                    w_bounds):
        super().__init__(name, u_name, y_name, memory_time, agent_step_size,
                                                                    u_bounds)
        self.u = u_bounds[0]
        self.w = w_user
        self.w_user = w_user
        self.y = w_bounds[0]
        self.y_old = self.y
        self.min_state = w_bounds[0]
        self.max_state = w_bounds[1]
        self.k_p = k_p
        self.k_i = k_i
        self.step_size = step_size
        self.controller = PI_Control(k_p, k_i, self.u_bounds, step_size)
        self.threshold = threshold
        self.old_help_value = 0


    def Calculate_u(self):
        """ Calculates the system input

        Calculation is done by controller
        Args:
            -
        
        Returns:
            u (float):  System input value
        """
        u = self.controller.calculate_u(self.w, self.y)
        return u


    def Calculate_problem(self):
        """ Calculate problem series and problem.

        Calculate next element of problem_series
        Store problem_series
        Calculate problem from problem_series

        Args:
            -

        Returns:
            problem_value (float):    Average of problem_series (#NOTE: can be adapted later)
        """
    
        self.problem_series = np.roll(self.problem_series, 1)
        if (self.min_state <= self.w_user <= self.max_state) or (self.w_user == 0):
            if self.w_user:
                self.problem_series[0] = (self.w_user - self.y)/self.w_user
            else:
                self.problem_series[0] = 0
        else:
            print("Error: Desired value is not within bounds")
        problem_value = np.mean(self.problem_series)
        return problem_value
        
    
    def Calculate_help_call(self):
        """ Calculates value of help call
        
        Identify if own problem is big enough and if so, send a help call.
        If own problem is not the biggest, or smaller than the threshold:
        Own problem is 0

        Args:
            -
        
        Returns:
            own_problem (float):    Own problem
        """
        max_problem = max(self.problems.values())
        own_problem = self.problems[self._name]
        if (own_problem != max_problem) or (own_problem <= self.threshold):
            own_problem = 0
        return own_problem


    def Calculate_proposal(self, help_calls):
        """ Calculates the proposal to make

        Args:
            help_calls (dict):
                key (string):           Name of the calling agent
                value (float):          Value of the help call

        Returns:
            help_call_name (string):    Name of the agent that proposal is for
            proposal_value (float):     Value of the proposal
            old_help_value (float):     Value of the help given by agent previous to current step
        """

        help_call_name = max(help_calls, key=help_calls.get)
        help_call_value = help_calls[help_call_name]
        if (help_call_name != self._name) and (self.y > self.min_state) and (help_call_value > 0):
            delta_help_proposal = (help_call_value - self.problems[self._name]) / 2
            proposal_value = delta_help_proposal
        else:                                                       
            proposal_value = - 0.5 * self.old_help_value  #NOTE: could be other value aswell
        return help_call_name, (proposal_value, self.old_help_value, self.w_user)   # proposal value := "how much more am I offering to help"
        
    
    def Calculate_command(self, proposals):
        """ Calculates the command to make

        Compare the proposals and send a command that is
            - proportional to the proposal the agent made
            - proportional to the portion the agent made to the sum of all proposals

        Args:
            proposals (DataFrame):  Pandas DataFrame of proposals
                column1: proposal_from
                column2: proposal_to
                column3: value

        Returns:
            commands (DataFrame):   Pandas DataFrame of commands
                column1: command_from
                column2: command_to
                column3: command_value
        """

        related_proposals = proposals[proposals['proposal_to'] == self._name]
        if not related_proposals.empty:
            delta_help_proposals = np.array([value[0] for value in related_proposals['value']], dtype= 'float')
            old_help_values = np.array([value[1] for value in related_proposals['value']], dtype= 'float')
            w_user_values = np.array([value[2] for value in related_proposals['value']], dtype= 'float')
            relative_delta_helps = delta_help_proposals * w_user_values / (w_user_values.sum() - self.w_user)
            new_help_values = old_help_values + relative_delta_helps
            commands_values = np.tanh(new_help_values)
            commands = pd.DataFrame({
                                'command_from': self._name,
                                'command_to': related_proposals['proposal_from'].tolist(),
                                'command_value': commands_values})
        else:
            commands = None
        return commands
        
    def Execute_command(self, commands):
        """ Executes incoming commands

        Reduce the reference value by subtracting the command
        The agent tries to help another agent to the cost of not fully
        satisfying the own user

        Args:
            commands (DataFrame):       Pandas DataFrame of commands
                    column1: command_from
                    column2: command_to
                    column3: command_value

        Returns:
            -
        """
        related_commands = commands[commands['command_to'] == self._name]
        command = related_commands['command_value'].sum()
        self.old_help_value = command
        self.w = (1 - command) * self.w_user
            


################################################################################
#                              Pump Agent Definition                           #
################################################################################
class Pump_Agent(Agent):
    """Sub Class of Agent for pump agents

    Attributes:
        u_init (float): Initial value for system input
        u (float):      System input

    Methods:
        Calculate_u():              Calculates the system input
        Calculate_problem():        Calculate problem series and problem
        Calculate_help_call():      Calculates value of help call
        Calculate_proposal():       Calculates the proposal to make
        Calculate_command():        Calculates the command to make
        Execute_command():          Executes incoming commands
          
    """
    def __init__(self, name, u_name, y_name, memory_time, agent_step_size,
                                                            u_bounds, u_init):
        super().__init__(name, u_name, y_name, memory_time, agent_step_size,
                                                                    u_bounds)
        self.u_init = u_init
        if u_bounds[0] <= u_init <= u_bounds[1]:
            self.u = u_init
        elif u_init < u_bounds[0]:
            self.u = u_bounds[0]
            print(f'Chosen u-value was too low, reset to {u_bounds[0]}')
        else:
            self.u = u_bounds[1]
            print(f'Chosen u-value was too high, reset to {u_bounds[1]}')
        self.y = 0
        self.y_old = self.y


    def Calculate_u(self):
        """ Calculates the system input

        Because the pump currently runs stationary, it just returns the
        stored system input
        
        Args:
            -
        
        Returns:
            u (float):  System input value
        """

        u = self.u
        return u


    def Calculate_problem(self):
        """ Calculates problem series and problem

        Because the pump currently runs stationary, the problem is always zero
        Store problem_series
        Calculate problem from problem_series

        Args:
            -

        Returns:
            problem_value (float):    Average of problem_series (#NOTE: can be adapted later)
        """
    
        self.problem_series = np.roll(self.problem_series, 1)
        self.problem_series[0] = 0
        problem_value = np.mean(self.problem_series)
        return problem_value
        
    
    def Calculate_help_call(self):
        """ Calculates value of help call

        Because the pump currently runs stationary, the help call value 
        (own problem) is always zero

        Args:
            -
        
        Returns:
            own_problem (float):    Own problem
        """
        own_problem = 0
        return own_problem

 

    def Calculate_proposal(self, help_calls):
        """ Calculates the proposal to make

        Because the pump currently runs stationary, the proposal value 
        is always zero

        Args:
            help_calls (dict):
                key (string):           Name of the calling agent
                value (float):          Value of the help call

        Returns:
            help_call_name (string):    Name of the agent that proposal is for
            proposal_value (float):     Value of the proposal
        """

        help_call_name = max(help_calls, key=help_calls.get)
        proposal_value = (0, 0, 0)
        return help_call_name, proposal_value
        
    
    def Calculate_command(self, proposals):
        """ Calculates the command to make

        Because the pump currently runs stationary, there are no commands 
        to calculate

        
        Args:
            proposals (DataFrame):  Pandas DataFrame of proposals
                column1: proposal_from
                column2: proposal_to
                column3: value

        Returns:
            commands (DataFrame):   Pandas DataFrame of commands
                column1: command_from
                column2: command_to
                column3: command_value
        """

        commands = None
        return commands
        
    def Execute_command(self, commands):
        """ Executes incoming commands

        Because the pump currently runs stationary, there are no commands 
        to execute

        Args:
            commands (DataFrame):       Pandas DataFrame of commands
                    column1: command_from
                    column2: command_to
                    column3: command_value

        Returns:
            -
        """
        pass



################################################################################
#                               Control Definition                             #
################################################################################

class PI_Control:
    """Discrete PI controller
    
    Tustin-Transformation of the continuous PI controller,
    represented by laplace transfer function G(s) = k_p + k_i/s

    Attributes:
        k_p (float):            Proportional gain of error value
        k_i (float):            Integral gain of error value
        u_max (float):          Maximal system input
        u_old (float):          System input of the last call of "calculate_u"
        e_old (float):          Error value of the last call of "calculate_u"
        step_size (float):      Sample step size in seconds

    Methods:
        calculate_u (float):    Calculates the system input u
    """
    def __init__(self, k_p, k_i, u_bounds, step_size):
        self.k_p = k_p
        self.k_i = k_i
        self.u_min = u_bounds[0]
        self.u_max = u_bounds[1]
        self.u_old = 0
        self.e_old = 0
        self.step_size = step_size
        
    def calculate_u(self, w, y):
        """Calculates system input u
        
        The corresponding system is assumed to have an input range of 
        [u_min, u_max] and a positive output range.

        Args:
            w (float): Reference value
            y (float): System output

        Returns:
            u (float): System input
        """

        if y < -1e-9:   # System output is negative (e.g. the tolerance <-1e-9)
            u = 1e-9
            self.u_old = 0
            self.e_old = 0
        else:   # System output is positive
            e = w - y                                       # Control
            g_0 = self.k_p + (self.step_size/2) * self.k_i  #
            g_1 = (self.step_size/2) * self.k_i - self.k_p  #
            u = g_0*e + g_1*self.e_old + self.u_old         #
            if u > self.u_max:          # Anti-Windup
                u = self.u_max          #
            elif u < self.u_min:        #
                u = self.u_min          #
            self.u_old = u      # Save system input and error
            self.e_old = e      #
        return u
