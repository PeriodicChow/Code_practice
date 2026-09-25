/*#include<string>
#include<fstream>
#include<iostream>
#include<sstream>
using namespace std;

struct Contacts{
    int num;
    string name;
    string gender;
    int age;
    string phonenum;
    string city;
    string unit;
    string address;
    string tag;
    Contacts* next;
};

string Select(string user);
Contacts *Create(string filepath);
void DisplayContacts(Contacts* head);
Contacts *Search(Contacts* head, Contacts info);
Contacts *Delete(Contacts* head, string name);
Contacts *Modify(Contacts* head, string name);
Contacts *Insert(Contacts* head);
void Save(string filepath, Contacts* head);
void Analyze();
void FreeList(Contacts* head);

string Select(string user){//选择文件
    if(user=="zhang"){
        return "/Users/zhouyaqian/Desktop/Haiwei/programming/CPP/txl/txl/contacts_zhang.txt";
    }
    else if(user=="li"){
        return "/Users/zhouyaqian/Desktop/Haiwei/programming/CPP/txl/txl/contacts_li.txt";
    }
    else if(user=="wang"){
        return "/Users/zhouyaqian/Desktop/Haiwei/programming/CPP/txl/txl/contacts_wang.txt";
    }
    else if(user=="zhao"){
        return "/Users/zhouyaqian/Desktop/Haiwei/programming/CPP/txl/txl/contacts_zhao.txt";
    }
    else{
        cout<<"用户不存在，请重新选择！"<<endl;
        return "";
    }
}

Contacts *Create(string filepath){
     if(filepath.empty()){
        cout<<"错误：文件路径为空！"<<endl;
        return NULL;
    }
 ifstream inFile(filepath);
    if(!inFile.is_open()){
        cout<<"文件打开失败！"<<endl;
        return NULL;
    }
    Contacts *head=NULL,*tail=NULL;
    string line;
    while(getline(inFile,line)){
        if(line.empty()){
  continue;
  }
        Contacts *p=new Contacts;
        stringstream ss(line);
        ss>>p->num>>p->name>>p->gender>>p->age>>p->phonenum>>p->city>>p->unit>>p->address>>p->tag;
        p->next=NULL;
        if(head==NULL){
            head=p;
            tail=p;
        }
        else{
            tail->next=p;
            tail=p;
        }
    }
    inFile.close();
    cout<<"成功加载文件："<<filepath<<endl;
    return head;
}

// 显示通讯录
void DisplayContacts(Contacts *head){
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return;
    }
    cout<<"\n========== 通讯录列表 =========="<<endl;
    Contacts *p=head;
    while(p!=NULL){
        cout<<p->num<<" "<<p->name<<" "<<p->gender<<" "<<p->age<<" "<<p->phonenum<<" "<<p->city<<" "<<p->unit<<" "<<p->address<<" "<<p->tag<<endl;
        p=p->next;
    }
    cout << "==========================================" << endl;
}
// 查询联系人
Contacts *Search(Contacts *head,Contacts info){
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return NULL;
    }
    
    
    Contacts *resultHead=NULL;
    Contacts *resultTail=NULL;
    Contacts *p=head;
    int count=0;
    
    while(p!=NULL){
        bool match=1;
        
        // 按姓名查询
        if(!info.name.empty()&&p->name!=info.name)
            match=0;
        
        // 按城市查询
        if(!info.city.empty()&&p->city!=info.city)
            match=0;
            
        // 按标签查询
        if(!info.tag.empty() && p->tag!=info.tag)
            match=0;
        
        if(match){
            count++;
            if(resultHead==NULL){
                resultHead=new Contacts(*p);
                resultHead->next=NULL;
                resultTail=resultHead;
            }
            else{
                resultTail->next=new Contacts(*p);
                resultTail=resultTail->next;
                resultTail->next=NULL;
            }
        }
        p=p->next;
    }
    
    if(count==0){
        cout<<"未找到符合条件的联系人！"<<endl;
        return NULL;
    }
    
    cout<<"找到 "<<count<<" 个符合条件的联系人："<<endl;
    DisplayContacts(resultHead);
    
    // 注意：这里创建了新的链表，使用后需要释放
    return resultHead;
}

// 删除联系人
Contacts *Delete(Contacts *head,string name){
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return NULL;
    }
    
    Contacts *p=head;
    Contacts *prev=NULL;
    bool found=0;
    
    // 处理头节点
    while(p!=NULL&&p->name==name){
        found=true;
        Contacts *temp=p;
        p=p->next;
        delete temp;
    }
    head=p;
    
    // 处理中间和尾部节点
    prev=p;
    if(p!=NULL) p=p->next;
    
    while(p!=NULL){
        if(p->name==name){
            found=true;
            prev->next=p->next;
            delete p;
            p=prev->next;
        }
        else{
            prev=p;
            p=p->next;
        }
    }
    
    if(found){
        cout<<"成功删除联系人："<<name<<endl;
    }
    else{
        cout<<"未找到联系人："<<name<<endl;
    }
    
    return head;
}

// 修改联系人
Contacts *Modify(Contacts *head,string name){
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return NULL;
    }
    
    Contacts *p=head;
    bool found=0;
    
    while(p!=NULL){
        if(p->name==name){
            found=1;
            cout<<"\n找到联系人："<<name<<endl;
            cout<<"当前信息："<<endl;
            cout<<"电话："<<p->phonenum<<endl;
            cout<<"单位："<<p->unit<<endl;
            cout << "城市："<<p->city<<endl;
            cout << "地址："<<p->address<<endl;
            
            cout << "\n请选择要修改的信息："<<endl;
            cout << "1.电话"<<endl;
            cout << "2.单位"<<endl;
            cout << "3.城市"<<endl;
            cout << "4.地址"<<endl;
            cout << "请输入选择(1-4)：";
            
            int choice;
            cin >> choice;
            cin.ignore();  // 清除缓冲区
            
            switch(choice){
                case 1:
                    cout << "请输入新电话：";
                    getline(cin, p->phonenum);
                    break;
                case 2:
                    cout << "请输入新单位：";
                    getline(cin, p->unit);
                    break;
                case 3:
                    cout << "请输入新城市：";
                    getline(cin, p->city);
                    break;
                case 4:
                    cout << "请输入新地址：";
                    getline(cin, p->address);
                    break;
                default:
                    cout << "无效选择！" << endl;
            }
            
            cout << "修改成功！" << endl;
            break;
        }
        p=p->next;
    }
    
    if(!found){
        cout<<"未找到联系人："<<name<<endl;
    }
    
    return head;
}

// 插入新联系人
Contacts *Insert(Contacts *head){
    Contacts *newContact=new Contacts;
    
    cout<<"\n请输入联系人信息："<<endl;
    cout<<"编号：";
    cin>>newContact->num;
    
    // 检查编号是否重复
    Contacts *p=head;
    while(p!=NULL){
        if(p->num==newContact->num){
            cout<<"编号已存在！"<<endl;
            delete newContact;
            return head;
        }
        p=p->next;
    }
    
    cin.ignore();  // 清除缓冲区
    
    cout<<"姓名：";
    getline(cin,newContact->name);
    
    cout<<"性别(男/女)：";
    getline(cin,newContact->gender);
    
    cout<<"年龄：";
    cin>>newContact->age;
    cin.ignore();
    
    cout<<"电话：";
    getline(cin,newContact->phonenum);
    
    cout<<"城市：";
    getline(cin,newContact->city);
    
    cout<<"单位：";
    getline(cin,newContact->unit);
    
    cout<<"地址：";
    getline(cin,newContact->address);
    
    cout<<"标签：";
    getline(cin,newContact->tag);
    
    newContact->next=NULL;
    
    // 插入到链表尾部
    if(head==NULL){
        head=newContact;
    }
    else{
        p=head;
        while(p->next!=NULL){
            p=p->next;
        }
        p->next=newContact;
    }
    
    cout<<"添加成功！"<<endl;
    return head;
}

// 保存文件
void Save(string filepath,Contacts *head){
    if(head==NULL){
        cout<<"通讯录为空，无内容可保存！"<<endl;
        return;
    }
    
    ofstream outFile(filepath);
    if(!outFile.is_open()){
        cout<<"文件保存失败！"<<endl;
        return;
    }
    
    Contacts *p=head;
    while(p!=NULL){
        outFile<<p->num<<" "<<p->name<<" "<<p->gender<<" "<<p->age<<" "<<p->phonenum<<" "<<p->city<<" "<<p->unit<<" " <<p->address<<" "<<p->tag;
        
        if(p->next!=NULL) outFile<<endl;
        p=p->next;
    }
    
    outFile.close();
    cout<<"成功保存到文件："<<filepath<<endl;
}

// 分析功能（简化版）
void Analyze(){
    cout<<"\n========== 分析功能 =========="<<endl;
    cout<<"1. 统计各标签联系人数量"<<endl;
    cout<<"2. 查找共同联系人"<<endl;
    cout<<"3. 计算社交关联度"<<endl;
    cout<<"请输入选择(1-3)：";
    
    int choice;
    cin>>choice;
    
    switch(choice){
        case 1:
            //cout<<"\n功能开发中..."<<endl;
            
        case 2:
            cout<<"\n功能开发中..."<<endl;
            break;
        case 3:
            cout<<"\n功能开发中..."<<endl;
            break;
        default:
            cout<<"无效选择！"<<endl;
    }
}

// 释放链表内存
void FreeList(Contacts *head){
    Contacts* p = head;
    while(p != NULL){
        Contacts* temp = p;
        p = p->next;
        delete temp;
    }
}

// 主函数
int main(){
    bool judge=true;
    Contacts *head=NULL;
    string user,filepath;
    bool fileLoaded=false;
    cout<<"=========================================="<<endl;
    cout<<"        欢迎使用通讯录管理系统！"<<endl;
    cout<<"=========================================="<<endl;
    while(judge){
        cout<<"\n========== 主菜单 =========="<<endl;
        cout<<"1. 选择文件"<<endl;
        cout<<"2. 显示通讯录"<<endl;
        cout<<"3. 查询信息"<<endl;
        cout<<"4. 删除通讯录成员"<<endl;
        cout<<"5. 修改通讯录成员"<<endl;
        cout<<"6. 添加通讯录成员"<<endl;
        cout<<"7. 保存"<<endl;
        cout<<"8. 分析"<<endl;
        cout<<"9. 退出系统"<<endl;
        cout<<"请输入操作序号:";
        int n;
        cin>>n;
        cin.ignore();  // 清除缓冲区
        switch(n){
            case 1:  // 选择文件
                cout<<"请输入用户名(zhang/li/wang/zhao): ";
                cin>>user;
                filepath=Select(user);
                
                if(filepath.empty()){
                    break;
                }
                // 释放之前的链表
                if(head!=NULL){
                    FreeList(head);
                }
                head = Create(filepath);
                if(head!=NULL){
                    fileLoaded = true;
                }
                break;
            case 2:  // 显示通讯录
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }
                else{
                    DisplayContacts(head);
                }
                break;
            case 3:  // 查询
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }
                else{
                    Contacts info;
                    cout<<"请输入查询条件（不查询的条件直接回车）:"<<endl;
                    
                    cout<<"姓名：";
                    getline(cin,info.name);
                    
                    cout<<"城市：";
                    getline(cin,info.city);
                    
                    cout<<"标签：";
                    getline(cin,info.tag);
                    
                    Contacts *result=Search(head,info);
                    // 释放查询结果链表
                    FreeList(result);
                }
                break;
            case 4:  // 删除
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }
                else{
                    string name;
                    cout<<"请输入要删除的联系人姓名: ";
                    getline(cin,name);
                    head=Delete(head,name);
                }
                break;
            case 5:  // 修改
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }
                else{
                    string name;
                    cout << "请输入要修改的联系人姓名: ";
                    getline(cin,name);
                    head = Modify(head,name);
                }
                break;
            case 6:  // 添加
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }
                else{
                    head=Insert(head);
                }
                break;
            case 7:  // 保存
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }
                else if(filepath.empty()){
                    cout<<"文件路径无效！"<<endl;
                }
                else{
                    Save(filepath,head);
                }
                break;
            case 8:  // 分析
                Analyze();
                break;
            case 9:  // 退出
                if(head != NULL){
                    cout<<"是否保存修改？(y/n): ";
                    char saveChoice;
                    cin>>saveChoice;
                    if(saveChoice=='y'){
                        Save(filepath,head);
                    }
                    FreeList(head);
                }
                judge = false;
                cout<<"感谢使用，再见！"<<endl;
                break;
            default:
                cout<<"请输入有效数字！"<<endl;
        }
    }
    return 0;
}
*/



