# -*- coding:utf-8 -*-  
# __auth__ = mocobk
# email: mailmzb@qq.com
import ctypes
import os
import sys
import time
import threading
import subprocess
import configparser
import zipfile
from axmlparserpy import axmlprinter
from xml.dom import minidom
from ctypes import wintypes, windll, byref
from globalhotkeys import GlobalHotKeys
from prompt_toolkit import print_formatted_text
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.formatted_text import FormattedText
# from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.shortcuts import set_title
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError
import monkeyTest


DEVICE_UDID = None
DEVICE_NAME = ''
PACKGE_NAME = ''
APP_PACKAGE_NAME = ''
CUR_PATH = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(CUR_PATH, 'adk_config.ini')
screenshot_hot_key = 'ALT+S'
printf = print_formatted_text

cf = configparser.ConfigParser()
cf.add_section('Config')
bindings = KeyBindings()

STYLE = Style.from_dict({
    'success': 'ansidarkgreen',  # 暗绿
    'info': 'ansiteal',  # 青色
    'warning': 'ansibrown',  # 褐色
    'error': 'ansired',  # 红色
    'tip': 'ansiturquoise',  # 蓝绿
    'bg_ansidarkgreen': 'bg:ansidarkgreen',  # 背景暗绿
    'bg_ansipurple': 'bg:ansipurple',  # 背景紫色
    'bg_ansilightgray': 'ansiblack bg:ansilightgray',  # 背景暗灰
})


#############################################################################
# adb 方法
#############################################################################
def adb_cmd(cmd):
    cmd = cmd.replace('adb', 'adb -s %s' % DEVICE_UDID)
    try:
        subprocess.call(cmd, shell=True)
    except KeyboardInterrupt:
        pass


def start_adb_server():
    return subprocess.check_output('adb start-server', shell=True)


def adb_screenshot():
    print_color('success', '正在截图...')
    # subprocess.Popen('adb -s {0} shell /system/bin/screencap -p /sdcard/screenshot.png & adb -s {1} pull '
    #                  '/sdcard/screenshot.png %tmp% & rundll32.exe shimgvw.dll,ImageView_Fullscreen '
    #                  '%tmp%\screenshot.png'.format(DEVICE_UDID, DEVICE_UDID), shell=True)  # 使用系统自带图片查看器打开
    subprocess.Popen('adb -s {0} shell /system/bin/screencap -p /sdcard/screenshot.png & adb -s {1} pull '
                     '/sdcard/screenshot.png %tmp% & start %tmp%\screenshot.png'.format(DEVICE_UDID, DEVICE_UDID),
                     shell=True)  # 使用默认图片打开方式


def adb_screenrecord():
    print_color('success', '正在录屏... Ctrl+C结束录制')
    subprocess.Popen('adb -s {0} shell /system/bin/screenrecord /sdcard/screenrecord.mp4'.format(DEVICE_UDID),
                     shell=True)
    seconds = 0
    cur_time = time.strftime("%Y-%m-%d_%H_%M_%S")
    ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11), 0x0c)
    while True:
        try:
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            record_time = '%02d:%02d:%02d' % (h, m, s)
            seconds += 1

            sys.stdout.write(' ' * 10 + '\r')
            sys.stdout.flush()
            sys.stdout.write('● [Recorde Time]: ' + str(record_time) + '\r')
            sys.stdout.flush()
            time.sleep(1)
        except:
            ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11), 0x04 | 0x02 | 0x01)
            time.sleep(1)  # 停顿一下再拉取，否则文件不完整，无法打开
            file_name = str(cur_time) + '_screenrecord.mp4'
            save_path = os.path.join(CUR_PATH, file_name)
            subprocess.Popen('adb -s {0} pull /sdcard/screenrecord.mp4 {1}'.format(DEVICE_UDID, save_path), shell=True)
            print_color('info', '\n文件保存在：%s' % save_path)
            break


def adb_input_keyevent(keyevent, info=None):
    if info:
        print_color('info', info)
    subprocess.call('adb -s %s shell input keyevent %s' % (DEVICE_UDID, keyevent), shell=True)


def adb_input_text(text):
    text = text.replace('input ', '')
    subprocess.call('adb -s %s shell input text %s' % (DEVICE_UDID, text), shell=True)


