// MIDIexample.cpp
#include "MIDIexample.h"
#include <iostream>
#include <cmath>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
using namespace std;

double gettime(int restart)
{
	const double c = 1.0/CLOCKS_PER_SEC; 
	static clock_t t = clock(); 
	if(restart) t = clock(); 
	return c*(clock()-t); 
}

// 全局状态
static PlayerState g_player[2];
static MMRESULT g_timerID;
static int g_channelCount;
static int g_channels[2];
static double g_startTime;
static bool g_playing;
static HMIDIOUT g_hMidiOut;

DWORD MidiOutMessage(HMIDIOUT hMidi, int iStatus, int iChannel, int iFlip, int iVolume)
{
	DWORD dwMessage = (iVolume << 16) | (iFlip << 8) | iStatus | iChannel; // 组装MIDI消息的32位数据
	return midiOutShortMsg(hMidi, dwMessage); // 把封装好的消息发送给MIDI设备
}

void HelloWorld(HMIDIOUT hMidiOut)
{
	MidiOutMessage(hMidiOut, 0xC0, 0, 0, 0);
	MidiOutMessage(hMidiOut, 0x90, 0, 60, 112);
	Sleep(500);
	MidiOutMessage(hMidiOut, 0x80, 0, 60, 127);
	MidiOutMessage(hMidiOut, 0x90, 0, 64, 80);
	Sleep(500);
	MidiOutMessage(hMidiOut, 0x80, 0, 64, 127);
	MidiOutMessage(hMidiOut, 0x90, 0, 67, 96);
	Sleep(500);
	MidiOutMessage(hMidiOut, 0x80, 0, 67, 127);
	MidiOutMessage(hMidiOut, 0x90, 0, 60, 80);
	MidiOutMessage(hMidiOut, 0x90, 0, 64, 80);
	MidiOutMessage(hMidiOut, 0x90, 0, 67, 80);
	MidiOutMessage(hMidiOut, 0x90, 0, 72, 80);
	Sleep(2500);
	MidiOutMessage(hMidiOut, 0x80, 0, 60, 127);
	MidiOutMessage(hMidiOut, 0x80, 0, 64, 127);
	MidiOutMessage(hMidiOut, 0x80, 0, 67, 127);
	MidiOutMessage(hMidiOut, 0x80, 0, 72, 127);
}

// 多媒体计时器回调函数，每1毫秒调用一次
void CALLBACK TimerProc(UINT uID, UINT uMsg, DWORD_PTR dwUser, DWORD_PTR dw1, DWORD_PTR dw2)
{
	double elapsed = gettime() - g_startTime;
	double elapsedMs = elapsed * 1000.0;
	bool allDone = true;
	for (int ch = 0; ch < g_channelCount; ch++) // 遍历参与播放的所有通道
	{
		int idx = g_channels[ch];
		PlayerState *st = &g_player[idx];
		for (int j = 0; j < st->activeCount; j++)
		{
			int noteIdx = st->activeNotes[j]; // 取出当前活跃音符的编号
			if (noteIdx < 0) continue; 
			Music *note = &st->musicData[noteIdx]; // 获取该音符的具体数据
			double noteEndTime = note->time + note->deltaTime; // 计算该音符应当结束的时间
			if (elapsedMs >= noteEndTime) 
			{
				MidiOutMessage(st->hMidiOut, 0x80, st->channel, note->note, 127); 
				st->activeNotes[j] = -1; 
			}
		}
		// 开启应该开始的新音符
		bool hasNewNote = false; 
		while (st->currentIndex < st->totalNotes)
		{
			Music *note = &st->musicData[st->currentIndex]; // 取出当前待播放音符
			if (elapsedMs >= note->time) 
			{
				if (!hasNewNote)
				{
					cout << '[' << st->channel << ']'; // 输出当前播放通道编号
					hasNewNote = true; 
				}
				// 开音
				MidiOutMessage(st->hMidiOut, 0x90, st->channel, note->note, note->volume); 
				cout << "\t(" << (int)note->note << ", " << note->deltaTime << ", " << (int)note->volume << ")"; 
				// 添加到活跃列表
				if (st->activeCount < st->totalNotes)
				{
					st->activeNotes[st->activeCount] = st->currentIndex; // 记录当前音符的索引
					st->activeCount++; // 活跃音符数量增加
				}
				st->currentIndex++; 
			}
			else
			{
				break; 
			}
		}
		if (hasNewNote)
		{
			cout << endl; 
		}
		// 检查这个通道是否播放完毕
		if (st->currentIndex < st->totalNotes)
			allDone = false; 
		// 检查是否所有活跃音符都已关闭
		for (int j = 0; j < st->activeCount; j++)
		{
			if (st->activeNotes[j] >= 0)
			{
				Music *note = &st->musicData[st->activeNotes[j]]; // 获取当前仍在发声的音符
				double noteEndTime = note->time + note->deltaTime; // 重新计算其结束时间
				if (elapsedMs < noteEndTime)
					allDone = false; 
			}
		}
	}
	// 3. 全部播放完毕，停止计时器
	if (allDone)
	{
		for (int ch = 0; ch < g_channelCount; ch++)
		{
			int idx = g_channels[ch]; 
			PlayerState *st = &g_player[idx]; 
			for (int j = 0; j < st->activeCount; j++)
			{
				if (st->activeNotes[j] >= 0)
				{
					Music *note = &st->musicData[st->activeNotes[j]]; // 取出仍在播放的音符
					MidiOutMessage(st->hMidiOut, 0x80, st->channel, note->note, 127); // 关闭音符
				}
			}
			st->activeCount = 0; 
		}
		timeKillEvent(g_timerID); 
		g_playing = false; 
	}
}