#include<string>
#include<fstream>
#include<iostream>
#include<sstream>
#include<map>
using namespace std;

struct Contacts {
    int num;
    string name;
    string gender;
    int age;
    string phonenum;
    string city;
    string unit;
    string address;
    string tag;
    Contacts* next;
};



string Select(string user) {
    if(user=="zhang"){
        return "contacts_zhang.txt";
    }
    else if(user=="li"){
        return "contacts_li.txt";
    }
    else if(user=="wang"){
        return "contacts_wang.txt";
    }
    else if(user=="zhao"){
        return "contacts_zhao.txt";
    }
    else{
        cout<<"用户不存在，请重新选择！"<<endl;
        return "";
    }
}




void FreeList(Contacts* head) {
    Contacts* p=head;
    while(p!=NULL){
        Contacts* temp=p;
        p=p->next;
        delete temp;
    }
}


Contacts* Create(string filepath) {
    ifstream inf(filepath);
    if(!inf.is_open()){
        cout<<"文件打开失败！"<<endl;
        return NULL;
    }else{
        Contacts *head=NULL;Contacts *q=NULL;
        string line;
        while(getline(inf,line)){
            if(line.empty()){
                continue;
            }
            Contacts* p=new Contacts;
            stringstream ss(line);
            ss>>p->num>>p->name>>p->gender>>p->age
              >>p->phonenum>>p->city>>p->unit>>p->address>>p->tag;
            p->next=NULL;
            if(head==NULL){
                head=p;q=p;
            }else{
                q->next=p;q=p;
            }
        }
        inf.close();cout<<"成功加载文件："<<filepath<<endl;return head;
    }
}

