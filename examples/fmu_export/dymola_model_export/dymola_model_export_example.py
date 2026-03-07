import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from sofirpy import export_dymola_model


def select_dymola_exe():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Dymola Executable",
        filetypes=[("Dymola Executable", "Dymola.exe")],
    )
    if not file_path:
        raise FileNotFoundError("No Dymola executable selected!")
    return Path(file_path)


dir_path = Path(__file__).parent
model_path = dir_path.parent / "DC_Motor.mo"
output_directory = dir_path
dymola_exe_path = select_dymola_exe()
model_name = "DC_Motor"
fmu_path = export_dymola_model(
    dymola_exe_path=dymola_exe_path,
    model_path=model_path,
    model_name=model_name,
    fmu_name="DC_Motor",
    output_directory=output_directory,
)
