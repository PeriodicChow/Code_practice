

def graycode(n,k):
    graycodelist = ["0","1"]
    for i in range(1,n+1):
        graycodelist2 = graycodelist.copy()
        for j in range(len(graycodelist)):
                graycodelist2.append(0)
        print(graycodelist2)
        for index,value in enumerate(graycodelist2):
            if index <= len(graycodelist2)/2-1:
                graycodelist2[index]="0" + graycodelist[index]
                print(graycodelist2[index])
            if index > len(graycodelist2)/2-1:
                graycodelist2.append("1" + graycodelist[index-int(len(graycodelist2)/2)])
        graycodelist = graycodelist2.copy()
        print(graycodelist2)
        
    return graycodelist[k-1]
    
        
if __name__ == "__main__":
    
    n = input("n= ")
    k = input("k= ")
    
    print(graycode(int(n),int(k)))