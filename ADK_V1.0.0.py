# -*- coding: utf-8 -*-
# __author__ = 'mocobk'
# for py2 & py3

import msvcrt
import os
import ctypes

select_udid = None


# 输出彩色字体
def print_color_font(message, font_color):
    setcolor = ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11), font_color)
    print(message)
    reset_color = ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11),
                                                                 0x04 | 0x02 | 0x01)


# 列出当前设备
def list_devices():
    # 检测当前所有连接设备
    t = os.popen('adb devices').read()  # 当adb未启动时，避免下一条卡住
    devices_list = os.popen('adb devices -l | findstr "model"').readlines()
    print('--------------------------------------------------------------------------------')
    if devices_list:
        num = 1
        udid_list = []
        for devices in devices_list:
            udid = devices.split()[0]
            device_name = (devices.split()[3]).split(":")[1]
            message = u'设备[%d]: %-20s\t%-20s\n' % (num, udid, device_name)
            print_color_font(message, 0x0a)
            num += 1
            udid_list.append(udid)
        print('--------------------------------------------------------------------------------')
        return udid_list
    else:
        print_color_font(u'当前未有任何设备连接,请插入设备或输入设备IP：\n', 0xe0 | 0x0c)
        print('--------------------------------------------------------------------------------')
        device_ip = input(u"输入设备IP或直接按ENTER重试：")
        t = os.system('adb connect %s:5555' % str(device_ip))
        t = os.system('cls')
        list_devices()


def select_device():
    global select_udid
    udid_list = list_devices()
    try:
        if len(udid_list) > 1:
            select_num = int(input(u'请输入要操作的设备序号：'))
            select_udid = udid_list[select_num - 1]
        else:
            select_udid = udid_list[0]
    except Exception as reason:
        t = os.system('cls')
        if str(reason) == 'list index out of range':
            print_color_font(u":( 输入的设备序号不正确，请重新输入！", 0x0e | 0x0c)
        select_device()
    create_bat_file()


def adb_input_keyevent(keyevent, print_text=None):
    if print_text:
        print(print_text)
    os.system('adb -s %s shell input keyevent %s' % (select_udid, keyevent))


def adb_input_text(text, print_text=None):
    if print_text:
        print(print_text)
    os.system('adb -s %s shell input text %s' % (select_udid, text))


def adb_install():
    app_path = input('>')
    os.system('adb -s %s install -r -d %s' % (select_udid, app_path))


def adb_force_stop():
    os.system('adb -s %s shell am force-stop %s' % (select_udid, get_cur_package_name()))


def adb_restart():
    cur_package_name = get_cur_package_name()
    os.system('adb -s %s shell am force-stop %s' % (select_udid, cur_package_name))
    # 这里加了read()方法，不然会阻塞
    t = os.popen('adb -s %s shell monkey -p %s -v 1' % (select_udid, cur_package_name)).read()


def adb_uninstall():
    os.system('adb -s %s uninstall %s' % (select_udid, get_cur_package_name()))


def adb_start_tcp_mode():
    ip = get_ip()
    if '5555' not in str(select_udid):
        print(select_udid)
        os.system('adb -s %s tcpip 5555' % select_udid)
        print(ip)
        os.system('adb connect %s' % ip)
        print_color_font(u'已开启adb-wifi连接模式，按F3刷新！', 0x0e)
    else:
        print_color_font(u'当前已是adb-wifi连接模式，无需启动！', 0x0e)


def get_cur_package_name():
    try:
        # 触发屏幕，激活当前应用为最上层，这里用短滑方法，避免误点
        os.system('adb -s %s shell input swipe 0 360 1 360 10' % select_udid)
        result = os.popen('adb -s %s shell dumpsys activity | findstr mFocusedActivity' % select_udid)
        cur_activity = result.read().split()[3]
        cur_package_name = cur_activity.split('/')[0]
        return cur_package_name
    except:
        # 当adb shell不支持dumpsys activity命令时
        pass


def get_product_model():
    return os.popen('adb -s %s shell getprop ro.product.model' % select_udid).read().strip()


def get_system_version():
    return os.popen('adb -s %s shell getprop ro.build.version.release' % select_udid).read().strip()


def get_ip():
    return os.popen('adb -s %s shell getprop dhcp.wlan0.ipaddress' % select_udid).read().strip()


