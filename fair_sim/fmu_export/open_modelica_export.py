from pathlib import Path
from export import FmuExport
from fair_sim.utils import delete_paths, move_files
from OMPython import ModelicaSystem

class OpenModelicaFmuExport(FmuExport):

    def __init__(self, model_path: Path) -> None:

        self.dump_directory = Path.cwd()
        fmu_path = self.dump_directory / f"{model_path.stem}.fmu"

        super().__init__(model_path, fmu_path)
        files_to_delete = [
            f"{self.model_name}.c",
            f"{self.model_name}.exe",
            f"{self.model_name}.libs",
            f"{self.model_name}.log",
            f"{self.model_name}.makefile",
            f"{self.model_name}.o",
            f"{self.model_name}_01exo.c",
            f"{self.model_name}_01exo.o",
            f"{self.model_name}_02nls.c",
            f"{self.model_name}_02nls.o",
            f"{self.model_name}_03lsy.c",
            f"{self.model_name}_03lsy.o",
            f"{self.model_name}_04set.c",
            f"{self.model_name}_04set.o",
            f"{self.model_name}_05evt.c",
            f"{self.model_name}_05evt.o",
            f"{self.model_name}_06inz.c",
            f"{self.model_name}_06inz.o",
            f"{self.model_name}_07dly.c",
            f"{self.model_name}_07dly.o",
            f"{self.model_name}_08bnd.c",
            f"{self.model_name}_08bnd.o",
            f"{self.model_name}_09alg.c",
            f"{self.model_name}_09alg.o",
            f"{self.model_name}_10asr.c",
            f"{self.model_name}_10asr.o",
            f"{self.model_name}_11mix.c",
            f"{self.model_name}_11mix.h",
            f"{self.model_name}_11mix.o",
            f"{self.model_name}_12jac.c",
            f"{self.model_name}_12jac.h",
            f"{self.model_name}_12jac.o",
            f"{self.model_name}_13opt.c",
            f"{self.model_name}_13opt.h",
            f"{self.model_name}_13opt.o",
            f"{self.model_name}_14lnz.c",
            f"{self.model_name}_14lnz.o",
            f"{self.model_name}_15syn.c",
            f"{self.model_name}_15syn.o",
            f"{self.model_name}_16dae.c",
            f"{self.model_name}_16dae.h",
            f"{self.model_name}_16dae.o",
            f"{self.model_name}_17inl.c",
            f"{self.model_name}_17inl.o",
            f"{self.model_name}_functions.c",
            f"{self.model_name}_functions.h",
            f"{self.model_name}_functions.o",
            f"{self.model_name}_includes.h",
            f"{self.model_name}_info.json",
            f"{self.model_name}_init.xml",
            f"{self.model_name}_literals.h",
            f"{self.model_name}_model.h",
            f"{self.model_name}_records.c",
            f"{self.model_name}_records.o",
            f"{self.model_name}_FMU.libs",
            f"{self.model_name}_FMU.log",
            f"{self.model_name}_FMU.makefile",
        ]

        self.files_to_move = [self.fmu_path]
        self.paths_to_delete = map(lambda file_name: self.dump_directory / file_name, files_to_delete)

    def export_fmu(self):
        om = ModelicaSystem(str(self.model_path).replace("\\", "//"), self.model_name)
        om.convertMo2Fmu()

def export_open_modelica_fmu(model_path: Path, output_directory: Path) -> bool:

    om_fmu_export = OpenModelicaFmuExport(model_path) 
    om_fmu_export.export_fmu()

    # delete unnecessary files
    delete_paths(om_fmu_export.paths_to_delete)

    if om_fmu_export.fmu_path.exists():
        print("The FMU Export was successful.")
        move_files(om_fmu_export.files_to_move, output_directory)
        return True
    else:
        print("The FMU Export was not successful")
        return False

if __name__ == "__main__":

    export_open_modelica_fmu(Path(r'C:\Users\Daniele\Desktop\export_test\test.mo'),
        Path(r'C:\Users\Daniele\Desktop\export_test_out'))
    
    