def get_apk_package_name(apk_path):
    """获取apk文件的包名信息"""
    zf = zipfile.ZipFile(apk_path, mode='r')
    AndroidManifest = zf.open('AndroidManifest.xml')
    ap = axmlprinter.AXMLPrinter(AndroidManifest.read())
    # buff = minidom.parseString(ap.getBuff()).toxml()
    package_name = minidom.parseString(ap.getBuff()).documentElement.getAttribute('package')
    return package_name


def app_install(app_path):
    """安装应用，支持安装网络地址包"""
    start_time = time.time()
    if str(app_path).startswith(('http://', '"http://', 'ftp://', '"ftp://', r'\\', r'"\\')):
        app_file_name = os.path.basename(app_path).replace('"', '')  # 避免"fi le.apk"带空格、引号的路径
        save_path = os.path.join(CUR_PATH, app_file_name)
        print_color('info', '正在下载网络资源到本地,请稍后...', end='\n')
        # 使用windows自带的 powershell 来下载文件
        subprocess.call(
            "powershell (new-object System.Net.WebClient).DownloadFile('{}', '{}')".format(app_path, save_path),
            shell=True)
        print_color('', save_path)
        app_path = save_path
    apk_package_name = get_apk_package_name(app_path)
    print_color('info', '正在安装,请稍后...', end='\n')
    log = subprocess.Popen('adb -s %s install -r -d %s' % (DEVICE_UDID, app_path), shell=True, stdout=subprocess.PIPE)
    result = [None]
    while True:
        new_line = log.stdout.readline().decode('utf-8')
        # 刷新打印进度百分比
        if '%' in new_line:
            sys.stdout.write(' ' * 200 + '\r')
            sys.stdout.flush()
            sys.stdout.write(new_line.strip() + '\r')
            sys.stdout.flush()
        else:
            if new_line == '':
                break
            print(new_line, end='')
            result.append(new_line)

    end_time = time.time()
    duration_time = round(end_time - start_time, 2)
    if 'Success' in result[-1]:
        print_color('success', '安装成功', end='\n')
    else:
        print_color('error', result[-1], end='\n')
    print_color('info', '总耗时 %s sec' % duration_time, end='\n')
    app_start(apk_package_name)


def app_force_stop(package_name):
    """kill掉应用"""
    try:
        subprocess.call('adb -s %s shell am force-stop %s' % (DEVICE_UDID, package_name), shell=True)
    except:
        pass


def app_start(package_name):
    """根据包名启动应用"""
    try:
        subprocess.check_output('adb -s %s shell monkey -p %s -v 1' % (DEVICE_UDID, package_name), shell=True)
    except:
        pass


def app_restart(package_name):
    app_force_stop(package_name)
    app_start(package_name)


def app_uninstall():
    subprocess.call('adb -s %s uninstall %s' % (DEVICE_UDID, get_app_package_name()), shell=True)


def app_clear():
    """清除应用数据及缓存"""
    subprocess.call('adb -s %s shell pm clear %s' % (DEVICE_UDID, get_app_package_name()), shell=True)


def app_info(end='\n>'):
    """输出应用信息"""
    print_color('info', '包 名 称：%s\n版 本 号：%s\n运行内存：%s Mb' % (get_app_package_name(), get_app_version(), get_app_mem()),
                end=end)


def adb_start_tcpip_mode():
    """开启设备tcpip连接模式，默认端口5555"""
    if '5555' not in str(DEVICE_UDID):
        subprocess.Popen('adb -s %s tcpip 5555' % DEVICE_UDID, stdout=subprocess.PIPE, shell=True)
    else:
        pass


def adb_connect_tcpip():
    """切换至tcpip连接设备"""
    global DEVICE_UDID
    print_color('info', '正在使用wifi连接设备...')
    ip = get_ip()
    try:
        result = subprocess.check_output('adb connect %s' % ip, shell=True).decode('utf-8')
        if 'connected to' in result:
            print_color('success', '已成功切换至wifi连接！')
            DEVICE_UDID = str(ip) + ':5555'
            set_console_title()

    except:
        print_color('warning', '切换失败，请检查设备网络是否正确！')


