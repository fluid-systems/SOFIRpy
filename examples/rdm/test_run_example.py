from pathlib import Path


def test_run_example():
    hdf5_path = Path(__file__).parent / "run_example.hdf5"
    hdf5_path.unlink(missing_ok=True)
    import run_example

    hdf5_path.unlink()
