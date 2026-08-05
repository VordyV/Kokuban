#include "debug.h"

void Print(string value)
{
    std::string text = std::format("[{}] {}\n", TITLE, value);
    OutputDebugStringA(text.c_str());
}
