// Sorts_Show.cpp
#include "SortShow.h"
#include <conio.h>

void Bubble_Sort(int *array, int length)
{
    bool swapped;
    ShowText(BAR_X(0) - 2, BAR_BASE + 1, 0, 15, "^");
    ShowText(BAR_X(length - 1) + 1, BAR_BASE + 1, 0, 15, "^");
    for (int i = 1; i < length; i++)
    {
        swapped = false;
        for (int j = 0; j < length - i; j++)
        {
            if (array[j] > array[j + 1])
            {
                SWAP(array, j, j + 1);
                swapped = true;
            }
            else
                ShowBars(j, array[j], j + 1, array[j + 1]);
        }
        if (!swapped)
        {
            ShowText(BAR_X(length - i) + 1, BAR_BASE + 1, 0, 15, "  ");
            break;
        }
        ShowText(BAR_X(length - i) + 1, BAR_BASE + 1, 0, 15, "  ");
        ShowText(BAR_X(length - i - 1) + 1, BAR_BASE + 1, 0, 15, "^");
    }
    ShowText(BAR_X(1) + 1, BAR_BASE + 1, 0, 15, "  ");
    ShowText(BAR_X(0) - 2, BAR_BASE + 1, 0, 15, "  ");
}

void Select_Sort(int *array, int length)
{
    int left = 0, right = length - 1;
    int minIndex, maxIndex;

    ShowText(BAR_X(length - 1) + 1, BAR_BASE + 1, 0, 15, "^ ");
    while (left < right)
    {
        minIndex = left;
        maxIndex = left;
        ShowText(BAR_X(left) - 2, BAR_BASE + 1, 0, 15, "^");
        ShowText(BAR_X(left), BAR_BASE + 1, 0, 15, "mn");
        ShowText(BAR_X(right), BAR_BASE + 1, 0, 15, "mx");
        for (int i = left + 1; i <= right; i++)
        {
            ShowBars(i, array[i], minIndex, array[minIndex]);
            if (array[i] < array[minIndex])
            {
                ShowText(BAR_X(minIndex), BAR_BASE + 1, 0, 15, "  ");
                minIndex = i;
                ShowText(BAR_X(minIndex), BAR_BASE + 1, 0, 15, "mn");
            }
            ShowBars(i, array[i], maxIndex, array[maxIndex]);
            if (array[i] > array[maxIndex])
            {
                ShowText(BAR_X(maxIndex), BAR_BASE + 1, 0, 15, "  ");
                maxIndex = i;
                ShowText(BAR_X(maxIndex), BAR_BASE + 1, 0, 15, "mx");
            }
        }
        if (minIndex != left)
            SWAP(array, minIndex, left);
        if (maxIndex == left)
            maxIndex = minIndex;
        if (maxIndex != right)
            SWAP(array, maxIndex, right);
        ShowText(BAR_X(minIndex), BAR_BASE + 1, 0, 15, "  ");
        ShowText(BAR_X(maxIndex), BAR_BASE + 1, 0, 15, "  ");
        ShowText(BAR_X(left) - 2, BAR_BASE + 1, 0, 15, "  ");
        ShowText(BAR_X(right), BAR_BASE + 1, 0, 15, "  ");
        left++;
        right--;
    }
    if (left == right)
    {
        ShowText(BAR_X(left) - 2, BAR_BASE + 1, 0, 15, "^");
        ShowText(BAR_X(left) - 2, BAR_BASE + 1, 0, 15, "  ");
    }
    ShowText(BAR_X(length - 1) + 1, BAR_BASE + 1, 0, 15, "   ");
}