void DisplayContacts(Contacts* head) {
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return;
    }else{
        cout<<"\n========== 通讯录列表 ==========\n";
        cout<<"编号 姓名 性别 年龄 电话 城市 单位 地址 标签"<<endl;
        cout<<"--------------------------------------------------------------"<<endl;
        Contacts* p=head;
        while(p!=NULL){
            cout<<p->num<<" "<<p->name<<" "<<p->gender<<" "<<p->age<<" "
                <<p->phonenum<<" "<<p->city<<" "<<p->unit<<" "
                <<p->address<<" "<<p->tag<<endl;
            p=p->next;
        }
        cout<<"=========================================="<<endl;
    }
    
}

Contacts* Search(Contacts* head,Contacts xx) {
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return NULL;
    }else{
        Contacts *H=NULL,*Q=NULL,*p=head;
        int k=0;
        while(p!=NULL){
            bool b=1;
            if(!xx.name.empty()&&p->name!=xx.name){
                b=0;
            }
            if(!xx.city.empty()&&p->city!=xx.city){
                b=0;
            }
            if(!xx.tag.empty()&&p->tag!=xx.tag){
                b=0;
            }
            if(b){
                k++;
                if(H==NULL){
                    H=new Contacts;
                    *H=*p;
                    H->next=NULL;
                    Q=H;
                }else{
                    Q->next=new Contacts;
                    Q=Q->next;
                    *Q=*p;
                    Q->next=NULL;
                }
            }
            p=p->next;
        }
        if(k==0){
            cout<<"未找到符合条件的联系人！"<<endl;
            return NULL;
        }
        cout<<"找到"<<k<<"个符合条件的联系人："<<endl;
        DisplayContacts(H);
        return H;
    }
}

