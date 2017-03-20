# -*- coding: utf-8 -*-
import sys
import os
import json
import requests
import roybot
import util as u # some local utility functions
import logging
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    global c
    # endpoint for processing incoming messaging events

    data = request.get_json()
    logger.debug(data)

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                    if 'attachments' in messaging_event["message"]:
                        if len(messaging_event["message"]["attachments"]) > 0:
                            attachment = messaging_event["message"]["attachments"][0]                   
                            send_message(sender_id, 'I do not know how to handle that attachment type :/')
                    else:
                        message_text = messaging_event["message"]["text"]  # the message's text

                        # process msg
                        c.check_input(message_text, True, True)
                        if 'http' in c.msg_output:
                            send_image(sender_id, c.msg_output)
                        else:
                            if c.msg_output.strip() == '':
                                c.msg_output == 'I\'m unsure what to say to that! :/'
                            send_message(sender_id, c.msg_output)
                        c.msg_output = ''

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    message_data = {
                "text": message_text
    }
    message_data_summmary = message_text
    send_generic(recipient_id=recipient_id, message_data=message_data, message_data_summmary=message_data_summmary, message_type='text')


def send_image(recipient_id, image_source):

    message_data = {
        "attachment": {
            "type": "image",
            "payload": {
                "url": image_source,
                "is_reusable": "false"
            }
        }
    }
    message_data_summmary = image_source
    send_generic(recipient_id=recipient_id, message_data=message_data, message_data_summmary=message_data_summmary, message_type='image')


def send_generic(recipient_id, message_data, message_data_summmary, message_type):

    try:
        logger.info("sending {type} to {recipient}: {data_summary}".format(type=message_type, recipient=recipient_id, data_summary=message_data_summmary))
    except UnicodeEncodeError:
        logger.info("sending {type} to {recipient}: {data_summary}".format(type=message_type, recipient=recipient_id, data_summary=message_data_summmary.encode('utf-8')))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": message_data
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        logger.info(r.status_code)
        logger.info(r.text)


logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)

global c
ch_in = 'screen'  # 'email' OR 'screen' OR 'online'
ch_out = {'facebook': True, 'email': False, 'online': False, 'screen': True}
# c = roybot.Core(channels_out = ch_out, channel_in = ch_in, loglvl = loglvl, config_override = config)
c = roybot.Core(channels_out = ch_out, channel_in = ch_in)
logger.info('Botname is ' + c.botname)

if __name__ == '__main__':
    app.run(debug=True)
