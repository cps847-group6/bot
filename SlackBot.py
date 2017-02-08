import os
import time
import re
import urllib
import urllib.request
import json
import spellcheck
from slackclient import SlackClient


# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
OWAPI_KEY = os.environ.get("OWAPI_KEY")
# constants
AT_BOT = "<@" + BOT_ID + ">"
ECHOCMD = "!echo"
WEATHERCMD = "!weather"
# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. I'm currently a basic bot :robot_face:. Available commands are \"!echo\" and \"!weather [city]\"."
    if command.startswith(ECHOCMD):
        response = re.sub('!echo','',command)
        slack_client.api_call("chat.postMessage", channel=channel,
                              text=response, as_user=True)
    if command.startswith(WEATHERCMD):
        city_province = re.sub('!weather','',command)
        try:
            url = "http://api.openweathermap.org/data/2.5/weather?q={0}&appid={1}&units=metric".format(city_province,OWAPI_KEY)
            resp = urllib.request.urlopen(url.replace(" ",""))
            str_response = resp.read().decode('utf-8')
            data = json.loads(str_response)
            location = data["name"]
            temperature = data["main"]["temp"]
            forecast = data["weather"][0]["main"]
            """
            Openweathermap tries its best to figure out what the user meant if they mispelled something. To use spellcheck.py replace "location" with following line of code:
            spellcheck.correct(city_province).capitalize()          
              
            """
            response = "The weather in {0} is {1} degrees Celcius. The forecast is {2}.".format(location,int(round(temperature)),forecast)
            slack_client.api_call("chat.postMessage", channel=channel,
                                  text=response, as_user=True)
        except urllib.request.HTTPError as err:
            if err.code == 404:
                slack_client.api_call("chat.postMessage", channel=channel,
                                      text="Sorry I could not find the weather for {0}!".format(city_province.capitalize()), as_user=True)
                
            elif err.code == 502:
                slack_client.api_call("chat.postMessage", channel=channel,
                          text="Temporary server error. Please try again.".format(city_province), as_user=True)



def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
