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

def install_cmake(base_dir: Path) -> Path:
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
    
    add_to_path(cmake_dir / "bin")
    return cmake_dir

def install_vcpkg(base_dir: Path) -> Path:
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
    
    add_to_path(vcpkg_dir)
    return vcpkg_dir

def install_self():
    src_file = Path(__file__).resolve()
    
    if platform.system() == "Windows":
        target_dir = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "kmake"
    else:
        target_dir = Path.home() / ".local" / "bin"
        
    target_dir.mkdir(parents=True, exist_ok=True)
    dst_file = target_dir / ("kmake.py" if platform.system() == "Windows" else "kmake")
    
    shutil.copy(src_file, dst_file)
    if platform.system() != "Windows":
        dst_file.chmod(0o755)

    add_to_path(target_dir)
    print(f"✅ kmake installed to: {dst_file}")

def handle_install(args):
    print("🚀 Initializing setup...")
    base_dir = Path.home() / ".kmake"
    base_dir.mkdir(exist_ok=True)
    
    install_self()
    cmake_dir = install_cmake(base_dir)
    vcpkg_dir = install_vcpkg(base_dir)
    
    print("\n🎉 Installation Complete!")
    print(f"CMake installed at: {cmake_dir}")
    print(f"vcpkg installed at: {vcpkg_dir}")
    run_vcpkg_command(["integrate", "install"])

    print("\nIMPORTANT: You must restart your terminal for PATH changes to take effect.")

def get_cmake_dir():
    return Path.home() / ".kmake" / "cmake"

def get_vcpkg_dir():
    return Path.home() / ".kmake" / "vcpkg"


