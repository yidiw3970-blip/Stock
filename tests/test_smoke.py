from pathlib import Path

import stock_alpha_lab
import stock_alpha_lab.config


def test_package_imports() -> None:
    assert stock_alpha_lab.__version__


def test_config_imports() -> None:
    settings = stock_alpha_lab.config.get_settings()

    assert settings.data_dir == Path("data")


def test_streamlit_app_exists() -> None:
    app_path = Path("src/stock_alpha_lab/ui/app.py")

    assert app_path.exists()