def adb_connect_usb():
    """切换至usb连接，并断开tcpip连接"""
    global DEVICE_UDID
    print_color('info', '正在使用USB连接设备...')
    serial_number = get_serialno()
    if serial_number in [device['device_udid'] for device in get_device_list()]:
        adb_disconnect_tcpip(DEVICE_UDID)
        DEVICE_UDID = serial_number
        set_console_title()
        print_color('success', '已成功切换至usb连接！')
    else:
        print_color('warning', '切换失败，请检查设备是否已插入！')


def adb_disconnect_tcpip(ip):
    """断开tcpip连接"""
    subprocess.call('adb disconnect %s' % ip, shell=True)


def get_cur_package_name():
    """获取当前应用包名"""
    try:
        result = subprocess.check_output('adb -s %s shell dumpsys activity | findstr top-activity' % DEVICE_UDID,
                                         shell=True).decode('utf-8')
        cur_activity = result.split(':')[-1]
        cur_package_name = cur_activity.split('/')[0]

        return cur_package_name
    except Exception as error:
        print_color('warning', error)


def get_product_model():
    """获取设备型号"""
    return subprocess.check_output('adb -s %s shell getprop ro.product.model' % DEVICE_UDID, shell=True).decode(
        'utf-8').strip()


def get_system_version():
    """获取系统版本"""
    return subprocess.check_output('adb -s %s shell getprop ro.build.version.release' % DEVICE_UDID, shell=True).decode(
        'utf-8').strip()


def get_serialno():
    """获取设备序列号"""
    return subprocess.check_output('adb -s %s shell getprop ro.serialno' % DEVICE_UDID, shell=True).decode(
        'utf-8').strip()


def get_ip():
    """获取设备ip"""
    ip = subprocess.check_output('adb -s %s shell ip route' % DEVICE_UDID, shell=True).decode('utf-8')
    return ip.split()[-1] if ip else 'network anomaly'
    # return subprocess.check_output('adb -s %s shell getprop dhcp.wlan0.ipaddress' % DEVICE_UDID, shell=True).decode(
    #     'utf-8').strip()  # android 8.0不支持


def get_resolution():
    """获取设备分辨率"""
    try:
        temp = subprocess.check_output('adb -s %s shell dumpsys window displays | findstr init' % DEVICE_UDID,
                                       shell=True).decode('utf-8')
        resolution = temp.split('=')[1].split()[0]
        return resolution
    except:
        return 'unknown'


def get_app_version():
    """获取app版本"""
    temp = subprocess.check_output(
        'adb -s %s shell dumpsys package %s | findstr  versionName' % (DEVICE_UDID, get_app_package_name()),
        shell=True).decode('utf-8').strip()
    try:
        version = temp.split('=')[1]
    except:
        version = 'unknown'
    return version


def get_apk_path():
    """获取app包路径"""
    path = subprocess.check_output('adb -s %s shell pm path %s' % (DEVICE_UDID, get_app_package_name()),
                                   shell=True).decode('utf-8').strip()
    return path.split(':')[1]


def get_app_mem():
    """获取app当前占用内存，计算多个进程之和"""
    result = subprocess.Popen(
        'adb -s %s shell dumpsys meminfo --package %s | findstr TOTAL' % (DEVICE_UDID, get_app_package_name()),
        shell=True, stdout=subprocess.PIPE)
    process_mem_list = []
    for eachline in result.stdout:
        if eachline:
            process_mem_list.append(int(eachline.decode('utf-8').split()[1]))
    return int(sum(process_mem_list) / 1024)


#############################################################################
# 绑定设备
#############################################################################
def get_device_list():
    """获取设备列表"""
    devices = subprocess.Popen('adb devices -l | findstr "model"', shell=True,
                               stdout=subprocess.PIPE).stdout.readlines()
    if devices:
        device_list = []
        device_id = 0
        for devices in devices:
            devices = devices.decode('utf-8')
            device_id += 1
            udid = devices.split()[0]
            device_name = (devices.split()[3]).split(":")[1]
            device_list.append({'device_id': device_id, 'device_name': device_name, 'device_udid': udid})
        return device_list
    else:
        return []


