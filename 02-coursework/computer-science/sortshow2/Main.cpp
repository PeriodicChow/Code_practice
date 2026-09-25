// Main.cpp
#include "SortShow.h"
#include <stdlib.h>
#include <time.h>
#include <conio.h>

int main()
{
    char text[100];
    const char *str[] = {
        "1 ---- Display raw data(D)",
        "2 ---- Bubble sort....(B)",
        "3 ---- Selection sort.(S)",
        "4 ---- Merge sort.....(M)",
        "5 ---- Quick sort.....(Q)",
        "0 ---- Exit.........(ESC)",
        "Select: "
    };
    int choice, n = sizeof(str) / sizeof(*str);

    srand((unsigned int)time(NULL));

    Init();

    while (true)
    {
        SetConsoleTitleA("SortShow - Sorting Algorithm Visualization");
        system("cls");
        for (int i = 0; i < n; i++)
            ShowText(20, i + 2, 0, 7, str[i]);
        choice = getch();
        if (choice == 27 || choice == '0')
            break;

        switch (choice)
        {
        case '1':
        case 'd':
        case 'D':   ShowText(2, 10, 0, 7, "1.Increase; 2.Decrease; 3.Random : ");
                    SetData(getch() - '0');
                    system("cls");
                    ShowData();                 break;
        case '2':
        case 'b':
        case 'B':   SetConsoleTitleA("Bubble Sorting");
                    Start();
                    Bubble_Sort(array, N);
                    Finish();                   break;
        case '3':
        case 's':
        case 'S':   SetConsoleTitleA("Selection Sorting");
                    Start();
                    Select_Sort(array, N);
                    Finish();                   break;
        case '4':
        case 'm':
        case 'M':   SetConsoleTitleA("Merge Sorting");
                    Start();
                    Merge_Sort(array, N);
                    Finish();                   break;
        case '5':
        case 'q':
        case 'Q':   SetConsoleTitleA("Quick Sorting");
                    Start();
                    Quick_Sort(array, N);
                    Finish();                   break;
        }
        sprintf(text, "Press Enter to continue...");
        ShowText(79 - (int)strlen(text), BAR_BASE + 4, 0, 7, text);
        while (getch() != '\r')
            ;
    }
    Quit();
    return 0;
}
