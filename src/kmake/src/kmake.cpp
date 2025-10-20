#include <sol/sol.hpp>
#include <kmake/kmake.hpp>

int main() {
    sol::state state;
    state.open_libraries();
    state.safe_script(R"""(
        print("Hello World!")
)""");
    return 0;
}