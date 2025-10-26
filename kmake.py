#!python3
"""
MIT License

Copyright (c) 2025 Darshan Koirala (theanimatorspal)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, **provided that the original author (Darshan Koirala) is credited**
in any distributed work or derivative.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import os
import sys
import platform
import subprocess
import urllib.request
import json
import zipfile
import tarfile
import argparse
import shutil
import tempfile
from pathlib import Path


CMAKE_MINIMUM_REQUIRED_STRING = "cmake_minimum_required(VERSION 3.28)"

"""

# UTILITY COMMANDS

"""

def _cmake_version() -> str | None:
    try:
        cmake = get_local_cmake()
        result = subprocess.run(
            [cmake, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        first_line = result.stdout.splitlines()[0]
        parts = first_line.strip().split()
        for p in parts:
            if p[0].isdigit():
                major_minor = ".".join(p.split(".")[:2])
                return major_minor
        return None
    except Exception:
        return None


def _cmake_find_package_str(pkg_name: str, required: bool = True) -> str:
    pkg_cmake = pkg_name.capitalize()
    if required:
        return f"find_package({pkg_cmake} REQUIRED)\n"
    else:
        return f"find_package({pkg_cmake})\n"

def _get_shell_config_file() -> Path | None:
    if platform.system() == "Windows":
        return None
    
    home = Path.home()
    zshrc = home / ".zshrc"
    if zshrc.exists():
        return zshrc
    
    bashrc = home / ".bashrc"
    if bashrc.exists():
        return bashrc

    bash_profile = home / ".bash_profile"
    if bash_profile.exists():
        return bash_profile
        
    return bashrc

if platform.system() == "Windows":
    import winreg
    import ctypes

def copy(src, dst):
    src_path = Path(src)
    dst_path = Path(dst)
    
    if not src_path.exists():
        raise FileNotFoundError(f"Source '{src}' does not exist")
    
    if src_path.is_file():
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)
    elif src_path.is_dir():
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
    else:
        raise ValueError(f"Unsupported source type: {src}")

def get_local_vcpkg() -> str:
    vcpkg = shutil.which("vcpkg")
    if not vcpkg:
        base_dir = Path.home() / ".kmake"
        vcpkg_dir = base_dir / "vcpkg"
        vcpkg_exe = "vcpkg.exe" if platform.system() == "Windows" else "vcpkg"
        local_vcpkg = vcpkg_dir / vcpkg_exe
        
        if local_vcpkg.exists():
            return str(local_vcpkg)
        else:
            install_vcpkg(base_dir, add_to_path=False)
            return str(local_vcpkg)
    return vcpkg

def get_local_emcc() -> str:
    emcc = shutil.which("emcc")
    if not emcc:
        base_dir = Path.home() / ".kmake"
        emsdk_dir = base_dir / "emsdk" / "upstream" / "emscripten"
        emcc_exe = "emcc.bat" if platform.system() == "Windows" else "emcc"
        local_emcc = emsdk_dir / emcc_exe
        
        if local_emcc.exists():
            return str(local_emcc)
        else:
            raise RuntimeError("Emscripten not found. Run 'kmake self-install' first.")
    return emcc

def get_local_cmake() -> str:
    cmake = shutil.which("cmake")
    if not cmake:
        base_dir = Path.home() / ".kmake"
        cmake_dir = base_dir / "cmake" / "bin"
        cmake_exe = "cmake.exe" if platform.system() == "Windows" else "cmake"
        local_cmake = cmake_dir / cmake_exe
        
        if local_cmake.exists():
            return str(local_cmake)
        else:
            raise RuntimeError("CMake not found. Run 'kmake self-install' first.")
    return cmake

def get_local_ninja() -> str:
    ninja = shutil.which("ninja")
    if not ninja:
        base_dir = Path.home() / ".kmake"
        ninja_dir = base_dir / "ninja"
        ninja_exe = "ninja.exe" if platform.system() == "Windows" else "ninja"
        local_ninja = ninja_dir / ninja_exe
        
        if local_ninja.exists():
            return str(local_ninja)
        else:
            raise RuntimeError("Ninja not found. Run 'kmake self-install' first.")
    return ninja

def add_to_path(path_to_add: Path):
    path_str = str(path_to_add)
    
    if platform.system() == "Windows":
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            current_path, _ = winreg.QueryValueEx(key, "PATH")
            paths = current_path.split(';')
            if path_str in paths:
                print(f"✅ {path_str} is already in PATH.")
                return
            
            new_path = f"{current_path};{path_str}"
        except FileNotFoundError:
            new_path = path_str

        print(f"➕ Adding {path_str} to user PATH...")
        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
        winreg.CloseKey(key)

        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x1A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_long()
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 5000, ctypes.byref(result))
        print("✅ PATH updated. You must restart your terminal for this to take effect.")

    else: 
        current_path = os.environ.get("PATH", "")
        if path_str in current_path.split(os.pathsep):
            return
            
        print(f"➕ Adding {path_str} to PATH...")
        config_file = _get_shell_config_file() 
        if config_file:
            with open(config_file, "a") as f:
                f.write(f'\nexport PATH="{path_str}:$PATH"\n')
            print(f"✅ Updated {config_file}. Please restart your shell or run 'source {config_file}'.")

def download_and_extract(url: str, dest_dir: Path):
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_name = url.split("/")[-1]
        archive_path = Path(tmpdir) / archive_name

        print(f"🌐 Downloading {archive_name}...")
        urllib.request.urlretrieve(url, archive_path)
        
        print(f"📦 Extracting to {dest_dir}...")
        if archive_name.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(dest_dir)
        elif archive_name.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as t:
                t.extractall(dest_dir)
        else:
            raise ValueError(f"Unsupported archive format for {archive_name}")

def get_latest_cmake_url() -> str:
    api_url = "https://api.github.com/repos/Kitware/CMake/releases/latest"
    system = platform.system()
    arch = platform.machine()

    if system == "Windows" and arch.endswith("64"):
        identifier = "windows-x86_64.zip"
    elif system == "Darwin":
        identifier = "macos-universal.tar.gz"
    elif system == "Linux" and arch == "x86_64":
        identifier = "linux-x86_64.tar.gz"
    else:
        raise OSError(f"Unsupported OS/architecture: {system}/{arch}")

    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read())
        
        for asset in data.get("assets", []):
            if identifier in asset.get("name", ""):
                return asset["browser_download_url"]
        
        raise FileNotFoundError(f"Could not find a CMake download link for {identifier}")

    except Exception as e:
        print(f"Error fetching latest CMake URL: {e}", file=sys.stderr)
        sys.exit(1)

def get_latest_ninja_url() -> str:
    api_url = "https://api.github.com/repos/ninja-build/ninja/releases/latest"
    system = platform.system()
    
    if system == "Windows":
        identifier = "win.zip"
    elif system == "Darwin":
        identifier = "mac.zip"
    elif system == "Linux":
        identifier = "linux.zip"
    else:
        raise OSError(f"Unsupported OS: {system}")
    
    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read())
        
        for asset in data.get("assets", []):
            if identifier in asset.get("name", ""):
                return asset["browser_download_url"]
        
        raise FileNotFoundError(f"Could not find a Ninja download link for {identifier}")
    
    except Exception as e:
        print(f"Error fetching latest Ninja URL: {e}", file=sys.stderr)
        sys.exit(1)

def install_cmake(base_dir: Path, should_add_to_path : bool) -> Path:
    cmake_dir = base_dir / "cmake"
    if cmake_dir.exists():
        print("✅ CMake is already installed.")
        return cmake_dir

    print("🚀 Installing CMake...")
    url = get_latest_cmake_url()
    
    temp_extract_dir = base_dir / "cmake_temp"
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir)
    temp_extract_dir.mkdir()

    download_and_extract(url, temp_extract_dir)
    
    extracted_items = list(temp_extract_dir.iterdir())
    if not extracted_items:
        raise IOError("Extraction failed, no directory found.")
    
    source_dir = extracted_items[0]
    shutil.move(str(source_dir), str(cmake_dir))
    shutil.rmtree(temp_extract_dir)
    
    if should_add_to_path:
        add_to_path(cmake_dir / "bin")

    return cmake_dir

def install_emsdk(base_dir: Path, should_add_to_path: bool = True) -> Path:
    emsdk_dir = base_dir / "emsdk"
    if emsdk_dir.exists():
        print("✅ Emscripten SDK is already installed.")
        return emsdk_dir
    
    print("🚀 Installing Emscripten SDK...")
    
    if not shutil.which("git"):
        raise RuntimeError("Git is required to install emsdk.")
    
    subprocess.run(
        ["git", "clone", "https://github.com/emscripten-core/emsdk.git", str(emsdk_dir), "--depth=1"],
        check=True
    )
    
    emsdk_script = "emsdk.bat" if platform.system() == "Windows" else "./emsdk"
    

    if platform.system() == "Windows":
        subprocess.run([emsdk_script, "install", "latest"], cwd=emsdk_dir, shell=True, check=True)
        subprocess.run([emsdk_script, "activate", "latest"], cwd=emsdk_dir, shell=True, check=True)
        subprocess.run([emsdk_script, "activate", "--permanent"], cwd=emsdk_dir, shell=True, check=True)
        subprocess.run(["emsdk_env.bat"], cwd=emsdk_dir, shell=True, check=True)
    else:
        subprocess.run("./emsdk install latest", cwd=emsdk_dir, shell=True, check=True)
        subprocess.run("./emsdk activate latest", cwd=emsdk_dir, shell=True, check=True)
        subprocess.run("./emsdk activate --permanent", cwd=emsdk_dir, shell=True, check=True)

    
    if should_add_to_path:
        add_to_path(emsdk_dir)
        add_to_path(emsdk_dir / "upstream" / "emscripten")
        node_bin = next((Path(emsdk_dir / "node").iterdir())).resolve() / "bin"
        add_to_path(node_bin)
    
    print("✅ Emscripten SDK installed!")
    return emsdk_dir

def install_ninja(base_dir: Path, should_add_to_path: bool = True) -> Path:
    ninja_dir = base_dir / "ninja"
    if ninja_dir.exists():
        print("✅ Ninja is already installed.")
        return ninja_dir
    
    print("🚀 Installing Ninja...")
    url = get_latest_ninja_url()
    
    ninja_dir.mkdir()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_name = url.split("/")[-1]
        archive_path = Path(tmpdir) / archive_name
        
        print(f"🌐 Downloading {archive_name}...")
        urllib.request.urlretrieve(url, archive_path)
        
        print(f"📦 Extracting to {ninja_dir}...")
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(ninja_dir)
    
    if platform.system() != "Windows":
        ninja_exe = ninja_dir / "ninja"
        ninja_exe.chmod(ninja_exe.stat().st_mode | 0o111)
    
    if should_add_to_path:
        add_to_path(ninja_dir)
    
    return ninja_dir

def install_vcpkg(base_dir: Path, should_add_to_path : bool) -> Path:
    vcpkg_dir = base_dir / "vcpkg"
    if vcpkg_dir.exists():
        print("✅ vcpkg is already installed.")
        return vcpkg_dir
    
    print("🚀 Installing vcpkg...")
    if not shutil.which("git"):
        raise RuntimeError("Git is not installed or not in PATH. Please install Git to continue.")
        
    subprocess.run(
        ["git", "clone", "https://github.com/microsoft/vcpkg.git", str(vcpkg_dir)], 
        check=True
    )
    
    bootstrap_script = "bootstrap-vcpkg.bat" if platform.system() == "Windows" else "bootstrap-vcpkg.sh"
    subprocess.run(
        [str(vcpkg_dir / bootstrap_script)], 
        shell=True, 
        check=True
    )
    
    if should_add_to_path:
        add_to_path(vcpkg_dir)

    return vcpkg_dir

def install_self():
    target_dir = Path(__file__).resolve().parent
    add_to_path(target_dir)
    if platform.system() != "Windows":
        for py_file in target_dir.glob("kmake"):
            py_file.chmod(py_file.stat().st_mode | 0o111)  # add executable bits
        print(f"✅ Made kmake in {target_dir} executable")

    print(f"✅ Added {target_dir} to PATH")

def handle_self_install(args):
    print("🚀 Initializing setup...")
    base_dir = Path.home() / ".kmake"
    base_dir.mkdir(exist_ok=True)
    
    add_kmake_to_path = get_yes_no("Add kmake to PATH?", default=True)
    add_cmake_to_path = get_yes_no("Add CMake to PATH?", default=True)
    add_vcpkg_to_path = get_yes_no("Add vcpkg to PATH?", default=True)    
    add_emsdk_to_path = get_yes_no("Add Emsdk to PATH?", default=True)
    add_ninja_to_path = get_yes_no("Add Ninja to PATH?", default=True)

    if add_kmake_to_path:
        install_self()

    cmake_dir = install_cmake(base_dir, add_cmake_to_path)
    vcpkg_dir = install_vcpkg(base_dir, add_vcpkg_to_path)
    emsdk_dir = install_emsdk(base_dir, add_emsdk_to_path)
    ninja_dir = install_ninja(base_dir, add_ninja_to_path)

    print("\n🎉 Installation Complete!")
    print(f"CMake installed at: {cmake_dir}")
    print(f"vcpkg installed at: {vcpkg_dir}")
    print(f"Ninja installed at: {ninja_dir}")

    print("\nIMPORTANT: You must restart your terminal for PATH changes to take effect.")

def get_cmake_dir():
    return Path.home() / ".kmake" / "cmake"

def get_vcpkg_dir():
    return Path.home() / ".kmake" / "vcpkg"

def get_emsdk_dir():
    return Path.home() / ".kmake" / "emsdk"

def run_vcpkg_command(args, cwd=None):
    vcpkg = get_local_vcpkg()
    process = subprocess.Popen(
        [vcpkg] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=cwd
    )

    output = ""
    for line in process.stdout:
        print(line, end="")
        output += line

    process.wait()
    return process.returncode, output

def install_vcpkg_package(name: str, project_name: str, system: str, version: str = ""):
    print(f"⏳ Installing package {name}")
    triplet = system

    if version:
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                vcpkg_root = os.path.dirname(get_local_vcpkg())
                baseline = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=vcpkg_root, text=True
                ).strip()
            except Exception:
                baseline = "0000000000000000000000000000000000000000"

            manifest = {
                "dependencies": [name],
                "overrides": [{"name": name, "version": version}],
                "builtin-baseline": baseline
            }

            manifest_path = os.path.join(tmpdir, "vcpkg.json")
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)

            code, output = run_vcpkg_command(
                ["install", f"--triplet={triplet}"], cwd=tmpdir
            )
    else:
        code, output = run_vcpkg_command(["install", f"{name}:{triplet}"])

    lines = [
        line.strip().replace("main", project_name)
        for line in output.splitlines()
        if line.strip().startswith(("find_", "target_"))
    ]

    print(f"✅ Installed {name} and Compiled into CMake Files")
    return "\n" + "\n".join(lines) + "\n\n"

def get_cmake_preset_file_string(
    compiler="clang",
    platform_triplet="x64-windows",
    android_toolchain="C:/AndroidSDK/ndk/26.3.11579264/build/cmake/android.toolchain.cmake",
    android_platform="android-31"
):
    vcpkg_toolchain = get_vcpkg_dir() / "scripts" / "buildsystems" / "vcpkg.cmake"
    emscripten_toolchain = get_emsdk_dir() / "upstream" / "emscripten" / "cmake" / "Modules" / "Platform" / "Emscripten.cmake"
    cmake_prefix_path = get_vcpkg_dir() / "installed" / platform_triplet
    
    compilers = {
        "clang": ("clang", "clang++"),
        "gcc": ("gcc", "g++"),
        "emcc": ("emcc", "em++")
    }

    # WORKAROUND
    if platform.system() == "Windows":
        compilers = {
            "clang": ("clang", "clang++"),
            "gcc": ("gcc", "g++"),
            "emcc": ("emcc.bat", "em++.bat")
        }

    c_compiler, cxx_compiler = compilers.get(compiler, ("clang", "clang++"))
    
    is_android = platform_triplet.startswith("arm") and "android" in platform_triplet
    is_web = "wasm" in platform_triplet or "emscripten" in platform_triplet
    
    base_cache = {
        "CMAKE_PRESET_NAME": "${presetName}",
        "CMAKE_TOOLCHAIN_FILE": str(vcpkg_toolchain).replace("\\", "/"),
        # "CMAKE_PREFIX_PATH" : str(cmake_prefix_path).replace("\\","/")
    }
    
    if is_android:
        base_cache.update({
            "CMAKE_SYSTEM_NAME": "Android",
            "CMAKE_ANDROID_NDK": android_toolchain.split("/build/cmake")[0],
            "CMAKE_ANDROID_STL_TYPE": "c++_shared",
            "VCPKG_TARGET_TRIPLET": platform_triplet
        })
    elif is_web:
        base_cache["VCPKG_TARGET_TRIPLET"] = platform_triplet
        base_cache.update({
            "CMAKE_C_COMPILER": c_compiler,
            "CMAKE_CXX_COMPILER": cxx_compiler,
            "CMAKE_TOOLCHAIN_FILE": str(vcpkg_toolchain).replace("\\", "/"),
            "VCPKG_CHAINLOAD_TOOLCHAIN_FILE": str(emscripten_toolchain).replace("\\", "/"),
        })
    else:
        base_cache.update({
            "CMAKE_C_COMPILER": c_compiler,
            "CMAKE_CXX_COMPILER": cxx_compiler
        })
    
    arch = "x64" if "x64" in platform_triplet or "arm64" in platform_triplet else "x86"
    strategy = "" if is_web or is_android else f''',
      "architecture": {{
        "value": "{arch}",
        "strategy": "external"
      }}'''
    
    build_types = ["Debug", "Release", "RelWithDebInfo", "MinSizeRel"]
    presets = []
    
    for build_type in build_types:
        preset_name = f"{platform_triplet}-{build_type.lower()}"
        display_name = f"{platform_triplet} {build_type}"
        
        cache_vars = '",\n        "'.join([f'{k}": "{v}' for k, v in base_cache.items()])
        
        presets.append(f'''    {{
      "name": "{preset_name}",
      "displayName": "{display_name}",
      "generator": "Ninja",
      "binaryDir": "${{sourceDir}}/out/build/${{presetName}}",
      "installDir": "${{sourceDir}}/out/install/${{presetName}}"{strategy},
      "cacheVariables": {{
        "{cache_vars}",
        "CMAKE_BUILD_TYPE": "{build_type}"
      }}
    }}''')
    
    return f'''{{
  "version": 3,
  "configurePresets": [
{",\n".join(presets)}
  ]
}}'''

def clear_screen():
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def get_input(prompt, default=""):
    if default:
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    return input(f"{prompt}: ").strip()

def get_choice(prompt, options):
    while True:
        print(f"\n{prompt}")
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
        choice = input("\nEnter choice (number): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print("❌ Invalid choice. Please try again.")

def get_yes_no(prompt, default=True):
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("❌ Please enter 'y' or 'n'")

def get_cmake_default_fill_string():
    cmake_start = r"""
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)  
function(RunOnce)
if(MSVC)
if(POLICY CMP0141)
cmake_policy(SET CMP0141 NEW)
set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()
endif()
cmake_policy(SET CMP0069 NEW) 
set(CMAKE_POLICY_DEFAULT_CMP0069 NEW)

