#include "debug.h"

void Print(string value)
{
    std::string text = fmt::format("[{}] {}\n", TITLE, value);
    OutputDebugStringA(text.c_str());
}
