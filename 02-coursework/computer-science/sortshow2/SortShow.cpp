// SortShow.cpp
#include "SortShow.h"
#include <stdlib.h>
#include <time.h>
#include <conio.h>

HANDLE        hStdIn, hStdOut;
HMIDIOUT      hMidiOut;
unsigned char notes[8] = {48, 50, 52, 53, 55, 57, 59};
int           array0[N], array[N], temp[N];
int           col1 = 5, col2 = 0, top = 1;

DWORD MidiOutMessage(HMIDIOUT hMidiOut, int iStatus, int iChannel, int iNote, int iVolume)
{
    DWORD dwMessage = (iVolume << 16) | (iNote << 8) | iStatus | iChannel;
    return midiOutShortMsg(hMidiOut, dwMessage);
}

void Init()
{
    hStdIn  = GetStdHandle(STD_INPUT_HANDLE);
    hStdOut = GetStdHandle(STD_OUTPUT_HANDLE);
    DWORD fdwMode;
    fdwMode = ENABLE_WINDOW_INPUT | ENABLE_MOUSE_INPUT | ENABLE_EXTENDED_FLAGS;
    fdwMode &= ~ENABLE_QUICK_EDIT_MODE;
    fdwMode &= ~ENABLE_INSERT_MODE;
    SetConsoleMode(hStdIn, fdwMode);
    SetConsoleTitleA("SortShow - Sorting Algorithm Visualization");
    midiOutOpen(&hMidiOut, MIDIMAPPER, 0, 0, 0);
    col2 = col1 + (N + 2) * STEP;
    SetData(3);
}

void Quit()
{
    midiOutClose(hMidiOut);
    CloseHandle(hStdOut);
    CloseHandle(hStdIn);
}

void ShowChar(int x, int y, int bkcolor, int color, char ch)
{
    char str[2] = {ch, '\0'};
    ShowText(x, y, bkcolor, color, str);
}

void ShowText(int x, int y, int bkcolor, int color, const char *str)
{
    DWORD result;
    COORD coord = {(SHORT)x, (SHORT)y};
    SetConsoleCursorPosition(hStdOut, coord);
    SetConsoleTextAttribute(hStdOut, (WORD)(bkcolor << 4 | color));
    WriteConsoleA(hStdOut, str, (DWORD)strlen(str), &result, NULL);
}

void SetData(int flag)
{
    int i;
    switch (flag)
    {
    case 1: for (i = 0; i < N; i++) array0[i] = i + 1;              break;
    case 2: for (i = 0; i < N; i++) array0[i] = N - i;              break;
    default:for (i = 0; i < N; i++) array0[i] = i + 1;
            for (int k = N * N / 2; k > 0; k--)
                swap(array0[rand() % N], array0[rand() % N]);
            break;
    }
    for (int i = 0; i < N; i++)
        array[i] = array0[i];
}

void ReSetData()
{
    for (int i = 0; i < N; i++)
        array[i] = array0[i];
}

void ShowData()
{
    for (int i = 0; i < N; i++)
        ShowBar(i, array[i]);
}

void Start()
{
    ReSetData();
    SetConsoleTextAttribute(hStdOut, 7);
    system("cls");
    ShowData();

    ShowText(3, BAR_BASE + 2, 4, 14, "Press any key to start...");
    getch();
    MidiOutMessage(hMidiOut, 0x90, 0x09, 71, 127);
    ShowText(3, BAR_BASE + 2, 4, 14, "Sorting...              ");
    Sleep(1000);
}

void Finish()
{
    MidiOutMessage(hMidiOut, 0x90, 0x09, 46, 127);
    Sleep(200);
    ShowData();
    ShowText(3, BAR_BASE + 2, 14, 4, "Sorting complete! ");
    ShowText(0, BAR_BASE + 3, 0, 7, "");
}

static void DrawBarCells(int idx, int value, int attr)
{
    DWORD result;
    int x = BAR_X(idx);
    char bar[BAR_W + 1];
    for (int i = 0; i < BAR_W; i++) bar[i] = ' ';
    bar[BAR_W] = '\0';

    for (int r = 0; r < value; r++)
    {
        COORD coord = {(SHORT)x, (SHORT)(BAR_BASE - r - 1)};
        SetConsoleCursorPosition(hStdOut, coord);
        SetConsoleTextAttribute(hStdOut, (WORD)attr);
        WriteConsoleA(hStdOut, bar, BAR_W, &result, NULL);
    }
}

