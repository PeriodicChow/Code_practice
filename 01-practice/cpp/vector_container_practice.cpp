// #include<iostream>
// #include<vector>
// #include<string>


// class Person{
// public:
//     Person(int age, std::string name){
//         this->m_Age = age;
//         this->m_Name = name;
//         std::cout<<m_Age<<m_Name<<"的构造函数调用"<<std::endl;
//     }
//     Person(const Person& p){
        
//         this->m_Age=p.m_Age;
//         this->m_Name=p.m_Name;
//         std::cout<<m_Age<<m_Name<<"的拷贝构造函数调用"<<std::endl;
//     }
//     ~Person(){
//         std::cout<<m_Age<<m_Name<<"的析构函数调用"<<std::endl;
//     }
//     int m_Age;
//     std::string m_Name;

// };

#include "Person.hpp"
using namespace std;



// void test01(){
//     std::vector<Person> personlist;
//     personlist.reserve(10);
//     for(int i=0;i<=5;++i){
//         personlist.push_back(Person(i,"000"+std::to_string(i)));
//     }

// }

void test02(){
    Person p;
    p << (p << cout);

int main(){
    test02();
    system("pause");
    return 0;


}