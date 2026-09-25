// SortString.cpp
/* 思考题
1.	strA、strB、strC、strD的字符串内容存储在什么区域？
	答：strA-栈；strB-只读数据区（字面常量）；strC-堆（new分配）；strD-堆。
2.	(1)如何比较字符串？(2)什么区域的字符串能交换内容？(3)不能交换内容时交换什么？
	答：(1)strcmp；(2)栈或堆上的可读写；(3)交换指针。
3.	GetStrings为什么是模板？两次调用T实例化成什么？
	答：strA是char[][20]，strB是char*[]，类型不同需模板适配。T分别为char[20]和char*。
4.	GetStrings/FreeStrings首参数为什么用引用型二级指针？不用会怎样？
	答：需修改调用者指针本身。不用引用则只改形参副本，导致内存泄漏(GetStrings)或野指针(FreeStrings)。
*/
#include <iostream>
#include <cstring>
using namespace std;

#define NUM 20

void BubbleA(char (*str)[NUM], int size)			// 数组指针
{
	int i, j;
	char temp[NUM];
	for(i=1; i<size; i++)
	{
		for(j=0; j<size-i; j++)
		{
			if(strcmp(str[j], str[j+1]) > 0)
			{
				strcpy(temp, str[j]);
				strcpy(str[j], str[j+1]);
				strcpy(str[j+1], temp);
			}
		}
	}
}

void BubbleB(char *str[], int size)					// 指针数组
{
	int i, j;
	char *temp;
	for(i=1; i<size; i++)
	{
		for(j=0; j<size-i; j++)
		{
			if(strcmp(str[j], str[j+1]) > 0)
			{
				temp = str[j];
				str[j] = str[j+1];
				str[j+1] = temp;
			}
		}
	}
}

template <typename T> void ShowStrings(const char *prompt, const T *strs, int n)
{
	if(n>0)
		cout << prompt << strs[0];
	for(int i=1; i<n; i++)
		cout << ", " << strs[i];
	cout << endl;
}

template <typename T> void GetStrings(char **&dest, const T *source, int n)
{
	dest = new char*[n];
	if(dest == NULL) return;
	int len;
	for(int i=0; i<n; i++)
	{
		len = strlen(source[i]);
		dest[i] = new char[len+1];
		strcpy(dest[i], source[i]);
	}
}

void FreeStrings(char **&strs, int n)
{
	if(strs!=NULL)
	{
		for(int i=0; i<n; i++)
			if(strs[i]!=NULL)
				delete [] strs[i];
		delete [] strs;
		strs = NULL;
	}
}

void TestString()
{
	char strA[][NUM]={"enter", "number", "size", "begin", "of", "cat", "case", "program", "certain", "a", "cake", "side"};
	char *strB[]    ={"enter", "number", "size", "begin", "of", "cat", "case", "program", "certain", "an", "cake", "side"};
	char **strC, **strD;
	int n1 = sizeof(strA)/sizeof(*strA), n2 = sizeof(strB)/sizeof(*strB);
	GetStrings(strC, strA, n1);
	GetStrings(strD, strB, n2);

	cout << "\n\t*** 多种不同存储方式的C-字符串数组的排序 ***" << endl;
	ShowStrings("\n原始数据: ", strA, n1);
	BubbleA(strA, n1);
	ShowStrings("排序结果: ",   strA, n1);
	
	ShowStrings("\n原始数据: ", strB, n2);
	BubbleB(strB, n2);
	ShowStrings("排序结果: ",   strB, n2);
	
	ShowStrings("\n原始数据: ", strC, n1);
	BubbleB(strC, n1);						// 调用一个排序函数执行排序操作
	ShowStrings("排序结果: ",   strC, n1);

	ShowStrings("\n原始数据: ", strD, n2);
	BubbleB(strD, n2);						// 调用一个排序函数执行排序操作
	ShowStrings("排序结果: ",   strD, n2);

	FreeStrings(strC, n1);
	FreeStrings(strD, n2);
}