def show_devices():
    printf(FormattedText([('class:warning', '=' * 79)]), style=STYLE)
    device_list = get_device_list()
    if device_list:
        for each_device in device_list:
            device = [('', '\n'),
                      ('class:bg_ansidarkgreen', ' [%d] ' % each_device['device_id']),
                      ('', ' '),
                      ('class:bg_ansipurple', '  %-20s' % each_device['device_name']),
                      ('class:bg_ansipurple', '  %-49s' % each_device['device_udid'])]
            printf(FormattedText(device), style=STYLE)
    else:
        print_color('error', '当前未有任何设备连接,请插入设备!', end='')
        printf(FormattedText([('class:warning', '\n' + '=' * 79 + '\n')]), style=STYLE)
        subprocess.check_output('adb wait-for-device', shell=True)  # 等待设备接入
        refresh()
    printf(FormattedText([('class:warning', '\n' + '=' * 79 + '\n')]), style=STYLE)


class DeviceIdValidator(Validator):
    """验证输入的设备序号是否存在，在prompt中使用"""

    def validate(self, document):
        try:
            if int(document.text) not in range(1, len(get_device_list()) + 1):
                raise ValidationError(
                    message='tips: 输入的设备序号不正确，请重新输入！',
                    cursor_position=len(document.text))  # Move cursor to end of input.
        except:
            raise ValidationError(
                message='tips: 输入的设备序号不正确，请重新输入！',
                cursor_position=len(document.text))


def select_device():
    global DEVICE_UDID
    global DEVICE_NAME
    device_list = get_device_list()
    if len(device_list) > 1:
        select_id = int(prompt('请输入要操作的设备序号：', validator=DeviceIdValidator(), validate_while_typing=False))
        for each_device in device_list:
            if each_device['device_id'] == select_id:
                DEVICE_UDID = each_device['device_udid']
                DEVICE_NAME = each_device['device_name']
                break
    elif len(device_list) == 1:
        DEVICE_UDID = device_list[0]['device_udid']
        DEVICE_NAME = device_list[0]['device_name']
    else:
        pass


def switch_device():
    global DEVICE_UDID, DEVICE_NAME
    cur_device = DEVICE_UDID
    device_list = get_device_list()
    device_list_sort_by_id = sorted(device_list, key=lambda x: x['device_id'])
    cur_device_id = [device['device_id'] for device in device_list_sort_by_id if cur_device == device['device_udid']][0]
    cur_device_index = cur_device_id - 1
    if cur_device_id < len(device_list):
        DEVICE_UDID = device_list_sort_by_id[cur_device_index + 1]['device_udid']
        device_id = device_list_sort_by_id[cur_device_index + 1]['device_id']
        DEVICE_NAME = device_list_sort_by_id[cur_device_index + 1]['device_name']
    else:
        DEVICE_UDID = device_list_sort_by_id[0]['device_udid']
        device_id = device_list_sort_by_id[0]['device_id']
        DEVICE_NAME = device_list_sort_by_id[0]['device_name']
    return '[%s] %s\t\t%s' % (device_id, DEVICE_NAME, DEVICE_UDID)


#############################################################################
# 配置
#############################################################################
def set_console_title():
    if APP_PACKAGE_NAME:
        set_title('ADK      %s    SN: %s   APP:%s' % (DEVICE_NAME, DEVICE_UDID, APP_PACKAGE_NAME))
    else:
        set_title('ADK      %s    SN: %s' % (DEVICE_NAME, DEVICE_UDID))


def set_console_size(buffer_width, buffer_height, window_width, window_height):
    """设备窗口的缓冲区大小及窗口大小"""
    stdout = -11
    hdl = windll.kernel32.GetStdHandle(stdout)  # 句柄
    bufsize = wintypes._COORD(buffer_width, buffer_height)  # rows, columns
    windll.kernel32.SetConsoleScreenBufferSize(hdl, bufsize)
    # 设置窗口大小，窗口大小不能大于缓冲区大小，否则设置无效
    # width = right - left + 1
    # height = bottom - top + 1
    rect = wintypes.SMALL_RECT(0, 0, window_width - 1, window_height - 1)  # (left, top, right, bottom)
    windll.kernel32.SetConsoleWindowInfo(hdl, True, byref(rect))


def print_color(style_class, content, end='\n>'):
    printf(FormattedText([('class:%s' % style_class, '%s' % content)]), style=STYLE, end=end)


