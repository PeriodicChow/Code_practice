//	main.cpp
#include "MIDIexample.h" 
#include <iostream> 
#include <conio.h>	
using namespace std; 

int main() 
{
	int choice;
	HMIDIOUT hMidiOut;							// 定义MIDI输出设备句柄
	midiOutOpen(&hMidiOut, MIDIMAPPER, 0, 0, 0); // 打开默认的MIDI播放设备
	
	HelloWorld(hMidiOut); // 启动音效
	
	while(true) 
	{
		cout << "\n1 --- Right\n2 --- Left\n3 --- Both\n4 --- File Both\n0 --- exit : "; 
		choice = getche(); // 读取输入的单字符选项
		cout << endl;
		if(choice<='0') break;
		switch(choice)
		{
		case '1':	Test(hMidiOut, 1);	break; // 播放右手音轨
		case '2': 	Test(hMidiOut, 2);	break; // 播放左手音轨
		case '3':	Test(hMidiOut, 3);	break; // 同时播放左右手音轨
		case '4':	TestFromFile(hMidiOut, "score_right.txt", "score_left.txt"); break; // 从文件读取乐谱并播放
		}
	}
	midiOutClose(hMidiOut);						// 关闭已打开的MIDI播放设备
	return 0;
}