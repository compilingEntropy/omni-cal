# omni-cal
#### Generate calendars from tasks in OmniFocus 3

### What's this?
For a long time, I have been frustrated by OmniGroup's decision to remove calendar support from OmniFocus 3. OmniFocus 2 had a [feature](https://support.omnigroup.com/omnifocus-ical-sync/) that would generate a calendar (an .ics file) from your tasks and allow you to subscribe to that calendar. I have missed that feature every day since I moved to OmniFocus 3. In my opinion, task management starts with time management, and time management starts with your calendar. That's why today, I'm bringing back calendar support.

### How can I use this?
This works best if you use a local database or, like me, WebDav. If you use OmniSync or whatever, this won't work yet because there's no integration for that right now. But you can always move your data to WebDav, and that's what I recommend (I use box.com, and the config file will show some defaults for that).
1. Download the files in this repo and fill out your credentials in the `config.ini` file.
2. Run `./calgen.py`

If everything goes well, you will have a file named `omnifocus-reminders-calgen.ics` both in your local directory, and on your WebDav server. You will now be able to import that file to your calendar, or subscribe to it. You can find good tutorials on how to do this by googling "Add a calendar subscription for [platform]". [Here's one I found for iPhone](https://www.macrumors.com/how-to/subscribe-to-calendars-on-iphone-ipad/). If you're using box.com or some other services, you will need to provide credentials.

### What is an encryption passphrase?
This could be the same as your sync password, or it could be different. See https://support.omnigroup.com/of-encryption-faq/

### How do I keep it up-to-date?
I recommend running this script on a cron, every 10 minutes or so, to keep your `.ics` file fresh.

### Tasks don't get added / updated right away
OmniFocus 3 does something weird where it stages commits to its database for a while before writing them. It's usually less than an hour or so.

#### Credits
Shout out to OmniGroup for actually providing a python script on [their repo](https://github.com/omnigroup/OmniGroup) which we use to decrypt the database. This would have been a very long project if I'd have had to reverse engineer and implement that myself, but it's all very well documented and their team definitely deserves props.

-----
Disclaimer: I am not affiliated with OmniGroup and this code is in no way affiliated with their team.
