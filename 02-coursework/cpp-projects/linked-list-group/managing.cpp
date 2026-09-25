#include <bits/stdc++.h>
using namespace std;
struct mem{
    int birthyear;
    int birthmonth;
    string name;
    mem *next;
};
struct mem *Create(){
    struct mem *head=NULL,*p,*q=NULL,*t;
    string line;
    cout<<"请每行输入：姓名 出生年份 出生月份（输入单独一行 0 结束）"<<endl;
    // 吸收可能残留的换行
    getline(cin, line);
    while(true){
        if(!getline(cin, line)) break;
        if(line=="0") break;
        if(line.size()==0) continue;
        istringstream iss(line);
        string name; int y, m;
        if(!(iss>>name>>y>>m)){
            cout<<"输入格式错误，请输入：姓名 出生年份 出生月份，或输入0结束"<<endl;
            continue;
        }
        p=new mem;
        p->name = name;
        p->birthyear = y;
        p->birthmonth = m;
        p->next = NULL;
        if(head==NULL){
            head = p;
            continue;
        }
        t=head;
        q=NULL;
        while(t!=NULL){
            if(p->birthyear < t->birthyear || (p->birthyear == t->birthyear && p->birthmonth < t->birthmonth)){
                if(t==head){
                    p->next=head;
                    head=p;
                }else{
                    p->next=t;
                    q->next=p;
                }
                break;
            }else{
                q=t;
                t=t->next;
            }
        }
        if(t==NULL && q!=NULL){
            q->next=p;
        }
    }
    return head;
}

struct mem* Insert(mem *head){
    struct mem *p=head,*q=NULL;
    struct mem *newmem=new mem;
    cin>>newmem->name;
    cin>>newmem->birthyear>>newmem->birthmonth;
    newmem->next=NULL;
    while(p!=NULL){
        if(newmem->birthyear < p->birthyear || (newmem->birthyear == p->birthyear && newmem->birthmonth < p->birthmonth)){
                if(p==head){
                    newmem->next=head;
                    head=newmem;
                }
                else{
                    newmem->next=p;
                    q->next=newmem;
                break;
                }
        }        
        else{
            q=p;
            p=p->next;
        }
	}
    if(q!=NULL){
        q->next=newmem;
    }
    return head;                    
}

struct mem* DeleteMem(mem* head,string name){
    struct mem *p,*q;
    p=head;
    q=NULL;
    while(p!=NULL){
        if(p->name==name){
            if(p==head){
                head=head->next;
                delete p;
                p=head;
            }
            else{
                q->next=p->next;
                delete p;
                p=q->next;
            }
            return head;
        }
        else{
            q=p;    
            p=p->next;
        }    
    }
    if(q!=NULL){
    	cout<<"没有查找到该成员"<<endl; 
	}
    return head;           
}

struct mem *DeleteGroup(mem *head){
    cout<<"DeleteGroup"<<endl;
    return head;
}
void Search(mem *head,string x){
    cout<<"Search"<<endl;
}
struct mem *Modify(mem *head,string y){
    cout<<"Modify"<<endl;
    return head;
}

void Print(mem *head){
    struct mem* p=head;
    while(p!=NULL){
        cout<<p->name<<" "<<p->birthyear<<"年"<<p->birthmonth<<"月"<<endl;
        p=p->next;
    }   
}

int main(){
bool judge=1;
mem *head = NULL;
string s;
bool flag = 0; // 标记是否已创建过小组，放在循环外以便持久化

cout<<"欢迎使用成员管理系统！"<<endl; 
    while(judge==1){
        cout<<endl<<"请选择您需要的操作："<<endl<<"1.创建小组"<<endl<<"2.添加小组成员"
		<<endl<<"3.删除小组成员"<<endl<<"4.修改小组成员信息"<<endl<<"5.查找小组成员信息"
		<<endl<<"6.删除小组"<<endl<<"7.输出小组信息"<<endl<<"8.退出系统"<<endl;
        int n;
        cin>>n;
        switch(n){
        case 1:
            if(flag==0){
                cout<<"请依次输入小组成员的姓名、出生年份和出生月份(若输入完毕请输入0)"<<endl;
                head=Create();flag=1;
            }else{
                cout<<"小组信息已存在！"<<endl;
            }
            break; // 必须加上
        case 2:
        	cout<<"请依次输入小组成员的姓名、出生年份和出生月份"<<endl;
        	head = Insert(head);
            break;
        case 3:
            cout<<"请输入您想删除的小组成员名字:"<<endl;
            cin>>s;
            head = DeleteMem(head, s);
            break;
        case 4:
            cout<<"请输入您想修改的小组成员名字:"<<endl;
            cin>>s;
            head = Modify(head, s);
            break;
        case 5:            
            cout<<"请输入您想查找的小组成员名字:"<<endl;
            cin>>s;
            Search( head, s);
            break;
        case 6:
            if(flag==1){
            head = DeleteGroup(head); flag=0;
            }else{
            cout<<"小组信息不存在！"<<endl;
            }
            break;
        case 7:
        	Print(head);break;
        case 8:
            judge=0;break;
        default : 
            cout<<"请输入有效数字！"<<endl;
        }
}
return 0;
}