Contacts* Delete(Contacts* head, string name) {
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return NULL;
    }else{
        Contacts *p=head,*q=NULL;
        bool f=0;
        if(p!=NULL&&p->name==name){
            f=true;
            head=p->next;
            delete p;
            p=head;
        }
        while(p!=NULL){
            if(p->name==name){
                f=1;
                if(q!=NULL){
                    q->next=p->next;
                }
                Contacts* temp=p;
                p=p->next;
                delete temp;
            }else{
                q=p;
                p=p->next;
            }
        }
        if(f){
            cout<<"成功删除联系人："<<name<<endl;
        }else{
            cout<<"未找到联系人："<<name<<endl;
        }
        return head;
    }
}

Contacts* Modify(Contacts* head, string name) {
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return NULL;
    }
    Contacts* p=head;
    bool found=false;
    while(p!=NULL){
        if(p->name==name){
            found=true;
            cout<<"\n找到联系人："<<name<<endl;
            cout<<"当前信息："<<endl;
            cout<<"电话："<<p->phonenum<<endl;
            cout<<"单位："<<p->unit<<endl;
            cout<<"城市："<<p->city<<endl;
            cout<<"地址："<<p->address<<endl;
            cout<<"\n请选择要修改的信息："<<endl;
            cout<<"1.电话"<<endl;
            cout<<"2.单位"<<endl;
            cout<<"3.城市"<<endl;
            cout<<"4.地址"<<endl;
            cout<<"请输入选择(1-4)：";
            int choice;
            cin>>choice;
            cin.ignore();
            switch(choice){
                case 1:
                    cout<<"请输入新电话：";
                    getline(cin,p->phonenum);
                    break;
                case 2:
                    cout<<"请输入新单位：";
                    getline(cin,p->unit);
                    break;
                case 3:
                    cout<<"请输入新城市：";
                    getline(cin,p->city);
                    break;
                case 4:
                    cout<<"请输入新地址：";
                    getline(cin,p->address);
                    break;
                default:
                    cout<<"无效选择！"<<endl;
            }
            cout<<"修改成功！"<<endl;
            break;
        }
        p=p->next;
    }
    if(!found){
        cout<<"未找到联系人："<<name<<endl;
    }
    return head;
}