def read_config_file():
    global APP_PACKAGE_NAME
    global screenshot_hot_key
    if os.path.exists(CONFIG_PATH):
        try:
            cf.read(CONFIG_PATH)
            screenshot_hot_key = cf.get('Config', 'screenshot_hot_key')
            APP_PACKAGE_NAME = cf.get('Config', 'package name')

        except:
            pass
    else:
        pass


def write_config():
    cf.set('Config', 'package name', APP_PACKAGE_NAME)
    cf.set('Config', 'screenshot_hot_key', screenshot_hot_key)
    cf.write(open(CONFIG_PATH, 'w'))


def set_global_hot_key(hot_key):
    global screenshot_hot_key
    screenshot_hot_key = hot_key
    try:
        t = GlobalHotKeys.register(get_hot_key()['key'], get_hot_key()['mod_key'], adb_screenshot)
        write_config()
        refresh()
    except:
        print_color('warning', '热键设置失败!')
        help_set_hot_key()


def set_app_package_name(package_name=None):
    global APP_PACKAGE_NAME
    if package_name:
        APP_PACKAGE_NAME = package_name
        write_config()
        print_color('info', '当前包名设置为：%s' % APP_PACKAGE_NAME, end='\n')
    else:
        APP_PACKAGE_NAME = get_cur_package_name()
        write_config()
        print_color('info', '当前包名设置为：%s' % APP_PACKAGE_NAME, end='\n')
    set_console_title()


def save_app_packge_name(packge_name):
    cf.set('Config', 'package name', packge_name)
    cf.write(open(CONFIG_PATH, 'w'))


def get_hot_key():
    mod_key_dict = {'ALT': 1, 'CONTROL': 2, 'CTRL': 2, 'SHIFT': 4, 'WIN': 8}
    mod_key = screenshot_hot_key.split('+')[0]
    key = screenshot_hot_key.split('+')[1]
    return {'mod_key': mod_key_dict[mod_key], 'key': ord(key)}


def get_app_package_name():
    if APP_PACKAGE_NAME:
        return APP_PACKAGE_NAME
    else:
        return get_cur_package_name()


def device_info(end='\n>'):
    product_model = get_product_model()
    system_version = get_system_version()
    ip = get_ip()
    resolution = get_resolution()
    print_color('info', '设备机型：%s\n系统版本：%s\n分 辨 率：%s\nIP 地 址：%s\n设备序列：%s' % (
                    product_model, system_version, resolution, ip, DEVICE_UDID), end=end)


def package_info(end='\n>'):
    print_color('info', get_app_package_name(), end=end)


def cls():
    subprocess.call('cls', shell=True)
    show_devices()
    show_help()


def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def exit_program():
    """退出应用"""
    os._exit(0)


def open_cur_dir():
    os.startfile(CUR_PATH)


def refresh():
    subprocess.call('cls', shell=True)
    # 重启脚本
    restart_program()


def start_global_key_thread():
    thread = threading.Thread(target=GlobalHotKeys.listen)
    thread.start()


#############################################################################
# 快捷键
#############################################################################
@bindings.add('f1')
def _help(event):  # 使用装饰器定义快捷键，需要传入一个参数
    print_color('tip', 'help', end='\n')
    show_all_help()


@bindings.add('f2')
def _device_info(event):
    print_color('tip', 'device info', end='\n')
    device_info()


@bindings.add('f3')
def _app_start(event):
    if APP_PACKAGE_NAME:
        print_color('tip', 'execute start %s' % APP_PACKAGE_NAME, end='\n')
        app_start(APP_PACKAGE_NAME)
    else:
        print_color('warning', '请先设置应用包名： set app [package name], 不填package name默认设置为当前应用包名')


@bindings.add('f4')
def _app_restart(event):
    app_package = get_app_package_name()
    print_color('tip', 'execute restart %s' % app_package, end='\n')
    app_restart(app_package)


@bindings.add('f5')
def _refresh(event):
    refresh()


@bindings.add('f6')
def _app_stop(event):
    print_color('tip', 'execute kill %s' % get_app_package_name(), end='\n')
    app_force_stop(get_app_package_name())


@bindings.add('f7')
def _app_uninstall(event):
    print_color('tip', 'execute uninstall %s' % get_app_package_name(), end='\n')
    app_uninstall()


@bindings.add('f8')
def _app_clear(event):
    print_color('tip', 'execute clear %s' % get_app_package_name(), end='\n')
    app_clear()


