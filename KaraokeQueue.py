debug = False

class KaraokeQueue:
    def __init__(self, newWork, keyExtractionFunc):
        self.userList = []
        self.currentUser = -1
        self.workDict = {}
        self.objKeyFunct = keyExtractionFunc
        self.print_status()
        while len(newWork) > 0:
            self.add(newWork.pop(0))

    def add(self, obj):
        if debug:
            print("ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING ADDING")
        key = self.objKeyFunct(obj)
        if key not in self.workDict.keys():
            self.userList.append(key)
            self.workDict[key] = []
        self.workDict[key].append(obj)
        if self.currentUser == -1:
            self.currentUser = 0
        self.print_status()
        

    def next(self):
        if debug:
            print("NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT NEXT")
        if self.currentUser == -1:
            return None
        user = self.userList[self.currentUser]
        userWork = self.workDict[user]
        obj = userWork.pop(0)
        if len(userWork) == 0:
            self.workDict.pop(user,None)
            self.userList.remove(user)
            self.currentUser -= 1

        self.currentUser += 1
        if self.currentUser == len(self.userList):
            if len(self.userList) == 0:
                self.currentUser = -1
            else:
                self.currentUser = 0
        self.print_status()
        
        return obj

    def print_status(self):
        if not debug:
            return
        print("UserList", self.userList)
        print("\tLength", len(self.userList))
        print("Current User:", self.currentUser)
        print("WorkDict", self.workDict)
    def hasItems(self):
        return len(self.userList) > 0


def main():
    global debug
    # debug = True
    fakeWork = [['adam', 1], ['betty', 2],['charles', 3], ['donna', 4], ['edward', 5], ['francine', 6], ['gary', 7], ['helena', 8]]
    kq = KaraokeQueue(fakeWork, lambda x:x[0])
    ob = kq.next()
    print("Initial deque")
    while ob is not None:
        print(1, ob)
        ob = kq.next()

    print("ob now None")
    print("\nQueuing more:")
    kq.add(['betty', 2])
    kq.add(['donna', 4])
    kq.add(['francine', 6])
    kq.add(['helena', 8])

    kq.add(['gary', 7])
    kq.add(['edward', 5])
    kq.add(['charles', 3])
    kq.add(['adam', 1])
    kq.add(['adam', 1])

    print("Secondary deque")
    ob = kq.next()
    while ob is not None:
        print(2, ob)
        ob = kq.next()

    print("ob is None again")

    print("\n\n\nFullKaraoke")
    print("\nQueuing more:")
    kq.add(['betty', 2])
    kq.add(['donna', 4])
    kq.add(['betty', 6])
    kq.add(['betty', 8])

    kq.add(['charles', 5])
    kq.add(['gary', 7])
    kq.add(['charles', 3])
    kq.add(['charles', 1])
    kq.add(['charles', 9])
    kq.add(['donna', 14])

    print("Karaoke deque")
    ob = kq.next()
    while ob is not None:
        print("Removed Obj:", ob)
        ob = kq.next()

    print("ob is None again")




    print("\ndone...")

if __name__ == '__main__':
    main()


    