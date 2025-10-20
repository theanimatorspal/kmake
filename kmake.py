#!python3
import os
import sys
import platform
import subprocess
import urllib.request
import json
import zipfile
import tarfile
import shutil
import tempfile
import argparse
import shutil
from pathlib import Path

"""

# ALL THE DATABASE and CONSTANT STRINGS should be here

"""


CMAKE_MINIMUM_REQUIRED_STRING = "cmake_minimum_required(VERSION 3.28)"

DATABASE = {
    "vulkan-all" : [
        "vulkan",
        "sdl2",
        "spirv-tools",
        "glslang",
        "spirv-cross",
        "freetype",
        "harfbuzz",
    ]
}

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
    
    subprocess.run([emsdk_script, "install", "latest"], cwd=emsdk_dir, shell=True, check=True)
    subprocess.run([emsdk_script, "activate", "latest"], cwd=emsdk_dir, shell=True, check=True)
    subprocess.run([emsdk_script, "activate", "--permanent"], cwd=emsdk_dir, shell=True, check=True)
    
    if should_add_to_path:
        add_to_path(emsdk_dir)
        add_to_path(emsdk_dir / "upstream" / "emscripten")
    
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
        ["git", "clone", "https://github.com/microsoft/vcpkg.git", str(vcpkg_dir), '--depth=1'], 
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
    src_dir = Path(__file__).resolve().parent
    if platform.system() == "Windows":
        target_dir = src_dir
    else:
        target_dir = src_dir

    add_to_path(target_dir)
    print(f"✅ Added {target_dir} to PATH")

def handle_self_install(args):
    print("🚀 Initializing setup...")
    base_dir = Path.home() / ".kmake"
    base_dir.mkdir(exist_ok=True)
    
    add_kmake_to_path = get_yes_no("Add kmake to PATH?", default=True)
    add_cmake_to_path = get_yes_no("Add CMake to PATH?", default=True)
    add_vcpkg_to_path = get_yes_no("Add vcpkg to PATH?", default=True)    
    add_emsdk_to_path = get_yes_no("Add Emsdk to PATH?", default=True)
    add_ninja_to_path = get_yes_no("Add Ninja to PATH? ⚠️ If not, You should already have Ninja installed and accesible from the path", default=True)

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

