"""Override type for replacing templates in their entirety."""

from pathlib import Path
from tutor_recon.util import vjson
from tutor_recon.config.tutor import render_template, template_source

from tutor_recon.config.override import OverrideMixin


class TemplateOverride(OverrideMixin):
    type_id = "template"

    def __init__(self, src: vjson.VJSON_T, dest: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Render the template to the tutor environment."""
        source_path = recon_root / self.src
        dest = tutor_root / self.dest
        render_template(source_path, dest, tutor_root)

    def scaffold(self, tutor_root: Path, recon_root: Path) -> None:
        """Create the template override, initially identical to the tutor version.

        Does nothing if the template already exists.
        """
        recon_template_path = recon_root / self.src
        if recon_template_path.exists():
            return
        tutor_template_path = template_source(Path(self.src).relative_to("templates"))
        with open(tutor_template_path, "r") as f:
            original_template = f.read()
        recon_template_path.parent.mkdir(exist_ok=True, parents=True)
        with open(recon_template_path, "w") as f:
            f.write(original_template)

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
    def for_template(cls, template_relpath: Path) -> "TemplateOverride":
        """Construct a TemplateOverride for the given tutor template."""
        instance = cls(
            src=str(Path("templates") / template_relpath),
            dest=str(Path("env") / template_relpath),
        )
        return instance
