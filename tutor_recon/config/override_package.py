"""Override type for packages of overrides."""

from pathlib import Path
from tutor_recon.util import vjson

from tutor_recon.config.override_sequence import OverrideSequence


class OverridePackage(OverrideSequence):
    type_id = "include"

    def __init__(self, url: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.url = url

    def scaffold(self, tutor_root: Path, recon_root: Path) -> None:
        """"""

    def to_object(self) -> dict:
        obj = super().to_object()
        obj.update(
            {
                "src": self.src,
                "dest": self.dest,
            }
        )
        return obj

    @classmethod
    def from_object(cls, obj: dict) -> "vjson.VJSONSerializableMixin":
        return cls(src=obj["src"], dest=obj["dest"])

    @classmethod
    def for_template(cls, template_relpath: Path) -> "TemplateOverride":
        """Construct a TemplateOverride for the given tutor template."""
        instance = cls(
            src=str(Path("templates") / template_relpath),
            dest=str(Path("env") / template_relpath),
        )
        return instance
