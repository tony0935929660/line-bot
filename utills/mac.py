import time
import os
from AppKit import NSPasteboard, NSPasteboardTypeTIFF, NSImage
from Foundation import NSAppleScript, NSError

def paste():
    os.system('osascript -e \'tell application "System Events" to keystroke "v" using command down\'')
    time.sleep(0.5)

def copy_image(path):
    if path is None:
        return
    ns_image = NSImage.alloc().initWithContentsOfFile_(path)
    if ns_image is None:
        return
    pasteboard = NSPasteboard.generalPasteboard()
    pasteboard.clearContents()
    pasteboard.setData_forType_(ns_image.TIFFRepresentation(), NSPasteboardTypeTIFF)
    time.sleep(0.2)

def get_position():
    # 先讓 LINE 到前景
    os.system('osascript -e \'tell application "LINE" to activate\'')
    time.sleep(0.5)  # 給一點時間切換

    applescript = '''
    tell application "System Events"
        tell process "LINE"
            set windowPosition to position of window 1
        end tell
    end tell
    '''
    # 直接執行 AppleScript 並處理結果
    result, _ = NSAppleScript.alloc().initWithSource_(applescript).executeAndReturnError_(None)
    
    if result:
        # 提取並返回坐標
        x = int(result.descriptorAtIndex_(1).stringValue()) + 164
        y = int(result.descriptorAtIndex_(2).stringValue()) + 180
        print(f"x = {x}, y = {y}")
        return [x, y]
    else:
        print("Could not get the window position.")
        exit()