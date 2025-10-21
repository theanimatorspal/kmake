#include <optional>

// Constructor of optional (monad) is basically like "unit" in monad terminology

std::optional<int> half(int x) {
    if (x % 2 == 0) return x / 2;
    return std::nullopt;
}

int main() {
    auto result = std::optional{20}
    .and_then(half) // Only supported in C++23
    .and_then(half)
    .and_then(half)
    .and_then(half)
    .and_then(half)
    .and_then(half)
    .and_then(half)
    .and_then(half)
    .and_then(half)
    .and_then(half);
}