def run_vcpkg_command(args):
    vcpkg = get_local_vcpkg()
    process = subprocess.Popen(
        [vcpkg] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    output = ""
    for line in process.stdout:
        print(line, end="")  # 👈 stream live to stdout
        output += line       # 👈 also keep collecting it

    process.wait()
    return process.returncode, output


def install_vcpkg_package(name: str, project_name : str, system : str):
    print(f"⏳ Installing package {name}")
    triplet = system
    code, output = run_vcpkg_command(["install", f"{name}:{triplet}"])
    lines = [line.strip().replace("main", project_name) for line in output.splitlines() if line.strip().startswith(("find_", "target_"))]
    return "\n" + "\n".join(lines) + "\n\n"


def get_cmake_preset_file_string(
    compiler="clang",
    platform="x64-windows",
    android_toolchain="C:/AndroidSDK/ndk/26.3.11579264/build/cmake/android.toolchain.cmake",
    android_platform="android-31"
):
    vcpkg_toolchain = get_vcpkg_dir() / "scripts" / "buildsystems" / "vcpkg.cmake"
    
    compilers = {
        "clang": ("clang", "clang++"),
        "gcc": ("gcc", "g++")
    }
    c_compiler, cxx_compiler = compilers.get(compiler, ("clang", "clang++"))
    
    is_android = platform.startswith("arm") and "android" in platform
    is_web = "wasm" in platform or "emscripten" in platform
    
    base_cache = {
        "CMAKE_PRESET_NAME": "${presetName}",
        "CMAKE_TOOLCHAIN_FILE": str(vcpkg_toolchain).replace("\\", "/")
    }
    
    if is_android:
        base_cache.update({
            "CMAKE_SYSTEM_NAME": "Android",
            "CMAKE_ANDROID_NDK": android_toolchain.split("/build/cmake")[0],
            "CMAKE_ANDROID_STL_TYPE": "c++_shared",
            "VCPKG_TARGET_TRIPLET": platform
        })
    elif is_web:
        base_cache["VCPKG_TARGET_TRIPLET"] = platform
    else:
        base_cache.update({
            "CMAKE_C_COMPILER": c_compiler,
            "CMAKE_CXX_COMPILER": cxx_compiler
        })
    
    arch = "x64" if "x64" in platform or "arm64" in platform else "x86"
    strategy = "" if is_web or is_android else f''',
      "architecture": {{
        "value": "{arch}",
        "strategy": "external"
      }}'''
    
    build_types = ["Debug", "Release", "RelWithDebInfo", "MinSizeRel"]
    presets = []
    
    for build_type in build_types:
        preset_name = f"{platform}-{build_type.lower()}"
        display_name = f"{platform} {build_type}"
        
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
    cmake_start = f"""
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)  
"""
    if platform.system() == "Windows":
        cmake_start += """ 

if(MSVC)
if(POLICY CMP0141)
cmake_policy(SET CMP0141 NEW)
set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()
endif()
cmake_policy(SET CMP0069 NEW) 
set(CMAKE_POLICY_DEFAULT_CMP0069 NEW)

        """

        cmake_start += """
if(WIN32)
    add_definitions(-DWIN32_LEAN_AND_MEAN -DNOMINMAX -D_CRT_SECURE_NO_WARNINGS -D_SDL_MAIN_HANDLED)
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
    Path("CMakePresets.json").write_text(get_cmake_preset_file_string(compiler=build_file["PROJECT_COMPILER"], platform=build_file["PROJECT_PLATFORM"]))
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
            raise("You have to specify the type - either binary, static-library or dynamic-library")

        if build_file["PROJECT_LANGUAGE"] == "C++":
            cmake_text+=f"""
PrecompileStdHeaders({project_name})
"""
        try:
            for dep, dep_detail in project_detail["deps"].items():
                if dep not in project_names:
                    cmake_text += install_vcpkg_package(dep, project_name, build_file["PROJECT_PLATFORM"])
        except Exception as e:
            pass

        try:
            if "deps" in project_detail:
                first = True
                for dep in project_detail["deps"].items():
                    if dep in project_names:
                        if first:
                            cmake_text += "target_link_libraries("
                            first = False
                        cmake_text += f" {dep}"
                if not first:
                    cmake_text += ")\n"

        except Exception as e:
            pass


        if is_main_project:
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
"""
            if build_file["PROJECT_LANGUAGE"] == "C++":
                cmake_text += f"""set(CMAKE_CXX_STANDARD {build_file["PROJECT_LANGUAGE_STANDARD"]})
set(CMAKE_CXX_STANDARD_REQUIRED ON)
"""
            for project_name in project_names:
                cmake_text += f"""
include_directories("src/{project_name}/include")
add_subdirectory("src/{project_name}")
"""
            cmake_text += f""""""
            Path("CMakeCommons.cmake").write_text(get_cmake_default_fill_string())
            Path("CMakeLists.txt").write_text(cmake_text)

def handle_init(args):
    clear_screen()
    print_header("🚀 kmake - C/C++ Project Initialization")
    project_name = get_input("Project name", "my_project")
    project_language = get_choice("Project Language", ["C", "C++"])
    project_compiler = get_choice("Project Compiler", ["clang", "gcc"])
    if project_language == "C":
        project_language_standard = get_choice("C Language Standard", ["89", "99", "11", "17"])
    if project_language == "C++":
        project_language_standard = get_choice("C++ Language Standard", ["03", "11", "14", "20", "23"])
    
    if "here" not in args:
        os.mkdir(os.path.join(os.getcwd(), project_name))
        os.chdir(os.path.join(os.getcwd(), project_name))
    
    
    Path("build.py").write_text(f"""
PROJECT_NAME = "{project_name}"
PROJECT_LANGUAGE = "{project_language}"
PROJECT_LANGUAGE_STANDARD = "{project_language_standard}"
PROJECT_COMPILER = "{project_compiler}"
PROJECT_PLATFORM = "x64-windows" # basically a vcpkg triplet. Can be any one from vcpkg's supported triplets like x64-windows, x64-windows-static, x64-linux (untested), x64-linux-dynamic (untested), x64-osx(untested), arm64-android (will be supported later), wasm32-emscripten, etc.
PROJECT_STRUCTURE = {{ }}
 """)

    print(f"\nProject name: {project_name} Created, fill the PROJECT_STRUCTURE in build.py, see github for reference")

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
        file2 = os.path.join("src", project_name, "include", f"{unit_name}.c")
        header_text = f"""#ifndef {header_guard}
#define {header_guard}

namespace {project_name} {{

}}

#endif // {header_guard}
"""
        Path(file1).write_text(header_text)
        Path(file2).write_text(f"""#include <{project_name}/{unit_name}.h>""")

def main():
    parser = argparse.ArgumentParser(
        description="A helper script for managing C++ development environments."
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    install_parser = subparsers.add_parser(
        'self-install', 
        help='Install kmake, the latest CMake, and vcpkg to the user directory.'
    )
    install_parser.set_defaults(func=handle_self_install)

    init_parser = subparsers.add_parser(
        'init', 
        help='Initialize Project'
    )
    init_parser.set_defaults(func=handle_init)
    init_parser.add_argument("here")

    run_parser = subparsers.add_parser(
        'run',
        help='Run build.py'
    )
    run_parser.set_defaults(func=handle_run)

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