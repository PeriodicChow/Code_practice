#include<bits/stdc++.h>
using namespace std;

int& test01(){
    int a = 10;
    return a;
}

int main(){
    int &ref = test01();
    cout << ref << endl;
    cout << ref << endl;
    return 0;

}