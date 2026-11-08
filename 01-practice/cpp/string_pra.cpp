#include<iostream>
#include<string>
using namespace std;

int main(){
    string s1 = "hello world";
    string s2 = "hello world";
    if (s1.compare(s2)==0){
        cout<<s1<<"相等"<<endl;
    }
    s1.assign(10,'c');
    cout<<s1<<endl;
}