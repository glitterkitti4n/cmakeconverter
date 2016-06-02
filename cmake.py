
import message as msg

class CMake(object):
    """
    CMake : create and open CMakeLists.txt
    """

    def __init__(self):
        self.cmake = None

    def create_cmake(self, cmake_path=None):
        if cmake_path is None:
            msg.send('CMakeLists will be build in current directory.', 'ok')
            self.cmake = open('CMakeLists.txt', 'w')
        else:
            msg.send('CmakeLists.txt will be build in : ' + str(cmake_path), 'warn')
            self.cmake = open(str(cmake_path) + 'CMakeLists.txt', 'w')

    def get_cmake(self):
        return self.cmake