#include<iostream>
using namespace std;

void first() {
    cout << "Three blind mice" << endl;
}

void second() {
    cout << "See how they run" << endl;
    
}

int main() {
    /*
    string paddress, name;
    cout << "your address is:" << endl;
    cin >> paddress;
    cout << "your name is:" << endl;
    cin >> name;
    cout << "Hello " << name << " from " << paddress << endl;
    cout << "input:" << endl;
    int a;
    cin >> a;
    long b;
    b = a*220;
    cout << b << endl;
    first();
    first();
    second();
    second();*/
    int age;
    cout << "Enter your age: ";
    cin >> age;

    cout << "Enter the number of hours: ";
    int hours;
    cin >> hours;

    int minutes; 
    cout << "Enter the number of minutes: ";
    cin >> minutes;
  
    cout << "Time: " << hours << ":" << minutes << endl;
    int allmouths =  age * 12;

    cout << "you have lived for " << allmouths << " months" << endl;




    return 0;

}
