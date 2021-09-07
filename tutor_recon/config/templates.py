"""Override type for replacing templates in their entirety."""

from pathlib import Path
from tutor_recon.util import vjson
from tutor_recon.config.tutor import render_template, template_source

from tutor_recon.config.override import OverrideMixin


class TemplateOverride(OverrideMixin):
    type_id = "template"

    def __init__(self, src: vjson.VJSON_T, dest: Path, **kwargs) -> None:
        super().__init__(src, dest, **kwargs)

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Render the template to the tutor environment."""
        source_path = recon_root / self.src
        dest_dir = tutor_root / "templates"
        render_template(source_path, dest_dir, tutor_root)

    def scaffold(self, recon_root: Path) -> None:
        """Create the template override, initially identical to the tutor version.

        Does nothing if the template already exists.
        """
        recon_template_path = recon_root / self.src
        if recon_template_path.exists():
            return
        tutor_template_path = template_source(self.src)
        with open(tutor_template_path, "r") as f:
            original_template = f.read()
        with open(recon_template_path, "w") as f:
            f.write(original_template)

    @classmethod
    def for_template(cls, template_relpath: Path, recon_root: Path) -> "TemplateOverride":
        """Construct and scaffold (if necessary) a TemplateOverride for the given tutor template."""
        instance = cls(src=str("templates" / template_relpath), dest=str(template_relpath))
        instance.scaffold(recon_root)
        return instance