def run_vcpkg_command(args):
    vcpkg = shutil.which("vcpkg")
    install_vcpkg(Path.home() / ".kmake")
    process = subprocess.run(
        ["vcpkg"] + args,
        check=False,
        text=True,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    return process.returncode

def get_cmake_preset_file_string(
    sourceDir="{sourceDir}",
    presetName="{presetName}",
    compiler="clang",
    android_toolchain="C:/AndroidSDK/ndk/26.3.11579264/build/cmake/android.toolchain.cmake",
    android_platform="android-31"
):
    vcpkg_toolchain= get_vcpkg_dir() / "scripts" / "buildsystems" / "vcpkg.cmake"
    if compiler == "clang":
        c_compiler = "clang"
        cxx_compiler = "clang++"

    if compiler == "gcc":
        c_compiler = "gcc"
        cxx_compiler = "g++"
    
    return f"""{{
  "version": 3,
  "configurePresets": [
    {{
      "name": "desktop-base",
      "hidden": true,
      "generator": "Ninja",
      "binaryDir": "${{{{sourceDir}}}}/out/build/${{{{presetName}}}}",
      "installDir": "${{{{sourceDir}}}}/out/install/${{{{presetName}}}}",
      "cacheVariables": {{
        "CMAKE_C_COMPILER": {c_compiler},
        "CMAKE_CXX_COMPILER": {cxx_compiler},
        "CMAKE_PRESET_NAME": "${{{{presetName}}}}",
        "CMAKE_TOOLCHAIN_FILE": "{vcpkg_toolchain}"
      }}
    }},
    {{
      "name": "x64-debug",
      "displayName": "x64 Debug",
      "inherits": "desktop-base",
      "architecture": {{
        "value": "x64",
        "strategy": "external"
      }},
      "cacheVariables": {{
        "CMAKE_BUILD_TYPE": "Debug"
      }}
    }},
    {{
      "name": "x64-release",
      "displayName": "x64 Release",
      "inherits": "x64-debug",
      "cacheVariables": {{
        "CMAKE_BUILD_TYPE": "Release"
      }}
    }},
    {{
      "name": "x64-release with debug",
      "displayName": "x64 Release DD",
      "inherits": "x64-release",
      "cacheVariables": {{
        "CMAKE_BUILD_TYPE": "RelWithDebInfo"
      }}
    }},
    {{
      "name": "x64-MinSizeRel",
      "displayName": "x64 Release MinSize",
      "inherits": "x64-release",
      "cacheVariables": {{
        "CMAKE_BUILD_TYPE": "MinSizeRel"
      }}
    }},
    {{
      "name": "x86-debug",
      "displayName": "x86 Debug",
      "inherits": "desktop-base",
      "architecture": {{
        "value": "x86",
        "strategy": "external"
      }},
      "cacheVariables": {{
        "CMAKE_BUILD_TYPE": "Debug"
      }}
    }},
    {{
      "name": "x86-release",
      "displayName": "x86 Release",
      "inherits": "x86-debug",
      "cacheVariables": {{
        "CMAKE_BUILD_TYPE": "Release"
      }}
    }},
    {{
      "name": "default",
      "hidden": true,
      "binaryDir": "${{{{sourceDir}}}}/out/build/${{{{presetName}}}}",
      "installDir": "${{{{sourceDir}}}}/out/install/${{{{presetName}}}}",
      "generator": "Ninja"
    }},
    {{
      "name": "android",
      "hidden": true,
      "displayName": "testandroid",
      "inherits": "default",
      "cacheVariables": {{
        "CMAKE_SYSTEM_NAME": "Android",
        "ANDROID_PLATFORM": "{android_platform}",
        "ANDROID": true,
        "CMAKE_TOOLCHAIN_FILE": "{android_toolchain}",
        "CMAKE_PRESET_NAME": "${{{{presetName}}}}"
      }}
    }},
    {{
      "name": "android-x86",
      "displayName": "Android x86",
      "inherits": "android",
      "cacheVariables": {{
        "CMAKE_ANDROID_ARCH_ABI": "x86"
      }}
    }},
    {{
      "name": "android-x86_64 Debug",
      "displayName": "Android x86_64 Debug",
      "inherits": "android",
      "cacheVariables": {{
        "CMAKE_ANDROID_ARCH_ABI": "x86_64",
        "CMAKE_BUILD_TYPE": "Debug"
      }}
    }},
    {{
      "name": "android-x86_64 Release",
      "displayName": "Android x86_64 Release",
      "inherits": "android",
      "cacheVariables": {{
        "CMAKE_ANDROID_ARCH_ABI": "x86_64",
        "CMAKE_BUILD_TYPE": "Release"
      }}
    }},
    {{
      "name": "android-armeabi-v7a",
      "displayName": "Android armeabi-v7a",
      "inherits": "android",
      "cacheVariables": {{
        "CMAKE_ANDROID_ARCH_ABI": "armeabi-v7a"
      }}
    }},
    {{
      "name": "android-arm64-v8a",
      "displayName": "Android arm64-v8a Debug",
      "inherits": "android",
      "cacheVariables": {{
        "CMAKE_ANDROID_ARCH_ABI": "arm64-v8a",
        "CMAKE_BUILD_TYPE": "Debug",
        "ANDROID_ABI": "arm64-v8a"
      }}
    }},
    {{
      "name": "android-arm64-v8a Release",
      "displayName": "Android arm64-v8a Release",
      "inherits": "android",
      "cacheVariables": {{
        "CMAKE_ANDROID_ARCH_ABI": "arm64-v8a",
        "CMAKE_BUILD_TYPE": "Release",
        "ANDROID_ABI": "arm64-v8a"
      }}
    }}
  ]
}}"""

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

def run_build_py():
    namespace = {}
    code = compile(Path("build.py").read_text(), "build.py", "exec")
    exec(code, namespace)
    cmake_start = f"""
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)  

"""
    if platform.system() == "Windows":
        programming_for_windows = get_yes_no("Would you like me to make windows not mess up with your min, max and Other stuff? Just say yes if you don't know about it or ask LLM. (Adding Defs WIN32_LEAN_AND_MEAN NOMINMAX _CRT_SECURE_NO_WARNINGS _SDL_MAIN_HANDLED)")
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
        if programming_for_windows:
            cmake_start += """
            if(WIN32)
                add_definitions(-DWIN32_LEAN_AND_MEAN -DNOMINMAX -D_CRT_SECURE_NO_WARNINGS -D_SDL_MAIN_HANDLED)
            endif()
            """


def handle_init(args):
    clear_screen()
    print_header("🚀 kmake - C/C++ Project Initialization")
    project_name = get_input("Project name", "my_project")
    project_type = get_choice("Project type", ["binary", "static-library", "shared-library"])
    project_language = get_choice("Project Language", ["C", "C++"])
    project_compiler = get_choice("Project Compiler", ["clang", "gcc"])
    if project_language == "C":
        project_language_standard = get_choice("C Language Standard", ["89", "99", "11", "17"])
    if project_language == "C++":
        project_language_standard = get_choice("C++ Language Standard", ["03", "11", "14", "20", "23"])
    
    Path("CMakePresets.json").write_text(get_cmake_preset_file_string(compiler=project_compiler))
    
    Path("build.py").write_text(f"""
PROJECT_NAME = "{project_name}"
PROJECT_TYPE = "{project_type}"
PROJECT_LANGUAGE = "{project_language}"
PROJECT_LANGUAGE_STANDARD = "{project_language_standard}"
PROJECT_LIBRARIES = []
 """)

    print(f"\nProject name: {project_name}")
    print(f"Project type: {project_type}")

def main():
    parser = argparse.ArgumentParser(
        description="A helper script for managing C++ development environments."
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    install_parser = subparsers.add_parser(
        'self-install', 
        help='Install kmake, the latest CMake, and vcpkg to the user directory.'
    )
    install_parser.set_defaults(func=handle_install)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ An error occurred: {e}", file=sys.stderr)
        sys.exit(1)