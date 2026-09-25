#include <bits/stdc++.h>
#include <time.h>
#include<random>
using namespace std;
const int MAXN=1e7;

vector<int>arr;

int readarr(int& n){
    cin>>n;
    arr.resize(n);
    int a=1,b=100;
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<int> dist(a,b);
    
    for(int i=0;i<n;i++){
        arr[i]=dist(gen);
    } 
    /*
    for(int i=0;i<n;i++){
        cout<<arr[i];
        if(i<n-1)cout<<" ";
    }
    cout<<endl;*/
    return 0;
}

int output(int n){
	for(int i=0;i<n;i++){
		cout<<arr[i]<<" ";
	}
	cout<<endl;
    return 0;
}

/*Bubble Sort-冒泡排序
Selection Sort-选择排序
Insertion Sort-插入排序
Merge Sort-归并排序
Heap Sort-堆排序
Shell Sort-希尔排序
Comb Sort-梳排序
Quick Sort-快速排序*/

//归并排序
void MergeSort(vector<int>&arr,int l, int r) {
    if (l >= r) return;
    int mid = l + (r - l) / 2;
    MergeSort(arr, l, mid);
    MergeSort(arr, mid + 1, r);
    vector<int> t;
    int i = l, j = mid + 1;
    while (i <= mid && j <= r) {
        if (arr[i] <= arr[j]) {
            t.push_back(arr[i]);
            i++; 
        } else {
            t.push_back(arr[j]);
            j++; 
        }
    }
    while (i <= mid) {
        t.push_back(arr[i]);
        i++;
    }
    while (j <= r) {
        t.push_back(arr[j]);
        j++;
    }
    for (int k = l; k <= r; k++) {
        arr[k] = t[k - l];
    }
}

//冒泡排序
int bubblesort(int n){
    for(int j=0;j<n;j++){
        for(int i=0;i<n-j-1;i++){
            if(arr[i]>arr[i+1]){
                swap(arr[i],arr[i+1]);
            }
	    }
    }
    return 0;
}

//快速排序
int ARR[MAXN]={};

void quicksort1(int s,int e){
    bool b=0;
    double m=(arr[e]+arr[s])/2;
    for(int i=s;i<e;i++){
        //m=m+arr[i];
        if(arr[i]>arr[i+1]){
            b=1;
        }
    }
    //m=m/(e-s+1);cout<<m<<endl;
    if(b){
        int S,E;
        S=s;
        E=e;
        for(int i=S;i<=E;i++){
            if(arr[i]<m){
                ARR[s]=arr[i];
                s++;
            }
            else if(arr[i]>m){
                ARR[e]=arr[i];
                e--;
            }
        }
        for(int i=s;i<=e;i++){
            ARR[i]=m;
        }
        s--;
        e++;
        
        for(int i=S;i<=E;i++){
        arr[i]=ARR[i];//cout<<arr[i]<<' ';
        }//cout<<endl;
        //cout<<' '<<s<<' '<<e<<endl;
        quicksort1(S,s);
        quicksort1(e,E);
    }
}

void quicksort2(int n){
    for(int i=0;i<n;i++){
        ARR[i]=arr[i];
        for(int j=0;j<i;j++){
            if(arr[i]<ARR[j]){
                for(int k=i-1;k>=j;k--){
                    ARR[k+1]=ARR[k];
                }
                ARR[j]=arr[i];
                break;
            }
        }
        //for(int l=0;l<n;l++){
        //    cout<<ARR[l]<<' ';
        //}cout<<endl;
    }
    for(int i=0;i<n;i++){
        arr[i]=ARR[i];
    }
}

int n=0;
int main(){
    cout<<"bubblesort"<<endl;
    readarr(n);
    clock_t start,end;
    start=clock();
    bubblesort(n);
    end=clock();
  //  output(n);
    cout<<"time = "<<end-start<<"ms"<<endl<<endl;
    

    cout<<"quicksort"<<endl;
    readarr(n);
    start=clock();
    quicksort2(n);
    end=clock();
  //  output(n);
    cout<<"time = "<<end-start<<"ms"<<endl<<endl;

    cout<<"quicksort"<<endl;
    readarr(n);
    start=clock();
    MergeSort(arr,0,n-1);
    end=clock();
 //   output(n);
    cout<<"time = "<<end-start<<"ms"<<endl<<endl;
 
}