Contacts* Insert(Contacts* head) {
    Contacts* newContact=new Contacts;
    cout<<"\n请输入联系人信息："<<endl;
    cout<<"编号：";
    cin>>newContact->num;
    Contacts* p=head;
    while(p!=NULL){
        if(p->num==newContact->num){
            cout<<"编号已存在！"<<endl;
            delete newContact;
            return head;
        }
        p=p->next;
    }
    cin.ignore();
    cout<<"姓名：";
    getline(cin,newContact->name);
    cout<<"性别(男/女)：";
    getline(cin,newContact->gender);
    cout<<"年龄：";
    cin>>newContact->age;
    cin.ignore();
    cout<<"电话：";
    getline(cin,newContact->phonenum);
    cout<<"城市：";
    getline(cin,newContact->city);
    cout<<"单位：";
    getline(cin,newContact->unit);
    cout<<"地址：";
    getline(cin,newContact->address);
    cout<<"标签：";
    getline(cin,newContact->tag);
    newContact->next=NULL;
    if(head==NULL){
        head=newContact;
    }else{
        p=head;
        while(p->next!=NULL){
            p=p->next;
        }
        p->next=newContact;
    }
    cout<<"添加成功！"<<endl;
    return head;
}

void Save(string filepath, Contacts* head) {
    if(head==NULL){
        cout<<"通讯录为空，无内容可保存！"<<endl;
        return;
    }
    ofstream ouf(filepath);
    if(!ouf.is_open()){
        cout<<"文件保存失败！"<<endl;
        return;
    }
    Contacts* p=head;
    while(p!=NULL){
        ouf<<p->num<<" "<<p->name<<" "<<p->gender<<" "<<p->age<<" "
               <<p->phonenum<<" "<<p->city<<" "<<p->unit<<" "
               <<p->address<<" "<<p->tag;
        if(p->next!=NULL){
            ouf<<endl;
        }
        p=p->next;
    }
    ouf.close();
    cout<<"成功保存到文件："<<filepath<<endl;
}

