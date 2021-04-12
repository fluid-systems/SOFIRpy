import matplotlib.pyplot as plt

def set_FST_template(project_directory):
    plt.style.use(f'{project_directory}\\Code\\''FST.mplstyle')

class Colors():
    def __init__(self):
        self.rgb_colors = {
            'blue' : (0, 0.31, 0.45),
            'red' : (0.91, 0.31, 0.24),
            'green' : (0.69, 0.8, 0.31),
            'black' : (0, 0, 0),
            'orange' : (0.93, 0.48, 0.20),
            'petrol' : (0.31, 0.71, 0.58),
            'grey' : (0.54, 0.54, 0.54),
            'yellow' : (0.99, 0.79, 0)
        }
    def get_rgb(self, color_name):
        if color_name in self.rgb_colors.keys():
            return self.rgb_colors[color_name]
        else:
            print(f"Error: Color '{color_name}' does not exist.\nAvailable colors are: {list(self.rgb_colors.keys())}")
    def get_color_names(self):
        return list(self.rgb_colors.keys())