# Installation

## TL;DR

To get a chat ID, visit https://medium.com/@ManHay_Hong/how-to-create-a-telegram-bot-and-send-messages-with-python-4cf314d9fa3e

## Description

Chat with your bot, first.

Open a new tab with your browser, enter https://api.telegram.org/bot&lt;yourtoken&gt;/getUpdates , replace &lt;yourtoken&gt; with your API token, press enter and you should see something like this:


```
{"ok":true,"result":[{"update_id":77xxxxxxx,
 "message":{"message_id":550,"from":{"id":34xxxxxxx,"is_bot":false,"first_name":"Man Hay","last_name":"Hong","username":"manhay212","language_code":"en-HK"}
 ```

Look for “id”, for instance, 34xxxxxxx above is my chat id. Look for yours and put it as your bot_chatID in the code above.

Now you are all set, run the code, and enjoy receiving messages from yourself :)


