#include <sol/sol.hpp>

int main() {
    sol::state s;
    s.open_libraries();
    s.script("print('hello world')");
}