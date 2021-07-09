
import matplotlib.pyplot as plt


class Analyze():
    
    @staticmethod
    def plot_results(style_sheet_path,results ,y, x = "time", x_label = None, y_label = None, title = None, legend  = None ):

        plt.style.use(style_sheet_path) 
        
        fig, ax = plt.subplots()
        
        if title:
            ax.set_title(title)
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
        for var in y:
            ax.plot(results[x], results[var])
        if legend:
            plt.legend

        return ax

    