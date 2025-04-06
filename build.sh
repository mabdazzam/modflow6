meson setup builddir -Ddebug=false -Dparallel=true --prefix=$(pwd) --libdir=bin
meson install -C builddir
meson test --verbose --no-rebuild -C builddir
