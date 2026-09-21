# Reader for PDBT / AutoDock-PDBQT files.
#
# These are PDB-like files carrying extra ROOT/BRANCH/TORSDOF records and a
# trailing per-atom charge/type column that the PDB reader does not like.  Two
# quirks are handled here:
#
#   * A residue's hydrogens are sometimes listed at the end of the file instead
#     of next to the rest of the residue.  ChimeraX only bonds atoms that are
#     contiguous within a residue, so atoms are regrouped by residue before the
#     data is handed to the PDB reader (otherwise hydrogens end up unbonded).
#   * Vinardock records the per-pose energy and RMSD as REMARK 980 and 990.
#
# This is an original implementation for the ChimeraX-Vinardock bundle,
# distributed under the GNU Lesser General Public License v2.1 (see LICENSE).

ENCODINGS = ('utf-8', 'utf-16', 'utf-32')

# Keys the ViewDock tool expects in a structure's "viewdock_data" attribute.
RATING_KEY = 'rating'
DEFAULT_RATING = 0

# PDB records forwarded to the PDB reader.  MODEL/ENDMDL are kept so that
# multi-model docking output becomes separate structures.
_KEPT_RECORDS = ("ATOM  ", "HETATM", "MODEL ", "ENDMDL", "TER   ", "CONECT")
_BREAK_RECORDS = ("MODEL ", "ENDMDL", "TER   ", "CONECT")


def open_pdbt(session, path, file_name, auto_style, atomic):
    """Read a PDBT/PDBQT file, returning (structures, status)."""
    error = None
    for encoding in ENCODINGS:
        try:
            return _open(session, path, file_name, encoding)
        except UnicodeError as e:
            error = e
    raise error


def _open(session, path, file_name, encoding):
    import os
    from tempfile import TemporaryDirectory
    from chimerax.io import open_input, open_output

    with TemporaryDirectory() as tmp:
        cleaned = os.path.join(tmp, os.path.splitext(os.path.basename(path))[0] + '.pdb')
        with open_output(cleaned, encoding) as out:
            with open_input(path, encoding) as stream:
                _write_cleaned_pdb(stream, out)
        structures, _status = session.open_command.open_data(cleaned, format='pdb', log_errors=False)

    with open_input(path, encoding='utf-8') as stream:
        _apply_metadata(session, stream, structures)

    status = "Opened %s containing %d structures (%d atoms, %d bonds)" % (
        file_name, len(structures),
        sum(s.num_atoms for s in structures),
        sum(s.num_bonds for s in structures))
    return structures, status


def _write_cleaned_pdb(stream, out):
    """Write a PDB-acceptable copy of a PDBT/PDBQT file to *out*."""
    pending = []

    def flush():
        # Group each residue's atoms together, preserving first-seen order.
        residues = {}
        for line in pending:
            residues.setdefault(line[17:27], []).append(line)
        for lines in residues.values():
            # PDBQT names every hydrogen "H".  Residue templates for standard
            # residues then bind all of them to the amide nitrogen.  Give each
            # hydrogen a unique name so the reader falls back to bonding by
            # distance, which puts it on the correct heavy atom.
            h = 0
            for line in lines:
                if line[12:16].strip() == 'H':
                    h += 1
                    line = line[:12] + (' %-3s' % ('H%d' % h))[:4] + line[16:]
                out.write(line + '\n')
        del pending[:]

    for raw in stream:
        line = raw.rstrip('\n')
        record = line[:6]
        if record in _BREAK_RECORDS:
            flush()
            out.write(line + '\n')
        elif record in _KEPT_RECORDS:
            pending.append(_fix_columns(line) if record == 'ATOM  ' else line)
    flush()


def _fix_columns(line):
    """Blank the AutoDock charge/type columns that confuse the PDB reader."""
    if len(line) > 78 and line[78].isupper():
        line = line[:78] + ' ' + line[79:]
    if len(line) > 70:
        line = line[:70] + '      ' + line[76:]
    if line[17:20] == '***':
        line = line[:17] + 'UNL' + line[20:]
    if line[25] == '*':
        line = line[:25] + '1' + line[26:]
    return line


def _apply_metadata(session, stream, structures):
    """Attach per-pose energy/RMSD values from REMARK records to structures."""
    model = -1
    values = None
    for line in stream:
        record = line[:6]
        if record == 'MODEL ':
            model += 1
            values = {RATING_KEY: DEFAULT_RATING}
        elif record == 'ENDMDL':
            if values is not None and 0 <= model < len(structures):
                from chimerax.atomic import Structure
                Structure.register_attr(session, 'viewdock_data', 'ViewDock')
                structures[model].viewdock_data = values
            values = None
        elif record == 'REMARK' and values is not None:
            values.update(_remark_values(line))


def _remark_values(line):
    if 'VINA RESULT:' in line:
        # AutoDock Vina: "REMARK VINA RESULT: -11.1 0.000 0.000"
        fields = line.split('VINA RESULT:', 1)[1].split()
        return dict(zip(('Score', 'RMSD l.b.', 'RMSD u.b.'), fields))
    if ':' not in line:
        return {}
    fields = line.split(':', 1)[1].split()
    if not fields:
        return {}
    remark = line[7:10].strip()
    if remark == '980':
        # "REMARK 980   NORMALIZED BINDING FREE ENERGY : -11.111 KCAL/MOL"
        return {'Energy': fields[0]}
    if remark == '990':
        # "REMARK 990   RMSD FROM INIT : 0.627 ANGSTROM"; 0.000 means the run
        # did not use --calc_lig_rmsd, so there is no useful RMSD column.
        try:
            nonzero = float(fields[0]) != 0.0
        except ValueError:
            nonzero = True
        if nonzero:
            return {'RMSD': fields[0]}
    return {}