void Merge_Sort(int *a, int size)
{
    if (size <= 1)
        return;
    if (size == 2)
    {
        if (a[0] > a[1])
            SWAP(a, 0, 1);
        else
            ShowBars(a - array, a[0], a - array + 1, a[1]);
        return;
    }
    int i = 0, j = 0, k = 0, len1 = size / 2, len2 = size - size / 2;
    int *b = a + len1;
    int a_offset = a - array;
    Merge_Sort(a, len1);
    Merge_Sort(b, len2);

    ShowText(BAR_X(a_offset) - 2, BAR_BASE + 1, 0, 15, "^");
    ShowText(BAR_X(a_offset + len1) - 2, BAR_BASE + 1, 0, 15, "^");
    ShowText(BAR_X(a_offset + size - 1) + 1, BAR_BASE + 1, 0, 15, "^");

    for (i = 0; i < len1; i++)
    {
        MoveBar(a_offset + i, a[i], N + 1 + i);
        temp[i] = a[i];
    }
    getch();

    i = j = k = 0;
    for (i = j = 0; i < len1 && j < len2; k++)
    {
        if (temp[i] <= b[j])
        {
            MoveBar(N + 1 + i, temp[i], a_offset + k);
            a[k] = temp[i++];
        }
        else
        {
            MoveBar(a_offset + len1 + j, b[j], a_offset + k);
            a[k] = b[j++];
        }
        getch();
    }
    while (i < len1)
    {
        MoveBar(N + 1 + i, temp[i], a_offset + k);
        a[k++] = temp[i++];
    }
    while (j < len2)
    {
        MoveBar(a_offset + len1 + j, b[j], a_offset + k);
        a[k++] = b[j++];
    }
    ShowText(BAR_X(a_offset) - 2, BAR_BASE + 1, 0, 15, "  ");
    ShowText(BAR_X(a_offset + len1) - 2, BAR_BASE + 1, 0, 15, "  ");
    ShowText(BAR_X(a_offset + size - 1) + 1, BAR_BASE + 1, 0, 15, "  ");
}

void Quick_Sort(int *a, int size)
{
    char lStr[] = "{[<abcdefghijkl", rStr[] = "}]>ABCDEFGHIJKL";
    int left = 0, right = size - 1;
    static int layer = -1;
    int a_offset = a - array;

    layer++;
    if (size <= 1)
    {
        layer--;
        return;
    }
    ShowChar(BAR_X(a_offset) + layer, BAR_BASE + 1, 0, 15, lStr[layer]);
    ShowChar(BAR_X(a_offset + size - 1) - layer, BAR_BASE + 1, 0, 15, rStr[layer]);
    if (size == 2)
    {
        if (a[0] > a[1])
        {
            SWAP(a, 0, 1);
        }
        ShowText(BAR_X(a_offset + size - 1), BAR_BASE + 1, 0, 15, " ");
        layer--;
        return;
    }

    int mid = (left + right) / 2;
    if (a[mid] < a[left])
        SWAP(a, left, mid);
    if (a[right] < a[left])
        SWAP(a, left, right);
    if (a[right] < a[mid])
        SWAP(a, mid, right);
    if (mid != right)
        SWAP(a, mid, right);

    int pivot = a[right];
    ShowText(BAR_X(a_offset + size - 1), BAR_BASE + 1, 0, 15, "*");
    do
    {
        ShowText(BAR_X(a_offset + left), BAR_BASE + 1, 0, 15, "L");
        ShowText(BAR_X(a_offset + right) - 1, BAR_BASE + 1, 0, 15, "R");
        while (left < right && (a[left] <= pivot))
        {
            ShowBars(a_offset + left, a[left], a_offset + size - 1, pivot);
            ShowText(BAR_X(a_offset + left), BAR_BASE + 1, 0, 15, " ");
            left++;
            ShowText(BAR_X(a_offset + left), BAR_BASE + 1, 0, 15, "L");
        }
        while (left < right && (pivot <= a[right]))
        {
            ShowBars(a_offset + right, a[right], a_offset + size - 1, pivot);
            ShowText(BAR_X(a_offset + right) - 1, BAR_BASE + 1, 0, 15, " ");
            right--;
            ShowText(BAR_X(a_offset + right) - 1, BAR_BASE + 1, 0, 15, "R");
        }
        if (left < right)
        {
            SWAP(a, left, right);
        }
    } while (left < right);
    SWAP(a, left, size - 1);
    ShowChar(BAR_X(a_offset + left), BAR_BASE + 1, 0, 15, '-');
    ShowText(BAR_X(a_offset + left), BAR_BASE + 1, 0, 15, " ");
    ShowText(BAR_X(a_offset + right) - 1, BAR_BASE + 1, 0, 15, " ");

    ShowText(BAR_X(a_offset + size - 1), BAR_BASE + 1, 0, 15, " ");

    Quick_Sort(a, left);
    ShowChar(BAR_X(a_offset + left), BAR_BASE + 1, 0, 15, ' ');
    Quick_Sort(a + left + 1, size - left - 1);
    layer--;
}