void StartPlay(HMIDIOUT hMidiOut, Music *data, int total, int channel)
{}

// 停止播放
void StopPlay()
{
	if (g_playing)
	{
		timeKillEvent(g_timerID);
		g_playing = false;
	}
}

// 查询是否正在播放
bool IsPlaying()
{
	return g_playing;
}

// 从文本乐谱文件读取音符数据，返回音符数量
// 文件格式：
//   # 开头是注释
//   每行一组音符，| 分隔和弦中的多个音符
//   每个音符：音高,时长(ms),力度
//   时长是相对于前一个音符的偏移量，0 表示同时开始（和弦）
int LoadScore(const char *filename, Music *&outData)
{
	ifstream file(filename);
	if (!file.is_open())
	{
		cout << "无法打开乐谱文件: " << filename << endl;
		outData = NULL;
		return 0;
	}
	vector<Music> notes;
	string line;
	while (getline(file, line))
	{
		if (line.empty() || line[0] == '#') continue;
		stringstream ss(line);
		string chordNote;
		while (getline(ss, chordNote, '|'))
		{
			// 去除首尾空格
			size_t start = chordNote.find_first_not_of(" \t"); 
			size_t end = chordNote.find_last_not_of(" \t"); 
			if (start == string::npos) continue; 
			chordNote = chordNote.substr(start, end - start + 1);
			// 按逗号分割 音符,时长,力度
			stringstream ns(chordNote); 
			string token; 
			int values[3]; 
			int vi = 0; 
			while (getline(ns, token, ',') && vi < 3) 
			{
				values[vi++] = atoi(token.c_str()); // 转换为整数
			}
			if (vi == 3) // 当字段数量完整时
			{
				Music m; 
				m.note = (char)values[0]; 
				m.deltaTime = (double)values[1]; 
				m.volume = (char)values[2]; 
				m.time = 0.0;  // 暂时设置为0，后面再计算绝对时间
				notes.push_back(m); // 把音符加入容器
			}
		}
	}
	file.close(); 
	// 分配输出数组并计算绝对时间
	int count = notes.size(); 
	outData = new Music[count]; 
	for (int i = 0; i < count; i++) 
	{
		outData[i] = notes[i]; 
		if (i == 0)
			outData[i].time = 0; 
		else
			outData[i].time = outData[i - 1].time + outData[i - 1].deltaTime; 
	}
	return count;
}
// 从文件播放
void TestFromFile(HMIDIOUT hMidiOut, const char *filename, const char *filename2)
{
	Music *scoreData[2] = { NULL, NULL };
	int total[2] = { 0, 0 };
	double totalTime = 0;
	total[0] = LoadScore(filename, scoreData[0]);
	if (total[0] == 0 || scoreData[0] == NULL)
	{
		cout << "乐谱加载失败: " << filename << endl;
		return;
	}
	double lastTime = scoreData[0][total[0] - 1].time + scoreData[0][total[0] - 1].deltaTime;
	if (lastTime > totalTime) totalTime = lastTime;
	if (filename2 != NULL)
	{
		total[1] = LoadScore(filename2, scoreData[1]); // 从左手乐谱文件读取数据
		if (total[1] == 0 || scoreData[1] == NULL) // 若加载失败
		{
			cout << "乐谱加载失败: " << filename2 << endl;
			delete[] scoreData[0];
			return;
		}
		lastTime = scoreData[1][total[1] - 1].time + scoreData[1][total[1] - 1].deltaTime;
		if (lastTime > totalTime) totalTime = lastTime;
	}
	g_channelCount = (filename2 != NULL) ? 2 : 1;
	cout << "\n\t\t播放文件: " << filename;
	if (filename2 != NULL) cout << " + " << filename2;
	cout << endl;
	for (int i = 0; i < g_channelCount; i++)
	{
		g_player[i].hMidiOut = hMidiOut;
		g_player[i].channel = i;         
		g_player[i].musicData = scoreData[i]; 
		g_player[i].totalNotes = total[i];
		g_player[i].currentIndex = 0; 
		g_player[i].activeCount = 0; 
		g_player[i].activeNotes = new int[total[i]]; 
		for (int j = 0; j < total[i]; j++)
			g_player[i].activeNotes[j] = -1; 
		g_channels[i] = i;
		// 设置音色为钢琴
		MidiOutMessage(hMidiOut, 0xC0, i, 0, 0);
	}
	g_hMidiOut = hMidiOut; 
	g_playing = true; 
	// 开始计时
	gettime(1); 
	g_startTime = gettime();
	g_timerID = timeSetEvent(
		1,                          
		0,                          
		TimerProc,               
		(DWORD_PTR)NULL,           
		TIME_PERIODIC              
	);
	// 阻塞等待播放完成
	while (g_playing) 
	{
		Sleep(10);
	}
	// 释放内存
	for (int i = 0; i < g_channelCount; i++) 
	{
		delete[] g_player[i].activeNotes; 
		g_player[i].activeNotes = NULL; 
		delete[] scoreData[i]; 
	}
	double actual = gettime(); 
	cout << "\n========== 播放统计 (从文件读取) ==========" << endl; 
	cout << "实际播放时长: " << actual << " 秒" << endl; 
	cout << "理论播放时长: " << totalTime/1000.0 << " 秒" << endl; 
	cout << "时间误差:     " << (actual - totalTime/1000.0) * 1000 << " 毫秒" << endl; 
	cout << "==========================================" << endl; 
}