void CountTags(Contacts* head) {
    if(head==NULL){
        cout<<"通讯录为空！"<<endl;
        return;
    }
    map<string,int> tagCount;
    Contacts* p=head;
    while(p!=NULL){
        tagCount[p->tag]++;
        p=p->next;
    }
    cout<<"\n=== 标签统计结果 ==="<<endl;
    for(auto i=tagCount.begin();i!=tagCount.end();i++){
        cout<<i->first<<"："<<i->second<<"人"<<endl;
    }
    cout<<"==================="<<endl;
}

void FindCommonContacts(Contacts* head1, Contacts* head2, string name1, string name2) {
    if(head1==NULL||head2==NULL){
        cout<<"请先加载两个用户的通讯录！"<<endl;
        return;
    }
    cout<<"\n=== "<<name1<<" 和 "<<name2<<" 的共同联系人 ==="<<endl;
    bool ff=0;
    Contacts* p1=head1;
    while(p1!=NULL){
        Contacts* p2=head2;
        while(p2!=NULL){
            if(p1->name==p2->name){
                cout<<"姓名："<<p1->name<<"，电话："<<p1->phonenum;
                cout<<"，城市："<<p1->city<<"，标签："<<p1->tag<<endl;
                ff=1;
                break;
            }
            p2=p2->next;
        }
        p1=p1->next;
    }
    if(!ff){
        cout<<"没有共同联系人"<<endl;
    }
    cout<<"======================================="<<endl;
}

