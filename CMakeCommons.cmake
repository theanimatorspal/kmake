
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)  
 

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
