// Sorts.h		三种（冒泡、选择、快速）基本排序算法（升序）
#ifndef SORTS_H
#define SORTS_H
#include <iostream>
using namespace std;

double gettime(int restart=0);

template <typename T> void GetMemory(T *&data, T *&data0, int n)	
{																
	if(data0!=NULL) delete [] data0;								// 先释放原先的堆空间资源
	if(data !=NULL) delete [] data;
	data0 = new T[n];												// 重新申请堆空间资源
	data = new T[n];
}

template <typename T> void FreeMemory(T *&data, T *&data0)		
{
	if(data0!=NULL) delete [] data0;
	if(data !=NULL) delete [] data;
	data0 = data = NULL;											
}

template <typename T> void ReSet(T *data, const T *data0, int n)	//用于恢复原始数据以保证不同的排序算法处理完全相同的数据
{
	for(int i=0; i<n; i++)
		data[i] = data0[i];
}

template <typename T> bool Check(const T *a, int size)				//仅检验数组元素是否满足升序
{
	for(int i=1; i<size; i++)
		if(a[i-1] > a[i])
			return false;
	return true;
}

// 三种基本的优化后的排序算法
template <typename T> void Bubble(T *a, int size, long long &compareCount, long long &assignCount)	//冒泡排序
{
	compareCount=0;
	assignCount=0;
	T temp;											//定义一个局部变量，数据类型与形式数据类型相同
	bool swapped;
	for(int i=1; i<size; i++)							// 共进行size-1轮比较和交换
	{
		swapped=false;
		for(int j=0; j<size-i; j++)
		{
			compareCount++;
			if(a[j] > a[j+1])						
			{
				temp=a[j];							
				a[j]=a[j+1];
				a[j+1]=temp;
				assignCount+=3;
				swapped=true;
			}
		}
		if(!swapped) break;							// 未发生交换，提前退出
	}
}

template <typename T> void Select(T *a, int size, long long &compareCount, long long &assignCount)
{
	compareCount=0;
	assignCount=0;
	T temp;
	int left=0, right=size-1;
	while(left < right)
	{
		int minIndex=left, maxIndex=left;
		for(int i=left+1; i<=right; i++)
		{
			compareCount++;
			if(a[i] < a[minIndex])
				minIndex=i;
			compareCount++;
			if(a[i] > a[maxIndex])
				maxIndex=i;
		}
		if(minIndex != left)
		{
			temp=a[left];
			a[left]=a[minIndex];
			a[minIndex]=temp;
			assignCount+=3;
		}
		// 如果最大值位置被最小值交换影响，修正maxIndex
		if(maxIndex == left)
			maxIndex = minIndex;
		if(maxIndex != right)
		{
			temp=a[right];
			a[right]=a[maxIndex];
			a[maxIndex]=temp;
			assignCount+=3;
		}
		left++;
		right--;
	}
}

template <typename T> void Qsort(T *a, int size, long long &compareCount, long long &assignCount)	//快速排序（三数取中优化）
{
	if(size <= 1) return;
	int left=0, right=size-1;				
	int mid=(left+right)/2;
	T temp;
	//三数取中：把中位数交换到right位置
	if(a[mid] < a[left])
	{
		temp=a[mid];
		a[mid]=a[left];
		a[left]=temp;
		assignCount+=3;
	}
	if(a[right] < a[left])
	{
		temp=a[right];
		a[right]=a[left];
		a[left]=temp;
		assignCount+=3;
	}
	if(a[right] < a[mid])
	{
		temp=a[right];
		a[right]=a[mid];
		a[mid]=temp;
		assignCount+=3;
	}
	if(mid != right)
	{
		temp=a[mid];
		a[mid]=a[right];
		a[right]=temp;
		assignCount+=3;
	}
	T pivot=a[right];								// 选择最后一个值为分界值
	int i=left-1;
	for(int j=left; j<right; j++)
	{
		compareCount++;
		if(a[j] <= pivot)
		{
			i++;
			if(i != j)
			{
				temp=a[i];
				a[i]=a[j];
				a[j]=temp;
				assignCount+=3;
			}
		}
	}
	if(i+1 != right)
	{
		temp=a[i+1];
		a[i+1]=a[right];
		a[right]=temp;
		assignCount+=3;
	}
	int pivotIndex=i+1;								// 找到分界点 pivotIndex
	Qsort(a, pivotIndex, compareCount, assignCount);						
	Qsort(a+pivotIndex+1, size-pivotIndex-1, compareCount, assignCount);
}

#endif