"""Override type for replacing templates in their entirety."""

from pathlib import Path
from tutor_recon.util import vjson
from tutor_recon.override.tutor import render_template, template_source

from tutor_recon.override.override import OverrideMixin


class TemplateOverride(OverrideMixin):
    type_id = "template"

    def __init__(self, src: vjson.VJSON_T, dest: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self._src = src
        self._effective_src = None
        self.dest = dest

    @property
    def src(self) -> str:
        if self._effective_src is None:
            return self._src
        return self._effective_src

    @property
    def claims(self) -> dict:
        return {(self.dest,): self}

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
        tutor_template_path = template_source(Path(self._src).relative_to("templates"))
        with open(tutor_template_path, "r") as f:
            original_template = f.read()
        recon_template_path.parent.mkdir(exist_ok=True, parents=True)
        with open(recon_template_path, "w") as f:
            f.write(original_template)

    def to_object(self) -> dict:
        obj = super().to_object()
        obj.update(
            {
                "src": self._src,
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

    def load_module_hook(
        self, module_root: Path, module_id: str, tutor_root: Path, recon_root: Path
    ) -> None:
        src_prefix = module_root.relative_to(recon_root)
        self._effective_src = src_prefix / self._src