if(WIN32)
    add_definitions(-DWIN32_LEAN_AND_MEAN -DNOMINMAX -D_CRT_SECURE_NO_WARNINGS -D_SDL_MAIN_HANDLED)
endif()
endfunction()

function(ClangTidyChecks)
find_program(CLANG_TIDY_EXE NAMES clang-tidy)
if(CLANG_TIDY_EXE)
set(CLANG_TIDY_CHECKS
    "clang-analyzer-*,hicpp-*,readability-simplify-boolean-expr,readability-delete-null-pointer,portability-simd-intrinsics"
)

set(CLANG_TIDY_ARGS
    --warnings-as-errors=*
    -header-filter=.*
    --checks=${CLANG_TIDY_CHECKS}
    --format-style=file
)

set(CMAKE_C_CLANG_TIDY   "${CLANG_TIDY_EXE};${CLANG_TIDY_ARGS}")
set(CMAKE_CXX_CLANG_TIDY "${CLANG_TIDY_EXE};${CLANG_TIDY_ARGS}")
else()
    message(WARNING "clang-tidy not found! Static analysis will be skipped.")
endif()

if (CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
    add_compile_options(-Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wsign-conversion)
elseif (MSVC)
    add_compile_options(/W4 /permissive-)
endif()

if(MSVC)
    message(STATUS "MSVC detected: enabling AddressSanitizer")
    add_compile_options(/fsanitize=address /Zi /Od)
    add_link_options(/INCREMENTAL:NO /fsanitize=address)
else()
    set(SANITIZERS "")
    set(SANITIZERS "${SANITIZERS}address,undefined")
    if(UNIX AND NOT APPLE)
        set(SANITIZERS "${SANITIZERS},leak")
    elseif(APPLE)
        set(SANITIZERS "${SANITIZERS},leak")
    endif()
    add_compile_options(-fsanitize=${SANITIZERS} -fno-omit-frame-pointer -g)
    add_link_options(-fsanitize=${SANITIZERS})
endif()
endfunction()

if(EMSCRIPTEN)
    # Disable cmake_ninja_dyndep for modules / PCH
    set(CMAKE_NINJA_FORCE_RESPONSE_FILE 1)
endif()


function(PrecompileStdHeaders TARGET_NAME)
    target_precompile_headers(${TARGET_NAME} PRIVATE
        # Standard C++ Headers
        <algorithm>
        <any>
        <array>
        <atomic>
        <bit>
        <bitset>
        <cassert>
        <cctype>
        <cerrno>
        <cfenv>
        <charconv>
        <chrono>
        <cinttypes>
        <climits>
        <clocale>
        <cmath>
        <codecvt>
        <compare>
        <complex>
        <concepts>
        <condition_variable>
        <coroutine>
        <csetjmp>
        <csignal>
        <cstdarg>
        <cstddef>
        <cstdint>
        <cstdio>
        <cstdlib>
        <cstring>
        <ctime>
        <deque>
        <exception>
        <execution>
        <expected>
        <filesystem>
        <format>
        <forward_list>
        <fstream>
        <functional>
        <future>
        <initializer_list>
        <iomanip>
        <ios>
        <iosfwd>
        <iostream>
        <istream>
        <iterator>
        <limits>
        <list>
        <locale>
        <map>
        <memory>
        <memory_resource>
        <mutex>
        <new>
        <numbers>
        <numeric>
        <optional>
        <ostream>
        <queue>
        <random>
        <ranges>
        <ratio>
        <regex>
        <scoped_allocator>
        <set>
        <shared_mutex>
        <source_location>
        <span>
        <sstream>
        <stack>
        <stdexcept>
        <streambuf>
        <string>
        <string_view>
        <system_error>
        <thread>
        <tuple>
        <type_traits>
        <typeindex>
        <typeinfo>
        <unordered_map>
        <unordered_set>
        <utility>
        <valarray>
        <variant>
        <vector>
        <version>

        # C Standard Library Headers (as C++ headers)
        <cctype>
        <cerrno>
        <cfenv>
        <cfloat>
        <climits>
        <clocale>
        <cmath>
        <csetjmp>
        <csignal>
        <cstdarg>
        <cstddef>
        <cstdint>
        <cstdio>
        <cstdlib>
        <cstring>
        <ctime>
        <cwchar>
        <cwctype>

        # Third-Party Headers (Example: Vulkan, GLM, Sol2)
    #     <sol/sol.hpp>
    #     <vulkan/vulkan.hpp>
    #     <glm/glm.hpp>
    #     <glm/fwd.hpp>
    #     <glm/gtc/matrix_transform.hpp>
    #     <glm/gtx/matrix_decompose.hpp>
    #     <glm/gtc/type_ptr.hpp>
    #     <glm/gtx/quaternion.hpp>
    #     <glm/ext.hpp>
    #     <glm/gtx/transform.hpp>
    )
endfunction()
"""
    
    return cmake_start

def get_build_file():
    build_file = {}
    code = compile(Path("build.py").read_text(), "build.py", "exec")
    exec(code, build_file)
    return build_file

def handle_run(arg):
    build_file = get_build_file()
    Path("CMakePresets.json").write_text(get_cmake_preset_file_string(compiler=build_file["PROJECT_COMPILER"], platform_triplet=build_file["PROJECT_PLATFORM"]))
    Path(".clang-format").write_text("""BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 100
""")
    project_names = []
    for project_name, project_detail in build_file["PROJECT_STRUCTURE"].items():
        project_names.append(project_name)

    for project_name, project_detail in build_file["PROJECT_STRUCTURE"].items():
        is_main_project = (project_name == project_names[-1])
        project_path = os.path.join(os.getcwd(), "src", project_name) 
        os.makedirs(project_path, exist_ok=True)
        os.makedirs(os.path.join(project_path, "include", project_name), exist_ok=True)
        os.makedirs(os.path.join(project_path, "src"), exist_ok=True)

        cmake_text = f"""{CMAKE_MINIMUM_REQUIRED_STRING}
include("../../CMakeCommons.cmake")
file(GLOB_RECURSE {project_name}_SRC CONFIGURE_DEPENDS  "${{CMAKE_CURRENT_SOURCE_DIR}}/*.cpp" "${{CMAKE_CURRENT_SOURCE_DIR}}/*.hpp" "${{CMAKE_CURRENT_SOURCE_DIR}}/*.c" "${{CMAKE_CURRENT_SOURCE_DIR}}/*.h")
"""
        if project_detail["type"] == "static-library":
            cmake_text += f"""
add_library({project_name} STATIC ${{{project_name}_SRC}})
"""
        elif project_detail["type"] == "dynamic-library":
            cmake_text += f"""
add_library({project_name} DYNAMIC ${{{project_name}_SRC}})
"""
        elif project_detail["type"] == "binary":
            cmake_text += f"""
add_executable({project_name}  ${{{project_name}_SRC}})
"""
        else:
            raise ValueError("You have to specify the type - either binary, static-library or dynamic-library")

        if build_file["PROJECT_LANGUAGE"] == "C++":
            cmake_text+=f"""
PrecompileStdHeaders({project_name})
"""
        try:
            for dep, dep_detail in project_detail["deps"].items():
                if dep not in project_names:
                    cmake_text += install_vcpkg_package(dep, project_name, build_file["PROJECT_PLATFORM"], dep_detail.get("version", ""))
        except Exception as e:
            pass

        try:
            if "deps" in project_detail:
                first = True
                for dep in project_detail["deps"].keys():
                    if dep in project_names:
                        if first:
                            cmake_text += f"target_link_libraries({project_name}"
                            first = False
                        cmake_text += f" {dep}"
                if not first:
                    cmake_text += ")\n"

        except Exception as e:
            pass


        if is_main_project:
            if project_name != build_file["PROJECT_NAME"]:
                print("ERROR: PROJECT_NAME should match the name of last project in PROJECT_STRUCTURE")
                sys.exit(1)

            cmake_text += f"""add_custom_command(
    TARGET {project_name} POST_BUILD
    COMMAND ${{CMAKE_COMMAND}} -E copy
            "${{CMAKE_SOURCE_DIR}}/out/build/${{CMAKE_PRESET_NAME}}/compile_commands.json"
            "${{CMAKE_SOURCE_DIR}}/compile_commands.json"
)
"""
        Path(os.path.join(project_path, "CMakeLists.txt")).write_text(cmake_text)

        if is_main_project:
            cmake_text = f"""
{CMAKE_MINIMUM_REQUIRED_STRING}
project({project_name})
include("CMakeCommons.cmake")
RunOnce()
"""
            if build_file["PROJECT_LANGUAGE"] == "C++":
                cmake_text += f"""set(CMAKE_CXX_STANDARD {build_file["PROJECT_LANGUAGE_STANDARD"]})
set(CMAKE_CXX_STANDARD_REQUIRED ON)
"""
            elif build_file["PROJECT_LANGUAGE"] == "C":
                cmake_text += f"""set(CMAKE_C_STANDARD {build_file["PROJECT_LANGUAGE_STANDARD"]})
set(CMAKE_C_STANDARD_REQUIRED ON)
"""

            for project_name in project_names:
                cmake_text += f"""
include_directories("src/{project_name}/include")
add_subdirectory("src/{project_name}")
"""
            cmake_text += f""""""
            Path("CMakeCommons.cmake").write_text(get_cmake_default_fill_string())
            Path("CMakeLists.txt").write_text(cmake_text)

def handle_build(args):
    import json
    should_ask = 'ask' in args.options if args.options else False
    should_run = 'run' in args.options if args.options else False
    should_browser = 'browser' in args.options if args.options else False
    should_clean = 'clean' in args.options if args.options else False
    binary_args = []
    if should_run and args.options:
        try:
            run_index = args.options.index('run')
            binary_args = args.options[run_index + 1:]
        except (ValueError, IndexError):
            pass
    presets_file = Path("CMakePresets.json")
    if not presets_file.exists():
        print("❌ CMakePresets.json not found. Run 'kmake run' first.")
        sys.exit(1)
    
    presets_data = json.loads(presets_file.read_text())
    configure_presets = presets_data.get("configurePresets", [])
    
    if not configure_presets:
        print("❌ No presets found in CMakePresets.json")
        sys.exit(1)
    
    if should_ask:
        print("\n🔧 Available build presets:")
        for i, preset in enumerate(configure_presets, 1):
            display_name = preset.get("displayName", preset["name"])
            print(f"  {i}. {display_name}")
        
        while True:
            choice = input("\nSelect preset (number): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(configure_presets):
                    selected_preset = configure_presets[idx]
                    break
            except ValueError:
                pass
            print("❌ Invalid choice. Please try again.")
    else:
        selected_preset = configure_presets[0]
    
    preset_name = selected_preset["name"]
    build_dir = selected_preset["binaryDir"].replace("${sourceDir}", os.getcwd()).replace("${presetName}", preset_name)
    print(f"\n🔨 Building with preset: {preset_name}")
    
    cmake = get_local_cmake()
    ninja = get_local_ninja()

    if should_clean:
        build_dir = os.path.join(os.getcwd(), "out")
        print(f"🧹 Cleaning build directory: {build_dir}")

        if not os.path.exists(build_dir):
            print("⚠️ Build directory not found, nothing to clean.")
            return

        try:
            shutil.rmtree(build_dir)
            print("✅ Build directory removed successfully.")
        except Exception as e:
            print(f"❌ Failed to remove build directory: {e}")
            sys.exit(1)
    
    print("\n⚙️  Configuring project...")
    configure_result = subprocess.run(
        [cmake, "--preset", preset_name, f"-DCMAKE_MAKE_PROGRAM={ninja}"],
        cwd=os.getcwd()
    )
    
    if configure_result.returncode != 0:
        print("❌ Configuration failed!")
        sys.exit(1)
    
    print("\n🔨 Building project...")
    build_result = subprocess.run(
        [cmake, "--build", build_dir],
        cwd=os.getcwd()
    )
    
    if build_result.returncode != 0:
        print("❌ Build failed!")
        sys.exit(1)
    
    print(f"\n✅ Build completed successfully!")
    print(f"📁 Output directory: {build_dir}")

    if should_run:
        build_file = get_build_file()
        project_name = build_file["PROJECT_NAME"]

        if "wasm" not in build_file["PROJECT_PLATFORM"]: 
            if "windows" in build_file["PROJECT_PLATFORM"]:
                binary_name = f"{project_name}.exe"
            else:
                binary_name = project_name
            binary_path = Path(build_dir) / "src" / project_name / binary_name
            
            if not binary_path.exists():
                print(f"❌ Binary not found at {binary_path}")
                sys.exit(1)
            
            print(f"\n🚀 Running {binary_name}...")
            run_result = subprocess.run(
                [str(binary_path)] + (binary_args if binary_args else []),
                cwd=os.getcwd()
            )
            
            if run_result.returncode != 0:
                print(f"\n⚠️  Program exited with code {run_result.returncode}")
            else:
                print(f"\n✅ Program completed successfully!")
        else:
            if should_browser:
                from http.server import HTTPServer, SimpleHTTPRequestHandler
                import time
                import threading
                html_content = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <title>{project_name}</title>
                    <style>
                        html, body {{
                            height: 100%;
                            margin: 0;
                        }}
                        body {{
                            display: flex;
                            justify-content: center;  /* horizontal center */
                            align-items: center;      /* vertical center */
                            background-color: #111;   /* dark background */
                        }}
                        canvas {{
                            width: 99vw;   /* 90% of viewport width */
                            height: 99vh;  /* 90% of viewport height */
                            border: 2px solid #fff; /* optional: see edges */
                        }}
                    </style>
                </head>
                <body>
                    <canvas id="canvas" width="1600" height="1200"></canvas>
                    <script src="{project_name}.js"></script>
                </body>
                </html>
                """

                binary_path = Path(build_dir) / "src" / project_name
                os.chdir(binary_path)

                Path(os.path.join(binary_path, f"{project_name}.html")).write_text(html_content)

                # here write the html content to {project_name}.html file
                # and then serve in this port
                # open browser at http://localhost:3475/{project_name}.html
                port = 3475
                httpd = HTTPServer(("", port), SimpleHTTPRequestHandler)
                url = f"http://localhost:{port}/{project_name}.html"

                # open browser
                try:
                    if sys.platform == "win32":
                        os.system(f"start {url}")
                    elif sys.platform == "darwin":
                        os.system(f"open {url}")
                    else:
                        os.system(f"xdg-open {url}")
                except:
                    print("Autolaunching browser failed, just launch it yourself at:")

                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    httpd.shutdown()
                    pass
            else:
                js_file = Path(build_dir) / "src" / project_name / f"{project_name}.js"
                os.system(f"node {js_file}")


def handle_doctor(args):
    import json
    
    vcpkg_dir = get_vcpkg_dir()
    versions_dir = vcpkg_dir / "versions"
    
    if not versions_dir.exists():
        print("❌ vcpkg versions directory not found. Run 'kmake self-install' first.")
        sys.exit(1)
    
    packages_to_check = []
    if args.packages:
        packages_to_check = args.packages
    else:
        try:
            build_file = get_build_file()
            for project_name, project_detail in build_file["PROJECT_STRUCTURE"].items():
                if "deps" in project_detail:
                    for dep in project_detail["deps"].keys():
                        if dep not in packages_to_check:
                            packages_to_check.append(dep)
        except Exception as e:
            print("❌ Could not read dependencies from build.py")
            print("💡 Usage: kmake doctor <package1> <package2> ...")
            sys.exit(1)
    
    if not packages_to_check:
        print("ℹ️  No dependencies found in build.py")
        print("💡 Usage: kmake doctor <package1> <package2> ...")
        return
    
    print("\n📦 Checking package versions in vcpkg...\n")
    
    for package in packages_to_check:
        first_letter = package[0].lower()
        if first_letter == '-':
            first_letter = '-'
        
        version_file = versions_dir / (first_letter + '-') / f"{package}.json"
        
        if not version_file.exists():
            print(f"❌ {package}: Not found in vcpkg")
            continue
        
        try:
            data = json.loads(version_file.read_text())
            versions_list = data.get("versions", [])
            
            if not versions_list:
                print(f"⚠️  {package}: No versions available")
                continue
            
            version_groups = {}
            for v in versions_list:
                version_str = v.get("version", v.get("version-string", "."))
                parts = version_str.split('.')
                major = parts[0] if parts else "."
                
                if major not in version_groups:
                    version_groups[major] = []
                version_groups[major].append(version_str)
            
            display_parts = []
            for major in sorted(version_groups.keys(), reverse=True):
                group = version_groups[major]
                if len(group) <= 3:
                    display_parts.append(", ".join(group))
                else:
                    display_parts.append(f"{group[0]}, {group[1]}, ... {group[-1]}")
            
            version_display = " | ".join(display_parts[:5]) 
            if len(version_groups) > 5:
                version_display += " | ..."
            
            print(f"✅ {package}: {version_display}")
            
        except Exception as e:
            print(f"❌ {package}: Error reading version file - {e}")
    
    print()

def handle_init(args):
    clear_screen()
    if args.here != ".":
        print("✅ Initializing Project by Making a Directory ....")
    else:
        print("✅ Initializing Project HERE....")

    print_header("🚀 kmake - C/C++ Project Initialization")
    project_name = get_input("Project name", "my_project")
    
    if args.here != ".":
        os.mkdir(os.path.join(os.getcwd(), project_name))
        os.chdir(os.path.join(os.getcwd(), project_name))
    
    print("Now edit the build.py file and setup your project")

    text = f'PROJECT_NAME = "{project_name}"'
    text += r"""PROJECT_LANGUAGE = "C++" # "C" or "C++"
PROJECT_LANGUAGE_STANDARD = "20" # 11, 14, 17, 20 etc for C++ and 89, 99, 11, 23 etc for C
PROJECT_COMPILER = "clang" # "clang" or "gcc" [whichever is installed/preferred] or "emcc" (for web-assembly)
PROJECT_STANDARD_LIBRARY = "default" # can change to "none" for no std library
PROJECT_PLATFORM = "x64-windows" # Can be any one from x64-windows, x64-windows-static, x64-linux (untested), x64-linux-dynamic (untested), x64-osx(untested), arm64-android (will be supported later), wasm32-emscripten [VCPKG triplets]
PROJECT_STRUCTURE = { # remember everywhere CURLY braces
    # This  is just an example, modify the following for your project.
    "kmakelib" : {
        "type" : "static-library", # can be "binary", "dynamic-library", OR "static-library"
        "deps" : {
            "lua" : {
                "version" : "5.4.7" # can omit this to use the latest version, so you have to "lua" : {}
            },
        }
    },

    # The order of the projects is the order in which each should compile
    # So the last one is going to be your "main project"
    # For example if you want to make a game engine, above will be your engine library and below will be your game(s).
    # if your project is really simple just create one entry like below, and remove other things in this PROJECT_STRUCTURE dictionary

    "kmake" : {
        "type" : "binary",
        "deps" : {
            "kmakelib" : {},
            "lua" : {
                "version" : "5.4.7" 
            },        
            "sol2" : {
                "version" : "3.5.0"
            }
        }
    }
}
# Now run "kmake run"  in order to setup the files and get started,
# use "kmake unit <project name> <unit name>" to create header + source file pair, like "kmake unit kmake main" will generate main.h/hpp and main.c/cpp respectively
# run "kmake build run" in order to run your project(make sure to add a main function in src/file.cpp)                               
"""
    Path("build.py").write_text(text)

def handle_unit(arg):
    build_file = get_build_file()
    project_name = arg.project_name
    unit_name = arg.unit_name
    if build_file["PROJECT_LANGUAGE"] == "C++":
        header_guard = f"_{unit_name.upper()}_HPP_"
        file1 = os.path.join("src", project_name, "include", project_name, f"{unit_name}.hpp")
        file2 = os.path.join("src", project_name, "src", f"{unit_name}.cpp")
        header_text = f"""#ifndef {header_guard}
#define {header_guard}

namespace {project_name} {{

}}

#endif // {header_guard}
"""
        Path(file1).write_text(header_text)
        Path(file2).write_text(f"""#include <{project_name}/{unit_name}.hpp>""")
    else:
        header_guard = f"_{unit_name.upper()}_H_"
        file1 = os.path.join("src", project_name, "include", project_name, f"{unit_name}.h")
        file2 = os.path.join("src", project_name, "src", f"{unit_name}.c")
        header_text = f"""#ifndef {header_guard}
#define {header_guard}

#endif // {header_guard}
"""
        Path(file1).write_text(header_text)
        Path(file2).write_text(f"""#include <{project_name}/{unit_name}.h>""")

def main():
    if platform.system() != "Windows":
        required_tools = ["unzip", "zip", "tar", "pkg-config", "autoconf", "automake"]

        for tool in required_tools:
            if shutil.which(tool) is None:
                print(f"Error: any of {required_tools} is not installed. Please install all of them first.")
                sys.exit(1)


    parser = argparse.ArgumentParser(
        description="A helper script for managing C++ development environments."
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    install_parser = subparsers.add_parser(
        'self-install', 
        help='Install kmake (myself), the latest CMake, Ninja and vcpkg to the user directory.'
    )
    install_parser.set_defaults(func=handle_self_install)

    init_parser = subparsers.add_parser(
        'init', 
        help='Initialize Project'
    )
    init_parser.set_defaults(func=handle_init)
    init_parser.add_argument(
        "here",             
        nargs="?",          
        default="not_here", 
        help="If you specify '.' then project will be initialized here, but you can make a project by writing a 'build.py' and running 'kmake run' as well"
    )

    run_parser = subparsers.add_parser(
        'run',
        help='Run build.py'
    )
    run_parser.set_defaults(func=handle_run)

    build_parser = subparsers.add_parser(
        'build',
        help="Builds the project with Ninja, If you want to build specific preset use 'kmake build ask', and then it will ask for specific preset from CMakePresets.json to be built"
    )
    build_parser.set_defaults(func=handle_build)
    build_parser.add_argument(
        'options',
        nargs='*',
        help='Options: "ask" to select preset, "run" to execute after building, followed by binary arguments'
    )

    doctor_parser = subparsers.add_parser(
        'doctor',
        help='List available package versions from vcpkg'
    )
    doctor_parser.add_argument(
        'packages',
        nargs='*',
        help='Specific packages to check (if none provided, checks all dependencies from build.py)'
    )
    doctor_parser.set_defaults(func=handle_doctor)

    unit_parser = subparsers.add_parser(
        'unit',
        help='This will add a translation Unit to your project'
    )
    unit_parser.add_argument("project_name", help="Name of the project")
    unit_parser.add_argument("unit_name", help="Name of the unit to add")
    unit_parser.set_defaults(func=handle_unit)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()