_envsh=$(realpath $BASH_SOURCE)
_bindir=$(dirname $_envsh)
_installdir=$(dirname $_bindir)
_pydir="$_installdir/ideal"

if [ -z "$VIRTUAL_ENV" ] ; then
    source $_installdir/venv/bin/activate
fi

if [ -z "$PYTHONPATH" ] ; then
    export PYTHONPATH="$_pydir"
else
    export PYTHONPATH="$_pydir:$PYTHONPATH"
fi

# a bit facetious
if [ -z "$PATH" ] ; then
    export PATH="$_bindir"
else
    export PATH="$_bindir:$PATH"
fi

unset _envsh
unset _bindir
unset _installdir
unset _pydir

# vim: filetype=sh et smartindent ai sw=4