@bindings.add('f9')
def _app_live_log(event):
    logcat_filter(DEVICE_UDID, get_app_package_name())


@bindings.add('f10')
def _screenrecord(event):
    adb_screenrecord()


@bindings.add('f12')
def _open_dir(event):
    open_cur_dir()


@bindings.add('c-a')
def _app_info(event):
    print_color('tip', 'app info', end='\n')
    app_info()


@bindings.add('c-p')
def _package_name(event):
    print_color('tip', 'package name', end='\n')
    package_info()
    # print_color('info', get_app_package_name(), end='\n')


@bindings.add('c-w')
def _switch_connect(event):
    if ':5555' in DEVICE_UDID:
        adb_connect_usb()
    else:
        adb_connect_tcpip()


@bindings.add('s-tab')
def _switch_device(event):
    device = switch_device()
    set_console_title()
    print_color('tip', '已切换至设备： %s' % device)


@bindings.add('escape')
def _exit_program(event):
    print_color('tip', '关闭ADK工具...')
    exit_program()


def get_pid(device_udid, package_name):
    cmd = 'for /f "tokens=2" %i in (\'adb -s {} shell ps ^| findstr /I {}\') do @echo %i'.format(device_udid,
                                                                                                 package_name)
    pid = subprocess.check_output(cmd, shell=True).strip().decode('utf-8')
    return pid.split()


def logcat_filter(device_udid, package_name, live_output=True):
    pid_list = get_pid(device_udid, package_name)
    filter_str = ' '.join(pid_list) + ' ' + package_name
    cmd = 'adb -s {} logcat -v threadtime | findstr "{}"'.format(device_udid, filter_str)
    # subprocess.call(cmd, shell=True)
    if live_output:
        # 在此使用shell=true时，PIPE有缓存，不能实时输出结果，待后研究（pexpect 无缓存输出）
        log = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            try:
                new_line = log.stdout.readline().decode('utf-8')
                print(new_line, end='')  # 打印时不能加其他条件过滤，否则运行时会打印不出，目前未找到好的解决方法
            except:
                break
    else:
        log = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        while True:
            try:
                new_line = log.stdout.readline().decode('utf-8')
                # 02-23 10:31:28.438 10896 11730 I RetrofitLog: retrofitBack = --> END POST (353-byte body)
                tag = str(new_line).split()[4]
                if tag in ['E', 'F']:
                    # set color
                    ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11), 0x0c)
                elif tag in ['W']:
                    ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11), 0x06)
                else:
                    pass
                print(new_line, end='')
                ctypes.windll.kernel32.SetConsoleTextAttribute(ctypes.windll.kernel32.GetStdHandle(-11),
                                                               0x04 | 0x02 | 0x01)
            except:
                break


#############################################################################
# 调用monkey
#############################################################################
def run_monkey(set_param=True):
    if set_param:
        try:
            set_parameter(get_app_package_name())
        except KeyboardInterrupt:
            return None
    monkeyTest.runnerPool(DEVICE_UDID)


event_parameter = """
--pct-touch     0：触摸事件百分比
--pct-motion    1：滑动事件百分比
--pct-pinchzoom 2：缩放事件百分比
--pct-trackball 3：轨迹球事件百分比
--pct-rotation  4：屏幕旋转事件百分比
--pct-nav       5：基本导航事件百分比
--pct-majornav  6：主要导航事件百分比
--pct-syskeys   7：系统事件百分比
--pct-appswitch 8：Activity启动事件百分比
--pct-flip      9：键盘翻转事件百分比
--pct-anyevent  10：其他事件百分比
example:--pct-touch 40 --pct-motion 30 --pct-rotation 20 --pct-appswitch 10
"""


def select_event():
    print_color('info', '1 触摸优先  2 滑动优先  3 屏幕旋转优先  4 Activity切换优先  5 自定义事件\n', end='\n')
    pattern_num = prompt('请选择事件：')
    if pattern_num == '1':
        event = '--pct-touch 50'  # 触摸事件优先
    elif pattern_num == '2':
        event = '--pct-motion 50'  # 滑动事件优先
    elif pattern_num == '3':
        event = '--pct-rotation 50'  # 屏幕旋转优先
    elif pattern_num == '4':
        event = '--pct-appswitch 50'  # Activity启动事件优先
    elif pattern_num == '5':
        print_color('info', event_parameter, end='\n')
        event = prompt('输入自定义参数：')  # 自定义事件
    else:
        event = ''  # 无优先事件
    return event


