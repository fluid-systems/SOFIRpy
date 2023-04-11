from pathlib import Path

import pytest

from sofirpy.fmu_export.dymola_fmu_export import export_dymola_model, DymolaFmuExport

@pytest.fixture
def dymola_fmu_exporter() -> DymolaFmuExport:
    model_path = Path(__file__).parent / "DC_Motor.mo"
    model_name = "DC_Motor"
    parameters = {"damper.d": 0.1, "damper.useHeatPort": False}
    with DymolaFmuExport(model_path, model_name, parameters=parameters, model_modifiers=None, packages=None) as dymola_fmu_exporter:
        yield dymola_fmu_exporter

def test_write_mos_script_default_fmu_export_settings(dymola_fmu_exporter: DymolaFmuExport) -> None:
    mos_script = dymola_fmu_exporter.write_mos_script(export_simulator_log=True)
    dymola_fmu_exporter.model_directory = dymola_fmu_exporter.model_directory.relative_to(Path(__file__).parent)
    dymola_fmu_exporter._model_path = dymola_fmu_exporter.model_path.relative_to(Path(__file__).parent)
    dymola_fmu_exporter.simulator_log_path = dymola_fmu_exporter.simulator_log_path.relative_to(dymola_fmu_exporter._dump_directory)
    dymola_fmu_exporter.error_log_path = dymola_fmu_exporter.error_log_path.relative_to(dymola_fmu_exporter._dump_directory)
    mos_script = dymola_fmu_exporter.write_mos_script()
    with open(Path(__file__).parent / "test_mos_script_default_settings.mos", mode="r", encoding="utf8") as f:
        assert f.read() == mos_script