void CalculateSocialRelation(Contacts* head1, Contacts* head2, string name1, string name2) {
    if(head1==NULL||head2==NULL){
        cout<<"请先加载两个用户的通讯录！"<<endl;
        return;
    }
    int cc=0;
    Contacts* p1=head1;Contacts* p2=head2;
    while(p1!=NULL){
        p2=head2;
        while(p2!=NULL){
            if(p1->name==p2->name){
                cc++;
                break;
            }
            p2=p2->next;
        }
        p1=p1->next;
    }
    map<string,int> cc1,cc2;
    p1=head1;
    while(p1!=NULL){
        cc1[p1->city]++;
        p1=p1->next;
    }
    p2=head2;
    while(p2!=NULL){
        cc2[p2->city]++;
        p2=p2->next;
    }
    int ccc=0;
    for(auto i=cc1.begin();i!=cc1.end();i++){
        string city=i->first;
        int c1=i->second;
        int c2=cc2[city];
        ccc=ccc+min(c1,c2);
    }
    int ct=0;
    p1=head1;
    while(p1!=NULL){
        p2=head2;
        while(p2!=NULL){
            if(p1->name==p2->name){
                if(p1->tag==p2->tag){
                    ct++;
                }
                break;
            }
            p2=p2->next;
        }
        p1=p1->next;
    }
    int n1=0;
    p1=head1;
    while(p1!=NULL){
        n1++;
        p1=p1->next;
    }
    int n2=0;
    p2=head2;
    while(p2!=NULL){
        n2++;
        p2=p2->next;
    }
    double cA=0;
    double ccA=0;
    double ctA=0;
    if(n1<=0){
        
    }else{
        cA=(double)cc/n1;
        ccA=(double)ccc/n1;
        ctA=(double)ct/n1;
    }
    double cB=0;
    double ccB=0;
    double ctB=0;
    if(n2<=0){
        
    }else{
        cB=(double)cc/n2;
        ccB=(double)ccc/n2;
        ctB=(double)ct/n2;
    }
    
    
    
    
    
    double AB=0.5*cA+0.3*ccA+0.2*ctA;
    double BA=0.5*cB+0.3*ccB+0.2*ctB;
    cout<<"\n=== 社交关联度分析 ==="<<endl;
    cout<<name1<<"->"<<name2<<"："<<endl;
    cout<<"共同联系人比例："<<cA<<endl;
    cout<<"城市相似度："<<ccA<<endl;
    cout<<"标签相似度："<<ctA<<endl;
    cout<<"社交关联度："<<AB<<endl;
    cout<<"\n"<<name2<<"->"<<name1<<"："<<endl;
    cout<<"共同联系人比例："<<cB<<endl;
    cout<<"城市相似度："<<ccB<<endl;
    cout<<"标签相似度："<<ctB<<endl;
    cout<<"社交关联度："<<BA<<endl;
    cout<<"\n=== 关系级别判断 ==="<<endl;
    string level;
    if(AB>=0.8){
        level="非常亲密";
    }else if(AB>=0.6){
        level="比较亲密";
    }else if(AB>=0.4){
        level="一般关系";
    }else if(AB>=0.2){
        level="较弱关系";
    }else{
        level="几乎无关";
    }
    cout<<name1<<"对"<<name2<<"的关系级别："<<level<<endl;
    if(BA>=0.8){
        level="非常亲密";
    }else if(BA>=0.6){
        level="比较亲密";
    }else if(BA>=0.4){
        level="一般关系";
    }else if(BA>=0.2){
        level="较弱关系";
    }else{
        level="几乎无关";
    }
    cout<<name2<<"对"<<name1<<"的关系级别："<<level<<endl;
    cout<<"=========================="<<endl;
}

void Analyze() {
    cout<<"\n========== 分析功能 =========="<<endl;
    cout<<"1.统计标签数量"<<endl;
    cout<<"2.查找共同联系人"<<endl;
    cout<<"3.计算社交关联度"<<endl;
    cout<<"4.返回主菜单"<<endl;
    cout<<"请输入选择(1-4)：";
    int choice;
    cin>>choice;
    switch(choice){
        case 1:{
            cout<<"\n=== 统计标签数量 ==="<<endl;
            cout<<"请输入要统计的用户名(zhang/li/wang/zhao)：";
            string user;
            cin>>user;
            string filepath=Select(user);
            if(!filepath.empty()){
                Contacts* head=Create(filepath);
                if(head!=NULL){
                    CountTags(head);
                    FreeList(head);
                }
            }
            break;
        }
        case 2:{
            cout<<"\n=== 查找共同联系人 ==="<<endl;
            cout<<"请输入第一个用户名：";
            string user1;
            cin>>user1;
            cout<<"请输入第二个用户名：";
            string user2;
            cin>>user2;
            string filepath1=Select(user1);
            string filepath2=Select(user2);
            if(!filepath1.empty()&&!filepath2.empty()){
                Contacts* head1=Create(filepath1);
                Contacts* head2=Create(filepath2);
                if(head1!=NULL&&head2!=NULL){
                    FindCommonContacts(head1,head2,user1,user2);
                }
                FreeList(head1);
                FreeList(head2);
            }
            break;
        }
        case 3:{
            cout<<"\n=== 计算社交关联度 ==="<<endl;
            cout<<"请输入第一个用户名：";
            string user1;
            cin>>user1;
            cout<<"请输入第二个用户名：";
            string user2;
            cin>>user2;
            string filepath1=Select(user1);
            string filepath2=Select(user2);
            if(!filepath1.empty()&&!filepath2.empty()){
                Contacts* head1=Create(filepath1);
                Contacts* head2=Create(filepath2);
                if(head1!=NULL&&head2!=NULL){
                    CalculateSocialRelation(head1,head2,user1,user2);
                }
                FreeList(head1);
                FreeList(head2);
            }
            break;
        }
        case 4:
            cout<<"返回主菜单"<<endl;
            break;
        default:
            cout<<"无效选择！"<<endl;
    }
}