static void ClearBarCells(int idx, int value)
{
    DWORD result;
    int x = BAR_X(idx);
    char spaces[BAR_W + 1];
    for (int i = 0; i < BAR_W; i++) spaces[i] = ' ';
    spaces[BAR_W] = '\0';

    for (int r = 0; r < value; r++)
    {
        COORD coord = {(SHORT)x, (SHORT)(BAR_BASE - r - 1)};
        SetConsoleCursorPosition(hStdOut, coord);
        SetConsoleTextAttribute(hStdOut, 0);
        WriteConsoleA(hStdOut, spaces, BAR_W, &result, NULL);
    }
}

void ShowBar(int idx, int value, bool blinding)
{
    int color = (value == 15 ? 15 : value % 15);
    int note = notes[(value - 1) % 7] + 12 * ((value - 1) / 7);

    MidiOutMessage(hMidiOut, 0x90, 0, note, 127);

    while (true)
    {
        DrawBarCells(idx, value, 7);
        Sleep(50);
        DrawBarCells(idx, value, color << 4 | (15 - color));
        Sleep(50);
        if (!blinding)
            break;
        if (kbhit())
        {
            getch(); break;
        }
    }
    MidiOutMessage(hMidiOut, 0x80, 0, note, 127);
}

void ShowBars(int idx1, int val1, int idx2, int val2, bool blinding)
{
    int color1 = (val1 == 15 ? 15 : val1 % 15);
    int color2 = (val2 == 15 ? 15 : val2 % 15);
    int note1 = notes[(val1 - 1) % 7] + 12 * ((val1 - 1) / 7);
    int note2 = notes[(val2 - 1) % 7] + 12 * ((val2 - 1) / 7);

    while (true)
    {
        MidiOutMessage(hMidiOut, 0x90, 0, note1, 127);
        DrawBarCells(idx1, val1, 7);
        Sleep(100);
        DrawBarCells(idx1, val1, color1 << 4 | (15 - color1));
        Sleep(100);
        MidiOutMessage(hMidiOut, 0x80, 0, note1, 127);

        MidiOutMessage(hMidiOut, 0x90, 0, note2, 127);
        DrawBarCells(idx2, val2, 7);
        Sleep(100);
        DrawBarCells(idx2, val2, color2 << 4 | (15 - color2));
        Sleep(100);
        MidiOutMessage(hMidiOut, 0x80, 0, note2, 127);
        if (!blinding)
            break;
        if (kbhit())
        {
            getch(); break;
        }
    }
}

void MoveBar(int src_idx, int value, int dst_idx)
{
    int color = (value == 15 ? 15 : value % 15);
    int note = notes[(value - 1) % 7] + 12 * ((value - 1) / 7);

    MidiOutMessage(hMidiOut, 0x90, 0x09, 84, 127);
    MidiOutMessage(hMidiOut, 0x90, 0, note, 127);
    Sleep(100);

    DrawBarCells(src_idx, value, color << 4 | (15 - color));
    Sleep(200);
    ClearBarCells(src_idx, value);
    Sleep(100);
    DrawBarCells(dst_idx, value, color << 4 | (15 - color));

    char valStr[4];
    sprintf(valStr, "%2d", value);
    ShowText(BAR_X(dst_idx), BAR_BASE, 0, color, valStr);
    Sleep(50);
    ShowText(BAR_X(dst_idx), BAR_BASE, 0, 0, "  ");

    MidiOutMessage(hMidiOut, 0x80, 0, note, 127);
}

void SWAP(int *a, int i, int j)
{
    int i1 = a - array + i;
    int j1 = a - array + j;
    if (i1 < 0 || j1 < 0 || i1 >= N || j1 >= N)
        return;

    MidiOutMessage(hMidiOut, 0x90, 0x09, 38, 127);
    ShowBars(i1, array[i1], j1, array[j1], true);

    ClearBarCells(i1, array[i1]);
    ClearBarCells(j1, array[j1]);

    int temp_val = array[i1];
    array[i1] = array[j1];
    array[j1] = temp_val;

    MidiOutMessage(hMidiOut, 0x90, 0x09, 38, 127);
    ShowBars(i1, array[i1], j1, array[j1]);
}
