#include "debug.h"

void Print(string value)
{
    std::string text = "[" + TITLE + "] " + value + "\n";
    OutputDebugStringA(text.c_str());
}
