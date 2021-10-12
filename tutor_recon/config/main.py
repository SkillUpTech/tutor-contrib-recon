from pathlib import Path

from tutor_recon.config.override_sequence import OverrideSequence


def main_config(recon_root: Path) -> OverrideSequence:
    main_path = recon_root / "main.v.json"
    if main_path.exists():
        return OverrideSequence.load(main_path)
    return OverrideSequence.default(recon_root)


def scaffold_all(tutor_root: Path, recon_root: Path) -> None:
    main = main_config(recon_root)
    main.scaffold(tutor_root, recon_root)
    main.save(to=recon_root / "main.v.json")


def override_all(tutor_root: Path, recon_root: Path) -> None:
    main_config(recon_root).override(tutor_root, recon_root)
