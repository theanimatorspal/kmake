<h1 align="center">🔨 kmake</h1>
<p align="center"><i>UnFuck C/C++ Project Setup & Build Management</i></p>
<p align="center"><b>Platform Support:</b> Windows ✅ | Linux ✅ | macOS ✅</p>

<p align="center">
  <img src="https://img.shields.io/badge/cmake-automatic-blue?style=flat-square&logo=cmake" />
  <img src="https://img.shields.io/badge/vcpkg-integrated-green?style=flat-square&logo=vcpkg" />
  <img src="https://img.shields.io/badge/setup-minutes-orange?style=flat-square&logo=clockify" />
  <img src="https://img.shields.io/badge/dependencies-painless-success?style=flat-square&logo=dependabot" />
  <img src="https://img.shields.io/badge/boilerplate-eliminated-critical?style=flat-square&logo=deletedotme" />
</p>

---

## 🎯 What is kmake?

**kmake** is a lightweight Python-based tool that eliminates the pain of setting up C/C++ projects. It automatically installs CMake and vcpkg, manages dependencies, generates build configurations, and lets you focus on writing code instead of fighting build systems.

### ✨ Key Features

- 🚀 **One-Command Setup** – Install CMake, vcpkg, and configure everything in seconds
- 📦 **Automatic Dependency Management** – Just declare what you need, kmake handles vcpkg
- 🎨 **Project Templates** – Initialize new projects with sensible defaults instantly
- 🔧 **Smart Build Configuration** – Pre-configured CMake presets
- 🧩 **Module System** – Create translation units with proper headers/sources automatically
- 🌐 **Cross-Platform** – Works seamlessly on Windows, Linux, and macOS
- 🔒 **Isolated Installation** – Keeps your system clean, doesn't mess with existing tools

---

## 🚀 Quick Start

### Step 1: Install kmake

```bash
# Clone or download kmake
git clone https://github.com/yourusername/kmake.git
cd kmake

# Install kmake and its dependencies
python kmake.py self-install
```

You'll be asked:
- ✅ Add kmake to PATH? (default: yes)
- ✅ Add CMake to PATH? (default: yes)
- ✅ Add vcpkg to PATH? (default: yes)

> 💡 **Pro Tip:** Say "no" to keep your existing installations untouched. kmake will use its own isolated tools in `~/.kmake/`

**Important:** Restart your terminal after installation!

---

### Step 2: Create Your First Project

```bash
# Initialize a new C++ project
kmake init

# Or initialize in the current directory
kmake init here
```

You'll be prompted for:
- Project name
- Language (C or C++)
- Compiler (clang or gcc)
- Language standard (C++20, C++23, etc.)

This creates a `build.py` configuration file.

---

### Step 3: Configure Your Project

Edit the generated `build.py`:

```python
PROJECT_NAME = "kmake"
PROJECT_TYPE = "binary"
PROJECT_LANGUAGE = "C++"
PROJECT_LANGUAGE_STANDARD = "20"
PROJECT_COMPILER = "clang"
PROJECT_STRUCTURE = {
    "kmakelib" : {
        "type" : "static-library",
        "deps" : {
            "lua" : {
                "type" : "static-library"
            }
        }
    },
    "kmake" : {
        "type" : "binary",
        "deps" : {
            "kmakelib" : {},
            "lua" : {
                "type" : "static-library"
            },
            "sol2" : {
                "type" : "header-only-library"
            }
        }
    }
}
```

### Dependency Types
- `"static-library"` – Link statically
- `"dynamic-library"` – Link dynamically  
- `"header-only"` – Header-only libraries

---

### Step 4: Generate Build Files

```bash
kmake run
```

This will:
- ✅ Create `src/` directory structure
- ✅ Generate CMakeLists.txt for each module
- ✅ Install vcpkg dependencies automatically
- ✅ Create CMakePresets.json for easy building

---

### Step 5: Build Your Project

```bash
# Configure
cmake --preset x64-debug

# Build
cmake --build out/build/x64-debug

# Your executable will be at:
# out/build/x64-debug/src/game/game(.exe on Windows)
```

---

## 📖 Usage Guide

### Creating Translation Units

Add a new header/source pair to your project:

```bash
kmake unit <project_name> <unit_name>
```

**Example:**
```bash
kmake unit engine renderer
```

This creates:
- `src/engine/include/engine/renderer.hpp`
- `src/engine/src/renderer.cpp`

With proper include guards and namespace boilerplate already set up!

---

### Using Dependency Bundles

kmake includes pre-configured dependency bundles for common use cases:

```python
PROJECT_STRUCTURE = {
    "myapp": {
        "type": "binary",
        "deps": {
            "vulkan-all": {"type": "static-library"}  # Installs vulkan, SDL2, SPIRV, etc.
        }
    }
}
```

**Available Bundles:**
- `vulkan-all` – Vulkan + SDL2 + SPIRV-Tools + glslang + spirv-cross + freetype + harfbuzz

