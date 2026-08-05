#include "debug.h"

extern "C" __declspec(dllexport)
void OnStart()
{
    Print("start");
}

extern "C" __declspec(dllexport)
void OnStop()
{
    Print("start");
}