def set_parameter(pck_name):
    event = select_event()
    seed = prompt('请输入种子数(1-10000)：')
    throttle_time = prompt('请输入事件间隔时间(ms)：')
    count = prompt('请输入事件运行次数：')
    monkey_cmd = 'monkey -p {pck_name} {event} -s {seed} --throttle {throttle_time} --ignore-timeouts ' \
                 '--ignore-crashes --monitor-native-crashes -v -v -v {count} >'.format(pck_name=pck_name,
                                                                                       event=event, seed=seed,
                                                                                       throttle_time=throttle_time,
                                                                                       count=count)
    print_color('warning',
                '\n您设置的命令参数如下(执行大约%s秒)：\n\n%s\n' % (str((float(throttle_time) / 1000) * int(count) / 3), monkey_cmd),
                end='\n')

    cf2 = configparser.ConfigParser()
    cf2.set('DEFAULT', 'cmd', value=monkey_cmd)
    cf2.set('DEFAULT', 'package_name', value=pck_name)
    cf2.set('DEFAULT', 'net', value='wifi')
    fp = open('monkey.ini', 'w+')
    cf2.write(fp)
    fp.close()
    prompt('按回车开始测试，Ctrl+C结束测试！')


auto_completer = WordCompleter([
    'adb',
    'app clear',
    'app info',
    'app logcat',
    'app logcat -l',
    'app restart',
    'app start',
    'app stop',
    'app uninstall',
    'cls',
    'device info',
    'exit',
    'help',
    'input',
    'monkey',
    'monkey -r',
    'open dir',
    'package name',
    'refresh',
    'screenrecord',
    'screencap',
    'set app',
    'set hotkey',
    'switch connect',
], ignore_case=True, sentence=True)

# history = InMemoryHistory()
history = FileHistory('./HistoryFile')


def start_option():
    """
    主循环
    :return:
    """

    while True:
        try:
            cmd = prompt('>', extra_key_bindings=bindings, completer=auto_completer, complete_while_typing=True,
                         history=history, prompt_continuation=True)
        except (KeyboardInterrupt, EOFError):
            start_option()
        if cmd == '':
            pass
        elif cmd == 'app clear':
            _app_clear(None)
        elif cmd == 'app info':
            app_info(end='\n')
        elif cmd == 'app logcat':
            _app_live_log(None)
        elif cmd == 'app logcat -l':
            logcat_filter(DEVICE_UDID, get_app_package_name(), live_output=False)
        elif cmd == 'app restart':
            _app_restart(None)
        elif cmd == 'set app':
            set_app_package_name()
        elif cmd == 'app start':
            _app_start(None)
        elif cmd == 'app stop':
            _app_stop(None)
        elif cmd == 'app uninstall':
            _app_uninstall(None)
        elif cmd == 'cls':
            cls()
        elif cmd == 'device info':
            device_info(end='\n')
        elif cmd == 'exit':
            exit_program()
        elif cmd == 'help':
            show_all_help()
        elif cmd == 'monkey':
            run_monkey(set_param=True)
        elif cmd == 'monkey -r':
            run_monkey(set_param=False)
        elif cmd == 'open dir':
            _open_dir(None)
        elif cmd == 'package name':
            package_info(end='\n')
        elif cmd == 'refresh':
            _refresh(None)
        elif cmd == 'screencap':
            adb_screenshot()
        elif cmd == 'screenrecord':
            _screenrecord(None)
        elif cmd == 'switch connect':
            _switch_connect(None)
        elif cmd == 'set hotkey' or cmd == 'set hotkey -h':
            help_set_hot_key()
        elif cmd.startswith('set app '):
            set_app_package_name(cmd.replace('set app ', ''))
        elif cmd.startswith('set hotkey '):
            set_global_hot_key(cmd.replace('set hotkey ', ''))
        elif cmd.startswith('adb '):
            adb_cmd(cmd)
        elif cmd.endswith('.apk') or cmd.endswith('.apk"'):
            app_install(cmd)
        elif cmd.startswith('input '):
            adb_input_text(cmd)

        else:
            print_color('warning', 'Command not found! Please check it again', end='\n')


