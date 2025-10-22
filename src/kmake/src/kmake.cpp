#include <sol/sol.hpp>

auto main() -> int {
    sol::state s;
    s.open_libraries();
    s.script("print('hello world')");
    int *x = new int[5];
    x[6] = 5;
    delete[] x;
}