> 🔧 Want to add more bundles? Edit the `DATABASE` dictionary in `kmake.py`

---

### CMake Presets Included

kmake generates these build configurations automatically:

#### Desktop Builds
- `x64-debug` – 64-bit Debug
- `x64-release` – 64-bit Release
- `x64-release with debug` – Release with debug symbols
- `x64-MinSizeRel` – Minimum size release
- `x86-debug` / `x86-release` – 32-bit builds

#### Android Builds
- `android-arm64-v8a` – ARM 64-bit (Debug/Release)
- `android-x86_64` – x86 64-bit (Debug/Release)
- `android-armeabi-v7a` – ARM 32-bit
- `android-x86` – x86 32-bit

**To use Android presets**, edit the toolchain path in `build.py` if needed.

---

## 🎓 Complete Example

Here's a complete workflow for a Vulkan-based game:

```bash
# 1. Initialize project
kmake init
# Enter: "my_game", "C++", "clang", "20"

# 2. Edit build.py
cat > build.py << 'EOF'
PROJECT_NAME = "my_game"
PROJECT_LANGUAGE = "C++"
PROJECT_LANGUAGE_STANDARD = "20"
PROJECT_COMPILER = "clang"

PROJECT_STRUCTURE = {
    "renderer": {
        "type": "static-library",
        "deps": {
            "vulkan": {"type": "static-library"},
            "sdl2": {"type": "dynamic-library"},
            "glm": {"type": "header-only"}
        }
    },
    "game": {
        "type": "binary",
        "deps": {
            "renderer": {"type": "static-library"}
        }
    }
}
EOF

# 3. Generate build system
kmake run

# 4. Add game logic files
kmake unit game main_loop
kmake unit renderer vulkan_context

# 5. Build
cmake --preset x64-debug
cmake --build out/build/x64-debug

# 6. Run
./out/build/x64-debug/src/game/game
```

---

## 🛠️ Advanced Configuration

### Custom Precompiled Headers

kmake automatically sets up PCH for all standard library headers. To add your own:

Edit `CMakeCommons.cmake` after running `kmake run`:

```cmake
function(PrecompileStdHeaders TARGET_NAME)
    target_precompile_headers(${TARGET_NAME} PRIVATE
        # ... existing headers ...
        
        # Add your custom headers
        <vulkan/vulkan.hpp>
        <glm/glm.hpp>
        <sol/sol.hpp>
    )
endfunction()
```

### Using System-Installed Tools

If you already have CMake or vcpkg installed, kmake will use them automatically if they're in your PATH. Otherwise, it uses its isolated installation in `~/.kmake/`.

### Clean Reinstall

```bash
# Remove kmake's installed tools
rm -rf ~/.kmake/

# Reinstall
python kmake.py self-install
```

---

## 📋 Requirements

- **Python 3.8+**
- **Git** (for vcpkg installation)
- **A C/C++ compiler** (clang, gcc, or MSVC)
- **Ninja** (recommended, or use your platform's default generator)

---

## 🐛 Troubleshooting

### "vcpkg not found" after installation
**Solution:** Restart your terminal or run:
```bash
source ~/.bashrc  # or ~/.zshrc on macOS
```

### "CMake not found" when building
**Solution:** Make sure you restarted your terminal after `self-install`, or use the full path:
```bash
~/.kmake/cmake/bin/cmake --preset x64-debug
```

### Dependencies fail to install
**Solution:** Check your internet connection. vcpkg downloads packages from GitHub. You can also manually retry:
```bash
~/.kmake/vcpkg/vcpkg install <package-name>
```

### "Preset not found" error
**Solution:** Make sure you ran `kmake run` before configuring with CMake.

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

- 🐛 Report bugs via GitHub Issues
- 💡 Suggest features or improvements
- 📝 Improve documentation
- 🔧 Submit pull requests

**Roadmap Ideas:**
- Template system (`kmake init --template sdl2-game`)
- Direct Integration with github for kmake based projects
- Dependency version locking
- `kmake doctor` command for diagnostics
- More dependency bundles

---

## 📜 License

MIT License – See `LICENSE` file for details

---

## 🙏 Acknowledgments

Built on top of:
- [CMake](https://cmake.org/) – Cross-platform build system
- [vcpkg](https://vcpkg.io/) – C/C++ package manager by Microsoft
- [Ninja](https://ninja-build.org/) – Fast build system

---

<p align="center">
  <b>Stop fighting build systems. Start building software.</b><br/>
  Made with 💪 and ☕ for C++ developers who just want things to work
</p>

<p align="center">
  <a href="https://github.com/yourusername/kmake">⭐ Star on GitHub</a> •
  <a href="https://github.com/yourusername/kmake/issues">🐛 Report Bug</a> •
  <a href="https://github.com/yourusername/kmake/issues">💡 Request Feature</a>
</p>