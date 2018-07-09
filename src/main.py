#!/usr/bin/env python

# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import print_function

import RPi.GPIO as GPIO
import sys

import subprocess
import argparse
import json
import os.path
import pathlib2 as pathlib

import google.oauth2.credentials

from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from google.assistant.library.device_helpers import register_device
import time

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

WARNING_NOT_REGISTERED = """
    This device is not registered. This means you will not be able to use
    Device Actions or see your device in Assistant Settings. In order to
    register this device follow instructions at:

    https://developers.google.com/assistant/sdk/guides/library/python/embed/register-device
"""


def process_event(event):
    """Pretty prints events.

    Prints all events that occur with two spaces between each new
    conversation and a single space between turns of a conversation.

    Args:
        event(event.Event): The current event to process.
    """
    if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        subprocess.Popen(["omxplayer", "/home/pi/pi_assistant/bin/audio/hangout_message.mp3"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print()

    print(event)

    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and not event.args['with_follow_on_turn']):
        subprocess.Popen(["omxplayer", "/home/pi/pi_assistant/bin/audio/hangout_message.mp3"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print()

    if event.type == EventType.ON_DEVICE_ACTION:
        for command, params in event.actions:
            print('Do command', command, 'with params', str(params))

            # Add the following lines after the existing line above:

            if command == "com.example.commands.BlinkLight":
                number = int(params['number'])
                for i in range(int(number)):
                    print('Device is blinking.')
                    # GPIO.output(25, 1)
                    print("blink1")
                    time.sleep(1)
                    # GPIO.output(25, 0)
                    print("blink2")
                time.sleep(1)
            if command == "action.devices.commands.OnOff":
                print(params)

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--device-model-id', '--device_model_id', type=str,
                        metavar='DEVICE_MODEL_ID', required=False,
                        help='the device model ID registered with Google')
    parser.add_argument('--project-id', '--project_id', type=str,
                        metavar='PROJECT_ID', required=False,
                        help='the project ID used to register this device')
    parser.add_argument('--device-config', type=str,
                        metavar='DEVICE_CONFIG_FILE',
                        default=os.path.join(
                            os.path.expanduser('~/.config'),
                            'googlesamples-assistant',
                            'device_config_library.json'
                        ),
                        help='path to store and read device configuration')
    parser.add_argument('--credentials', type=existing_file,
                        metavar='OAUTH2_CREDENTIALS_FILE',
                        default=os.path.join(
                            os.path.expanduser('~/.config'),
                            'google-oauthlib-tool',
                            'credentials.json'
                        ),
                        help='path to store and read OAuth2 credentials')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + Assistant.__version_str__())

    args = parser.parse_args()
    with open(args.credentials, 'r') as f:
        credentials = google.oauth2.credentials.Credentials(token=None,
                                                            **json.load(f))

    device_model_id = None
    last_device_id = None
    try:
        with open(args.device_config) as f:
            device_config = json.load(f)
            device_model_id = device_config['model_id']
            last_device_id = device_config.get('last_device_id', None)
    except FileNotFoundError:
        pass

    if not args.device_model_id and not device_model_id:
        raise Exception('Missing --device-model-id option')

    # Re-register if "device_model_id" is given by the user and it differs
    # from what we previously registered with.
    should_register = (
            args.device_model_id and args.device_model_id != device_model_id)

    device_model_id = args.device_model_id or device_model_id

    with Assistant(credentials, device_model_id) as assistant:
        events = assistant.start()
        subprocess.Popen(["omxplayer", "/home/pi/pi_assistant/bin/audio/hangout_message.mp3"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        FAN1 = 31
        GPIO.setup(FAN1,GPIO.OUT,initial = 1)
        FAN2 = 35
        GPIO.setup(FAN2,GPIO.OUT, initial = 1)
        LIGHT1 = 37
        GPIO.setup(LIGHT1,GPIO.OUT, initial = 1)
        LIGHT2 = 33
        GPIO.setup(LIGHT2,GPIO.OUT, initial = 1)
        appliance = [FAN1,FAN2,LIGHT1,LIGHT2]
        switch = 1

        
        device_id = assistant.device_id
        print('device_model_id:', device_model_id)
        print('device_id:', device_id + '\n')

        # Re-register if "device_id" is different from the last "device_id":
        if should_register or (device_id != last_device_id):
            if args.project_id:
                register_device(args.project_id, credentials,
                                device_model_id, device_id)
                pathlib.Path(os.path.dirname(args.device_config)).mkdir(
                    exist_ok=True)
                with open(args.device_config, 'w') as f:
                    json.dump({
                        'last_device_id': device_id,
                        'model_id': device_model_id,
                    }, f)
            else:
                print(WARNING_NOT_REGISTERED)

        for event in events:
            process_event(event)
            command = event.args
            try : 
                command = str(command["text"]).lower()
            except:
                pass
            print(command)
            if command is not None :
                if 'turn' in command  or 'switch' in command :
                    assistant.stop_conversation()
                    if 'on' in command :
                        switch = 0
                    elif 'off' in command :
                        switch = 1
                      
                    if 'bed' in command :
                        appliance = [FAN1,LIGHT1]
                    elif 'fan' in command :
                        if ('one' in command) or ('1' in command):
                            appliance = FAN1
                            
                        if ('two' in command) or ('2' in command):
                            appliance = FAN2
                     
                    elif 'light' in command :
                        if ('one' in command) or ('1' in command):
                            appliance = LIGHT1
                            
                        if ('two' in command) or ('2' in command):
                            appliance = LIGHT2
                    GPIO.output(appliance,switch)
                    
            appliance = [FAN1,FAN2,LIGHT1,LIGHT2]


if __name__ == '__main__':
    main()