def get_resolution():
    try:
        temp = os.popen('adb -s %s shell dumpsys window displays | findstr init' % select_udid).read()
        resolution = temp.split('=')[1].split()[0]
        return resolution
    except:
        return 'unknown'


def create_bat_file():
    # 创建截图批处理（直接用python命令调用不能连续截图，有阻塞）
    f = open(os.getenv('tmp') + '\\screenshot.bat', 'w')
    f.write('@echo off\nadb -s {0} shell /system/bin/screencap -p /sdcard/screenshot.png & adb -s {1} pull '
            '/sdcard/screenshot.png %tmp% & rundll32.exe shimgvw.dll,ImageView_Fullscreen '
            '%tmp%\screenshot.png'.format(select_udid, select_udid))
    f.close()


def screenshot():
    os.system('start cmd cmd /c call ' + os.getenv('tmp') + '\\screenshot.bat')


def main():
    keymap = u'''
|  Ctrl+Tab(菜单)  |  Space(Home键)     |  Esc(返回)       |  Enter(确认)  |
|  Ctrl+S(截图)    |  Ctrl+↓(音量减)   |  Ctrl+↑(音量+)  |  F5(安装apk)  |
|  F6(结束当前应用)|  F7(卸载当前应用)  |  F8(重启应用)    |  F2(设备信息) |'''
    print_color_font(keymap, 0x00 | 0x70)
    print_color_font(u'\n*****设备连接成功，开始操作*****', 0x0a)
    while True:
        key = ord(msvcrt.getch())
        if key == 224:
            key2 = ord(msvcrt.getch())
            if key2 == 72:
                adb_input_keyevent('KEYCODE_DPAD_UP', u'↑')
            elif key2 == 80:
                adb_input_keyevent('KEYCODE_DPAD_DOWN', u'↓')
            elif key2 == 75:
                adb_input_keyevent('KEYCODE_DPAD_LEFT', u'←')
            elif key2 == 77:
                adb_input_keyevent('KEYCODE_DPAD_RIGHT', u'→')
            elif key2 == 141:
                adb_input_keyevent('KEYCODE_VOLUME_UP', u'音量+')
            elif key2 == 145:
                adb_input_keyevent('KEYCODE_VOLUME_DOWN', u'音量-')
        elif key == 13:
            adb_input_keyevent('KEYCODE_DPAD_CENTER', 'OK')
        elif key == 32:
            adb_input_keyevent('KEYCODE_HOME', 'HOME')
        elif key == 27:
            adb_input_keyevent('KEYCODE_BACK', 'BACK')
        elif key == 0:
            key2 = ord(msvcrt.getch())
            if key2 == 148:
                adb_input_keyevent('KEYCODE_MENU', 'MENU')
            # F5安装新应用
            elif key2 == 63:
                print_color_font(u'请输入要安装的apk完整路径(可拖拽apk至此)：\n', 0x0e)
                adb_install()
            # F6杀掉当前应用进程
            elif key2 == 64:
                print_color_font(u'停止当前应用进程…', 0x0e)
                adb_force_stop()
            # F7卸载当前应用进程
            elif key2 == 65:
                print_color_font(u'正在卸载当前应用…', 0x0e)
                adb_uninstall()
            elif key2 == 66:
                print_color_font(u'重启当前应用…', 0x0e)
                adb_restart()
            elif key2 == 59:
                print_color_font(keymap, 0x00 | 0x70)
            elif key2 == 60:
                product_model = get_product_model()
                system_version = get_system_version()
                ip = get_ip()
                resolution = get_resolution()
                print_color_font(u'设备机型：%s\n系统版本：%s\n分 辨 率：%s\nIP 地 址：%s' %
                                 (product_model, system_version, resolution, ip), 0x0b)
            # F9开启tcpip监听模式
            elif key2 == 67:
                adb_start_tcp_mode()
            # F3清空并刷新列表
            elif key2 == 61:
                os.system('cls')
                select_device()
                main()
        elif key == 19:
            print_color_font(u'开始截图，并打开…', 0x0e)
            screenshot()
        elif key == 3:
            exit(0)
        else:
            try:
                adb_input_text('%c' % key, '%c' % key)
            except:
                print_color_font(u'输入有误，请重新输入！', 0x0e)


if __name__ == '__main__':
    select_device()
    main()
