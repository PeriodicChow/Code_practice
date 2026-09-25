/*	MIDIexample.h											*
 *  注: 请在Project/Settings.../Link/Libraries:下面输入		*
 *		C:\MinGWStudio\MinGW\lib\libwinmm.a					*
 *      Debug 和 Release 都需要配置                         */
#ifndef MIDI_EXAMPLE_H
#define MIDI_EXAMPLE_H
#include <windows.h> 
#include <mmsystem.h>  
#pragma comment(lib, "winmm.lib") 

double gettime(int restart=0); // 获取相对时间
DWORD MidiOutMessage(HMIDIOUT hMidi, int iStatus, int iChannel, int iFlip, int iVolume); // 发送MIDI消息

struct Music
{
	char note, volume; // 保存音符编号和音量
	double deltaTime, time; // 保存相对时长和绝对时间
};

// 播放器状态结构体 传递给回调函数
struct PlayerState
{
	HMIDIOUT hMidiOut;       
	int channel;                
	Music *musicData;          
	int totalNotes;             
	int currentIndex;        
	int *activeNotes;        
	int activeCount;            
	double startTime;         
	bool isPlaying;            
};

// 多媒体计时器回调函数
void CALLBACK TimerProc(UINT uID, UINT uMsg, DWORD_PTR dwUser, DWORD_PTR dw1, DWORD_PTR dw2);

// 播放控制函数
void StartPlay(HMIDIOUT hMidiOut, Music *data, int total, int channel); 
void StopPlay(); 
bool IsPlaying();

// 加载文件
int LoadScore(const char *filename, Music *&outData);
// filename2为NULL时单通道，否则双通道
void TestFromFile(HMIDIOUT hMidiOut, const char *filename, const char *filename2 = NULL); 

void Test(HMIDIOUT hMidiOut, int flag=3); 
void HelloWorld(HMIDIOUT hMidiOut); 
#endif