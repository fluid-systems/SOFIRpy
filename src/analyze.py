
import matplotlib.pyplot as plt

def plot_results(y, x, x_label = None, y_label = None, title = None, 
        legend  = None, style_sheet_path = None, **plt_kwargs): 

    if style_sheet_path:
        plt.style.use(style_sheet_path) 
    
    fig, ax = plt.subplots(**plt_kwargs)
    
    if title:
        ax.set_title(title)
    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    for _y in y:
        ax.plot(x, _y)
    if legend: 
        ax.legend(legend)

    return ax

    