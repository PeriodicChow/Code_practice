#include<iostream>
#include<vector>
#include<string>


class Person{
public:
    Person(){}
    Person(int age, std::string name){
        this->m_Age = age;
        this->m_Name = name;
        std::cout<<m_Age<<m_Name<<"的构造函数调用"<<std::endl;
    }
    Person(const Person& p){
        
        this->m_Age=p.m_Age;
        this->m_Name=p.m_Name;
        std::cout<<m_Age<<m_Name<<"的拷贝构造函数调用"<<std::endl;
    }
    ~Person(){
        std::cout<<m_Age<<m_Name<<"的析构函数调用"<<std::endl;
    }
    int m_Age;
    std::string m_Name;
    std::ostream& operator<<(std::ostream& cout){
        cout<<"Age:"<<this->m_Age<<" Name:"<<this->m_Name<<std::endl;
        return cout;
    }

};

