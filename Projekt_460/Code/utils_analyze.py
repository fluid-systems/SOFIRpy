import numpy as np
import matplotlib.pyplot as plt
from FST_colors import Colors
import utils_Data as Data

def RMSE(recorded_values):
    """ Calculate the root mean squared error between user's reference values and system's outputs
    Args:
        recorded_values (dict): As returned by "return_record()" of "Recorder"

    Returns:
        rmse (dict):
            keys (string):      Names of valve agents
            values (float):     Corresponding root mean squared error
    """
    valve_agents = recorded_values['valve_agent_names']
    reference = recorded_values['w_series_user_valves']
    measured = recorded_values['y_series_valves']
    rmse = {}
    for i, agent in enumerate(valve_agents):
        rmse[agent] = np.sqrt(np.mean(np.square(reference[:,i] - measured[:,i])))
    return rmse

def plot_w_y_valves(recorded_values, project_owner, project_number, run_name,
                                                            project_directory):
    """Plots and saves user's reference values of valves and their corresponding system's outputs

    Args:
        recorded_values (dict):     As returned by "return_record()" of "Recorder"
        project_owner (string):     Name of project owner
        project_number (int):       Number of project
        run_name (string):          Name of run
        project_directory (string): Path to project's directory

    Returns:
        (dict):
            keys (string):      Name of plot
            values (float):     PID of plot
    
    """
    colors = Colors()
    valve_agents = recorded_values['valve_agent_names']
    time_series = recorded_values['time_series']
    w_user_series = recorded_values['w_series_user_valves']
    w_series = recorded_values['w_series_valves']
    y_series = recorded_values['y_series_valves']
    color_loop = colors.get_color_names()[:len(valve_agents)]
    fig = plt.figure('Measured- vs. reference- values of valves')
    ax = fig.add_subplot(111)
    for i, agent in enumerate(valve_agents):
        color = color_loop[i]
        agent_plot_name = agent.replace('_',',')
        # ax.plot(time_series, w_user_series[:,i], color= color, linestyle= ':',
        #             label= f'w_user_{agent}')
        ax.plot(time_series, w_series[:,i], color= colors.get_rgb(color), linestyle= '--',
                    label= f'w$_{{{agent_plot_name}}}$')
        ax.plot(time_series, y_series[:,i], color= colors.get_rgb(color), linestyle= '-',
                    label= f'y$_{{{agent_plot_name}}}$')
        # add text
        y_pos = 0.1 + 0.15*(len(valve_agents)-1) - 0.15*i
        ax.text(0.2, y_pos, f'w$_{{user,{{{agent_plot_name}}}}}$ = {w_user_series[0,i]} $m^3/h$')
    ax.set_xlabel(r'TIME in $s$')
    ax.set_ylabel(r'VOLUME FLOW in $m^3/h$')
    handles, labels = ax.get_legend_handles_labels()
    order = np.argsort(labels)
    ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order], loc= 'lower right')
    #save
    type_PID = 'plot_w_y_valves'
    run_PID = run_name.split("_")[1]
    PID = Data.create_PID(type_PID, project_owner, project_number, run_PID)
    plt.savefig(f'{project_directory}/Runs/{run_name}/{PID}.png')#, bbox_inches = "tight")
    return {'plot_w_y_valves': PID}

def plot_u(recorded_values, project_owner, project_number, run_name,
                                                            project_directory):
    """Plots and saves system's inputs

    Args:
        recorded_values (dict):     As returned by "return_record()" of "Recorder"
        project_owner (string):     Name of project owner
        project_number (int):       Number of project
        run_name (string):          Name of run
        project_directory (string): Path to project's directory

    Returns:
        (dict):
            keys (string):      Name of plot
            values (float):     PID of plot
    
    """
    colors = Colors()
    valve_agents = recorded_values['valve_agent_names']
    pump_agents = recorded_values['pump_agent_names']
    agents = valve_agents + pump_agents
    time_series = recorded_values['time_series']
    u_series_valves = recorded_values['u_series_valves']
    u_series_pumps = recorded_values['u_series_pumps']
    u_series = np.concatenate((u_series_valves, u_series_pumps), axis=1)
    color_loop = colors.get_color_names()[:len(agents)]
    fig = plt.figure('System input values')
    ax = fig.add_subplot(111)
    for i, agent in enumerate(agents):
        color = color_loop[i]
        agent_plot_name = agent.replace('_',',')
        ax.plot(time_series, u_series[:,i]*100, color= colors.get_rgb(color), linestyle= '-',
                    label= f'u$_{{{agent_plot_name}}}$')
    
    ax.set_xlabel(r'TIME in $s$')
    ax.set_ylabel(r'RELATIVE SYSTEM INPUT in %')
    handles, labels = ax.get_legend_handles_labels()
    order = np.argsort(labels)
    ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order])
    #save
    type_PID = 'plot_u'
    run_PID = run_name.split("_")[1]
    PID = Data.create_PID(type_PID, project_owner, project_number, run_PID)
    plt.savefig(f'{project_directory}/Runs/{run_name}/{PID}.png')#, bbox_inches = "tight")
    return {'plot_u': PID}

def plot_y_pumps(recorded_values, project_owner, project_number, run_name,
                                                            project_directory):
    """Plots and saves outputs of pumps

    Args:
        recorded_values (dict):     As returned by "return_record()" of "Recorder"
        project_owner (string):     Name of project owner
        project_number (int):       Number of project
        run_name (string):          Name of run
        project_directory (string): Path to project's directory

    Returns:
        (dict):
            keys (string):      Name of plot
            values (float):     PID of plot
    
    """
    colors = Colors()
    pump_agents = recorded_values['pump_agent_names']
    time_series = recorded_values['time_series']
    y_series = recorded_values['y_series_pumps']
    color_loop = colors.get_color_names()[:len(pump_agents)]
    fig = plt.figure('Measured values of pumps')
    ax = fig.add_subplot(111)
    for i, agent in enumerate(pump_agents):
        color = color_loop[i]
        agent_plot_name = agent.replace('_',',')
        ax.plot(time_series, y_series[:,i], color= colors.get_rgb(color), linestyle= '-',
                    label= f'y$_{{{agent_plot_name}}}$')
    ax.set_xlabel(r'TIME in $s$')
    ax.set_ylabel(r'PRESSURE in $Pa$')
    handles, labels = ax.get_legend_handles_labels()
    order = np.argsort(labels)
    ax.legend([handles[idx] for idx in order],[labels[idx] for idx in order])
    #save
    type_PID = 'plot_y_pumps'
    run_PID = run_name.split("_")[1]
    PID = Data.create_PID(type_PID, project_owner, project_number, run_PID)
    plt.savefig(f'{project_directory}/Runs/{run_name}/{PID}.png')#, bbox_inches = "tight")
    return {'plot_y_pumps': PID}