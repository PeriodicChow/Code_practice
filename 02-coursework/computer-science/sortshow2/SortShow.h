// SortShow.h
#ifndef SORTSHOW_H
#define SORTSHOW_H
#include <windows.h>
#include <stdio.h>

const int N = 16;
const int STEP = 3;
const int BAR_W = 2;

extern HANDLE        hStdIn, hStdOut;
extern HMIDIOUT      hMidiOut;
extern unsigned char notes[8];
extern int           array0[N], array[N], temp[N];
extern int           col1, col2, top;

#define BAR_X(idx)   (col1 + (idx) * STEP)
#define BAR_BASE     (top + N + 2)

DWORD MidiOutMessage(HMIDIOUT hMidiOut, int iStatus, int iChannel, int iNote, int iVolume);

void Init();
void Quit();
void SetData(int flag = 3);
void ReSetData();
void Start();
void Finish();
void ShowData();

#ifndef swap
template <typename T>
void swap(T &a, T &b)
{
    T temp = a;
    a = b;
    b = temp;
}
#endif

void ShowChar(int x, int y, int bkcolor, int color, char ch);
void ShowText(int x, int y, int bkcolor, int color, const char *str);
void SWAP(int *a, int i, int j);
void ShowBar(int idx, int value, bool blinding = false);
void ShowBars(int idx1, int val1, int idx2, int val2, bool blinding = false);
void MoveBar(int src_idx, int value, int dst_idx);

double gettime(int restart = 0);

void Bubble_Sort(int *array, int length);
void Select_Sort(int *array, int length);
void Merge_Sort(int *array, int length);
void Quick_Sort(int *array, int length);

#endif
