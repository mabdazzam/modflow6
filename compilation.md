# Compile MODLFOW6 Parallel on Slackware

## Navigating dependencies issues (PETSc and test-drive)

```sh
# switch to root
su -

# install openmpi and python3-numpy; petsc requires python3-numpy and OpenBLAS
# (now a core package in Slackware);
# build queuefiles, not packages, to automatically build any other dependencies
sbopkg -k -i "openmpi python3-numpy"
```
### Configuring PETSc
MODFLOW 6 currently supports PETSc up to 3.22.5 due to issues with PETSc 3.23.
PETSc releases above 3.22.5 are not guaranteed to be compatible with MF6
([MF6 PR #2260](https://github.com/MODFLOW-ORG/modflow6/pull/2260/files)). At the same
time, PETSc ≤ 3.22.5 ships petsc4py sources that are incompatible with Cython ≥
3.0, which causes build failures ([broken
petsc4py](https://lists.mcs.anl.gov/pipermail/petsc-users/2024-June/050910.html)).
To resolve this cleanly, PETSc (and petsc4py) are built inside an isolated
Python virtual environment that uses an older Cython (< 3), while the final
PETSc installation is system-wide and usable from the normal Python
environment.

```sh
cd ~abd/usr/local/src
python3 -m venv /tmp/petsc-build-venv
. /tmp/petsc-build-venv/bin/activate
pip install --upgrade pip
pip install 'cython<3' numpy wheel setuptools mpi4py

git clone git@github.com:mabdazzam/slackbuilds-geni.git
cd slackbuilds-geni/geni/petsc
wget https://web.cels.anl.gov/projects/petsc/download/release-snapshots/petsc-3.18.6.tar.gz
./petsc.Slackbuild

# deactivate the virtual env
deactivate

# switch to user
exit
```

### Fortran Test Drive
```sh
cd ~/usr/local/src/
git clone git@github.com:fortran-lang/test-drive.git
cd test-drive
```
You can either use meson/ninja or cmake/make.
Default meson build is broken seems like overzealous checking of stricter
gfortran 15.1.0.
```sh
# running without `-Dtesting=disabled` will blowup the test
#`-Dtesting` flag doesn't compile test/test_select.F90
meson setup builddir -Dtesting=disabled
meson compile -C builddir

# meson fix is brittle, instead CMAKE is recommended
(mkdir build; cd build; cmake  -DCMAKE_INSTALL_PREFIX=$HOME/usr/local ..)
cd build
make
make install
```
## Download and Compile MODFLOW6

```sh
cd ~/usr/local/src/
git clone git@github.com:MODFLOW-ORG/modflow6.git
cd modflow6
rm -rf builddir
meson setup builddir -Ddebug=false -Dparallel=true --prefix=$(pwd) --libdir=bin
meson install -C builddir
meson test --verbose --no-rebuild -C builddir

# add executable to path
mkdir ~/usr/local/bin
cp -a bin/mf6 ~/usr/local/bin
if ! echo $PATH | grep -q $HOME/usr/local/bin; then
  echo 'export PATH="$HOME/usr/local/bin:$PATH"' > ~/.bash_profile
  . ~/.bash_profile
fi
```
