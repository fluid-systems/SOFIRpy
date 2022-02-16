from pathlib import Path

class FmuExport:

    def __init__(self, model_path: Path, fmu_path: Path) -> None:
        
        self.model_path = model_path
        self.model_directory = model_path.parent
        self.model_name = model_path.stem
        self.fmu_path = fmu_path

    @property
    def model_path(self) -> Path:
        return self._model_path

    @model_path.setter
    def model_path(self, model_path: Path) -> None:

        if not isinstance(model_path, Path):
            raise TypeError(f"'model_path' is {type(model_path)}; expected Path")
        if model_path.exists():
            self._model_path = model_path
        else:    
            raise FileNotFoundError(model_path)

    @property
    def fmu_path(self) -> Path:
        return self._fmu_path

    @fmu_path.setter
    def fmu_path(self, fmu_path: Path) -> None:

        if not isinstance(fmu_path, Path):
            raise TypeError(f"'fmu_path' is {type(fmu_path)}; expected Path")

        if fmu_path.exists():
            while True:
                overwrite = input(
                    "The new fmu will have the same path as an existing fmu. Overwrite? [y/n]"
                )
                if overwrite == "y" or overwrite == "n":
                    if overwrite == "y":
                        break
                    elif overwrite == "n":
                        raise FmuAlreadyExistsError("Stopping execution.")
                    else:
                        print("Enter 'y' or 'n'")

        self._fmu_path = fmu_path

class FmuAlreadyExistsError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)