void Test(HMIDIOUT hMidiOut, int flag)
{
	double t = 1000;							
	char mf = 80;								
	Music PianoR[] = { {77,mf-10,0,0}, {81,mf-10,0}, {84,mf-10,0}, {89,mf-10,t/2},
					   {77,mf   ,0},   {81,mf   ,0}, {84,mf   ,0}, {89,mf   ,t},
					   {79,mf-10,0},   {91,mf-10,t/2},
					   {77,mf-10,0},   {82,mf-10,0}, {86,mf-10,0}, {89,mf-10,t/4},
					   {74,mf- 5,0},   {86,mf- 5,t/2},
					   {72,mf-10,0},   {84,mf-10,t/4},
					   {70,mf-10,0},   {82,mf-10,t/2},
					   {69,mf-10,0},   {81,mf-10,t/2},
					   {72,mf   ,0}, {77,mf   ,0}, {81,mf,0}, {84,mf,t/2},
					   {72,mf   ,0}, {77,mf   ,0}, {81,mf,0}, {84,mf,t/4},
					   {74,mf   ,0}, {86,mf   ,t/4},
					   {72,mf-10,0}, {84,mf-10,t/2},
					   {70,mf-10,0}, {82,mf-10,t/4},
					   {69,mf-10,0}, {81,mf-10,t/4},
					   {67,mf- 5,0}, {72,mf- 5,0}, {76,mf-5,0}, {79,mf-2,2*t} }; 
	Music PianoL[] = { {41,mf   ,t/4,0}, {48,mf   ,t/4}, {57,mf   ,t/4}, {60,mf   ,t/4},
					   {69,mf-10,t/4},   {65,mf-10,t/4}, {60,mf-10,t/4}, {57,mf-10,t/4},
					   {46,mf- 5,t/4},   {53,mf- 5,t/4}, {58,mf- 5,t/4}, {62,mf- 5,t/4},
					   {65,mf-10,t/4},   {62,mf-10,t/4}, {58,mf-10,t/4}, {53,mf-10,t/4},
					   {41,mf   ,t/4},   {48,mf   ,t/4}, {57,mf   ,t/4}, {60,mf   ,t/4},
					   {69,mf-10,t/4},   {65,mf-10,t/4}, {60,mf-10,t/4}, {57,mf-10,t/4},
					   {48,mf- 5,t/4},   {55,mf- 5,t/4}, {60,mf- 5,t/4}, {64,mf- 5,t/4},
					   {67,mf-10,t/4},   {64,mf-10,t/4}, {60,mf-10,t/4}, {55,mf-10,t/4} }; 
	Music *p[] = { PianoR, PianoL }; 
	int len[] = { sizeof(PianoR) / sizeof(*PianoR), sizeof(PianoL) / sizeof(*PianoL) }; 
	int channel[] = { 0, 1 }; 
	// 确定播放哪些通道
	int i0 = 0, i1 = 2; 
	if (flag == 1)			
		i1 = 1; 
	else if (flag == 2)		
		i0 = 1; 
	// 计算每个音符的绝对时间
	double totalTime = 0; 
	for (int i = i0; i < i1; i++) // 遍历要播放的声部
	{
		for (int j = 0; j < len[i]; j++) 
		{
			if (j == 0)
				p[i][j].time = 0; // 第一个音符的绝对时间为0
			else
				p[i][j].time = p[i][j - 1].time + p[i][j - 1].deltaTime; // 计算当前音符的绝对时间
		}
		double lastTime = p[i][len[i] - 1].time + p[i][len[i] - 1].deltaTime; // 计算当前声部的结束时间
		if (lastTime > totalTime)
			totalTime = lastTime; // 更新总时长
	}
	cout << "\n\t\t党啊，亲爱的妈妈(钢琴伴奏前2小节)" << endl;
	// 设置各通道音色为钢琴
	for (int i = i0; i < i1; i++)
	{
		MidiOutMessage(hMidiOut, 0xC0, channel[i], 0, 0);
	}
	// 初始化播放器状态
	g_channelCount = 0; 
	int activeChannels[2]; 
	for (int i = i0; i < i1; i++) 
	{
		PlayerState *st = &g_player[i];
		st->hMidiOut = hMidiOut; 
		st->channel = channel[i]; 
		st->musicData = p[i];
		st->totalNotes = len[i];
		st->currentIndex = 0; 
		st->activeCount = 0;
		// 动态分配活跃音符数组
		st->activeNotes = new int[len[i]]; // 为当前声部分配活跃音符数组
		for (int j = 0; j < len[i]; j++)
			st->activeNotes[j] = -1;
		activeChannels[g_channelCount] = i; 
		g_channelCount++; 
	}
	// 复制到全局通道映射
	for (int i = 0; i < g_channelCount; i++)
		g_channels[i] = activeChannels[i];
	g_hMidiOut = hMidiOut; 
	g_playing = true;
	// 开始计时
	gettime(1); // 重置计时器
	g_startTime = gettime(); // 记录播放开始时间
	g_timerID = timeSetEvent(
		1,                          // 间隔1毫秒
		0,                          // 0=最大可能精度
		TimerProc,  
		(DWORD_PTR)NULL,            // 用户数据
		TIME_PERIODIC               // 周期性触发
	);
	// 阻塞等待播放完成
	while (g_playing){
		Sleep(10);  // 每10毫秒检查一次，减少CPU占用
	}
	// 释放动态内存
	for (int i = i0; i < i1; i++)
	{
		delete[] g_player[i].activeNotes; 
		g_player[i].activeNotes = NULL; 
	}
	double actual = gettime(); 
	cout << "\n========== 播放统计 ==========" << endl;
	cout << "实际播放时长: " << actual << " 秒" << endl; 
	cout << "理论播放时长: " << totalTime/1000.0 << " 秒" << endl; 
	cout << "时间误差:     " << (actual - totalTime/1000.0) * 1000 << " 毫秒" << endl; 
	cout << "==============================" << endl; 
}