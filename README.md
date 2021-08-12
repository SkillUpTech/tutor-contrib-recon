# tutor-contrib-recon
[Work-In-Progress] Reconfigure your Tutor-managed OpenEdx environment for rapid development.

Installation
------------

```bash
pip install git+https://github.com/SkillUpTech/tutor-contrib-recon
```

Usage
-----

```bash
tutor plugins enable tutor_recon`
```

Development
-----------

### Setting Up

First, install poetry on your system using the [official installation instructions](https://python-poetry.org/docs/)
or with the following command:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -
```

Next, clone the recon git repository and enter the directory:

```bash
git clone https://github.com/SkillUpTech/tutor-contrib-recon.git
cd tutor-contrib-recon
```

Now, generate and activate a poetry-managed virtualenv:

```bash
poetry install
poetry shell
```

### Building the Project

Do this each time you make a change to your plugin that you would like to use.

```bash
poetry build
```

### Installing the Built Plugin

If your Tutor installation lives in a separate environment from the Poetry-managed environment created above,
navigate to that environment (for instance, if it is the system-wide environment, just type `exit` from within the poetry shell).
Then, use:

```bash
pip install [the location of your package]/tutor-contrib-recon/dist/tutor_recon-[your current version].whl
```

If recon and Tutor live in the same environment, simply using:

```bash
poetry install
```

from within the `tutor-contrib-recon` directory should suffice.

For further details on using Poetry, please refer to the [official docs](https://python-poetry.org/docs/).

### Adding the Plugin to Tutor

You should now see `tutor-contrib-recon` plugin listed when you type:

```bash
tutor plugins list
```

Use:

```bash
tutor plugins enable tutor_recon
```

to enable it.

# Copyright

Unless otherwise noted, all software in this repository is licensed under the AGPL. 
A copy of the AGPL can be found in the `LICENSE` file at the root of this repository.

```
tutor-contrib-recon: Reconfigure your Tutor-managed OpenEdx environment for rapid development.
    Copyright (C) 2021 Skill-Up Technologies

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
