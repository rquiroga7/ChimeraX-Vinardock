ChimeraX-Vinardock
==================

An original `UCSF ChimeraX <https://www.rbvi.ucsf.edu/chimerax/>`_ bundle with two
related features for docking with `Vinardock <https://github.com/>`_ / DOCK:

* **PDBT / PDBQT reader** — opens Vinardock and DOCK ``.pdbt`` and AutoDock
  ``.pdbqt`` files.  It regroups each residue's atoms so that hydrogens appended
  at the end of the file are bonded to the correct heavy atoms, and it reads
  per-pose metadata (Vinardock ``REMARK 980`` energy / ``REMARK 990`` RMSD;
  AutoDock Vina ``REMARK VINA RESULT``) into the ViewDock table.
* **Docking Box tool** — draws and edits a docking search box: type the center
  and size, autobox around a chosen ligand (default padding 10 Å), and move /
  resize the box with the mouse (left-drag moves; right-drag a side resizes it,
  keeping the opposite side fixed).

This repository contains only the bundle.  It does **not** include ChimeraX.

Requirements
------------

* UCSF ChimeraX — install the official **prebuilt** application from
  https://www.rbvi.ucsf.edu/chimerax/download.html .  There is no need to build
  ChimeraX from source.  A current 1.x release is recommended.

Installation
------------

Install the bundle with ChimeraX's own installer, ``toolshed``.  Do **not** use
plain ``pip``: this bundle depends on other ChimeraX bundles (such as
``ChimeraX-OpenCommand``) which are not Python packages on PyPI.

From a prebuilt wheel::

    chimerax --nogui --exit --cmd "toolshed install /path/to/chimerax_vinardock-*.whl"

From this source checkout (builds and installs in one step)::

    ./install.sh

If ``chimerax`` is not on your ``PATH``, point the script at it::

    CHIMERAX=/path/to/ChimeraX ./install.sh

Restart ChimeraX afterwards.

To build a redistributable wheel::

    ./build.sh

The wheel is written to ``src/bundles/vinardock/dist``.

Usage
-----

Commands::

    dockbox center 1,2,3 size 10,20,30
    dockbox autobox #1 autobox_size 10
    dockbox close true
    dockbox                         # show the Docking Box tool

The **Docking Box** tool is under *Binding Analysis*.  Its ligand list defaults
to the first docking pose in an opened ``.pdbt`` output file.

License
-------

GNU Lesser General Public License, version 2.1 (see ``LICENSE``).  This bundle
is an original work and is not part of UCSF ChimeraX.
