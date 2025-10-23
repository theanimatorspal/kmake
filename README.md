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

**kmake** is a lightweight single file (Will always be single-file) Python-based tool that eliminates the pain of setting up C/C++ projects. It automatically installs CMake, vcpkg, ninja, manages dependencies, generates build configurations, and lets you focus on writing code instead of fighting build systems.

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
- ✅ Add Ninja to PATH? (default: yes)

> 💡 **Pro Tip:** Say "no" to keep your existing installations untouched. kmake will use its own isolated tools in `~/.kmake/`

> 💡 **Pro Tip2:** If you don't want any hassle just press enter in every prompt

**Important:** Restart your terminal after installation!

---

### Step 2: Create Your First Project

```bash
# Initialize a new C++ project
kmake init

# Or initialize in the current directory
kmake init .
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
PROJECT_PLATFORM = "x64-windows" # basically a vcpkg triplet. Can be any one from vcpkg's supported triplets like x64-windows, x64-windows-static, x64-linux (untested), x64-linux-dynamic (untested), x64-osx(untested), arm64-android (will be supported later), wasm32-emscripten (untested), etc.
PROJECT_STRUCTURE = {
    "kmakelib" : {
        "type" : "static-library",
        "deps" : {
            "lua" : {
                "version" : "5.4.7" 
            },
        }
    },
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
```

If version is not given, like "lua" : {} then latest package is going to be installed. Remember that you can only compile one project at a time (so if one of your programs uses old lua and another uses new lua then you cannot compile those in parallel, you have to compile one)


Also if you use wasm32-emscripten as the platform then make sure to select C++ standard <=17, it has issues with C++ standard >20.
Suggestion is -> Use C++17 for best of both worlds (compatibility and latest features of C++). Or just write in C (Any Standard).
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

If you use VSCode, then install these extensions:

* C/C++ Extension Pack From Microsoft
* Clangd

And Make sure to add this in your settings.json file (If you install Clangd, VSCode itself will prompt you for this).
` "C_Cpp.intelliSenseEngine": "disabled" `

Then run `kmake run` to generate appropriate files ready for build (will also install all packages specified in your build.py).

After that, just press "Build ⚙️" button you see at VSCode bottom left. It will build the package for you.

However if you want to build and run yourself, you can do `kmake build run <arguments to your binary>` this will compile and run the binary with the command line arguments you give to it, using the first preset in the generated CMakePresets.json (generally a debug build). If you want release then you can run `kmake build ask run <arguments to your binary>` then it will prompt which preset to build and run and from there you can select the appropriate option you'd like.

Note that arguments to your binary is not tested for now (for all platforms), will test it later.

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
- **LLVM** Just install LLVM from official website or package manager (Later, will integrate compilers + LLVM in this tool itself)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

- 🐛 Report bugs via GitHub Issues
- 💡 Suggest features or improvements
- 📝 Improve documentation
- 🔧 Submit pull requests

**Roadmap Ideas:**
- Template system (`kmake init --template sdl2-game`)
- Direct Integration with github for kmake based projects (similar to go's)
- Dependency version locking
- Automatic installation of various compilers

---

## 📜 License

MIT License – See `LICENSE` file for details

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
