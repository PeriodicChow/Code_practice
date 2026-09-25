#include <iostream>
#include <ctime>
#include <chrono>
using namespace std;

struct tickets{
	int birth_year;
    int birth_month;
    int birth_day;
    float height;
    int enter_year;
    int enter_month;
    int enter_day;
    int type;
};

int getWeekday(int year, int month, int day) {
        std::chrono::year y{year};
        std::chrono::month m{static_cast<unsigned int>(month)};
        std::chrono::day d{static_cast<unsigned int>(day)};

        std::chrono::year_month_day ymd{y,m,d};
        auto weekday = std::chrono::weekday{ymd};
        return weekday;
}

int age_calculate(int by,int bm,int bd,int ey,int em,int ed){
    int age = ey - by;
    if (em < bm || (em == bm && ed < bd)){
        age--;
    }
    return age;
}

int ticket_price(int age,int h,int ey,int em,int ed,int t){
	return 0;
    
}

int main(){
	tickets ticket;
	cout << "你的出生日期是：（年 月 日）";
    cin >> ticket.birth_year >> ticket.birth_year >> ticket.birth_day;
    cout << "你的身高是：";
    cin >> ticket.height;
    auto now = std::chrono::system_clock::now();
    std::time_t current_time = std::chrono::system_clock::to_time_t(now);
    std::tm* local_time = std::localtime(&current_time);
    ticket.enter_year = localtime->tm_year + 1900;
    ticket.enter_month = localtime->tm_mon + 1;
    ticket.enter_day = localtime->tm_mday;
    cout << "你的入园日期是：(年 月 日)";
    cin >> ticket.enter_year >> ticket.enter_month >> ticket.enter_day;
    cout << "请输入你的票种：（1.一日票 2.两日票）";
    cin >> ticket.type;
    cout << ticket_price(age_calculate(ticket.birth_year,
        ticket.birth_month,
        ticket.birth_day,
        ticket.enter_year,
        ticket.enter_month,
        ticket.enter_day),
        ticket.height,
        ticket.enter_year,
        ticket.enter_month,
        ticket.enter_day,
        ticket.type);
    return 0;



}
    
    