int main(){
    bool judge=true;
    Contacts* head=NULL;
    string user,filepath;
    bool fileLoaded=false;
    cout<<"=========================================="<<endl;
    cout<<"欢迎使用通讯录管理系统！"<<endl;
    cout<<"=========================================="<<endl;
    while(judge){
        cout<<"\n========== 主菜单 =========="<<endl;
        cout<<"1.选择文件"<<endl;
        cout<<"2.显示通讯录"<<endl;
        cout<<"3.查询信息"<<endl;
        cout<<"4.删除通讯录成员"<<endl;
        cout<<"5.修改通讯录成员"<<endl;
        cout<<"6.添加通讯录成员"<<endl;
        cout<<"7.保存"<<endl;
        cout<<"8.分析"<<endl;
        cout<<"9.退出系统"<<endl;
        cout<<"请输入操作序号(1-9)：";
        int n;char nn;
        cin>>nn;n=int(nn-'0');
        cin.ignore();
        switch(n){
            case 1:{
                cout<<"请输入用户名(zhang/li/wang/zhao)：";
                cin>>user;
                filepath=Select(user);
                if(filepath.empty()){
                    break;
                }
                if(head!=NULL){
                    FreeList(head);
                }
                head=Create(filepath);
                if(head!=NULL){
                    fileLoaded=true;
                }
                break;
            }
            case 2:{
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }else{
                    DisplayContacts(head);
                }
                break;
            }
            case 3:{
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }else{
                    Contacts info;
                    cout<<"请输入查询条件（不查询的条件直接回车）："<<endl;
                    cout<<"姓名：";
                    getline(cin,info.name);
                    cout<<"城市：";
                    getline(cin,info.city);
                    cout<<"标签：";
                    getline(cin,info.tag);
                    Contacts* result=Search(head,info);
                    FreeList(result);
                }
                break;
            }
            case 4:{
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }else{
                    string name;
                    cout<<"请输入要删除的联系人姓名：";
                    getline(cin,name);
                    head=Delete(head,name);
                }
                break;
            }
            case 5:{
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }else{
                    string name;
                    cout<<"请输入要修改的联系人姓名：";
                    getline(cin,name);
                    head=Modify(head,name);
                }
                break;
            }
            case 6:{
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }else{
                    head=Insert(head);
                }
                break;
            }
            case 7:{
                if(!fileLoaded){
                    cout<<"请先选择文件！"<<endl;
                }else if(filepath.empty()){
                    cout<<"文件路径无效！"<<endl;
                }else{
                    Save(filepath,head);
                }
                break;
            }
            case 8:{
                Analyze();
                break;
            }
            case 9:{
                if(head!=NULL){
                    cout<<"是否保存修改？(y/n)：";
                    char saveChoice;
                    cin>>saveChoice;
                    if(saveChoice=='y'||saveChoice=='Y'){
                        Save(filepath,head);
                    }
                    FreeList(head);
                }
                judge=false;
                cout<<"感谢使用，再见！"<<endl;
                break;
            }
            default:{
                cout<<"请输入有效数字(1-9)！"<<endl;
            }
        }
    }
}
