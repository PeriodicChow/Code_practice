// MyRand.cpp		�������Ӹ�˹�ֲ�����̬�ֲ����;��ȷֲ��������
#define _USE_MATH_DEFINES
#include <cstdlib>
#include <ctime>
#include <cmath>

/*
Box-Muller�ǲ����������һ�ַ�����Box-Muller �㷨������ԭ���ǳ���£������ȴ���൱�򵥡�
�����(0,1]ֵ����������һ�µ��������u1��u2����
����ʹ����������ʽ���е���һ�����һ����̬�ֲ����������z
z = r * cos(��) �� z = r * sin(��)
���� r = sqrt(-2 * ln(u2)), ��= 2 * �� * u1
��z����N(0, 1)�����ͨ�����Ա任
x = m + (z * ��)����N(m, ��^2)��
�μ�https://baike.baidu.com/item/box-muller/4023794?fr=aladdin
*/
double GaussRand(double mean, double variance)	// mena:��ֵ����ѧ������variance����
{
	static double u, v;
	static int phase = 0;
	double z;

	if(phase == 0)
	{
		u = (rand() + 1.0) / (RAND_MAX + 1.0);	// ����u��vΪ0ʱ�������log����
		v = (rand() + 1.0) / (RAND_MAX + 1.0);
		z = sqrt(-2.0 * log(u))* sin(2.0 * M_PI * v);
	}
	else
	{
		z = sqrt(-2.0 * log(u)) * cos(2.0 * M_PI * v);
	}
	phase = 1 - phase;
	return mean + z*sqrt(variance);
}

// ����rand()����0~RAND_MAX֮���"����"�ֲ���������������м򵥵����Ա任
double UniformRand(double a, double b)			// ����[a, b]�ϵľ��ȷֲ�
{
	return a + rand()*(b-a)/RAND_MAX;			// ��������(0,a)��(RAND_MAX,b)��ֱ�߷���
}
