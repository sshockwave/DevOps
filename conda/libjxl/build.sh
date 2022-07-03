git clone https://github.com/libjxl/libjxl.git --depth 1 --branch "$JXL_VER"  --recursive --shallow-submodules
cd libjxl
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF ..
cmake --build . -- -j$(nproc)
cmake --install . --prefix="$PREFIX"