#############################################################################
# 帮助
#############################################################################
def show_help():
    strings = ['F1(help)', 'F4(app restart)', 'F7(app uninstall)', 'F10(screenrecord)',
               'F2(device info)', 'F5(refresh)', 'F8(app clear)', 'F12(open dir)',
               'F3(app start)', 'F6(app stop)', 'F9(app logcat)', '%s(screencap)' % screenshot_hot_key]
    keymap_help = []
    i = 1
    for each in strings:
        each = ' ' + each
        if i % 4 == 0:
            keymap_help.append(('class:bg_ansilightgray', '{0:19}'.format(each)))
        else:
            keymap_help.append(('class:bg_ansilightgray', '{0:19}'.format(each)))
        if i % 4 == 0:
            keymap_help.append(('', '\n'))
        else:
            keymap_help.append(('', ' '))
        i += 1
    printf(FormattedText(keymap_help), style=STYLE, end='\n')


def show_all_help():
    strings = [('F1', '常用快捷键帮助'),
               ('F2', '显示设备信息 -机型 -系统版本 -分辨率 -IP'),
               ('F3', '快速启动指定的APP'),
               ('F4', '重启APP'),
               ('F5', '重启并刷新设备列表'),
               ('F6', '结束APP进程'),
               ('F7', '卸载APP'),
               ('F8', '清除APP数据、缓存'),
               ('F9', '查看APP实时日志'),
               ('F10', '录屏'),
               ('F11', '打开文件保存目录'),
               ('F12', '截图并打开（全局）'),
               ('Shift+Tab', '按顺序切换已连接的设备'),
               ('Ctrl+A', '显示当前APP信息'),
               ('Ctrl+W', '切换设备连接方式，USB | WIFI'),
               ('Ctrl+P', '显示APP包名，未指定时默认显示当前APP'),
               ('命令模式：', ''),
               ('adb ', '运行adb命令'),
               ('apk_path.apk', '安装apk，支持http、ftp'),
               ('app clear ', '清除APP数据、缓存'),
               ('app info', '显示APP信息 -包名 -版本号 -包路径'),
               ('app logcat', '查看APP实时日志，加参数 -l 高亮显示'),
               ('app restart', '重启APP'),
               ('app start', '快速启动指定的APP'),
               ('app stop', '结束APP进程'),
               ('app uninstall', '卸载APP'),
               ('cls', '清屏'),
               ('device info', '显示设备信息 -机型 -系统版本 -分辨率 -IP -设备序列号'),
               ('exit', '退出程序'),
               ('help', '显示所有帮助'),
               ('input', '输入文本内容到设备，暂不支持中文'),
               ('monkey', '运行monkey测试，加参数 -r 重复上一次的monkey测试'),
               ('open dir', '打开文件保存的目录'),
               ('package name', '显示APP包名，未指定时默认显示当前APP'),
               ('refresh', '重启并刷新设备列表'),
               ('screencap', '截图'),
               ('screenrecord', '录屏'),
               ('set app[ package_name]', '指定调试APP包名，不填包名，默认为当前APP'),
               ('set hotkey', '设置截图全局热键 set hotkey CTRL+Q; set hotkey ALT+Q'),
               ('switch connect', '切换设备连接方式，USB | WIFI'),
               ]
    print_color('info', '-' * 79, end='\n')
    print_color('info', '  Android Debug Keyboard V1.1.2   @mocobk', end='\n')
    print_color('info', '-' * 79, end='\n')
    for each in strings:
        print_color('info', '  {0:24}{1}'.format(each[0], each[1]), end='\n')
    print_color('info', '-' * 79, end='\n')


def help_set_hot_key():
    print_color('info', 'help: set hotkey CTRL+Q; set hotkey ALT+Q', end='\n')


def main():
    set_console_size(500, 1000, 80, 25)
    start_adb_server()
    show_devices()
    select_device()

    read_config_file()
    set_console_title()
    adb_start_tcpip_mode()
    show_help()
    # 设置全局截图热键，默认ALT + S
    GlobalHotKeys.register(get_hot_key()['key'], get_hot_key()['mod_key'], adb_screenshot)
    start_global_key_thread()
    start_option()


if __name__ == '__main__':
    main()
