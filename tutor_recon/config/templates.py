"""Override type for replacing templates in their entirety."""

from pathlib import Path

from tutor_recon.config.override import OverrideMixin


class TemplateOverride(OverrideMixin):
    label = 'template'

    def override(self, tutor_root: Path, recon_root: Path) -> None:
        """Render the template to the tutor environment."""
        # TODO use tutor's rendering functionality to perform the override.

    def save(self, recon_root: Path) -> None:
        """Create the template override, initially identical to the tutor version.
        
        Does nothing if the template already exists.
        """
        recon_template_path = recon_root / self.src
        if recon_template_path.exists():
            return
        tutor_template_path = None  # TODO get path to template files from tutor module.
        with open(tutor_template_path, "r") as f:
            original_template = f.read()
        with open(recon_template_path, "w") as f:
            f.write(original_template)
