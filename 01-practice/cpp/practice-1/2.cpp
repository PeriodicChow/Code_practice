#include<iostream>
using namespace std;

class Person{
public:
int m_age;
int *m_height;
Person(int age,int height){
    cout<<"gouzao"<<endl;
    m_age=age;
    m_height=new int(height);
}
~Person(){
    
    if(m_height != NULL){
        delete m_height;
        m_height = NULL;

    }
    cout<<"xigou"<<endl;

}

};


void test(){
    Person p(18,3);
    cout<<p.m_age<<" "<<*p.m_height<<endl;
    Person p2(p);
    cout<<p2.m_age<<" "<<*p2.m_height<<endl;
}

int main(){
    test();
    system("pause");
    return 0;
}