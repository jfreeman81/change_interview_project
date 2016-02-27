from twitter import *
from collections import OrderedDict

class Message:
    def __init__(self, message):
        self.user = ""
        self.message = message
        self.dollars = []
        self.cents = []
        self.change = []
        self.amount_found = False
        self.error_message = ""

    def get_user(self):
        return self.user

    def is_change_inquiry(self):
        if 'direct_message' in self.message:
            recipient = self.message['direct_message']['recipient_screen_name']
            if self.message['direct_message']['sender_screen_name'] != recipient:
                self.user = self.message['direct_message']['sender_screen_name']
                self.message = self.message['direct_message']['text']
                self.parse_amount()
                return True
        else:
            return False

    def parse_amount(self):
        string = self.message
        # check that the message contains a dollar sign
        if string.find('$') != -1:
            # split the message at the dollar sign
            dollar_index = string.index('$')
            string = string[dollar_index+1:].split()[0].lstrip()
            # find the dollar and cent values
            for char in string:
                if not char.isdigit():
                    char_index = string.index(char)
                    # check if reached the decimal point, that it's not at the end of the message,
                    # and that the next character is a digit (first cent)
                    if char == '.' and char_index != len(string)-1 and string[char_index+1].isdigit():
                        # append next character (first cent digit) to cents
                        self.cents.append(string[char_index+1])
                        # check if another cent digit follows the one above
                        if char_index != len(string)-2 and string[char_index+2].isdigit():
                            # if so, append it to cents
                            self.cents.append(string[char_index+2])
                        else:
                            # if not, append a zero
                            self.cents.append('0')
                        # finished finding the dollar amount, break out of loop
                        break
                else:
                    # haven't reached the decimal point, space, or end of message yet
                    # append character (digit) to dollars
                    self.dollars.append(char)
        else:
            # dollar sign not found
            self.error_message = "Invalid inquiry. Make sure to precede the dollar amount with a '$'"
            return

        # if dollars were found, join the list into one integer
        if len(self.dollars) > 0:
            self.dollars = int(''.join(self.dollars))
        # else, set dollars to zero
        else:
            self.dollars = 0

        # if cents were found, join the list into one integer
        if len(self.cents) > 0:
            self.cents = int(''.join(self.cents))
        # else, set cents to zero
        else:
            self.cents = 0

        self.amount_found = True
        return

    def dollar_amount_found(self):
        return self.amount_found

    def get_change(self):
        # divide out the number of each bill type - hundreds, twenties, tens, fives, and ones
        dollars_temp = self.dollars
        hundreds = int(dollars_temp/100)
        dollars_temp -= hundreds * 100
        
        twenties = int(dollars_temp/20)
        dollars_temp -= twenties * 20
        
        tens = int(dollars_temp/10)
        dollars_temp -= tens * 10
        
        fives = int(dollars_temp/5)
        dollars_temp -= fives * 5
        
        ones = int(dollars_temp)
        dollars_temp -= ones

        # divide out the amount of each coin type - quarters, dimes, nickels, and pennies
        cents_temp = self.cents
        quarters = int(cents_temp/25)
        cents_temp -= quarters * 25
        
        dimes = int(cents_temp/10)
        cents_temp -= dimes * 10
        
        nickels = int(cents_temp/5)
        cents_temp -= nickels * 5
    
        pennies = int(cents_temp)
        cents_temp -= pennies

        # load the amounts into an ordered dictionary
        # using ordered to simplify constructing the response direct message
        self.change = OrderedDict([
            ('$100',hundreds),
            ('$20',twenties),
            ('$10',tens),
            ('$5',fives),
            ('$1',ones),
            ('Quarters',quarters),
            ('Dimes',dimes),
            ('Nickels',nickels),
            ('Pennies',pennies)])
        return self.change

    def get_change_message(self):
        self.get_change()
        # construct change message with bills/coins amounts that aren't zero
        change_message = "Change for $" + str(self.dollars) + "." + str(self.cents).zfill(2) + ":\n"
        for each in self.change:
            if self.change[each] != 0:
                change_message += each + ': ' + str(self.change[each]) + '\n'
        return change_message

    def get_error_message(self):
        return self.error_message

class TwitterBot:
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        self.con_key = consumer_key
        self.con_secret = consumer_secret
        self.token = access_token
        self.token_secret = access_token_secret
        self.auth = self.set_auth()
        self.twit = Twitter(auth=self.auth)

    def set_auth(self):
        auth = OAuth(
            token=self.token,
            token_secret=self.token_secret,
            consumer_secret=self.con_secret,
            consumer_key=self.con_key
        )
        return auth

    def get_auth(self):
        return self.auth;

    def send_message(self, user, message):
        self.twit.direct_messages.new(
            user=user,
            text=message
        )

def main():
    bot_name = "smith2015_kevin"
    consumer_key = "fj11Yo7eXLCVLjs6jdmTp2WsM"
    consumer_secret = "b0MnvU7LRDLRHG78vrhAPM24G99geOdRakgAiXCF33FJqtqc0Q"
    access_token = "3340282143-L5CHCLYK3Xo5xJJHwj0QXTnPqHGqRLOUsXCnFxt"
    access_token_secret = "pZK3vwLFPdWIzJGu1lM26cQu00IWDhOXL8j1DNdAeUM8i"

    change_bot = TwitterBot(
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret)

    stream = TwitterStream(auth=change_bot.get_auth(), domain="userstream.twitter.com")
    for msg in stream.user():
        dm = Message(msg)
        if dm.is_change_inquiry() and dm.get_user() != bot_name:
            if dm.dollar_amount_found():
                reply = dm.get_change_message()
            else:
                reply = dm.get_error_message()
            change_bot.send_message(dm.get_user(), reply)
    return

if __name__ == "__main__":
    # using while True for if/when the stream ends
    while True:
        main()
