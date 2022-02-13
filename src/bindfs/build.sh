./autogen.sh
PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig ./configure --prefix="$PREFIX"
make
make install
