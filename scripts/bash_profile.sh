# Test Mainline QEMU
unset https_proxy; unset http_proxy; unset HTTP_PROXY; unset HTTPS_PROXY;
export https_proxy="http://172.20.201.1:8080"
export http_proxy="http://172.20.201.1:8080"
make docker-test-quick@centos6 DOCKER_CCACHE_DIR="/scratch/alistai/.cache/qemu-docker-ccache" J=8
make docker-test-build@min-glib DOCKER_CCACHE_DIR="/scratch/alistai/.cache/qemu-docker-ccache" J=8
make docker-test-mingw@fedora DOCKER_CCACHE_DIR="/scratch/alistai/.cache/qemu-docker-ccache" J=8

## Git patch work
QEMU:
../QEMUPatchWork/git_make_series <branch> 1 xilinx/master "QEMU PATCH" "next"
Mainline QEMU
../QEMUPatchWork/git_make_series <branch> 1 mainline/master "PATCH" "next" ../QEMUPatchWork/clean_and_conf ../QEMUPatchWork/cp_and_build PUBLIC

## Dump assembly
arm-xilinx-eabi-objdump -D
microblaze-xilinx-elf-objdump -d

### Patches
python setup.py build
./bin/patches fetch http://vmsplice.net/~patches/patches.json

### Find and Replace
find ./* -type f -not -path "*/.git*" -exec sed -i 's|FIND|REPLACE|g' {} +

qemu_log_mask_level\((.*?,) (.*?,)		qemu_log_mask\(\2 

### Build Kernel
CROSS_COMPILE=aarch64-none-elf- ARCH=arm64 make xilinx_zynqmp_defconfig && CROSS_COMPILE=aarch64-none-elf- ARCH=arm64 make -j8

### Build ATF (Arm Trusted Firmware)
export CROSS_COMPILE=aarch64-linux-gnu-
make PLAT=zynqmp all

### Log Buf
objdump -x ./tmp/work/zcu102_zynqmp-poky-linux/linux-xlnx/4.4-xilinx+gitAUTOINC+89cc643aff-r0/linux-zcu102_zynqmp-standard-build/arch/arm64/boot/vmlinux | grep "__log_buf"
memsave 0xffffffc000b96a18 16384 dumpmem.logbuf
./logbufreader.py dumpmem.logbuf | less

### QEMU Tagging
git tag -s -a "xilinx-v2017.4" -m "Tag QEMU for the Xilinx 2017.4 release."
git tag -s -a "xilinx-v2017.4" -m "Tag the QEMU device trees for the Xilinx 2017.4 release."

### QEMU MinGW
SDKMACHINE=x86_64-mingw32 bitbake nativesdk-qemu

PACKAGE_CLASSES ?= "package_ipk"
PACKAGECONFIG_remove_pn-nativesdk-qemu = "sdl"
PACKAGECONFIG_remove_pn-nativesdk-opkg-utils = "python"

# Yocto Kernel Dev
bitbake virtual/kernel -c compile -f


# Zephyr QEMU
cmake -DBOARD=qemu_riscv32 -DTOOLCHAIN_HOME=/usr/local/oecore-x86_64/sysroots/x86_64-oesdk-linux/usr/bin/riscv32-oe-linux/ -DLIBGCC_FILE_NAME=/usr/local/oecore-x86_64/sysroots/riscv32-oe-linux/usr/lib/riscv32-oe-linux/8.2.0/libgcc.a -DPYTHON_EXECUTABLE=/usr/bin/python3 ..
make

# Jenkins
docker pull jenkins/jenkins
docker run -p 8080:8080 -p 50000:50000 --dns 10.86.1.1 -v jenkins_home:/var/jenkins_home jenkins/jenkins
